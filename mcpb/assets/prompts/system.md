# yahboom-mcp — MCP Server Capabilities

## Server Overview

yahboom-mcp is a comprehensive MCP (Model Context Protocol) server for controlling the Yahboom Raspbot v2, a ROS 2 Humble-based four-wheel mecanum robot powered by a Raspberry Pi 5. The server exposes the full hardware surface of the robot through a **portmanteau tool pattern** (single `yahboom_tool` with 36+ operations) plus dedicated atomic tools for specialized functions (LIDAR, audio, demos, mission planning, ROS 2 management). It runs as a **Unified Gateway** — combining FastMCP SSE transport with a FastAPI REST API on a single process — so both AI clients (Claude Desktop, Cursor) and the web dashboard can interact with the robot simultaneously.

The server connects to the robot over WiFi via one of three bridge modes: **ROS 2 bridge** (roslibpy WebSocket to rosbridge_server on port 9090, default), **ESP32 serial bridge** (direct TCP to ESP32 on port 2323), or **Mock bridge** (for CI/testing with no hardware). An SSH control channel provides secondary access for hardware recovery, OLED display, camera PTZ servo control, I2C device probing, and command execution on the Pi. A **connection watchdog** with auto-reconnect keeps the robot reachable even across temporary WiFi interruptions.

**Key features**: holonomic mecanum motion (forward, backward, strafe, rotate), 9-axis IMU (heading, pitch, roll), battery telemetry (voltage, percentage), wheel encoder odometry, LIDAR obstacle scanning (Yahboom /scan + optional Dreame D20 Pro maps), MJPEG camera streaming, I2C OLED display (SSD1306), RGB lightstrip (WS2812B-style with patterns), piezo buzzer, USB voice module (speech synthesis, built-in sound effects, audio file playback), camera PTZ (pan/tilt servo), TTS via eSpeak on the Pi or speech-mcp, GPIO control (headlight LEDs), SLAM mapping (slam_toolbox with /map topic), trajectory recording/replay, and autonomous mission planning via LLM (Ollama or Gemini).

## Tools

### yahboom_tool (Portmanteau — 36+ Operations)

The primary robot control interface. Single `@mcp.tool()` with an `operation` discriminator.

**Parameters**: operation (required), param1 (str|float|None — duration, speed, or basename), param2, param3 (RGB blue channel), payload (dict|None for future key-value).

**Operations**:

#### Motion Control
- `health_check` — Returns bridge connection state, battery percentage, and ROS topic readiness. Always call first before any motion.
- `forward` — Move forward at speed. param1: linear velocity 0.0–1.0 m/s (default 0.3).
- `backward` — Move backward. param1: negative linear velocity -0.1 to -1.0 m/s (default -0.3).
- `turn_left` — Rotate counter-clockwise. param1: angular velocity 0.1–2.0 rad/s (default 0.4).
- `turn_right` — Rotate clockwise. param1: angular velocity (default 0.4).
- `strafe_left` — Strafe left (mecanum sideways). param1: lateral velocity 0.0–0.5 m/s (default 0.2).
- `strafe_right` — Strafe right. param1: lateral velocity (default 0.2).
- `stop` — Immediate halt. Publishes zero Twist to /cmd_vel.
- `stop_all` — Global emergency stop via safety module. Halts motion, cancels trajectories, stops audio.

#### Sensor Reading
- `read_imu` — Returns 9-axis IMU data: heading (degrees 0-360), pitch, roll, angular velocity, linear acceleration.
- `read_battery` — Returns battery percentage (0-100), voltage, and power status.
- `read_encoders` — Returns wheel encoder counts for all four mecanum wheels.
- `read_all` — Combines IMU + battery + encoder data in a single call.
- `read_lidar` — Returns 8-sector obstacle distances (front, front-left, left, back-left, back, back-right, right, front-right) and nearest obstacle distance in metres.

#### Voice
- `say` — Speak text through the USB voice module. param1: text string.
- `play` — Play a built-in sound ID (1-15: siren, ding, buzzer, reveal, alarm, etc.). param1: sound ID.
- `play_beep` — Short beep via piezo buzzer. param1: duration in seconds (default 0.2).
- `play_file` — Play an audio file from the Pi filesystem. param1: file path.
- `chat_and_say` — Combined TTS + voice module speech. param1: text string.

#### Camera PTZ
- `camera_up` — Tilt camera upward. param1: step in degrees (default 15).
- `camera_down` — Tilt camera downward. param1: step (default 15).
- `camera_left` — Pan camera left. param1: step (default 15).
- `camera_right` — Pan camera right. param1: step (default 15).
- `camera_reset` — Reset camera to center position (pan=90, tilt=90).
- `camera_set_pos` — Set exact camera position. param1: pan (0-180, default 90), param2: tilt (0-180, default 90).
- `camera_move` — Move camera in a direction by a step. param1: direction (up/down/left/right), param2: step (default 15).

#### Display
- `display` — Write text to the I2C OLED display (SSD1306). param1: text string, param2: line number (0-3).
- `clear_display` — Clear the OLED display.

#### Lightstrip
- `led` — Set RGB lightstrip colour. param1: red (0-255), param2: green (0-255), param3: blue (0-255).
- `led_off` — Turn off all lightstrip LEDs.
- `light_effect` — Run a named light pattern. param1: pattern name (rainbow, breathe, fire, police, strobe).
- `patrol_car` — Activate police-style red/blue strobe pattern.

#### Audio
- `audio_play` — Upload and play a local .mp3/.wav file through the USB voice module. param1: local file path.
- `audio_store` — Upload a file to the Pi's ~/boomy_audio/ depot. param1: local file path, param2: filename for storage.
- `audio_play_stored` — Play a previously stored file by name. param1: filename.
- `audio_list_stored` — List all stored audio files.
- `audio_delete_stored` — Delete a stored audio file. param1: filename.
- `audio_stop` — Kill all running audio playback.
- `audio_sound` — Play a built-in sound effect. param1: sound name (fart, ding, buzzer, clap, boo, circus, elevator, siren, applause, tada, sad_trombone, take_five, coin, zap, reveille, deguello, beep).

#### Trajectory
- `start_recording` — Begin recording robot trajectory (pose history at 10 Hz).
- `stop_recording` — Stop recording and save the trajectory. param1: filename (default "trajectory").
- `list_trajectories` — List all saved trajectories on the server.

#### Diagnostics
- `config_show` — Show current server configuration (robot IP, bridge port, connection mode).
- `inspect_stack` — Inspect the full ROS 2 driver stack via SSH (nodes, I2C, serial devices).
- `execute_command` — Execute an arbitrary shell command on the Pi via SSH (sandboxed to read-only operations).

#### Mission
- `explore` / `explore_and_map` — Start the autonomous exploration and SLAM mapping mission.

### yahboom_demo

Show-floor demonstration modes for the Boomy robot persona.

**Parameters**: operation (describe|draw|draw_status|draw_stop|talkbot|talkbot_status|talkbot_stop|status|stop), pattern (smiley|heart|boomy_b), speed, skip_color_swap_pause, approach, max_turns, use_speech_mcp, scripted_user_lines.

**Operations**:
- `describe` — Describe available demo capabilities.
- `draw` — Execute mecanum path drawing. `smiley` draws a smiley face, `heart` draws a heart. Two-color layers pause for chalk swap unless skip_color_swap_pause=True.
- `draw_status` — Check current drawing operation status.
- `draw_stop` — Abort the current drawing operation.
- `talkbot` — Interactive social mode: optional approach motion, PTZ wiggle, "Hi, I am Boomy. Who are you?", then listen/reply turns. Uses speech-mcp TTS when reachable, else eSpeak on Pi.
- `talkbot_status` — Check talkbot conversation status.
- `talkbot_stop` — End the talkbot session.
- `stop` — Stop any active demo.

### yahboom_agentic_workflow

High-level goal execution via MCP sampling (SEP-1577). The LLM plans and executes sequences using three sub-tools: `get_robot_health` (connection and battery), `move_robot` (direction, duration_seconds), and `read_sensors` (sensor_type). Returns a summary of steps taken and outcome.

**Examples**: "patrol in a square and report battery", "check health, then move forward 2 seconds".

### yahboom_agent_mission

LLM-powered mission planner that converts a natural-language goal into a structured JSON mission plan (intent, behavior, target_description, optional nav2_goal, voice_feedback). Supports Ollama (default) and Gemini backends. Can publish the plan as JSON on std_msgs/String topic (/boomy/mission) for execution by the Pi's mission executor, and optionally speak voice_feedback through the voice module.

**Parameters**: goal (required), provider (auto|ollama|gemini), publish_to_ros (default True), speak (default False).

### yahboom_help_tool

Multi-level hierarchical help system. Call with no args for category list, category for topic list, or category+topic for full detail.

**Categories**: motion, sensors, connection, api, mcp_tools, startup, troubleshooting.

### ros_topic_list

Lists all active ROS 2 topics and their message types from the bridge. Returns topics array or error message if bridge is offline.

### ros_node_info

Queries ROS 2 node info (publishers, subscribers, services) via SSH into the robot container. Requires SSH connection.

### ros_resync

Forces re-discovery of all ROS 2 topics and re-subscription to sensor streams. Useful when telemetry (Battery, IMU) is missing while wheels still work.

### ros_restart_bringup

Remotely restarts the Yahboom bringup launch file via SSH. This kills and re-starts the ROS 2 driver nodes (motion, sensors, etc.) inside the robot container. Use as a nuclear option when the robot is unresponsive or nodes are missing.

### lidar

LIDAR sensor data from two sources: the Yahboom /scan ROS topic and optionally the Dreame D20 Pro vacuum cleaner map.

**Operations**:
- `read` — Return obstacle distances by sector (8 sectors) and nearest obstacle. source param: yahboom, dreame, or auto.
- `read_raw` — Return raw LIDAR scan points (ranges, angles, intensities).
- `read_dreame_map` — Fetch Dreame D20 Pro floorplan map via DREAME_MAP_URL.

### audio

Standalone audio management tool for playing local files and built-in sounds through the USB voice module.

**Operations**:
- `play` — Upload and play a local audio file. file_path: absolute path to .mp3/.wav.
- `sound` — Play a built-in sound effect by name. file_name: one of fart, ding, buzzer, clap, boo, circus, elevator, siren, applause, tada, sad_trombone, take_five, coin, zap, reveille, deguello, beep.
- `store` — Upload an audio file to the Pi's persistent depot. file_path: local path, file_name: target name.
- `play_stored` — Play a previously stored file. file_name: stored filename.
- `list_stored` — List all audio files in the Pi depot.
- `delete_stored` — Remove a stored audio file. file_name: filename to delete.
- `stop` — Immediately stop any playing audio.

## Prompts

Five registered FastMCP prompts for common robot workflows:

1. **yahboom_quick_start(robot_ip)** — Step-by-step setup and first-use instructions.
2. **yahboom_patrol(duration_seconds)** — Generate a patrol plan (square, figure-8).
3. **yahboom_diagnostics()** — Diagnostic checklist for the robot and server setup.
4. **yahboom_patrol_apartment()** — Standard apartment patrol circuit.
5. **yahboom_go_to_recharge()** — Drive to the charging station sequence.

## Skills

Four registered FastMCP skills (registered via skills/__init__.py):

1. **yahboom_quick_pilot** — Immediate robot control and quick-start guidance.
2. **yahboom_patrol_sweep** — Autonomous area coverage patrol.
3. **yahboom_emergency_halt** — Immediate emergency stop procedure.
4. **yahboom_diagnostic_triage** — Systematic robot health and connectivity check.

## REST API (FastAPI Unified Gateway)

### Health & Telemetry
- `GET /api/v1/health` — Robot connection status, ROS bridge state, video/SSH status, driver stack.
- `GET /api/v1/telemetry` — Live sensor data: battery %, IMU, velocity, odometry position.
- `GET /api/v1/sensors` — Legacy alias for /api/v1/telemetry.
- `GET /api/v1/snapshot` — Single JPEG frame from the robot camera (204 if unavailable).

### Motion Control
- `POST /api/v1/control/move?linear=0.2&angular=0.0&linear_y=0.0` — Direct Twist command to /cmd_vel.
- `POST /api/v1/stop_all` — Global emergency stop.
- `POST /api/v1/reconnect` — Trigger ROS bridge reconnection.

### Video Streaming
- `GET /stream` — MJPEG video stream. First tries VideoBridge, then ROS bridge JPEG cache, then robot demo proxy.

### SLAM Mapping
- `GET /api/v1/slam/map` — PNG occupancy grid map from slam_toolbox.
- `GET /api/v1/slam/data` — Map metadata, robot pose (x, y, heading), LIDAR scan points.

### Audio & Voice
- `POST /api/v1/voice` — Speak text via voice module. Body: {"text": "hello"}.
- `POST /api/v1/voice/play` — Play built-in sound by ID.
- `POST /api/v1/control/voice` — Say, play, set volume, get status.
- `POST /api/v1/tapo/audio/listen` — Capture Tapo RTSP mic audio and transcribe.
- `POST /api/v1/tapo/audio/speak` — TTS through Pi audio output.
- `POST /api/v1/audio/upload` — Upload audio file for soundboard.

### Display
- `POST /api/v1/display` — Write text to OLED. Body: {"text": "...", "line": 0}.
- `POST /api/v1/display/clear` — Clear OLED.
- `POST /api/v1/display/scroll` — Start background scrolling text.

### Lightstrip & GPIO
- `POST /api/v1/led` — Set RGB. Body: {"r": 255, "g": 0, "b": 0}.
- `POST /api/v1/control/lightstrip` — Set, off, pattern, get_status.
- `POST /api/v1/control/buzzer` — Buzz piezo. Body: {"duration": 2.0}.
- `POST /api/v1/gpio` — Set GPIO pin (headlight LED).
- `GET /api/v1/gpio` — Get all GPIO pin states.

### Diagnostics
- `GET /api/v1/diagnostics/ros/topics` — ROS topic explorer.
- `POST /api/v1/diagnostics/ros/resync` — Force topic re-discovery.
- `POST /api/v1/diagnostics/ros/restart` — Restart bringup via SSH.
- `GET /api/v1/diagnostics/stack` — Full diagnostic stack (ROS nodes, I2C, serial).
- `GET /api/v1/diagnostics/logs` — Ring buffer logs (500 lines).
- `POST /api/v1/diagnostics/exec` — Sandboxed SSH command execution.

### Demos
- `GET /api/v1/demo` — Describe demo capabilities.
- `POST /api/v1/demo/draw` — Start drawing pattern.
- `POST /api/v1/demo/talkbot` — Start talkbot interaction.

### Agent & Missions
- `POST /api/v1/agent/mission` — Plan embodied mission from free text.
- `POST /api/v1/missions/run/{id}` — Run a named mission.
- `GET /api/v1/missions/status` — Current mission status.
- `POST /api/v1/missions/stop` — Abort current mission.

### LLM & Settings
- `GET /api/v1/settings/ollama/status` — Ollama connectivity check.
- `GET /api/v1/settings/ollama/models` — Local Ollama model list.
- `GET /api/v1/settings/lmstudio/status` — LM Studio connectivity check.
- `GET /api/v1/settings/lmstudio/models` — LM Studio model list.
- `GET /api/v1/settings/gpu` — GPU detection (nvidia-smi).
- `GET /api/v1/settings/llm` — Current LLM provider and model.
- `PUT /api/v1/settings/llm` — Update LLM provider/model.
- `POST /api/v1/chat` — Chat completion via Ollama/LM Studio with Yahboom preprompt.

### Tool Execution
- `POST /api/v1/control/tool` — Web dashboard bridge to yahboom_tool.

### Capabilities
- `GET /api/capabilities` — Runtime source of truth: tool surface, operations list, prompts, skills, features.
- `GET /api/v1/bridge/proxies` — Active MCP bridge proxy providers.

### Emergency
- `POST /api/v1/emergency` — Toggle red/blue LED strobe + siren sequence.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| YAHBOOM_IP | 192.168.1.11 | Robot IP address |
| YAHBOOM_FALLBACK_IP | (empty) | Ethernet recovery host |
| YAHBOOM_BRIDGE_PORT | 9090 | ROSBridge WebSocket port |
| YAHBOOM_CONNECTION | rosbridge | Bridge type: rosbridge, esp32, mock |
| YAHBOOM_ESP32_PORT | 2323 | ESP32 serial TCP port |
| YAHBOOM_USE_MOCK_BRIDGE | (unset) | Use mock bridge for testing |
| YAHBOOM_PASSWORD | yahboom | Pi SSH password |
| YAHBOOM_MISSION_TOPIC | /boomy/mission | ROS topic for mission JSON |
| YAHBOOM_GEMINI_API_KEY | (unset) | Gemini API key for mission planner |
| YAHBOOM_GEMINI_MISSION_MODEL | gemini-2.0-flash | Gemini model for mission planning |
| YAHBOOM_ROS2_CONTAINER | yahboom_ros2_final | Docker container name on robot |
| OLLAMA_BASE_URL | http://192.168.1.11:11434 | Ollama server URL |
| LMSTUDIO_BASE_URL | http://localhost:1234 | LM Studio server URL |
| MCP_BRIDGE_URLS | (empty) | Comma-separated MCP proxy URLs |
| DREAME_MAP_URL | (unset) | Dreame D20 Pro map API URL |

### CLI Arguments

`uv run python -m yahboom_mcp --mode [stdio|http|dual] --host 0.0.0.0 --port 10892 --robot-ip 192.168.1.11 --debug`

### Transport Modes

- **stdio** — MCP over stdin/stdout. Use for Claude Desktop, Cursor.
- **http** — FastAPI + SSE transport only. No MCP stdio.
- **dual** (default) — Both stdio and HTTP. Start with this for development.

## Architecture

The server uses a **Unified Gateway** pattern: FastMCP mounts directly onto a FastAPI ASGI app via `FastMCP.from_fastapi(app)`. This gives a single HTTP process with both MCP SSE endpoints and REST API routes. The lifecycle is managed via FastAPI's lifespan context manager: on startup it connects to the robot bridge (ROS/ESP32/Mock), starts the video bridge, and launches a watchdog for auto-reconnect. On shutdown it cleanly disconnects all bridges and stops all background tasks.

State is stored in a global `_state` dict (`state.py`): bridge, ssh, video_bridge, trajectory_manager, sequencer, and resync callback. Tools look up the current bridge from this shared state.

The **TCP bridge** (ROS2Bridge) maintains a roslibpy WebSocket to the robot's rosbridge_server. It publishes Twist commands to /cmd_vel, subscribes to /imu, /battery, /odom, /scan, and /camera/image, and maintains a cache of the latest sensor readings. An SSH control channel (SSHBridge) runs parallel for Pi-level operations (OLED, camera servo control via GPIO/I2C, hardware bringup restart, command execution).

For environments without a physical robot, the **Mock bridge** (MockROS2Bridge) simulates sensor data and velocity publishing, useful for CI testing and development.

## Data Sources

- **ROS 2 topics**: /cmd_vel (publish), /imu, /battery, /odom, /scan, /camera/image, /map (subscribe)
- **SSH control**: Docker container exec, GPIO sysfs, I2C bus, serial devices, filesystem
- **Dreame D20 Pro**: Optional map data via HTTP API
- **Ollama/LM Studio**: Local LLM for chat, mission planning, agentic workflows
- **Tapo camera**: Optional RTSP audio capture

## Error Handling

All tools return structured error responses. The portmanteau tool wraps all exceptions and returns `{"success": False, "operation": str, "error": str, "correlation_id": str}`. Common error scenarios:

- **Bridge not connected**: The robot is offline or rosbridge_server is not running. Check YAHBOOM_IP and robot power. Use POST /api/v1/reconnect to trigger a reconnection attempt.
- **SSH not available**: SSH bridge failed to connect. Verify YAHBOOM_PASSWORD and that SSH is enabled on the Pi (default username "pi").
- **cmd_vel not ready**: The robot driver has not published /cmd_vel yet. Wait for bringup or call ros_resync() to force topic re-discovery.
- **Operation timeout**: Motion commands and sensor reads have a 15-second timeout. On timeout, check robot WiFi signal strength and bridge connection.
- **Audio file not found**: When using audio(operation="play") or store operations, the local file path must be accessible from the server process.

## Security Model

The server binds to localhost by default (0.0.0.0 in production). CORS middleware is configured to allow all origins for web dashboard flexibility — restrict in production by setting specific origins in the CORSMiddleware configuration. SSH control commands are sandboxed: the /api/v1/diagnostics/exec endpoint blocks destructive commands (rm, mkfs, dd, shutdown, reboot, passwd). The execute_command operation in the portmanteau is also restricted. No authentication is implemented by default; deploy behind a reverse proxy with auth for production use. Mock bridge mode should NEVER be used with a real robot as it simulates sensor data that could mislead autonomous logic.

## Performance Characteristics

Motion commands take 10-50ms to reach the robot (WiFi + ROS bridge latency). Sensor reads are cached on the bridge and return instantly (sub-millisecond). The video stream runs at 10 FPS in fallback mode and up to 30 FPS with VideoBridge active. The MJPEG stream consumes approximately 1-5 Mbps of WiFi bandwidth depending on resolution and frame rate. The connection watchdog polls every 5 seconds and triggers a full reconnection sequence (3-5 seconds) if the bridge disconnects. SLAM map updates arrive at the same rate as the /map topic publishes (typically 1-5 Hz depending on slam_toolbox configuration).

## Version History

- 2.5.0b1: FastMCP >= 3.4.2, expanded prompts, prefab-ui, agent mission Gemini support.
- 2.4.0: Portmanteau refactor, skills registration, demo showcase, audio overhaul.
- 2.3.0: Lidar portmanteau, trajectory recording, Dreame D20 Pro map integration.
- 2.2.0: Unified Gateway, FastAPI lifespan, connection watchdog, auto-reconnect.
- 2.1.0: ROS 2 bridge, SSH control, IMU/battery telemetry, camera streaming.
- 2.0.0: Initial ROS 2 Humble support, mecanum motion, basic sensor reading.
