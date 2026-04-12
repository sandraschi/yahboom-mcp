# Changelog - Yahboom ROS 2 MCP

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
