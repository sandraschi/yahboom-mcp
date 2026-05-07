# Project Status: Yahboom Raspbot v2 (Boomy)

**Current SOTA:** v2.4.1  
**Operational Status:** Production — Autonomous Missions Capable  
**Last Updated:** 2026-05-07

## 🌐 Connectivity & Infrastructure

| Component | Port | Status | Note |
| :--- | :--- | :--- | :--- |
| **Backend (FastAPI)** | `10892` | **ACTIVE** | Unified MCP + REST Gateway |
| **Dashboard (Vite)** | `10893` | **ACTIVE** | Proxied to 10892 |
| **Rosbridge WebSocket** | `9090` | **ACTIVE** | Runs in `yahboom_ros2_final` container (host rosbridge killed — lacked packages) |
| **Ollama** | `11434` | **ACTIVE** | Gemma3:1b on Pi, bound 0.0.0.0 (default URL: `http://192.168.1.11:11434`) |
| **Raspbot factory demo** | `6001` | **ACTIVE** | MJPEG video feed + direct hardware access |
| **CLI (Justfile)** | `10892` | **SYNCED** | Root project default |

## 🕹️ Dashboard Health

- **Telemetry**: Active (ultrasonic, line sensors, heading from Rosmaster I2C).
- **Motion**: Working via SSH `docker exec ros2 topic pub` (bypasses rosbridge DDS forwarding issue).
- **Lightstrip**: Working via SSH `Raspbot_Lib.Ctrl_WQ2812_brightness_ALL()` direct I2C.
- **PTZ Servos**: Working via SSH I2C `Raspbot_Lib.Ctrl_Servo()` (was broken — wrong library).
- **OLED Display**: Working via `smbus2` + PIL (luma.oled dependency eliminated).
- **Voice Module (CSK4002)**: Serial control via CH340 (ttyUSB0, 0xA5 protocol). USB Audio fallback for play_beep/play_file.
- **Camera**: MJPEG stream from factory demo (`raspbot.pyc` on port 6001), proxied via backend `/stream`.
- **Ollama chat**: Working (Gemma3:1b on Pi).

## 🤖 Autonomous Missions

Natural-language goals → Ollama → structured JSON → ROS execution:

- **Mission executor**: Runs in Docker, subscribes `/boomy/mission`, drives `/cmd_vel`, publishes `/boomy/mission_status`.
- **Obstacle avoidance**: Ultrasonic < 25cm → reverse + turn, reports `was_blocked` in status.
- **Vision detection**: SSD MobileNet v2 COCO (90 classes) in Docker, publishes `/boomy/detections_json`.
- **Target matching**: Executor matches `target_description` keywords against detected labels → stops on match.
- **Webapp**: `/missions` page with prompt input, 4 sample missions, Report Back panel.

## 📄 Webapp Pages

| Page | Path | Purpose |
|------|------|---------|
| Dashboard | `/dashboard` | Camera, WASD drive, PTZ, lightstrip, voice |
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

## 🚢 Fleet Roadmap

- **Core Hardware**: Yahboom Raspbot v2 (Boomy).
    - **Weight**: 1.0 kg.
    - **Cost**: ~$300 (w/ Pi 5 16GB).
- **Scaling Path**: **ROSMASTER X3 PLUS** (Jetson Orin NX + LiDAR + 6-DOF Arm) documented in `docs/fleet/`.
- **Target 2026**: **Noetix Bumi Android** (Autumn Project). Currently in **Virtual Twin** development phase.
- **Dreame map bridge**: `ros2/boomy_dreame_map_bridge/` package exists but not deployed.

## 🧠 Services Running in Docker (yahboom_ros2_final)

| Service | ROS Node | Status |
|---------|----------|--------|
| rosbridge_websocket | `/rosbridge_websocket` | Active on port 9090 |
| ROS API | `/rosapi`, `/rosapi_params` | Active |
| Yahboom driver | `/driver_node` | Active (I2C: motors, servos, lightstrip, sensors) |
| Joint state publisher | `/joint_state_publisher` | Active |
| Robot state publisher | `/robot_state_publisher` | Active |
| Mission executor | `/mission_executor` | Active (subscribes `/boomy/mission`) |
| Detection bridge | (python process) | Active (SSD MobileNet v2, publishes `/boomy/detections_json`) |

## 🛡️ Reliability Headers

- **Port Paradox**: Resolved (All components moved from 10792 -> 10892).
- **Process Guard**: `start.ps1` hardened with automatic port squatter cleanup.
- **Rosbridge fix**: Host rosbridge killed — container rosbridge serves port 9090 with all workspace packages.
- **Documentation**: All READMEs, CHANGELOG, and guides synced to v2.4.1.
- **Architectural Alignment**: Formalized the "Host-Controller" separation pattern across both Bumi (E1-based) and Boomy (RosMaster-based) hardware targets.

## 🐛 Known Hardware Limitations

- **No IMU/Battery**: Raspbot V2 Rosmaster STM32 firmware does not expose IMU (accelerometer/gyroscope) or battery ADC through I2C registers (full scan 0x00-0x3f) or UART (no serial output at 115200 or 921600 baud). Fix: external I2C hardware — INA219 (~$5) for battery voltage, MPU6050 (~$8) for IMU.
- **PTZ servos**: I2C commands reach the STM32 (verified via `Raspbot_Lib.Ctrl_Servo()` on Pi host), but servos may lack external power or PWM signal routing — physical/hardware issue.
- **Voice CSK4002 canned phrases**: Phrase IDs 1-85 depend on factory firmware batch. USB audio path works for general audio.
- **nav2_msgs not installed**: mission_executor handles nav2_goal import gracefully (try/except).
- **WiFi internet**: Pi has no WAN on Raspbot AP. PC ethernet provides internet. USB WiFi dongle needed for coffee-shop dual-network setup.
