# yahboom-mcp — User Guide

## Quick Start

### Prerequisites

1. **Yahboom Raspbot v2 robot** — powered on, Raspberry Pi booted, ROS 2 Humble running.
2. **ROS 2 environment** — robot must be running `rosbridge_server` (websocket on port 9090). On the robot: `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`.
3. **Control computer** — Windows (this MCP server runs on the developer's workstation, not on the robot).
4. **Network** — Both machines on the same LAN. Robot default IP is 192.168.1.11 (WiFi hotspot mode). For production setups, connect both to the same WiFi router.
5. **MCP client** — Claude Desktop, Cursor IDE, Windsurf, or any FastMCP-compatible tool.

### Installation

```bash
# Clone the repository
git clone https://github.com/sandraschi/yahboom-mcp.git
cd yahboom-mcp

# Install dependencies with uv
uv sync --all-extras

# Set the robot IP (optional if using default 192.168.1.11)
$env:YAHBOOM_IP = "192.168.1.11"

# Start the server in dual mode (both MCP stdio + HTTP API)
uv run python -m yahboom_mcp.server --mode dual --port 10892
```

### First Connection

1. Verify the robot is reachable: `ping 192.168.1.11`
2. Start the server (see above). Wait for the log message: "Initial VideoBridge activation successful."
3. Check server health: `curl http://localhost:10892/api/v1/health` — look for `"ros": "connected"`.
4. Open the web dashboard at `http://localhost:10893` for the Mission Control UI.
5. In your MCP client, add this server to mcp_servers config:
```json
{
  "mcpServers": {
    "yahboom-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "D:/Dev/repos/yahboom-mcp", "python", "-m", "yahboom_mcp", "--mode", "stdio"]
    }
  }
}
```

## Tutorial 1: Health Check and Basic Diagnostics

Always start by checking the robot's health before any operation:

```
await yahboom_tool(operation="health_check")
```

Expected response:
```json
{
  "success": true,
  "operation": "health_check",
  "result": {
    "connected": true,
    "battery": 85,
    "voltage": 12.3,
    "cmd_vel_ready": true,
    "topics_count": 12
  }
}
```

If `connected` is false, check the robot IP, restart rosbridge on the robot, or try the reconnect endpoint: `POST /api/v1/reconnect`.

For a full diagnostic inspection (requires SSH):
```
await yahboom_tool(operation="inspect_stack")
```

This returns ROS node list, I2C bus state (for IMU/servos), voice module serial device status, and the driver stack inside the robot Docker container.

## Tutorial 2: Driving the Robot

The robot has four mecanum wheels, giving it **holonomic** motion: it can move forward, backward, strafe left/right, and rotate in place simultaneously.

### Forward and Backward
```
await yahboom_tool(operation="forward", param1=0.3)
# param1 = linear velocity in m/s. Range: 0.0 to 1.0. 0.3 is a safe walking pace.
```

To move backward, pass a negative velocity. However the portmanteau converts `backward` to negative:
```
await yahboom_tool(operation="backward", param1=0.2)
```

### Turning in Place
```
await yahboom_tool(operation="turn_left", param1=0.5)
# param1 = angular velocity in rad/s. 0.5 rad/s ~ 29 degrees/sec.
await yahboom_tool(operation="turn_right", param1=0.3)
```

### Strafe (Mecanum Sideways Movement)
```
await yahboom_tool(operation="strafe_left", param1=0.2)
await yahboom_tool(operation="strafe_right", param1=0.2)
```

### Stopping
```
await yahboom_tool(operation="stop")
# Publishes zero velocity and halts immediately.
await yahboom_tool(operation="stop_all")
# Emergency stop — also kills audio, stops trajectories, and cancels missions.
```

### Sequential Motion: Drive a Square Pattern
```
# 1. Check health first
await yahboom_tool(operation="health_check")

# 2. Forward 2 seconds
await yahboom_tool(operation="forward", param1=0.3)
import asyncio; await asyncio.sleep(2)
await yahboom_tool(operation="stop")

# 3. Turn left 90 degrees (~1.5 sec at 0.5 rad/s)
await yahboom_tool(operation="turn_left", param1=0.5)
await asyncio.sleep(1.5)
await yahboom_tool(operation="stop")

# 4. Repeat for each side...
```

## Tutorial 3: Reading Sensors

### IMU (Heading, Pitch, Roll)
```
await yahboom_tool(operation="read_imu")
```

Returns heading in degrees (0-360, 0 = North), pitch, roll, angular velocity (rad/s), and linear acceleration (m/s^2). The IMU is a 9-axis sensor (accelerometer + gyroscope + magnetometer) connected via I2C.

### Battery
```
await yahboom_tool(operation="read_battery")
```

Returns battery percentage (0-100), voltage, and whether the robot is charging. Below 20% is the low-warning threshold — avoid long motion sequences and consider recharging. Below 10% the robot may shut down unexpectedly.

### Combined Reading
```
await yahboom_tool(operation="read_all")
```

Returns IMU, battery, and encoder data in a single call. Useful for quick status snapshots before/after a mission.

### Encoders
```
await yahboom_tool(operation="read_encoders")
```

Returns wheel encoder counts for all four mecanum wheels. The odometry estimate is computed from these counts integrated over time.

## Tutorial 4: LIDAR Obstacle Detection

The robot's LIDAR (Yahboom /scan topic, optional Dreame D20 Pro) provides 360-degree obstacle detection.

### Read Obstacle Distances
```
await lidar(operation="read", source="yahboom")
```

Returns 8 sectors (front, front-left, left, back-left, back, back-right, right, front-right) with minimum distance in each sector and overall nearest obstacle distance. Use this to avoid collisions during autonomous navigation.

### Raw Scan Points
```
await lidar(operation="read_raw")
```

Returns the full LIDAR scan: an array of {angle, distance, intensity} points. Useful for detailed environment mapping or path planning.

### Dreame D20 Pro Map
```
await lidar(operation="read_dreame_map")
```

If DREAME_MAP_URL is configured, returns the Dreame D20 Pro vacuum cleaner's floorplan map data. This gives a house-level map that can overlay the robot's local LIDAR data.

## Tutorial 5: Voice and Audio

### Make the Robot Speak
```
await yahboom_tool(operation="say", param1="Hello, I am Boomy the robot!")
```

Text is spoken through the USB voice module connected to the Pi. The module uses a hardware speech synthesis chip with configurable volume (set via voice module's volume control).

### Built-in Sound Effects
```
await yahboom_tool(operation="play", param1=1)
```

Sound ID 1-15 map to built-in effects: 1=siren, 2=ding, 3=buzzer, 4=reveal, 5=alarm, 6=applause, 7=tada, 8=beep, 9=boo, 10=circus, 11=elevator, 12=fart, 13=clap, 14=sad_trombone, 15=coin.

### Audio File Playback
```
# Upload and play a local file
await audio(operation="play", file_path="C:/music/hello.mp3")

# Store a file on the robot for later use
await audio(operation="store", file_path="C:/music/jazz.mp3", file_name="background.mp3")

# Play a stored file
await audio(operation="play_stored", file_name="background.mp3")

# List stored files
await audio(operation="list_stored")

# Stop all playback
await audio(operation="stop")
```

### Built-in Sound Effects (Named)
```
await audio(operation="sound", file_name="ding")
await audio(operation="sound", file_name="fart")
await audio(operation="sound", file_name="siren")
```

Available named sounds: fart, ding, buzzer, clap, boo, circus, elevator, siren, applause, tada, sad_trombone, take_five, coin, zap, reveille, deguello, beep.

## Tutorial 6: Camera and Vision

### Streaming Video
Open `http://localhost:10892/stream` in any browser for an MJPEG video stream from the robot's camera. The stream auto-falls back from VideoBridge to ROS bridge JPEG cache to the robot's raw demo proxy.

### Snapshot for AI
```
# Fetches a single JPEG frame (good for VLM/vision AI ingestion)
GET http://localhost:10892/api/v1/snapshot
```

Returns 204 if no frame is available yet.

### Camera PTZ Control (Pan/Tilt Servos)
```
await yahboom_tool(operation="camera_up", param1=15)     # Tilt up 15 degrees
await yahboom_tool(operation="camera_down", param1=10)   # Tilt down 10 degrees
await yahboom_tool(operation="camera_left", param1=20)   # Pan left 20 degrees
await yahboom_tool(operation="camera_right", param1=30)  # Pan right 30 degrees
await yahboom_tool(operation="camera_reset")             # Reset to center
await yahboom_tool(operation="camera_set_pos", param1=90, param2=90)  # Set exact pan/tilt
await yahboom_tool(operation="camera_move", param1="up", param2=15)    # Move relative
```

The camera PTZ is controlled by two servos (pan and tilt) connected to the Pi's GPIO/I2C interface. The servos have a range of 0-180 degrees each, with (90, 90) being the center position.

## Tutorial 7: Display and LEDs

### OLED Display
The robot has a 128x64 monochrome OLED display (SSD1306) connected via I2C:

```
await yahboom_tool(operation="display", param1="Hello World", param2=0)
# param1 = text to display, param2 = line number (0-3)
await yahboom_tool(operation="clear_display")
```

### RGB Lightstrip
```
await yahboom_tool(operation="led", param1=255, param2=0, param3=0)  # Red
await yahboom_tool(operation="led", param1=0, param2=255, param3=0)    # Green
await yahboom_tool(operation="led", param1=0, param2=0, param3=255)    # Blue
await yahboom_tool(operation="led_off")                                  # Off
await yahboom_tool(operation="light_effect", param1="rainbow")          # Rainbow cycle
await yahboom_tool(operation="patrol_car")                               # Red/blue strobe
```

Available light effects: rainbow, breathe, fire, police, strobe.

## Tutorial 8: Trajectory Recording

The robot can record and replay motion trajectories for precise path following:

```
# Start recording
await yahboom_tool(operation="start_recording")

# Drive around manually
await yahboom_tool(operation="forward", param1=0.3)
# ... wait, turn, strafe, etc. ...

# Stop recording and save
await yahboom_tool(operation="stop_recording", param1="my_path")

# List all saved trajectories
await yahboom_tool(operation="list_trajectories")
```

Trajectories are stored as timestamped pose sequences on the server. Each trajectory contains (x, y, theta, timestamp) samples at ~10 Hz during the recording window.

## Tutorial 9: Agentic Workflow

Use the agentic workflow tool for high-level autonomous tasks. The LLM (via MCP sampling) plans and executes the steps:

```
await yahboom_agentic_workflow(goal="patrol in a square and report battery")
```

The agent will:
1. Call get_robot_health() to check connection and battery.
2. If battery > 20%, execute a square patrol (forward, turn left, repeat 4 times).
3. Read sensors again for the final battery report.
4. Summarize the outcome.

Other example goals:
- "check health, then move forward 2 seconds, report IMU heading"
- "trace a triangle: move forward 1 sec, turn 120 degrees, repeat 3 times"
- "explore forward until LIDAR shows an obstacle within 0.5m, then stop"

## Tutorial 10: LLM Mission Planning

The mission planner converts natural language to structured JSON plans using an LLM (Ollama or Gemini):

```
await yahboom_agent_mission(goal="find Benny the dog and guide him to the kitchen")
```

This generates a mission plan with intent, behavior sequence, target description, optional nav2 goal coordinates, and voice feedback. The plan is published as JSON on the /boomy/mission ROS topic for the Pi's mission executor to process.

The `speak` option reads the voice_feedback through the robot speaker:
```
await yahboom_agent_mission(goal="patrol the living room", speak=True, publish_to_ros=True)
```

Provider selection:
- `auto` — Prefers Gemini if YAHBOOM_GEMINI_API_KEY is set, falls back to Ollama.
- `ollama` — Force Ollama (requires OLLAMA_BASE_URL, default http://192.168.1.11:11434).
- `gemini` — Force Gemini (requires YAHBOOM_GEMINI_API_KEY).

## Tutorial 11: Demos (Show Floor Mode)

### Chalk Drawing
```
await yahboom_demo(operation="draw", pattern="smiley")
await yahboom_demo(operation="draw", pattern="heart")
await yahboom_demo(operation="draw_status")
await yahboom_demo(operation="draw_stop")
```

The robot draws patterns on the floor using two-color chalk (pauses mid-way for chalk swap unless skip_color_swap_pause=True). Uses precise mecanum path execution.

### Talkbot (Interactive Social Mode)
```
await yahboom_demo(operation="talkbot", max_turns=5, approach=True)
```

The robot approaches (optional), does a playful camera PTZ wiggle, says "Hi, I am Boomy. Who are you?", then listens for responses and replies. Uses speech-mcp TTS when available, otherwise eSpeak on the Pi.

```
await yahboom_demo(operation="talkbot_status")
await yahboom_demo(operation="talkbot_stop")
```

## Tutorial 12: ROS 2 Management

### List ROS Topics
```
await ros_topic_list()
```

Returns all active ROS 2 topics with their message types. Typical output includes /cmd_vel (geometry_msgs/Twist), /imu (sensor_msgs/Imu), /battery (sensor_msgs/BatteryState), /odom (nav_msgs/Odometry), /scan (sensor_msgs/LaserScan), /camera/image (sensor_msgs/Image).

### Node Info
```
await ros_node_info(node_name="/yahboom_driver")
```

Returns publishers, subscribers, and services for the specified ROS 2 node.

### Resync Topics
```
await ros_resync()
```

Forces re-discovery of all ROS 2 topics. Use if telemetry shows zeros while wheels still respond.

### Restart Bringup (Nuclear Option)
```
await ros_restart_bringup()
```

Restarts the entire Yahboom bringup launch file inside the robot Docker container. Use as last resort when the robot is completely unresponsive. The server waits 5 seconds then resyncs topics.

## Tutorial 13: Web Dashboard

The web dashboard (http://localhost:10893) provides:

1. **Dashboard** — Live robot status, battery gauge, connection indicators.
2. **Mission Control** — Telemetry panel (IMU heading, battery, velocity), motion control sliders, LIDAR visualization, camera stream.
3. **3D Viz** — SLAM map overlay with robot pose marker, LIDAR scan points.
4. **Chat** — LLM-powered chat with Yahboom context preprompt. Ask about the robot, get troubleshooting help, plan missions.
5. **Settings** — LLM provider/model configuration, Ollama/LM Studio status.
6. **Help** — Multi-level help system mirroring yahboom_help_tool.
7. **Emergency** — Stop-all button and emergency strobe toggle.

## Tutorial 14: Emergency Procedures

### Immediate Stop
```
await yahboom_tool(operation="stop")
# or stronger:
await yahboom_tool(operation="stop_all")
```

### Emergency Strobe Mode
`POST /api/v1/emergency` with `{"active": true}` — activates red/blue LED strobe + siren. Toggle off with `{"active": false}`.

### When Robot is Unresponsive
1. Check `GET /api/v1/health` — is ROS connected?
2. If not, try `POST /api/v1/reconnect`.
3. If still down, check robot power and WiFi.
4. Last resort: `ros_restart_bringup()` to restart all ROS 2 nodes.

## REST API Reference

### Health and Status
```
GET /api/v1/health
Response: {status: "online", robot_connection: {ros, video, ssh}, stack: {...}, system: {uptime, version}}
```

### Telemetry
```
GET /api/v1/telemetry
Response: {battery: 85, voltage: 12.3, imu: {heading: 180.5, pitch: 0.2, roll: -0.1}, velocity: {linear: 0.0, angular: 0.0}, status: "live"}
```

### Motion Control
```
POST /api/v1/control/move?linear=0.3&angular=0.0
Response: {status: "success", command: {linear: 0.3, angular: 0.0, linear_y: 0.0}}
```

### Capabilities
```
GET /api/capabilities
Response: {status: "ok", server: {name, version}, tool_surface: {portmanteau_count, atomic_tools}, features: {sampling, agentic_workflows, prompts}}
```

## Troubleshooting

### Common Issues

**"ROS bridge not connected"**
Check robot IP (`YAHBOOM_IP`), ensure robot is running `rosbridge_server`, verify network connectivity with ping.

**"SSH not connected"**
Verify `YAHBOOM_PASSWORD` is correct. Default is "yahboom". The robot must have SSH enabled.

**No video stream**
Wait 10-15 seconds after server start for video bridge activation. Check `/api/v1/health` — video should show "active".

**Dashboard blank**
Ensure BrowserRouter is present in the frontend. Check browser console for JavaScript errors.

**Port conflict on 10892**
Run `netstat -ano | findstr 10892` to find the conflicting process, or change the port with `--port`.

**MCP client cannot find tools**
Verify the server is running in stdio or dual mode. Check MCP client logs for connection errors.

**Motion commands do nothing**
Check `cmd_vel_ready` in health response. If false, the robot's ROS driver may not have published the /cmd_vel topic yet. Use `ros_resync()` or wait for bringup to complete.

**Low battery warnings**
Below 20%: avoid long motion sequences. Below 10%: recharge immediately. Motion at low battery may cause sudden shutdown if voltage drops under load.

### FAQ

**Q: Can I control the robot without ROS?**
A: Yes, use connection_type=esp32 for direct serial control, or use the mock bridge for testing.

**Q: Does the robot need internet?**
A: No. All control is local over LAN. Ollama runs on the robot or local workstation. Gemini missions need internet for the API call.

**Q: How do I update the robot's software?**
A: Use `just deploy-upgrades` which runs deploy_robot_upgrades.py over SSH.

**Q: What is the max range?**
A: WiFi range depends on your access point. Typically 30-50m indoors. The robot uses an onboard Raspberry Pi 5, so it stays connected as long as WiFi reaches.

**Q: Can I use multiple control methods simultaneously?**
A: Yes. The MCP tool and REST API access the same bridge state. Commands from Claude Desktop and the web dashboard work concurrently.

**Q: How do I add a new sound effect?**
A: Upload the audio file via `audio(operation="store")` or use the web dashboard upload form, then play it with `audio(operation="play_stored")`.

## Tutorial 15: SLAM Mapping and Navigation

The robot supports real-time SLAM (Simultaneous Localization and Mapping) using slam_toolbox, which provides occupancy grid maps of the environment and estimates the robot's pose within that map.

### Viewing the SLAM Map
```
GET http://localhost:10892/api/v1/slam/map
```
Returns a PNG image of the current occupancy grid. White pixels are free space, black pixels are obstacles, gray pixels are unknown areas.

### Getting Map Data for Overlay
```
GET http://localhost:10892/api/v1/slam/data
```
Returns JSON with map dimensions (width, height, resolution), robot pose (x, y, heading in degrees), and LIDAR scan points for rendering an overlay on the web dashboard.

### Starting Exploration and Mapping
```
await yahboom_tool(operation="explore_and_map")
```
Starts autonomous exploration: the robot moves through the environment while slam_toolbox builds the map. The map is viewable in real-time via the web dashboard 3D Viz page.

### Required Robot Setup
For SLAM to work, the robot must be running slam_toolbox and publishing the /map topic. On the robot:
```
ros2 launch slam_toolbox online_async.launch.py
```
The robot's odometry (from wheel encoders or an external tracking system) provides the initial pose estimate. The LIDAR scan data (/scan topic) is used for loop closure and map refinement.

## Tutorial 16: MCP Bridge Federation

The server supports MCP bridge proxies for multi-server federation. Set MCP_BRIDGE_URLS with comma-separated URLs of other MCP servers to proxy their tools through this server:

```
$env:MCP_BRIDGE_URLS = "http://localhost:10966/mcp,http://localhost:10944/mcp"
```

This mounts the remote servers' tools alongside yahboom-mcp's own tools. Use GET /api/v1/bridge/proxies to see active proxies.

## Tutorial 17: Integration with Other Fleet MCP Servers

### speech-mcp Integration
The demo talkbot uses speech-mcp for TTS when reachable at speech-mcp's default URL, falling back to eSpeak on the Pi. Set `use_speech_mcp=true` (default) to use speech-mcp, or `false` for local-only eSpeak.

### freecad-mcp Integration
Export CAD models from freecad-mcp as STL or STEP files, then transfer them to the robot via SSH for 3D printing or fabrication. The robot's Pi can run PrusaSlicer for G-code generation directly.

### Monitoring-mcp Integration
Feed robot telemetry (battery, IMU, position) into monitoring-mcp for fleet-wide robot health dashboards and alerting. The /api/v1/telemetry endpoint returns structured JSON that monitoring-mcp can ingest.

### Custom Integration Example
```python
import httpx
# Read telemetry from yahboom-mcp
r = httpx.get("http://localhost:10892/api/v1/telemetry")
telemetry = r.json()
print(f"Battery: {telemetry['battery']}%, Heading: {telemetry['imu']['heading']}°")
# Send a motion command
r = httpx.post("http://localhost:10892/api/v1/control/move", params={"linear": 0.3, "angular": 0.0})
print(r.json())
```

## Tutorial 18: GPIO and Hardware Control

### Headlight LED
The robot has a GPIO-controlled headlight LED on GPIO 17:
```
await yahboom_tool(operation="execute_command", param1='echo 1 > /sys/class/gpio/gpio17/value')
await yahboom_tool(operation="execute_command", param1='echo 0 > /sys/class/gpio/gpio17/value')
```

Or use the REST API:
```
POST /api/v1/gpio {"pin": "headlight", "value": true}
GET /api/v1/gpio  # list all GPIO states
```

### Piezo Buzzer
```
POST /api/v1/control/buzzer {"duration": 2.0}
```
Buzzer is controlled via I2C, not GPIO.

### I2C Bus
The IMU, OLED display, and servo controller are all on the I2C bus (addresses 0x68 for IMU, 0x3C for OLED). Check I2C device presence:
```
await yahboom_tool(operation="inspect_stack")
```
The diagnostic output includes I2C bus detection results.

## Tutorial 19: Audio Soundboard (Built-in Effects)

The audio tool's `sound` operation gives access to 17 built-in sound effects. These are stored as WAV files on the Pi and play through the USB voice module speaker:

```
Fart:       audio(operation="sound", file_name="fart")
Ding:       audio(operation="sound", file_name="ding")
Buzzer:     audio(operation="sound", file_name="buzzer")
Clap:       audio(operation="sound", file_name="clap")
Boo:        audio(operation="sound", file_name="boo")
Circus:     audio(operation="sound", file_name="circus")
Elevator:   audio(operation="sound", file_name="elevator")
Siren:      audio(operation="sound", file_name="siren")
Applause:   audio(operation="sound", file_name="applause")
Tada:       audio(operation="sound", file_name="tada")
Sad Trombone: audio(operation="sound", file_name="sad_trombone")
Take Five:  audio(operation="sound", file_name="take_five")
Coin:       audio(operation="sound", file_name="coin")
Zap:        audio(operation="sound", file_name="zap")
Reveille:   audio(operation="sound", file_name="reveille")
Deguello:   audio(operation="sound", file_name="deguello")
Beep:       audio(operation="sound", file_name="beep")
```

Combine sounds with motion for interactive robot performances. For example, a robot dance routine: play circus music, set rainbow light effect, and execute forward/backward/strafe motion in sequence.

## Tutorial 20: Full Autonomous Patrol Mission

Complete end-to-end patrol workflow using multiple tools:

```
Step 1: Health check
await yahboom_tool(operation="health_check")
# Ensure battery > 20% and ROS is connected

Step 2: Set lights to patrol mode
await yahboom_tool(operation="patrol_car")

Step 3: Write status to OLED
await yahboom_tool(operation="display", param1="PATROL ACTIVE", param2=0)

Step 4: Start trajectory recording
await yahboom_tool(operation="start_recording")

Step 5: Execute patrol pattern using agentic workflow
await yahboom_agentic_workflow(goal="patrol in a square: forward 2s, turn left 90 degrees, repeat 4 times")

Step 6: Stop recording
await yahboom_tool(operation="stop_recording", param1="patrol_route")

Step 7: Final health check
await yahboom_tool(operation="read_all")

Step 8: Turn off lights
await yahboom_tool(operation="led_off")

Step 9: Clear display
await yahboom_tool(operation="clear_display")

Step 10: Sign off
await audio(operation="sound", file_name="tada")
```

## Robot Hardware Reference

### Yahboom Raspbot v2 Specifications
- **Platform**: Raspberry Pi 5 (4GB or 8GB RAM)
- **ROS Distribution**: ROS 2 Humble Hawksbill
- **Drivetrain**: 4x mecanum wheels, 4x encoder-equipped motors
- **Max linear velocity**: 1.0 m/s (firmware-limited)
- **Max angular velocity**: 2.0 rad/s (firmware-limited)
- **Sensors**: 9-axis IMU (MPU9250), 360-degree LIDAR (YDLIDAR X4), wheel encoders, camera (USB or Pi Camera)
- **Display**: 128x64 OLED SSD1306 (I2C, address 0x3C)
- **Lighting**: RGB LED lightstrip (WS2812B-style)
- **Audio**: USB voice module with hardware speech synthesis, piezo buzzer (I2C)
- **Camera PTZ**: 2x servos (pan on GPIO-18, tilt on GPIO-13)
- **Battery**: 11.1V 3S LiPo, 2200mAh, ~30-60 min runtime
- **WiFi**: 2.4/5 GHz onboard Pi 5 WiFi
- **Dimensions**: ~250x250x200mm (LxWxH)
- **Weight**: ~1.5 kg

### Port Assignment
- **10892**: Backend (REST + MCP SSE)
- **10893**: Frontend (Vite dev dashboard)
- **9090**: ROSBridge WebSocket (robot internal)
- **6000**: ROSBridge alternative port (robot hotspot mode)
- **6001**: Raspberry Pi demo video feed
- **2323**: ESP32 serial bridge
- **11434**: Ollama (robot or local)
- **1234**: LM Studio (local workstation)

## Using the Justfile

The project includes a justfile for common operations:

- `just serve` — Start the MCP server in dual mode on port 10892
- `just stdio` — Start in stdio mode for MCP clients
- `just web` — Start the web dashboard frontend
- `just dev` — Start server with hot reload (uvicorn)
- `just lint` — Run ruff + TypeScript + Biome linting
- `just fix` — Auto-fix and format all code
- `just test` — Run full pytest suite
- `just test-unit` — Fast unit tests only
- `just health` — Check robot health via script
- `just patrol` — Run autonomous patrol mission
- `just embodied` — Start embodied AI observation loop
- `just deploy-cognitive` — Deploy cognitive pack to robot

## Troubleshooting Advanced Topics

### Debugging Connection Issues
To diagnose why the bridge won't connect, start the server with `--debug` for verbose logging:
```
uv run python -m yahboom_mcp.server --mode dual --port 10892 --debug
```

### Checking Robot Logs via SSH
```
await yahboom_tool(operation="execute_command", param1="docker logs yahboom_ros2_final --tail 50")
```

### Resetting the Robot Mid-Session
If the robot becomes unresponsive:
1. Call ros_restart_bringup() to restart ROS nodes
2. Wait 10 seconds
3. Check health with yahboom_tool(operation="health_check")
4. If still offline, call POST /api/v1/reconnect
5. As last resort, power-cycle the robot

### Audio Playback Troubleshooting
If audio files don't play:
- Check that the USB voice module is connected and recognized: inspect_stack should show /dev/ttyUSB0
- Verify file exists on Pi: execute_command with "ls -la ~/boomy_audio/"
- Test with a built-in sound first: audio(operation="sound", file_name="ding")
- The voice module supports WAV and MP3 at sample rates up to 48kHz

### Mission Planning Troubleshooting
If the agent_mission tool returns errors:
- Check which LLM provider is configured. If using Ollama, verify YAHBOOM_IP points to a machine running Ollama (default http://192.168.1.11:11434). If using Gemini, ensure YAHBOOM_GEMINI_API_KEY is set correctly.
- The mission planner requires an LLM that can output valid JSON without markdown fences. If you get JSON parse errors, try a different model (gemini-2.0-flash is recommended for Gemini, llama3.2 or qwen2.5 for Ollama).
- Set publish_to_ros=false to test the plan generation without sending it to the robot.
- Use speak=true to get verbal feedback from the robot confirming the mission plan was received.

### Tapo Audio Integration
If you have a Tapo camera (e.g., Tapo C200) integrated with the robot:
- The robot can use the Tapo camera's built-in microphone for listening and its speaker for TTS output, extending the audio capabilities beyond the USB voice module.
- Configure Tapo credentials via TAPO_EMAIL and TAPO_PASSWORD environment variables.
- The Tapo communicates over the local network (RTSP for audio streaming, HTTP for control).
- POST /api/v1/tapo/audio/listen captures audio from the camera's RTSP stream and transcribes it using faster-whisper.
- POST /api/v1/tapo/audio/speak converts text to speech and plays it through the camera's speaker.
- The Tapo two-way audio feature is useful for remote interaction: you can hear what the robot hears and speak through the robot's location.
- Check Tapo connectivity at any time with GET /api/v1/tapo/audio/status.

### Performance Optimization Tips
For the best robot control experience:
- Keep the robot within strong WiFi range. The ROS bridge connection drops above ~50m indoor distance or through multiple walls. A dedicated 5 GHz access point near the robot's operating area provides the best performance.
- Reduce camera resolution if the video stream lags. The default 640x480 at 10 FPS is a good balance of quality and bandwidth for AI vision.
- For mission-critical operations, connect the robot via ethernet to a Raspberry Pi Compute Module or use YAHBOOM_FALLBACK_IP for ethernet recovery.
- The IMU heading drifts over time due to magnetometer interference from the motors. Re-calibrate by calling read_imu after 30 seconds of stationary operation. For accurate heading data, ensure the robot is on a level surface.
- Battery readings are more accurate when the robot is stationary. Under heavy acceleration, voltage sag can cause the reported percentage to drop temporarily by 5-10%.
- Restart the server periodically (every 24-48 hours) to clear the log ring buffer and prevent memory growth from long-running video streaming.
- When using the agentic workflow for multi-step tasks, prefer concise goals (under 200 characters) for faster planning. Very long or ambiguous goals may cause the LLM to produce incomplete or incorrect step sequences.
- The OLED display driver supports both SSD1306 and SH1106 controllers. If your display shows garbled characters, try setting the driver to "sh1106" in the display request.

### Camera Stream Issues
If the video stream shows no image:
- Check health: video should show "active" in robot_connection
- The camera needs 10-15s to initialize after server start
- Try accessing the robot's raw stream directly at http://192.168.1.11:6001/video_feed
- The server auto-falls back through three tiers: VideoBridge → ROS bridge JPEG cache → robot demo proxy
