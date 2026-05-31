# YDLIDAR Tmini Plus + SLAM Integration

**Target**: June 12 — LIDAR arrives.
**Scope**: Mount → driver → slam_toolbox → explore_and_map mission → Nav2.

## Prerequisites

- Yahboom Raspbot v2 with Docker container `yahboom_ros2_final` running ROS 2 Humble
- SSH access to the Pi (`YAHBOOM_IP`)
- USB port free on the Pi (Tmini Plus uses USB-to-serial)

## Phase 1 — YDLIDAR Driver (Day 1)

```bash
# 1. SSH into the Pi, enter the container
docker exec -it yahboom_ros2_final bash

# 2. In container: install ydlidar ROS2 driver
cd /root/yahboomcar_ws/src
git clone https://github.com/YahboomTechnology/ydlidar_ros2_driver.git
cd /root/yahboomcar_ws
colcon build --packages-select ydlidar_ros2_driver
source install/setup.bash
```

### Verify

```bash
# Outside container on the Pi:
ls /dev/ttyUSB*          # Should show /dev/ttyUSB0 after plugging in the LIDAR

# Inside container — launch the driver node
ros2 run ydlidar_ros2_driver ydlidar_ros2_driver_node --ros-args \
  -p port:=/dev/ttyUSB0 \
  -p frame_id:=laser_frame

# Separate terminal — verify /scan is publishing
ros2 topic echo /scan --once
```

Expected: one LaserScan message with ~360 range readings.

### Device Rules (persistent port name)

On the Pi (outside container), create `/etc/udev/rules.d/ydlidar.rules`:

```
KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", SYMLINK+="ydlidar"
```

Then `sudo udevadm trigger` — LIDAR will always be at `/dev/ydlidar`.

### Launch Integration

Add a `ydlidar.launch.py` to the yahboomcar_bringup package:

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ydlidar_ros2_driver',
            executable='ydlidar_ros2_driver_node',
            name='ydlidar_driver',
            parameters=[{
                'port': '/dev/ydlidar',
                'frame_id': 'laser_frame',
                'angle_min': -3.14159,
                'angle_max': 3.14159,
                'range_min': 0.05,
                'range_max': 12.0,
            }],
            output='screen',
        ),
    ])
```

Then edit the main `yahboomcar_bringup.launch.py` to `include` this. Or just run it separately — the bringup launch already has the Mcnamu driver.

## Phase 2 — slam_toolbox (Day 2)

```bash
# Inside the container
apt update
apt install -y ros-humble-slam-toolbox ros-humble-nav2-map-server

# Verify
ros2 run slam_toolbox async_slam_toolbox_node --help
```

### TF Tree

`slam_toolbox` needs:
```
map ← odom ← base_footprint ← laser_frame
```

The Mcnamu driver publishes `odom→base_footprint` already (wheel odometry). The YDLIDAR driver publishes with `frame_id:=laser_frame`. We need a static transform `base_footprint→laser_frame`:

```bash
ros2 run tf2_ros static_transform_publisher \
  0 0 0.15 0 0 0 \
  base_footprint laser_frame
```

This can go in the bringup launch or in a separate `tf.launch.py`.

### Verify

```
ros2 run tf2_echo base_footprint laser_frame    # Should show ~0.15m offset
ros2 run tf2_echo odom base_footprint           # Should update as robot moves
```

## Phase 3 — Launch slam_toolbox async

```bash
ros2 run slam_toolbox async_slam_toolbox_node --ros-args \
  -p odom_frame:=odom \
  -p base_frame:=base_footprint \
  -p map_frame:=map \
  -p use_sim_time:=false \
  -p resolution:=0.05 \
  -p publish_period:=2.0
```

The `explore_and_map` mission in yahboom-mcp already runs this exact command via SSH (see `missions.py:_explore_and_map_mission` step 2).

### Map save (for later use with Nav2)

```bash
ros2 run nav2_map_server map_saver_cli \
  -f /home/pi/maps/apartment \
  --ros-args -p map_subscribe_transient_local:=true
```

Produces: `apartment.pgm` (occupancy grid image) + `apartment.yaml` (ROS2 nav2_map_server config).

## Phase 4 — RViz Verification (Desktop)

RViz runs on your **workstation** (not the Pi — it's a GUI):

```bash
# Windows: install ROS2 Humble desktop on WSL or a VM
# Or use Docker:
docker run -it --rm \
  -e DISPLAY=host.docker.internal:0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  osrf/ros:humble-desktop \
  rviz2
```

Then:
1. Set Fixed Frame: `map`
2. Add → `RobotModel` (not applicable — we don't have a URDF)
3. Add → `LaserScan` topic: `/scan`
4. Add → `Map` topic: `/map` (occupancy grid from slam_toolbox)
5. Add → `TF` (to see the transform tree)
6. Drive Boomy with `explore_and_map` → watch the map build in real-time

## Phase 5 — Nav2 Autonomous Navigation (Future)

```bash
apt install ros-humble-navigation2 ros-humble-nav2-bringup
```

This gets complex. It needs:
- Costmap config (inflation radius, footprint)
- Global planner (`NavFn` or `SmacPlanner`)
- Local planner (`RegulatedPurePursuit` or `DWB`)
- AMCL for relocalization on the saved map

Not needed for June 12 — map-building alone covers your stated use case ("map the apartment").

## Quick Reference

| Step | Command | Expected |
|------|---------|----------|
| LIDAR driver | `ros2 run ydlidar_ros2_driver ydlidar_ros2_driver_node` | `/scan` publishes |
| TF base→laser | `ros2 run tf2_ros static_transform_publisher 0 0 0.15 base_footprint laser_frame` | `tf2_echo` shows transform |
| SLAM | `ros2 run slam_toolbox async_slam_toolbox_node` | `/map` publishes occupancy grid |
| Save map | `ros2 run nav2_map_server map_saver_cli -f /home/pi/maps/apartment` | `.pgm` + `.yaml` |

## MCP-Side (already done)

- `missions.py:_lidar_available()` — detects `/scan` presence
- `missions.py:_sense_obstacle()` — uses LIDAR front sectors when available (graceful fallback to ultrasonic)
- `missions.py:_explore_and_map_mission()` — runs the full pipeline: LIDAR check → SSH launch slam_toolbox → boustrophedon drive → save map → return
- `portmanteau.py` — routes `explore`/`explore_and_map` to the mission runner
