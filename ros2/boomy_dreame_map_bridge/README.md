# boomy_dreame_map_bridge

ROS 2 **Humble** (Python) node: **GET** the JSON from [dreame-mcp](https://github.com/sandraschi/dreame-mcp) **`/api/v1/map`**, take the **base64 PNG** (`image` field), and publish a **`nav_msgs/OccupancyGrid`** for **Nav2** (static layer / planning context).

Boomy (Raspbot v2) can add an **MS200** later for **`/scan`**; this node does **not** replace LiDAR — it adds a **floor plan** from the Dreame vacuum (different robot, see alignment below).

## Prereqs

- **dreame-mcp** running with a successful **rendered** map (JSON must include **`image`**; `raw_b64` alone is not converted here).
- **On the robot**: `sudo apt install python3-pil` (Pillow) if not already there.
- Network: the Pi (or WSL) must **reach** the host that runs dreame-mcp: use **`http://<pc-lan-ip>:10894/api/v1/map`**, not `127.0.0.1`, when the node runs on the Pi.

## Build (Pi or dev machine with ROS 2)

```bash
cd ~/yahboomcar_ws/src
ln -sf /path/to/yahboom-mcp/ros2/boomy_dreame_map_bridge .
cd ~/yahboomcar_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select boomy_dreame_map_bridge
source install/setup.bash
```

## Run

```bash
# Override URL to your dreame-mcp (required on the Pi: use PC IP)
ros2 run boomy_dreame_map_bridge dreame_map_publisher --ros-args \
  -p dreame_map_url:="http://192.168.1.10:10894/api/v1/map"
```

Or:

```bash
ros2 launch boomy_dreame_map_bridge dreame_map_bridge.launch.py
```

(After editing the `dreame_map_url` in the launch file, or add a param override in your own launch.)

## Nav2

- Publishes **`/dreame_floorplan` by default** (QoS: transient local, like `map_server`). In Nav2 **global costmap** static layer, set the **topic** to **`/dreame_floorplan`**, or remap the topic to **`/map`** if you do **not** use another map source.
- **No automatic alignment** between the Dreame drawing and the Raspbot. Tune **`map_origin_x` / `map_origin_y` / `map_origin_yaw_deg`**, **`map_resolution`**, and **`flip_image_y`** so the plan matches your odom/robot frame once MS200 + localization are in place.
- **Optional** **`publish_map_to_odom_tf: true`**: static identity `map` → `odom` (demo only; turn **off** when **AMCL** or another localizer provides **`map`→`odom`**).
- For **Rviz**: add **Map** display, topic **`/dreame_floorplan`**, **Fixed Frame** `map` (or your `map_frame` param).

## Parameters (summary)

| Parameter | Default | Note |
|-----------|---------|------|
| `dreame_map_url` | `http://127.0.0.1:10894/api/v1/map` | Must point to dreame-mcp root host from this machine |
| `http_timeout_sec` | 25.0 | GET timeout |
| `update_period_sec` | 0.0 | If `>0`, refetch on that interval (seconds) |
| `map_topic` | `/dreame_floorplan` | OccupancyGrid topic |
| `map_frame` | `map` | `OccupancyGrid.header.frame_id` |
| `map_resolution` | 0.05 | Metres / cell (match your alignment choice) |
| `map_origin_x` … | 0.0 | World origin of cell (0,0) in metres |
| `map_origin_yaw_deg` | 0.0 | Origin rotation |
| `image_free_pixel_gte` | 200 | Grayscale ≥ this → free |
| `image_occupied_pixel_lte` | 50 | Grayscale ≤ this → occupied; between → unknown |
| `flip_image_y` | `true` | Image row order vs `nav_msgs` |
| `publish_map_to_odom_tf` | `false` | Static TF `map`→`odom` (identity) |

## See also

- dreame-mcp: `docs/MAP_AND_ROBOTICS.md`
- yahboom-mcp: `docs/fleet/DREAME_STANDALONE_RECOMMENDATION.md`, `DREAME_MAP_URL` (MCP HTTP, separate from this ROS node)
