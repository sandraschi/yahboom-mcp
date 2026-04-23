# ROS 2 Bridge — Complete Reference

**Platform:** Yahboom Raspbot v2 (Boomy)  
**Date:** 2026-04-14  
**Tags:** `[yahboom-mcp, rosbridge, ros2, roslibpy, architecture]`  
**Source:** `src/yahboom_mcp/core/ros2_bridge.py`  
**Related:** [`ROSBRIDGE_AT_BOOT.md`](../ops/ROSBRIDGE_AT_BOOT.md) · [`SENSORS.md`](SENSORS.md)

---

## 1. What the Bridge Is

`ROS2Bridge` is the single class in `core/ros2_bridge.py` that mediates between the `yahboom-mcp` FastAPI/FastMCP server (running on Goliath, port 10892) and the ROS 2 graph running on Boomy's Raspberry Pi 5. It is not a generic ROS bridge — it is purpose-built for the Raspbot v2 topic set.

```
Goliath (Windows)
  └── yahboom-mcp FastAPI server
        └── ROS2Bridge (roslibpy client)
              ↕ WebSocket ws://192.168.1.11:9090
        Raspberry Pi 5
              └── rosbridge_suite (WebSocket server, port 9090)
                    ↕ DDS / ROS 2 intraprocess
              └── ROS 2 Humble nodes
                    ├── Mcnamu_driver (ROSMASTER board driver)
                    ├── camera node
                    └── sensor nodes
```

The bridge does **not** SSH into the Pi for normal operation. SSH is used only for display (luma.oled) and TTS (espeak-ng/Piper) operations — separate facilities documented in [`VOICE_AUDIO.md`](VOICE_AUDIO.md).

---

## 2. Terminology: ROS 2 vs rosbridge (software) vs USB hardware under the Pi

Three different layers are easy to merge in conversation:

| Name | Meaning |
|------|--------|
| **ROS 2 graph** | DDS nodes on the Pi (drivers, sensors, `cmd_vel`, etc.) — often inside **Docker**. |
| **rosbridge_suite** | **Python/ROS packages** exposing a **WebSocket** (e.g. port **9090**) so non-ROS programs (`roslibpy` on Goliath) can publish/subscribe. This is **not** a PCB. |
| **Lower motion/sensor hardware** | Yahboom stack: a **controller tier physically under** the Raspberry Pi, linked by **USB** (`/dev/ttyUSB*`, etc.). It participates in ROS 2 through onboard drivers. People sometimes say “rosbridge board” — that is **misleading**; the WebSocket server is **software on the Pi**. Prefer **ROSMASTER / driver board** vs **rosbridge_suite**. |

**Why it matters:** if Goliath cannot ping the network path to the Pi, **both** SSH and WebSocket fail — no amount of dashboard clicking starts Docker or the USB-attached controller. After power and link are good, **rosbridge** must be running for `ROS2Bridge`, and **ROS bringup** must be running for topics to exist.

**Rosbridge does not implement Micro-ROS.** Micro-ROS is **MCU firmware + agent** for the **Pi ↔ Rosmaster board** serial link; rosbridge is **JSON/WebSocket** for the **PC ↔ Pi** link. Full definitions: **[RASPBOT_V2_HARDWARE_STACK.md §1](RASPBOT_V2_HARDWARE_STACK.md#1-terms-and-layers-read-this-first)** and **§9.3**.

Operator starter (boot order, systemd scripts, webapp buttons): [`../ops/STARTUP_AND_BRINGUP.md`](../ops/STARTUP_AND_BRINGUP.md).

---

## 3. Connection Lifecycle

### 2.1 Startup (lifespan in `server.py`)

On MCP server startup, the lifespan handler:

1. Reads `YAHBOOM_ROBOT_IP` env var (default `192.168.1.11`) and `YAHBOOM_ROSBRIDGE_PORT` (default `9090`).
2. Calls `bridge.connect()`.
3. On success, calls `_setup_topics()` which creates and advertises all publisher topics and subscribes all sensor topics.
4. Stores the bridge in `_state["bridge"]`.

### 2.2 TCP Preflight

Before creating the roslibpy client, `_tcp_reachable(host, port, timeout=0.8)` does a raw TCP connect to verify the Pi is up and rosbridge is listening. This prevents roslibpy from hanging for 30+ seconds on connection attempts to an offline robot.

If the primary IP is unreachable and a `YAHBOOM_FALLBACK_IP` is set, the bridge tries the fallback. Useful when the robot switches between home WiFi and hotspot.

### 2.3 `connect()` method

```python
bridge = ROS2Bridge(host="192.168.1.11", port=9090, fallback_host="192.168.0.11")
await bridge.connect()
```

- Creates `roslibpy.Ros` instance.
- Registers `on_ready` callback that calls `_setup_topics()`.
- Registers `on_error` and `on_close` callbacks for reconnect logic.
- Calls `ros.run()` in a thread (roslibpy is synchronous internally, run in executor).
- Waits up to 5 seconds for the `on_ready` event; returns False if timeout.

### 2.4 Reconnect

The bridge does not auto-reconnect by default. If `on_reconnect_callback` is set (done in lifespan), the server will attempt to call `connect()` again after a 10-second delay when the connection drops. The dashboard header polls `/api/v1/health` every 5 seconds and shows the amber "Link Lost" state when `bridge.connected` is False.

---

## 4. State Cache

All sensor data is cached in `bridge.state` — a plain dict updated by ROS callbacks. The `/api/v1/telemetry` endpoint returns a snapshot of this dict (no blocking ROS call). Freshness is indicated by `last_update` (Unix timestamp).

```python
bridge.state = {
    "imu":          {},   # → dict from /imu/data callback
    "odom":         {},   # → dict from /odom callback
    "battery":      {},   # → dict from /battery_state callback
    "scan":         {},   # → dict from /scan callback (obstacle summary + raw nearest)
    "ir_proximity": None, # → list[float] from /sonar (when connected)
    "line_sensors": None, # → list[int] from /line_sensor (when connected)
    "last_image":   None, # → bytes from /image_raw/compressed (when camera active)
    "last_update":  0,    # → float Unix timestamp of last any-topic update
}
```

---

## 5. Topic Map

### 4.1 Subscriptions (bridge reads from ROS)

| ROS Topic | ROS Message Type | Callback | `bridge.state` key |
|---|---|---|---|
| `/imu/data` | `sensor_msgs/Imu` | `_imu_callback` | `imu` |
| `/battery_state` | `sensor_msgs/BatteryState` | `_battery_callback` | `battery` |
| `/odom` | `nav_msgs/Odometry` | `_odom_callback` | `odom` |
| `/scan` | `sensor_msgs/LaserScan` | `_scan_callback` | `scan` |
| `/sonar` | `sensor_msgs/Range` | `_sonar_callback` | `ir_proximity` |
| `/line_sensor` | `std_msgs/Int32MultiArray` | `_line_callback` | `line_sensors` |
| `/button` | `std_msgs/Bool` | `_button_callback` | (event only) |
| `/image_raw/compressed` | `sensor_msgs/CompressedImage` | `_image_callback` | `last_image` |

Topic names for IMU, ultrasonic, and line sensor can be overridden via environment variables (see §7).

### 4.2 Publishers (bridge writes to ROS)

| ROS Topic | ROS Message Type | Purpose | Advertised on connect |
|---|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | Drive motors (mecanum) | Yes |
| `/rgblight` | `std_msgs/Int32MultiArray` | LED lightstrip RGB value | Yes |
| `/servo` | `yahboomcar_msgs/msg/ServoControl` | PTZ camera servos | Yes |

> [!IMPORTANT]
> `.advertise()` must be called on publisher topics before `.publish()`. Without it, roslibpy silently drops publishes. All three publishers now advertise in `_setup_topics()`. This was a bug that caused lightstrip and servo commands to have no effect until fixed.

---

## 6. Sensor Callback Details

### 5.1 IMU (`_imu_callback`)

Raw `sensor_msgs/Imu` from the MPU-9250 on the ROSMASTER board. The callback:

- Extracts `linear_acceleration` {x, y, z} (m/s²)
- Extracts `angular_velocity` {x, y, z} (rad/s)
- Calls `_quat_valid()` — if the quaternion is all-zero (driver marks orientation as unusable on some firmware revisions), falls back to `_accel_tilt_deg()` to estimate pitch/roll from the gravity vector
- If quaternion valid, calls `_quat_to_euler_deg()` for roll/pitch/yaw/heading
- Rounds all values to 2 dp

Stored in `bridge.state["imu"]`:
```json
{
  "roll": 1.23,
  "pitch": 0.45,
  "yaw": -12.3,
  "heading": 347.7,
  "accel": {"x": 0.1, "y": 0.0, "z": 9.8},
  "gyro": {"x": 0.001, "y": 0.002, "z": 0.0},
  "source": "quaternion"
}
```

### 5.2 Battery (`_battery_callback`)

`sensor_msgs/BatteryState`. The raw `percentage` field is 0.0–1.0; multiplied by 100. Voltage is direct. Low-battery threshold: < 20% turns the dashboard battery bar red.

```json
{
  "voltage": 11.6,
  "percentage": 78.0,
  "power_supply_status": 2
}
```

### 5.3 Odometry (`_odom_callback`)

`nav_msgs/Odometry`. Dead-reckoning from wheel encoders. Accumulated position from start point.

```json
{
  "position": {"x": 0.45, "y": -0.12, "z": 0.0},
  "heading": 93.4,
  "velocity": {"linear": 0.3, "angular": 0.01}
}
```

Drift: ~2–5 cm per metre on hard floor. Fuse with LIDAR/SLAM for long-range accuracy.

### 5.4 LIDAR scan (`_scan_callback`)

`sensor_msgs/LaserScan`. The full `ranges[]` array (up to 8000+ points on a 5 Hz scanner) is passed to `_scan_to_obstacle_summary()` which collapses it to 8 sectors:

```
front | front_right | right | back_right | back | back_left | left | front_left
```

Each sector holds the nearest non-Inf reading in metres (or `null` if clear).

```json
{
  "nearest_m": 0.42,
  "obstacles": {
    "front":       0.42,
    "front_right": 1.10,
    "right":       null,
    "back_right":  null,
    "back":        null,
    "back_left":   1.85,
    "left":        null,
    "front_left":  0.67
  }
}
```

Dashboard Safety panel shows `nearest_m` and turns text red below 0.4 m.

---

## 7. Publisher Method Details

### 6.1 `publish_cmd_vel(linear_x, linear_y, angular_z)`

Publishes `geometry_msgs/Twist`. The Raspbot v2 uses mecanum wheels so `linear_y` produces lateral strafing. All three axes are used.

```python
await bridge.publish_cmd_vel(linear_x=0.3, linear_y=0.0, angular_z=0.0)  # forward
await bridge.publish_cmd_vel(linear_x=0.0, linear_y=0.3, angular_z=0.0)  # strafe left
await bridge.publish_cmd_vel(linear_x=0.0, linear_y=0.0, angular_z=0.5)  # spin
await bridge.publish_cmd_vel(0, 0, 0)                                      # stop
```

Speed is clamped by `YAHBOOM_MAX_LINEAR_SPEED` and `YAHBOOM_MAX_ANGULAR_SPEED` env vars.

### 6.2 `publish_rgblight(r, g, b)`

Publishes `std_msgs/Int32MultiArray` with `data: [r, g, b]`. Values 0–255.

Dynamic patterns (patrol car, rainbow, breathe, fire) are asyncio tasks in `operations/lightstrip.py` that call this method in a loop — they are not ROS-native.

### 6.3 `publish_servo(servo_s1, servo_s2)`

Publishes `yahboomcar_msgs/msg/ServoControl`.

> [!WARNING]
> **Field names matter.** The `ServoControl` message has fields `servo_s1` (pan, ID 1) and `servo_s2` (tilt, ID 2). The driver callback writes both channels unconditionally:
> ```python
> Ctrl_Servo(1, msg.servo_s1)
> Ctrl_Servo(2, msg.servo_s2)
> ```
> **Both angles must be supplied on every publish.** Sending only one field (or using wrong field names like the former `"id"/"angle"`) zeroes the other servo. `camera_ptz.py` always passes both current angles from `_camera_state` via `_publish_both(pan, tilt)`.

```python
await bridge.publish_servo(servo_s1=90, servo_s2=90)   # centre both
await bridge.publish_servo(servo_s1=60, servo_s2=90)   # pan left, tilt unchanged
```

---

## 8. Environment Variables

All read at startup from the process environment or `.env` file.

| Variable | Default | Description |
|---|---|---|
| `YAHBOOM_ROBOT_IP` | `192.168.1.11` | Pi IP address |
| `YAHBOOM_ROSBRIDGE_PORT` | `9090` | rosbridge WebSocket port |
| `YAHBOOM_FALLBACK_IP` | *(unset)* | Secondary IP tried if primary unreachable |
| `YAHBOOM_IMU_TOPIC` | `/imu/data` | Override IMU topic name |
| `YAHBOOM_ULTRASONIC_TOPIC` | `/ultrasonic` | Override ultrasonic/sonar topic |
| `YAHBOOM_LINE_TOPIC` | `/line_sensor` | Override line sensor topic |
| `YAHBOOM_LINE_MSG_TYPE` | `std_msgs/msg/Int32MultiArray` | Message type for line sensor |
| `YAHBOOM_MAX_LINEAR_SPEED` | `0.5` | m/s clamp on cmd_vel linear |
| `YAHBOOM_MAX_ANGULAR_SPEED` | `1.5` | rad/s clamp on cmd_vel angular |

---

## 9. Known Behaviour Notes

**Why servos went to 0° on previous code:**  
`_publish_servo(servo_id, angle)` used `{"id": servo_id, "angle": angle}` — both wrong field names. ROSBridge silently accepted the message (it doesn't validate field names for custom message types), published it with `servo_s1=0, servo_s2=0` defaults. Driver ran `Ctrl_Servo(1, 0)` and `Ctrl_Servo(2, 0)`. Fixed by `_publish_both(pan, tilt)` with `{"servo_s1": pan, "servo_s2": tilt}`.

**Why the advertise() fix mattered:**  
roslibpy Topics created without `.advertise()` are subscribe-only from ROSBridge's perspective. Calling `.publish()` on an unadvertised topic sends the message over the WebSocket but ROSBridge silently drops it — the publisher is not registered. `cmd_vel`, `rgblight`, and `servo` all needed this. After the fix, all three respond immediately.

**Connection state during API calls:**  
All operations check `bridge.connected` before attempting publishes. If disconnected, operations return `{"success": false, "error": "Bridge not connected"}` rather than hanging. The `/api/v1/health` endpoint reports the connection state separately from the `connected` field so the dashboard can distinguish "robot online, ROS offline" from "robot unreachable".

**roslibpy thread model:**  
roslibpy runs its event loop in a background thread via `ros.run()`. All callbacks fire in that thread. The FastAPI async handlers use `asyncio.get_event_loop().run_in_executor()` for blocking roslibpy calls to avoid blocking the ASGI server.

---

## 10. Data Flow Diagram

```
                    ┌─────────────────────────────────────┐
                    │  Goliath — yahboom-mcp FastAPI :10892 │
                    │                                       │
  MCP client ──────▶│  portmanteau.py                       │
  Dashboard ──────▶│  ├── operations/motion.py              │
                    │  ├── operations/lightstrip.py          │
                    │  ├── operations/camera_ptz.py          │
                    │  ├── operations/sensors.py             │
                    │  └── (display, voice via SSH)          │
                    │             │  ▲                       │
                    │    publish  │  │  state cache reads    │
                    │             ▼  │                       │
                    │  ROS2Bridge (core/ros2_bridge.py)      │
                    └────────────┬──────────────────────────┘
                                 │ WebSocket ws://:9090
                    ┌────────────▼──────────────────────────┐
                    │  Raspberry Pi 5 — rosbridge_suite      │
                    │                                        │
                    │  /cmd_vel   ◀── publish (bridge)       │
                    │  /rgblight  ◀── publish (bridge)       │
                    │  /servo     ◀── publish (bridge)       │
                    │                                        │
                    │  /imu/data       ──▶ subscribe         │
                    │  /battery_state  ──▶ subscribe         │
                    │  /odom           ──▶ subscribe         │
                    │  /scan           ──▶ subscribe         │
                    │  /sonar          ──▶ subscribe         │
                    │  /line_sensor    ──▶ subscribe         │
                    └────────────────────────────────────────┘
```

---

## 11. See Also

- [`STARTUP_AND_BRINGUP.md`](../ops/STARTUP_AND_BRINGUP.md) — boot order, Docker/systemd on Pi, webapp restart vs reconnect
- [`RASPBOT_V2_HARDWARE_STACK.md`](RASPBOT_V2_HARDWARE_STACK.md) — physical stack, expansion board vs rosbridge software
- [`ROSBRIDGE_AT_BOOT.md`](../ops/ROSBRIDGE_AT_BOOT.md) — systemd service setup (run once on Pi)
- [`HARDWARE_AND_ROS2.md`](HARDWARE_AND_ROS2.md) — hardware tier overview, Pi vs Pi-less
- [`SENSORS.md`](SENSORS.md) — individual sensor technical specs (IMU, odometry, LIDAR, battery)
- [`ROSMASTER_ESP32.md`](ROSMASTER_ESP32.md) — ROSMASTER board (STM32) low-level details
- `src/yahboom_mcp/core/ros2_bridge.py` — implementation
- `src/yahboom_mcp/operations/camera_ptz.py` — servo publish with correct field names
