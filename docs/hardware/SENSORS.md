# Yahboom G1 — Sensor Integration Reference

**Timestamp**: 2026-03-04  
**Platform**: Yahboom G1 (ROSMASTER series, Mecanum wheel, Raspberry Pi 5)  
**Server**: `yahboom-mcp` — ROS 2 Humble + ROSBridge WebSocket (port 9090)

---

## 1. Sensor Inventory

### 1.1 IMU — 9-Axis Inertial Measurement Unit

| Property | Value |
|---|---|
| **IC** | MPU-9250 (or ICM-42670 depending on board revision) |
| **Location** | Onboard ROSMASTER control board |
| **Interface** | I²C → Raspberry Pi → ROS 2 |
| **ROS topic** | `/imu/data` |
| **ROS message type** | `sensor_msgs/Imu` |
| **Publish rate** | ~100 Hz |

**Raw fields published by `/imu/data`:**

```
orientation {x, y, z, w}         — fused quaternion (from onboard DMP)
angular_velocity {x, y, z}       — gyroscope, rad/s
linear_acceleration {x, y, z}    — accelerometer, m/s²
orientation_covariance[9]        — 3×3 covariance matrix
angular_velocity_covariance[9]
linear_acceleration_covariance[9]
```

**Derived values (computed by `yahboom-mcp`):**

The raw quaternion is converted to Euler angles in `core/ros2_bridge.py → _quat_to_euler_deg()`:

| Derived field | Source | Unit |
|---|---|---|
| `heading` | yaw normalised to 0–360° | degrees |
| `yaw` | rotation around Z-axis, −180–+180° | degrees |
| `pitch` | nose up/down | degrees |
| `roll` | side tilt | degrees |

**Integration status**: Live — subscribed in `_setup_topics()`, cached in `bridge.state["imu"]`, exposed via:
- `GET /api/v1/telemetry` → `imu` object
- MCP tool `yahboom(action='read_imu')`

---

### 1.2 Odometry — Wheel Encoder Dead Reckoning

| Property | Value |
|---|---|
| **Source** | Wheel encoders on each of the 4 mecanum wheels |
| **ROS topic** | `/odom` |
| **ROS message type** | `nav_msgs/Odometry` |
| **Publish rate** | ~50 Hz |

**Fields:**

```
pose.pose.position {x, y, z}        — accumulated distance from start (metres)
pose.pose.orientation {x, y, z, w}  — quaternion heading
twist.twist.linear {x, y, z}        — current velocity (m/s)
twist.twist.angular {x, y, z}       — current turn rate (rad/s)
```

**Derived values (computed by `yahboom-mcp`):**

The callback `_odom_callback()` extracts:
- `position.{x, y, z}` in metres (rounded to 4 dp)
- `heading` (degrees, from orientation quaternion)
- `velocity.linear` (m/s, from twist.linear.x)
- `velocity.angular` (rad/s, from twist.angular.z)

**Limitations**: Odometry is *dead reckoning* — errors accumulate over time due to wheel slip and encoder tolerances. On a hard floor with good traction, drift is ~2–5 cm per metre of travel. Fusing with LIDAR (SLAM) corrects this.

**Integration status**: Live — subscribed in `_setup_topics()`, cached in `bridge.state["odom"]`, exposed via:
- `GET /api/v1/telemetry` → `velocity`, `position`
- `yahboom(action='read_odom')`

---

### 1.3 Battery — 12V LiPo Pack

| Property | Value |
|---|---|
| **Source** | Voltage divider on ROSMASTER board |
| **ROS topic** | `/battery_state` |
| **ROS message type** | `sensor_msgs/BatteryState` |
| **Publish rate** | ~1 Hz |

**Fields:**

```
voltage             — pack voltage (V)
percentage          — ROS sends 0.0–1.0 (0%–100%)
power_supply_status — 0=unknown, 1=charging, 2=discharging, 3=not-charging, 4=full
```

> [!NOTE]
> `percentage` in the raw ROS message is 0.0→1.0. The `_battery_callback()` in `ros2_bridge.py` multiplies by 100 to return 0–100%.

**Low battery threshold**: < 20% — the dashboard battery bar turns red below this level.

**Integration status**: Live — subscribed in `_setup_topics()`, cached in `bridge.state["battery"]`, exposed via:
- `GET /api/v1/telemetry` → `battery`, `voltage`
- `yahboom(action='read_battery')`

---

### 1.4 LIDAR — 360° Laser Scanner *(optional module)*

> [!IMPORTANT]
> LIDAR is an **optional add-on** for the G1. The base unit does not include it.
> The `yahboom-mcp` server subscribes to `/scan` but handles the case where the topic is absent — `scan` fields in telemetry will be `null` when no LIDAR is fitted.

**Compatible modules:**

| Module | Price (approx.) | Range | Scan rate | ROS 2 driver |
|---|---|---|---|---|
| YDLIDAR X2 | €45 | 8 m | 3000 pts/s | `ydlidar_ros2_driver` |
| YDLIDAR X2L | €38 | 6 m | 2000 pts/s | `ydlidar_ros2_driver` |
| YDLIDAR X4 | €75 | 10 m | 5000 pts/s | `ydlidar_ros2_driver` |
| RPLidar A1M8 | €90 | 12 m | 8000 pts/s | `rplidar_ros` |

The YDLIDAR X2/X4 is the natural choice — Yahboom's own ROSMASTER X3 uses YDLIDAR, so the `automaticaddison/yahboom_rosmaster` launch files work out-of-the-box.

**Installing the YDLIDAR X2 driver (on the Raspberry Pi):**

```bash
sudo apt install ros-humble-ydlidar-ros2-driver
# Connect the LIDAR via USB, then:
ros2 launch ydlidar_ros2_driver ydlidar_launch.py
```

**ROS topic**: `/scan`  
**ROS message type**: `sensor_msgs/LaserScan`

**Key fields:**

```
angle_min / angle_max       — scan arc (typically -π to +π = full 360°)
angle_increment             — angular resolution per step (rad)
range_min / range_max       — valid distance window (metres)
ranges[]                    — array of distances, one per angle step
                              NaN or Inf = no return (beyond range / transparent surface)
intensities[]               — signal strength per step (not always populated)
```

**Processing in `yahboom-mcp`** (`_scan_callback()` + `_scan_to_obstacle_summary()`):

The full `ranges[]` array (8000+ points) is distilled into an 8-sector obstacle map:

```
front | front_right | right | back_right | back | back_left | left | front_left
```

Each sector reports the **nearest detection** within that 45° arc (in metres, or `null` if clear/no data).

**Exposed fields in `/api/v1/telemetry`:**

```json
"scan": {
  "nearest_m":  0.42,       // global nearest obstacle across all sectors
  "obstacles": {
    "front":       0.42,
    "front_right": 1.10,
    "right":       null,    // null = no return within range_max
    "back_right":  null,
    "back":        null,
    "back_left":   1.85,
    "left":        null,
    "front_left":  0.67
  }
}
```

The dashboard Safety panel shows `nearest_m` and turns the text **red** when < 0.4 m.

**Hardware connection** (Raspberry Pi):
1. Plug LIDAR USB cable into any Pi USB-A port
2. Add udev rule (usually done by the driver package): `SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", MODE="0666"`
3. Mount LIDAR on the robot top plate — M3 holes are pre-drilled on the ROSMASTER chassis

---

### 1.5 Camera — MJPEG Video Stream

| Property | Value |
|---|---|
| **Source** | USB webcam or RPi Camera Module on forward chassis |
| **ROS topic** | `/camera/image_raw` *(optional)* |
| **MCP endpoint** | `GET http://localhost:10792/stream` — MJPEG |
| **Dashboard** | Camera feed panel in Mission Control |

The `VideoBridge` class in `core/video_bridge.py` connects to the ROS image topic and re-streams it as MJPEG to the dashboard. When `VideoBridge` is not active (no camera connected), the `/stream` endpoint returns an error and the dashboard feed shows a blank `<img>` element.

---

## 2. Data Flow Architecture

```
Robot Hardware
      │
ROSMASTER Board (onboard)
      │── IMU (MPU-9250)   → /imu/data          100 Hz
      │── Battery Monitor  → /battery_state        1 Hz
      │── Wheel Encoders   → /odom               50 Hz
      │
Raspberry Pi 5
      │── YDLIDAR (USB)    → /scan              varies
      │── Camera (USB/CSI) → /camera/image_raw    30 Hz
      │
ROSBridge WebSocket (port 9090)
      │
ROS2Bridge (core/ros2_bridge.py)
      │── Subscribes to all topics via roslibpy
      │── Caches latest message in bridge.state{}
      │── Converts quaternion → Euler
      │── Summarises LaserScan → 8 obstacle sectors
      │
FastAPI (port 10792)
      │── GET /api/v1/telemetry  → full snapshot JSON (2 s polling)
      │── GET /api/v1/health     → connection status
      │── GET /stream            → MJPEG video
      │── POST /api/v1/control/move → cmd_vel publish
      │
Vite Dashboard (port 10793)
      └── Mission Control page polls /telemetry every 2 s
          Displays: battery %, voltage, heading, pitch, roll,
                    accel xyz, position xyz, nearest obstacle,
                    obstacle sector map (Safety panel)
```

---

## 3. Simulated Fallback (offline development)

When the ROSBridge is not reachable, `/api/v1/telemetry` returns plausible static values tagged with `"source": "simulated"`. The dashboard shows a `[simulated]` label below the battery percentage. All null-safe code paths render `—` for missing live values.

---

## 4. MCP Tool Reference

| Tool call | Returns |
|---|---|
| `yahboom(action='read_imu')` | heading, pitch, roll, accel, gyro |
| `yahboom(action='read_battery')` | voltage, percentage, power_supply_status |
| `yahboom(action='read_odom')` | position {x,y,z}, velocity {linear,angular}, heading |
| `yahboom(action='read_lidar')` | nearest_m, obstacles per sector, num_points |
| `yahboom(action='read_all')` | Full snapshot of all sensors above |
| `yahboom(action='health')` | bridge connected, battery % |
| `yahboom(action='move', linear=0.3, angular=0.0)` | Sends Twist to /cmd_vel |

---

## 5. Wiring Notes for LIDAR Add-On (YDLIDAR X2)

```
YDLIDAR X2
  └── USB-A → Raspberry Pi USB port
  └── Powered by USB (5V, ~400 mA)
  └── Mounts on top plate with M3 × 4 screws
  └── Connector clearance: cable routes through chassis slot near Pi

Launch on the Pi:
  ros2 launch ydlidar_ros2_driver ydlidar_launch.py \
    serial_port:=/dev/ttyUSB0 \
    serial_baudrate:=115200

Verify publishing:
  ros2 topic hz /scan    # should show ~5–8 Hz for X2
  ros2 topic echo /scan  # check ranges[] are non-Inf
```

> [!TIP]
> If `/scan` always returns Inf, check that the LIDAR motor is spinning (audible hum). The X2 has a non-default baud rate on some firmware versions — try `115200` then `128000`.
