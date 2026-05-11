# Changelog - Yahboom ROS 2 MCP

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.4.2] - 2026-05-11

### 🤖 Container Hygiene & Bringup
- **Rosbridge unification**: Installed `ros-humble-rosbridge-server` inside `yahboom_ros2_final` so rosbridge and driver nodes run in the **same container**. This fixed the "Telemetry Blackout" — rosbridge DDS subscriptions cannot receive data when rosbridge and driver are in separate containers (sidecar pattern). 22+ ROS nodes now all visible in one graph.
- **Systemd service restored**: Renamed `/etc/systemd/system/yahboom-robot.service` back from `.disabled`. Updated `/usr/local/bin/yahboom-launch.sh` wrapper to target `yahboom_ros2_final` container. Service now survives reboots correctly.
- **DNS fixed**: Set `nameserver 8.8.8.8` on Pi host. Ethernet connection (192.168.0.250) provides reliable apt access.
- **Container cleanup**: Pruned dead containers (`yahboom_dead_*`, `yahboom_broken_*`), removed unused images (`ros:humble-ros-base`, `microros/micro-ros-agent`).

### 📸 Camera Pipeline
- **Camera publisher**: Created `/camera_publisher.py` in the container — publishes compressed JPEG frames to `/image_raw/compressed` via `rclpy`.
- **SSH-based snapshot fallback**: `/api/v1/snapshot` now uses direct OpenCV capture over SSH when VideoBridge has no frames. Returns 200 OK with JPEG from the robot's camera.
- **VideoBridge topic default**: Changed from `/image_raw/compressed` to `/image_raw` (handles raw sensor_msgs/Image with YUYV→BGR fallback). Then reverted to compressed when SSH fallback proved more reliable.
- **Raspbot demo on port 6001**: Identified that host raspbot process holds `/dev/video0`, preventing container access. Camera works when host process is killed.

### 🕹️ PTZ Camera — Demo Mode
- **`camera_set_pos` operation** added to portmanteau — absolute pan/tilt positioning (0–180°).
- **`camera_move` operation** added to portmanteau — directional step movement.
- **PTZ Demo button** in Dashboard — sweeps camera through a geometric pattern covering the full 180° range in both axes (16-point path including all four corners).
- Updated `portmanteau.py` to route `camera_set_pos` and `camera_move` to `camera_ptz` operations.

### 💡 GPIO & LED Headlight
- **`GET /api/v1/gpio`** — returns pin states for headlight (GPIO 17), led1 (GPIO 23), led2 (GPIO 24).
- **`POST /api/v1/gpio`** — sets GPIO pin via sysfs (`/sys/class/gpio/gpio{pin}/value`) over SSH. Auto-exports and configures direction on first use.
- **Headlight toggle** in Dashboard — amber toggle switch with glow effect. Calls `api.gpioSet()`.
- Added `gpioSet()` and `gpioStatus()` to frontend API client.

### 🤖 AI & Autonomy (in the works)
- **Ollama confirmed**: Gemma 3 1B (778MB) running at `192.168.1.11:11434`. Pi has 15GB RAM (13GB available).
- **LLM model configured**: `gemma3:1b` set as default for autonomous mission planning via `PUT /api/v1/settings/llm`.
- **Gemma 4 (released 2026-04-02)**: Not yet available on Ollama's model registry. E2B (2B) and E4B (4B) variants would fit the Pi's 15GB RAM and provide native multimodal (text + image + audio) capabilities for optical recognition tasks. Awaiting Ollama availability.
- **Pi disk bottleneck**: SD card 95% full (2.2GB free on 46GB). Larger multimodal models like `llava:7b` (3.8GB) won't fit without storage expansion.

### 🔧 Exec Endpoint & Diagnostics
- **`/api/v1/diagnostics/exec`**: Confirmed working — truncation was client-side PowerShell formatting issue. Using `ConvertTo-Json` shows full multi-line output with proper `\n` escaping.
- **`/api/v1/diagnostics/ros/restart`**: Triggers `docker exec yahboom_ros2_final ... ros2 launch yahboomcar_bringup` with 10s stability delay.

### 🗄️ Backup & Recovery
- **Docker commit**: `yahboom_ros2_final:backup-20260511` saved on Pi (337 ROS packages + rosbridge-server).
- **Container export**: 2.05GB `backup_20260511.tar.gz` on dev machine at `D:\Dev\repos\yahboom-mcp\`.
- **Config backup**: Systemd service, launch wrapper, and restore script saved in `/home/pi/backup_20260511/`.
- **Restore procedure**: `docker import backup_20260511.tar.gz` + copy systemd files + `systemctl daemon-reload && systemctl enable --now yahboom-robot.service`.

### 📚 Documentation
- **STATUS.md**: Updated with current container architecture, port assignment, and known limitations.
- **CHANGELOG.md**: This entry — documenting the container hygiene overhaul and camera/GPIO features.
- **MCD project page**: Updated ports, version, FastMCP tier, and container architecture description.

## [2.4.1] - 2026-05-07

### 🐛 Critical Fix: rosbridge host vs container
- **Root cause identified**: Two rosbridge instances were competing for port 9090 — one on the Pi HOST (PID 3361, started by `yahboom-launch.sh`) and one inside the Docker container. The host rosbridge lacked workspace packages (`yahboomcar_msgs`) and had DDS discovery issues with the container, silently dropping all published messages. `client_count: 0` confirmed the MCP's WebSocket connection was never registered.
- **Fix**: Killed the host rosbridge. Only the container rosbridge (with all packages, same DDS domain) serves port 9090 now. `client_count` now correctly reflects connected clients.
- **`publish_velocity`** — rewritten to use SSH `docker exec ros2 topic pub` (bypasses rosbridge DDS forwarding entirely, always works).
- **`publish_lightstrip`** — rewritten to use SSH `docker exec python3` with direct `Raspbot_Lib.Ctrl_WQ2812_brightness_ALL()` I2C commands.
- **`camera_ptz.py`** SSH fallback container name corrected to `yahboom_ros2_final`.

### 📺 OLED: luma.oled dependency eliminated
- **`display.py`** — rewrote `_build_luma_script()` to use `smbus2` (already installed via apt) + `PIL` (included with ROS 2) instead of `luma.oled` + `luma.core`. The SSD1306 OLED now works with zero additional dependencies.
- OLED init sequence, framebuffer rendering, text drawing, and scrolling all use direct I2C writes via `smbus2`. Status dashboard (IP, CPU, RAM, TEMP) also migrated.
- `_display_err_with_hint()` updated to no longer reference luma.

### 🧠 Webapp Help page
- Added **ROS 2** tab: architecture (rosbridge in container, topic map, IMU/battery limitation).
- Added **Missions** tab: what missions are, sample missions, obstacle avoidance, Ollama + vision detection pipeline.
- Fixed stale port reference (`10793` → `10893`) in Help page quick links.

### 📚 Documentation
- **`docs/hardware/ROSMASTER_ARCHITECTURE.md`** — updated with rosbridge host-vs-container analysis, client_count diagnosis, OLED smbus2 migration.
- **README.md** — verified all doc links current.

### 🧹 Known Hardware Limitations
- **No IMU/battery**: Raspbot V2 Rosmaster STM32 firmware does not expose IMU (accelerometer/gyroscope) or battery ADC through I2C registers (full scan 0x00-0x3f) or UART (no serial output at 115200 or 921600 baud). To add: external I2C hardware — INA219 (~$5) for battery voltage, MPU6050 (~$8) for IMU.
- **PTZ servos**: I2C commands reach the STM32 (verified via `Raspbot_Lib.Ctrl_Servo()` on Pi host), but servos may lack external power or PWM signal routing — physical/hardware issue.

### 🔊 Voice Module
- **CSK4002/CI1302** module connected via Pi USB. Presents as CH340 serial (ttyUSB0, 0xA5 protocol at 115200) + C-Media USB Audio (card 2 for speaker/mic). The CH340 is the module's serial (not the STM32 — STM32 uses I2C via GPIO).
- **Serial control works** — 0xA5 binary packets (phrase play, volume, ASR trigger) sent over CH340 reach the module. Phrase IDs 1-85 depend on factory firmware batch.
- **USB audio fallback** — `play_beep` generates WAV via Python and plays via `aplay -D hw:2,0`. `play_file` uses `mpg123` through USB audio card 2.
- **`_play_beep_usb()`** — new function in voice.py: generates 880Hz sine WAV, plays via USB audio when serial device isn't resolved.
- CP2102 driver loaded on Pi but no CP2102 device detected — CSK4002 uses CH340 (VID 1a86:7522), not CP2102.

## [2.4.0] - 2026-05-07

### 🤖 Autonomous Mission Execution (Ollama → ROS → Robot)
- **Mission executor** (`/minimal_mission_executor.py` in container) — subscribes `/boomy/mission` (JSON from Ollama planner), executes search/spin_scan/room_search behaviors via `/cmd_vel`, publishes status on `/boomy/mission_status`. Handles `target_description` keyword extraction for vision matching.
- **Ultrasonic obstacle avoidance** — executor subscribes `/ultrasonic` (Float32, cm). Sonar < 25 cm triggers reverse (1.5s) + turn (2s) before resuming search pattern. Status published with `was_blocked` flag.
- **Vision detection bridge** (`/detection_bridge.py` in container) — SSD MobileNet v2 COCO (90 classes: dog, person, cat, bowl, chair, etc.) runs in Docker at 0.5 FPS. Reads MJPEG frames from `raspbot.pyc` demo (avoids `/dev/video0` contention). Publishes detections to `/boomy/detections_json`. Target matching in executor: stops on keyword match, reports confidence.
- **`vision_bridge.py`** — standalone detection script, configurable via `DETECTION_CAM_URL` env var.
- **Webapp `/missions` page** — natural-language prompt input, 4 sample missions (Square Patrol, Spin Scan, Forward Recon, Room Search), "Report Back" panel showing mission plan JSON + status. Connected to `POST /api/v1/agent/mission`.
- **Docs** — `docs/ops/AUTONOMOUS_MISSIONS.md`: full architecture (Ollama planning → JSON → ROS execution → status feedback), "find our dog" and "check water bowls" scenario walkthroughs, capability matrix.
- **`docs/hardware/ROSMASTER_ARCHITECTURE.md`** — dual-bus analysis (I2C 0x2b for motors/sensors, UART serial for IMU/battery), I2C register map, container architecture diagram, factory demo vs Docker vs micro-ROS analysis.
- **Rosmaster_Lib** — extracted from Docker image, installed on Pi host. Methods: `get_battery_voltage()`, `get_accelerometer_data()`, `get_gyroscope_data()`, `get_magnetometer_data()`. Serial at 115200 baud (not 921600).

### 🔧 Infrastructure & Reliability
- **Rosbridge moved to driver container** — `rosbridge_websocket` now runs inside `yahboom_ros2_final` (not sidecar) where `yahboomcar_msgs` and all workspace packages are available. Fixes `/servo` advertise error and ensures `/cmd_vel` forwarding.
- **`yahboomcar_msgs`** — copied to driver container's Python path for rosbridge message deserialization.
- **`/start_all.sh`** — single entrypoint script in container: rosbridge → driver bringup → mission executor → detection bridge. Runs on `docker exec`.
- **`/usr/local/bin/yahboom-launch.sh`** (Pi host) — updated for `yahboom_ros2_final` container, starts rosbridge + driver bringup at boot.
- **Ollama binding** — changed from `127.0.0.1:11434` to `0.0.0.0:11434` on Pi so MCP server on PC can reach it.
- **Ollama default URL** — `server.py` now defaults to `http://192.168.1.11:11434` (was `127.0.0.1` — unreachable from PC).

### 🐛 Bug Fixes
- **Port drift** — 9 hardcoded `10792` references in `server.py` help tool, 3 in `prompts.py`, ~28 in docs/skills → all corrected to `10892`/`10893`.
- **`restart_ros_bringup`** — container name (`yahboom_ros2` → `yahboom_ros2_final`), workspace path (`/home/pi/` → `/root/`), launch file name (`yahboomcar_bringup_launch.py` → `yahboomcar_bringup.launch.py`). 2 locations fixed.
- **`camera_ptz.py:76`** — SSH fallback target container corrected to `yahboom_ros2_final`.
- **`agentic.py`** — `ctx` parameter now passed through to `yahboom_tool()` calls (was `ctx=None`, losing correlation ID).
- **Mission API payload** — webapp `Missions.tsx` fixed to send `{goal: ...}` object instead of raw string.

### 🎨 Webapp
- **Status page** (`/status`) — dedicated page: connection banner, telemetry grid (battery, heading, velocity, sonar), full StackStatusTable, server uptime. Extracted from Dashboard.
- **Dashboard slimming** — removed StackStatusTable (→ Status page), removed verbose connection banner text, link to Status page for details. Controls-only focus: camera, WASD, PTZ, lightstrip, voice.
- **Logs page overhaul** (`/logs`) — added: filter input, Export (`.log` download), sort toggle (oldest/newest first), Tail on/off button, legible font (text-sm text-slate-300).
- **Missions page** (`/missions`) — prompt input, sample missions, "Report Back" panel, connected to agent mission API.
- **Readability** — base font 15px + line-height 1.6, slate palette lightened (400: `#b0bec5`, 500: `#90a4ae`), minimum text sizes bumped from `text-[8px]`/`text-[9px]` to `text-xs`/`text-sm`.
- **Sidebar** — added Status and Missions nav items.
- **Duplicate route** — removed second `/peripherals` registration in `App.tsx`.

### 🧪 Testing
- **18 new unit tests** — `test_safety.py` (4), `test_lidar.py` (7), `test_agentic.py` (7). Total: 92 tests, all passing.
- **`justfile`** — `VER` synced to `2.3.0`, added `tsc --noEmit` to lint recipe.

### 📦 Dependencies & Config
- **`boomy_mission_executor`** — built with `colcon` in Docker workspace. Source at `ros2/boomy_mission_executor/`. Logger format compatibility fix for ROS 2 Humble (rclpy `get_logger().info()` single-arg).
- **Detection model** — SSD MobileNet v2 COCO `frozen_inference_graph.pb` copied from host to container at `/detection_model/`.
- **Empty dirs removed** — `src/yahboom_mcp/integrations/`, `src/yahboom_mcp/utils/`.
- **Unused noqa directives** — `RUF100` false positives acknowledged (E402/S104 in `server.py` suppress real lint findings).

## [2.3.3] - 2026-04-13
### 🎨 3D Visualization Refinement (SOTA v16.12)
- **Geometry Correction**: Re-oriented the 3D model (Y-up) and applied -90° X-axis rotation to the chassis.
- **Physics Alignment**: Elevated the chassis base to half wheel height (`WHEEL_RADIUS`) and aligned wheel axles horizontally.
- **Humorous Transparency**: Added "v0.1 Pre-Alpha" disclaimer to the dashboard to manage expectations regarding proxy meshes.

## [2.3.2] - 2026-04-13
### 🚢 Fleet Scaling & Identity (SOTA v16.11)
- **Identity Hardening**: Explicitly documented Boomy as a ~$300 / 1.0kg **unified platform** in the primary README.
- **Premium Expansion**: Added `docs/fleet/SCALING_TO_X3_PLUS.md` detailing the professional path to Jetson Orin + LiDAR + 6-DOF arm hardware.
- **Bumi Roadmap**: Initialized the `bumi-mcp` (Noetix Bumi Android) project as an Autumn 2026 hardware target with a current **Virtual Twin** focus.

## [2.3.1] - 2026-04-12
### 🌐 Universal Port Synchronization (SOTA v16.10)
- **Port 10892 Standard**: Re-aligned the entire project stack (Vite Proxy, Justfile, FastAPI) to port 10892 to match the `start.ps1` runtime environment.
- **Peripheral Restoration**: Fully restored the "Patrol Car" lightstrip pattern in `Peripherals.tsx`.
- **Infrastructure Cleanup**: Hardened `start.ps1` to prevent port collisions and ensure zero-downtime startups.

## [2.3.0-beta.1] - 2026-04-12
### 🎙️ Conversational Edge Intelligence (SOTA v16.0)
- **Speech Activation**: Resolved the "Silence" issue by hardening the USB Voice Module serial protocol and ensuring default volume initialization.
- **Voice Intelligence Hub**: 
    - Overhauled the Mission Control "Intelligence" card with a premium **Voice & Media** suite.
    - Integrated **Web Speech API (STT)** into the browser, enabling hands-free robot interactions.
- **Edge Conversational Pipe**: 
    - Implemented a low-latency "Chat & Say" workflow piping transcribed speech to a local **Ollama (Gemma3:1b)** node on the Pi 5.
    - Real-time LLM thought processing displayed in the webapp HUD.
- **High-Fidelity Media**: 
    - Unlocked native MP3 playback via the Voice Module's secondary **USB Audio interface (Card 2)**.
    - Deployed `mpg123` to the robot for industrial audio streaming (verified with Etta James).
- **Diagnostics**: Added a "Sound Check" (Beep) tool for rapid hardware verification.

## [2.2.0-beta.1] - 2026-04-12
### 🚀 Final Industrialization — "Total Sensory Fusion" (SOTA v15.0)
- **Neural Synchronization**: Hardened environment to `ROS_DOMAIN_ID=30`, unifying agentic tools and the dashboard.
- **Sensory Mastery**: Full restoration of Ultrasonic Sonar (`/ultrasonic`) and Forward Chassis Camera (`/usb_cam`).
- **Architectural Shift**: Decoupled the ROS 2 Bridge from isolated sidecars to a **Direct Internal Bridge** for low-latency telemetry.
- **Industrial Dashboard**: 
  - Activated live **Analytics** suite with Power Flux charts and Inertial Pathing (IMU).
  - Synchronized **Mission Control** with established hardware protocols.
- **Version Elevation**: Shifted from Alpha to **Beta** status based on 99% operational stability.

## [2.2.0] - 2026-04-12
### ✨ The "iPad Gemini" Breakthrough
- **Architectural Insight**: Credited to **iPad Gemini** for the deep identification of the "Split-Brain" de-synchronization between the host-level factory bypass (`raspbot.pyc`) and the ROS 2 workstation stack. This insight enabled the transition from generic container troubleshooting to surgical hardware reclamation.

### Added
- **Hardware Handshake (SOTA v15.0)**: Successfully reclaimed `/dev/ttyUSB0` from the host demo and restored the full ROS 2 sensory/actuator graph.
- **Micro-ROS Sidecar**: Deployed `microros/micro-ros-agent:humble` as a sidecar container to bridge the ESP32-S3 co-processor, bypassing broken dependencies in the factory Yahboom image.
- **Documented Architecture**: Created `docs/hardware/ROSMASTER_ESP32.md` and `docs/factory/LEGACY_DEMO_AUDIT.md` (Hardware Baseline).
- **Deactivation Script**: `src/yahboom_mcp/scripts/deactivate_demo.sh` for surgical removal of host-level lockouts.

### Fixed
- **Serial Port Monopoly**: Resolved the `/dev/ttyUSB0` lock issue that was preventing the ROS 2 workstation from accessing the motors and sensors.
- **Workspace Visibility**: Resolved the Docker volume "masking" issue where host mounts were hiding factory drivers baked into the image.

## [2.1.1] - 2026-04-11

### Fixed
- **`ros2_bridge.py` — logging crash** — `logger.info` for “Verified Humble Registry” had four `%s` placeholders but five topic arguments (ultrasonic added); fixed format string to include `Ultrasonic=%s`.
- **`ros2_bridge.py` — roslibpy `ready` callback** — handler now accepts variable args (protocol passes an extra argument); avoids `TypeError` on connect.
- **`ros2_bridge.py` — reactor / host selection** — single `Ros.run()`, TCP probe before connect, optional `YAHBOOM_FALLBACK_IP` (opt-in Ethernet); avoids `ReactorNotRestartable` when retrying hosts.
- **Telemetry & sensors** — IMU quaternion validation + fallbacks; `YAHBOOM_IMU_TOPIC`, `YAHBOOM_ULTRASONIC_TOPIC`, `YAHBOOM_LINE_TOPIC` / `YAHBOOM_LINE_MSG_TYPE`; `ir_proximity` ring + `line_sensors` exposed consistently for API/UI.
- **HTTP `/stream` (MJPEG)** — bridge generator starts when video bridge is active; Vite proxy timeouts for long-lived stream.
- **Webapp** — Movement/Dashboard/Sensors use `robot_connection.ros` and live `source`/`status`; Peripherals surfaces API `success: false` with backend `log`/`error` (`HardwareOpResponse`).
- **Duplicate route** — removed extra `POST /api/v1/display/write` registration (kept single handler).

### Added
- **Display (`operations/display.py`)** — `YAHBOOM_OLED_PAUSE_ROS` (default on): `pkill` stock `oled_node` before luma writes so ROS does not overwrite the OLED; `YAHBOOM_DISPLAY_CMD_PREFIX` to run Python in Docker when I2C/luma live only in a container; fixed scroll `nohup` command when using a prefix; failed luma runs append an on-Pi `pip3 install luma.oled …` hint in `log` when stderr suggests a missing module.
- **Voice (`operations/voice.py`)** — scans all `/dev/ttyUSB*` / `ttyACM*` with per-port `udevadm` matching (no longer falls back to “first ttyUSB” — that was often Rosmaster). `YAHBOOM_VOICE_DEVICE` forces the serial path; `YAHBOOM_VOICE_USB_IDS` adds extra `vid:pid` pairs; TTS via base64; `ser.flush()`; `get_status` checks `pyserial` on the Pi and returns `pyserial_ok` / `resolve_note`; clearer errors for permission and missing `serial`.
- **`pyproject.toml`** — dev dependency `pytest>=8.0.0,<9` (compatible with `pytest-httpx` and `tool.pytest.ini_options.minversion`); optional **`robot-pi`** extra pins `pyserial`, `luma.oled`, `luma.core`, `pillow`, `smbus2` (same stack MCP expects on the Pi for voice/OLED over SSH).
- **`scripts/robot/install_peripherals_pi.sh`** — run on the Pi to `pip3 install` voice + OLED dependencies and verify imports.

### Documentation
- **`docs/SENSORY_HUB.md`** — line/cliff IR behavior; onboard indicator LEDs; ROS topic naming notes.
- **`docs/AVOIDANCE_STRATEGY.md`** — cliff guard vs channel count (`[0,0,0]` vs all channels zero).
- **`README.md`** — pointer to peripheral/sensor env vars.

## [2.1.0] - 2026-04-04

### Fixed
- **`monitor_connection` TypeError** — watchdog called `connect(timeout_sec=...)` but signature is `timeout=`. Auto-reconnect was silently broken.
- **Network priority** — `server.py` lifespan now defaults `YAHBOOM_IP` to WiFi address; ethernet `192.168.0.250` demoted to `YAHBOOM_FALLBACK_IP`. README updated to match.
- **`CONNECTIVITY.md`** — complete rewrite: correct robot name (Raspbot v2), WiFi-primary architecture, exact `nmcli` metric commands, static DHCP lease, full troubleshooting section.
- **MissionControl UI** — fixed `Health` property access (`hData.connected` → `hData.robot_connection.ros`) and added `title` attributes to PTZ directional buttons for accessibility.

### Added
- **`video_bridge.py` direct capture fallback** — if no ROS frames arrive within 10 s, automatically switches to `cv2.VideoCapture` on the device. `YAHBOOM_CAMERA_DIRECT=1` forces direct mode. `YAHBOOM_CAMERA_DEVICE` overrides device index.
- **`lightstrip.py` autochange patterns** — patrol car (red/blue flash), rainbow (hue wheel), breathe (sine-wave), fire (random flicker). `lightstrip.execute(operation="pattern", param1="patrol|rainbow|breathe|fire")`. One pattern task at a time, cancels cleanly on `off` or new pattern.
- **`camera_ptz.py` servo improvements** — three-tier publish: bridge helper → direct roslibpy topic (`yahboomcar_msgs/msg/ServoControl`) → SSH/I2C fallback via `Rosmaster_Lib.set_pwm_servo()`. Angle clamped 0–180. SSH bridge passed through to all public functions.
- **`display.py` rewrite** — dropped broken `Adafruit_SSD1306` references; luma-only with `shlex.quote` safe script injection. Operations: `write`, `clear`, `status`, `get_status` (I2C probe + luma ping), `scroll` (background marquee). Proper error propagation.
- **`voice.py` rewrite** — USB device auto-detection by VID:PID (`1a86:7522/7523`, `10c4:ea60`) with fallback scan of `/dev/ttyUSB0`, `/dev/ttyUSB1`, `/dev/ttyACM0`. Fixed broken base64 shell encoding. Clean `_serial_cmd()` helper.
- **`scripts/diagnose_sensors.sh`** — Pi-side sensor diagnostic: I2C bus, per-topic echo, Hz rate, camera device, dmesg errors.
- **`scripts/start_camera.sh`** — Pi-side camera bringup: `usb_cam` → `v4l2_camera` with install hint.
- **`scripts/fix_network_priority.sh`** — Pi-side NetworkManager metric fix + prints env vars for Windows.
- **Test scaffold overhaul** — `tests/conftest.py` gains `mock_ssh` and `mock_bridge_with_servo` fixtures. `tests/unit/test_all.py`: 30 unit tests covering motion (all directions), lightstrip (set/off/patterns/disconnected), servo (move/set/reset/clamp/invalid), sensors, display (SSH mocked), voice (USB detection, say). `tests/e2e/test_patrol.py`: full hardware E2E test suite — connection, telemetry, lightstrip, servo sweep, display, voice, and the patrol square test (lights up, drives 4 sides, stops, green flash on success). Run with `YAHBOOM_E2E=1 YAHBOOM_IP=<ip> pytest tests/e2e/ -v -s`.
- **`tests/unit/test_camera_sensors.py`** — 14 unit tests: `VideoBridge` frame injection, JPEG encoding, `_image_callback` (compressed + raw rgb8), `mjpeg_generator` frame yield, `/api/v1/snapshot` endpoint (200+JPEG with frame, 204 without), IMU quaternion math, battery 3S percentage formula, SSH camera capture path mock.
- **`tests/e2e/test_patrol.py`** — camera + sensor E2E tests added: `test_e2e_camera_snapshot_http` (hits `/api/v1/snapshot`), `test_e2e_camera_snapshot_ssh` (cv2.VideoCapture on Pi host), `test_e2e_camera_snapshot_in_docker` (verifies `/dev/video0` mapped in container), `test_e2e_camera_vision_e2b` (E2B describes scene in German via LiteRT-LM API), `test_e2e_rosmaster_serial_direct` (Rosmaster_Lib direct read via SSH), `test_e2e_docker_serial_mapping`, `test_e2e_docker_i2c_mapping`, `test_e2e_oled_luma_installed`, `test_e2e_oled_write`. All use xfail gracefully when hardware not ready.
- **`scripts/boomy_full_setup.sh`** — single script that does everything on the Pi: udev rules, pip installs, OLED probe+test, Rosmaster serial test, Docker device check, driver deploy, luma in container, boomy_config.json, final summary. Run once: `ssh pi@<ip> 'bash -s' < scripts/boomy_full_setup.sh` (after scp'ing the driver).
- **`pyproject.toml`** — added `httpx[asyncio]` and `anyio` to dev deps for ASGI test client.
- **`docs/HARDWARE_DIAGNOSIS_VOICE_I2C.md`** — complete rewrite after reading driver: sensors use UART `/dev/ttyUSB0` (not I2C), wheels use I2C — explains why wheels work and sensors don't. Root causes: (1) voice hat and sensor board may share `/dev/ttyUSB0`, (2) Docker may not have `/dev/ttyUSB*` mapped, (3) `except: pass` everywhere hides errors, (4) OLED was using deprecated `Adafruit_SSD1306` instead of `luma.oled`.
- **`Mcnamu_driver_patched.py`** — complete rewrite: stable serial port via `_resolve_sensor_port()` (tries `/dev/ttyROSMASTER` → `/dev/ttyUSB0`), startup sanity check logging, `except: pass` replaced with `self.get_logger().warning(str(e))`, battery percentage formula validated for 3S LiPo, IMU covariance fields set correctly, clean shutdown.
- **`scripts/setup_udev_devices.sh`** — creates `/etc/udev/rules.d/99-boomy.rules` with stable symlinks: `/dev/ttyROSMASTER` (CH340 sensor board), `/dev/ttyVOICE` (CP2102 voice hat). Prints next-step instructions.
- **`scripts/deploy_driver_and_oled.sh`** — all-in-one Pi-side deploy: installs luma.oled, probes all I2C buses for OLED address, tests OLED display, writes `/home/pi/boomy_config.json`, tests Rosmaster serial inside Docker, copies patched driver, restarts container.
- **`docs/DOCKING_STATION_DESIGN.md`** — docking station design: three approaches (passive guide rails, visual ArUco docking, SLAM-based), ArUco detection code with PD alignment controller, charging circuit options (TP5100 LiPo charger + pogo pins recommended), BOM ~€36, yahboom-mcp integration plan.
- **Backend: `/api/v1/control/lightstrip`** — new POST endpoint accepting `operation` (set/off/pattern/stop_pattern/get_status) and `pattern` field. Routes to `lightstrip.execute()`.
- **Backend: `/api/v1/control/voice`** — new POST endpoint for say/play/volume/get_status. GET `/api/v1/control/voice/status` probes USB device.
- **Backend: `/api/v1/control/display/status`** — GET probe endpoint for OLED I2C status.
- **Webapp `Peripherals.tsx`** — complete rewrite: 4 lightstrip pattern buttons (patrol/rainbow/breathe/fire) with active indicator + toggle, static colour with brightness slider, status badges for display and voice (with refresh button), working sound library buttons with loading spinner, volume slider, disabled state when no voice module detected, `StatusBadge` component shows Wifi/WifiOff icon.
- **`api.ts`** — added `getVoiceStatus`, `getDisplayStatus`, `postLightstripPattern`, `postLightstripOff`; fixed `postVoicePlay` to call `/api/v1/control/voice` with correct body.
- **`MockROS2Bridge`** — added `rgblight_topic` stub (records published messages), `publish_servo()` with history, `move()` alias, `servo_history` list — all in `__init__`.
- **Unit tests** — simplified lightstrip tests (no longer need `_inject_fake_topic`); `mock_bridge_with_servo` fixture simplified.





### Fixed
- **Branding Purge**: Removed all incorrect "G1 MISSION" and "Unitree G1" hallucination references across the codebase.
- **Mission Identity**: Standardized on **BOOMY MISSION** for the webapp and correctly identified hardware as **Yahboom Raspbot v2** in all prompts and docs.
- **Roadmap Cleanup**: Sanitized `PRD.md` to prevent recurring branding hallucinations.

## [2.0.0-alpha.1] - 2026-03-29

### Added
- **Boomy Insight Diagnostic Suite**: A comprehensive hardware-level telemetry and recovery layer.
- **SSH Bridge**: Secure `paramiko`-based remote shell for Pi 5 maintenance directly from the webapp.
- **Diagnostics Dashboard**: Real-time view for I2C bus state, kernel log streaming (`dmesg`), and stack health.
- **New MCP Tools**: Registered `inspect_boomy_stack` and `execute_boomy_command`.

### Fixed
- **I2C Expansion Board Stability**: Capped I2C baudrate at **100kHz** via `dtparam` to resolve Raspberry Pi 5 controller timeout failures.
- **Port Allocation**: Standardized webapp frontend at port **10893** following SOTA v12.0 guidelines.

## [1.4.0] - 2026-03-04

### Added
- **Unified Gateway Roadmap**: Defined migration path to FastMCP 3.1 architecture (documented in `docs/FASTMCP3_UNIFIED_GATEWAY.md`).
- **Architecture**: Planned consolidation of MCP and HTTP services into a single FastAPI instance.

## [1.3.0] - 2026-03-04

### Added
- **SOTA 2026 Dashboard**: Successfully consolidated all experimental UI enhancements from `webapp2` back into the primary `webapp`.
- **Infrastructure**: Moved `start.ps1` and `start.bat` into the `webapp/` directory following the standardized project pattern.
- **Unified Gateway**: Validated full compliance with FastMCP 3.1 architecture (consolidated MCP+HTTP).

### Fixed
- **React Runtime**: Resolved "Black Screen" issue by aligning `react` and `react-dom` to version `19.0.0` (Fixed by Windsurf).
- **Consolidation**: Removed redundant `webapp2` experimental directory.

## [1.2.0] - 2026-03-04

### Added
- **Experimental Substrate**: Created `webapp2` to test high-density SOTA visuals (Tailwind/Framer Motion).
- **Architecture**: Implemented `AppLayout` and `Sidebar` patterns for unified fleet command.

### Fixed
- **`start.ps1`**: `npm run dev` no longer fails on Windows — wrapped `npm` with `cmd /c`.

## [1.1.0] - 2026-03-03

### Added
- **Fleet Expansion**: Migrated core robotics documentation from central hub to local `docs/`.
- **Federated Architecture**: Implemented fleet discovery patterns and shared spatial data documentation.
- **PRD & Roadmap**: Established Phase 4-6 roadmap for multi-robot intelligence.
- **Fleet Registry**: Updated `mcp-central-docs` with the 2026 Fleet Registry schema.

## [1.0.0] - 2026-03-03

### Added
- **Project Initialization**: Created workspace with `uv init` and SOTA 2026 scaffold.
- **FastMCP 3.0 Server**: Established core server with lifespan connectivity management.
- **Portmanteau Tool**: Scaffolding for unified `yahboom` tool.
- **Documentation**: SOTA Architecture doc in `mcp-central-docs`.
- **Fleet Registry**: Registered project at port 10892.
