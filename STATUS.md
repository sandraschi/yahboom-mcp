# Project Status: Yahboom Raspbot v2 (Boomy)

**Current SOTA:** v2.4.2
**Operational Status:** Production — Autonomous Missions Capable
**Last Updated:** 2026-05-11

## Connectivity & Infrastructure

| Component | Port | Status | Note |
| :--- | :--- | :--- | :--- |
| **Backend (FastAPI)** | `10892` | **ACTIVE** | Unified MCP + REST Gateway |
| **Dashboard (Vite)** | `10893` | **ACTIVE** | Proxied to 10892 |
| **Rosbridge WebSocket** | `9090` | **ACTIVE** | Runs **inside** `yahboom_ros2_final` container (unified architecture — no sidecar) |
| **Ollama** | `11434` | **ACTIVE** | Gemma3:1b (778MB) on Pi. Pi has 15GB RAM (13GB avail). Gemma 4 not yet on registry. |
| **Raspbot factory demo** | `6001` | **MOVED** | Killed — holds `/dev/video0`. Replacement: SSH-based OpenCV capture via `/api/v1/snapshot` |
| **CLI (Justfile)** | `10892` | **SYNCED** | Root project default |

## Container Architecture (v2.4.2)

**Single unified container** (`yahboom_ros2_final`, image `yahboomtechnology/ros-humble:0.1.0`, 6.3GB):

```
yahboom_ros2_final (host networking, privileged)
├── rosbridge_websocket (port 9090)  ← installed via apt
├── Mcnamu_driver (driver_node)
├── robot_state_publisher, joint_state_publisher
├── camera_publisher (/image_raw/compressed)
├── mission_executor
├── detection_bridge
└── rosapi
```

**Why unified**: Rosbridge in a separate container (the old "sidecar" pattern) cannot receive DDS subscription data — inbound sensor data never reaches the MCP. Both rosbridge and driver must share one DDS participant (one container) for bidirectional communication.

##  Dashboard Health

- **Telemetry**: Active (ultrasonic, line sensors, sonar — confirmed live data flow).
- **Motion**: Working via roslibpy `cmd_vel` publish (DDS bridge inside container).
- **Lightstrip**: Working via ROS topic `/rgblight` (std_msgs/Int32MultiArray).
- **PTZ Servos**: Working via ROS topic `/servo` (yahboomcar_msgs/ServoControl). Demo sweeps full 0–180° range.
- **OLED Display**: Working via `smbus2` + PIL.
- **Voice Module (CSK4002)**: Serial control via CH340 (ttyUSB0, 0xA5 protocol).
- **Camera**: SSH-based OpenCV snapshot fallback at `/api/v1/snapshot` (returns JPEG 200 OK). VideoBridge subscribes to `/image_raw/compressed` but rosbridge large-message delivery is unreliable.
- **GPIO Headlight**: GPIO 17 via `/api/v1/gpio`. Toggle in Dashboard.
- **Ollama chat**: Working (Gemma3:1b on Pi at 192.168.1.11:11434).

##  Autonomous Missions

Natural-language goals → Ollama → structured JSON → ROS execution:

- **Mission executor**: Runs in Docker, subscribes `/boomy/mission`, drives `/cmd_vel`, publishes `/boomy/mission_status`.
- **Obstacle avoidance**: Ultrasonic < 25cm → reverse + turn, reports `was_blocked` in status.
- **Vision detection**: SSD MobileNet v2 COCO (90 classes) in Docker, publishes `/boomy/detections_json`.
- **Target matching**: Executor matches `target_description` keywords against detected labels → stops on match.
- **Webapp**: `/missions` page with prompt input, 4 sample missions, Report Back panel.

### AI Roadmap

| Item | Status |
|------|--------|
| **Gemma 3 1B** | Running — text-only mission planning |
| **Gemma 4** | Released 2026-04-02. E2B (2B) and E4B (4B) multimodal. **Not yet on Ollama.** |
| **Pi storage** | 95% full (2.2GB free). Can't pull larger models without expansion. |
| **Camera for optical recog** | SSH snapshot captures work. MJPEG stream needs fix. |

##  Webapp Pages

| Page | Path | Purpose |
|------|------|---------|
| Dashboard | `/dashboard` | Camera, WASD drive, PTZ (with demo), GPIO headlight, lightstrip, voice |
| Status | `/status` | Connection health, telemetry grid, stack health table |
| Missions | `/missions` | Natural-language goals, sample missions, report-back |
| Missions Control | `/mission-control` | Telemetry-focused view |
| Diagnostic Hub | `/diagnostics` | ROS topics/nodes, SSH shell, stack table |
| Server logs | `/logs` | Live SSE log stream with filter, export, sort |
| Help | `/help` | 8 tabs: hardware, quickstart, MCP tools, REST API, connection, ROS 2, missions, troubleshooting |
| Chat | `/chat` | AI Companion via Ollama |
| Settings | `/settings` | LLM model selection, provider config |
| Peripherals | `/peripherals` | Lightstrip patterns, OLED status, voice controls |
| Visualization | `/viz` | 3D Three.js model with real-time telemetry |

##  Services Running in Docker (yahboom_ros2_final)

| Service | ROS Node | Status |
|---------|----------|--------|
| rosbridge_websocket | `/rosbridge_websocket` | Active on port 9090 |
| ROS API | `/rosapi`, `/rosapi_params` | Active |
| Yahboom driver | `/driver_node` | Active (I2C: motors, servos, lightstrip, sensors) |
| Joint state publisher | `/joint_state_publisher` | Active |
| Robot state publisher | `/robot_state_publisher` | Active |
| Mission executor | `/mission_executor` | Active (subscribes `/boomy/mission`) |
| Detection bridge | (python process) | Active (SSD MobileNet v2, publishes `/boomy/detections_json`) |
| Camera publisher | `/camera_publisher` | Active (OpenCV → `/image_raw/compressed` via rclpy) |
| Image republisher | `/image_republisher` | Active (raw → compressed) |
| Total nodes | | **22+ ROS nodes** in graph |

## Fleet Roadmap

- **Core Hardware**: Yahboom Raspbot v2 (Boomy). Weight: 1.0 kg. Cost: ~$300 (w/ Pi 5 16GB).
- **Scaling Path**: **ROSMASTER X3 PLUS** (Jetson Orin NX + LiDAR + 6-DOF Arm) documented in `docs/fleet/`.
- **Target 2026**: **Noetix Bumi Android** — Shipping now from ~10,000 CNY (~€1,300). 98cm / 17kg / 21 DoF. Models from Lite to EDU-Max with NVIDIA Jetson Orin. SDK + open source tools available. Architecture ported to `bumi-mcp`.
- **Dreame map bridge**: `ros2/boomy_dreame_map_bridge/` package exists but not deployed.

## Reliability Headers

- **Systemd survive-reboot**: `yahboom-robot.service` enabled. Wrapper targets `yahboom_ros2_final`. Container `--restart unless-stopped`.
- **Port Paradox**: Resolved (All components on 10892/10893).
- **Process Guard**: `start.ps1` hardened with automatic port squatter cleanup.
- **Unified container**: Rosbridge + driver in one container — no DDS subscription blackout.
- **Backup**: 2.05GB container export on dev machine. Docker commit `yahboom_ros2_final:backup-20260511` on Pi. Configs in `/home/pi/backup_20260511/`.
- **Architectural Alignment**: Formalized the "Host-Controller" separation pattern across both Bumi (E1-based) and Boomy (RosMaster-based) hardware targets.

## Known Hardware Limitations

- **No IMU/Battery**: Raspbot V2 Rosmaster STM32 firmware does not expose IMU or battery ADC through I2C registers. Fix: external I2C hardware — INA219 for battery, MPU6050 for IMU.
- **PTZ servos**: I2C commands reach the STM32 but servos may lack external power or PWM signal routing — physical/hardware check needed.
- **Voice CSK4002 canned phrases**: Phrase IDs 1-85 depend on factory firmware batch. USB audio path works for general audio.
- **Nav2**: mission_executor handles nav2_goal import gracefully (try/except).
- **WiFi internet**: Pi has no WAN on Raspbot AP. Ethernet provides internet.
- **Camera contention**: `/dev/video0` can only be opened by one process. Host `raspbot` and container `camera_publisher` compete.

## Container Hygiene — Lessons Learned (2026-05-11)

A multi-hour debugging session that culminated in a single root cause:

1. Host rosbridge was disabled (renamed to `.disabled`). Later re-enabled after fixing the wrapper to use the correct container name.
2. Sidecar pattern failed — rosbridge in `yahboom_rosbridge_sidecar`, driver in `yahboom_ros2_final`. Inbound DDS subscriptions broke (Telemetry Blackout).
3. Fixed by installing `ros-humble-rosbridge-server` inside the driver container. Both rosbridge and driver now share one DDS participant.
4. Camera contention — host raspbot holds `/dev/video0`. Kill host process or use SSH capture.
5. Pi disk 95% full. Pruned dead containers and unused images to recover space.
