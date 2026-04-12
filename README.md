# Yahboom ROS 2 MCP Server (v2.2.0-alpha.2)

> [!IMPORTANT]
> **HARDWARE HANDSHAKE SUCCESSFUL**: The "Split-Brain" architecture has been resolved. The `/dev/ttyUSB0` serial port is now successfully reclaimed from the host demo and bridged via a Micro-ROS sidecar. Motors, IMU, ultrasonic sensors, and actuators are now native to the ROS 2 graph.

Industrial-grade agentic control interface for the **Yahboom Raspbot v2** (Raspberry Pi 5 / ROS 2 Humble). This project is a core component of the [Robotics Fleet](docs/fleet_overview.md).

##  Federated Robotics Fleet
Yahboom-MCP operates as a specialized manipulation and navigation node within a wider federated fleet including:
- **Dreame-MCP**: Floor mapping and autonomous sweeping.
- **Virtual-Robotics-MCP**: Physics-based simulation and testing.
- **Central-Hub**: Intelligent orchestration and fleet-wide lifecycle management.

##  SOTA 2026 Architecture (v2.2.0-alpha.2)

### ✨ The "iPad Gemini" Breakthrough
This version marks the successful execution of the **Rosmaster Blueprint**. Credit is due to the **iPad Gemini** for the architectural breakthrough that identified the dual-brain de-synchronization between the host and the ROS 2 workstation. This insight allowed us to surgically deactivate the factory bypass and restore the formal control plane.

This server is built on **FastMCP 3.1** and implements high-density agentic workflows using the **Portmanteau Pattern**, **sampling** (SEP-1577), **prompts**, **skills**, and **scripts**.

- **Port**: `10792` (backend), `10893` (Vite dashboard)
- **Protocol**: FastMCP 3.1
- **AI Core**: SEP-1577 sampling via `yahboom_agentic_workflow`; prompts for quick-start, patrol, diagnostics.

##  Tools

| Tool | Description |
|------|-------------|
| `yahboom(operation, ...)` | Single operation: health_check, forward, backward, turn_left, turn_right, strafe_*, stop, read_imu, read_battery, trajectory recording, config_show |
| `yahboom_help(category, topic)` | Multi-level help (motion, sensors, connection, api, mcp_tools, startup, troubleshooting) |
| `yahboom_agentic_workflow(goal)` | High-level goal; LLM plans and runs a sequence of health/motion/sensor steps (sampling with sub-tools) |

##  Sensory Hub & Expansion (RPi 5 Bridge)

Boomy's sensory substrate is expanded via a dedicated **Peripheral Bridge** running on the Pi 5, mapping local GPIO and I2C sensors to the ROS 2 bus.

- **Ultrasound (Sonar)**: Proximity detection for reactive avoidance (Benny-safe).
- **Line Follower**: Cliff detection (Table Guard) and line navigation.
- **Physical Button**: Top-mounted "KEY" button for silencing alarms (Snooze) and aborting missions.
- **Auto-Discovery**: I2C bus scanning for SSD1306/SH1106 displays and environmental sensors.

> [!TIP]
> Details on the ESP32-S3 co-processor can be found in [ROSMASTER_ESP32.md](docs/hardware/ROSMASTER_ESP32.md). The factory bypass audit is recorded in [LEGACY_DEMO_AUDIT.md](docs/factory/LEGACY_DEMO_AUDIT.md).

### Peripheral & display env (host running MCP)

| Variable | Purpose |
|----------|---------|
| `YAHBOOM_OLED_PAUSE_ROS` | `1` (default): stop stock `oled_node` before luma OLED writes so the display is not overwritten. Set `0` to skip. |
| `YAHBOOM_DISPLAY_CMD_PREFIX` | Optional prefix before `python3` on SSH (e.g. `docker exec -i yahboom_ros2`) if luma/I2C must run in a container. |
| `YAHBOOM_VOICE_BAUD` | Serial baud for the AI voice module (default `9600`). |
| `YAHBOOM_VOICE_DEVICE` | Force serial path on the robot (e.g. `/dev/ttyUSB1`) when auto-discovery picks the wrong port. |
| `YAHBOOM_VOICE_USB_IDS` | Extra `vid:pid` values (comma-separated) for nonstandard USB-UART chips. |
| `YAHBOOM_LINE_TOPIC` / `YAHBOOM_LINE_MSG_TYPE` | Override ROS topic/type for line sensors (default `/line_sensor`, `std_msgs/Int32MultiArray`). |

See [CHANGELOG.md](CHANGELOG.md) for recent bridge and webapp fixes.

##  Mission Intelligence

Advanced autonomous behaviors utilizing the expanded sensory substrate for safe navigation.

- **"Cliff Guard" Dominance**: Real-time cliff detection overrides all movement with an immediate `Emergency Halt`.
- **"Benny-Safe" Avoidance**: Reactive state-machine that executes a 45 tangent-pivot maneuver to bypass obstacles detected by sonar.
- **Physical Silence**: The hardware button provides an immediate manual override for "Smart Alarm" and "Emergency Mode" sequences.

> [!IMPORTANT]
> Detailed autonomous logic and avoidance maneuvers are documented in [AVOIDANCE_STRATEGY.md](docs/AVOIDANCE_STRATEGY.md).

##  Prompts

- `yahboom_quick_start(robot_ip)`  Setup and connect instructions
- `yahboom_patrol(duration_seconds)`  Patrol plan (e.g. square)
- `yahboom_diagnostics()`  Diagnostic checklist

##  Skills & Scripts

- **skills/yahboom-operator.md**  Operator skill: tool usage, prompts, workflow rules
- **skills/yahboom-robots-expert.md**  Expert skill: hardware, ROS 2, URDF/frames, mecanum, fleet integration
- **scripts/check_health.py**  REST health/telemetry (no MCP client): `python scripts/check_health.py [--base http://localhost:10792]`
- **scripts/run_patrol_square.ps1**  Check server and print agentic workflow usage

##  Getting Started

**Robot connection:** The server connects to ROSBridge on the robot. **WiFi is the primary interface.** Set `YAHBOOM_IP` to the robot's WiFi IP (check your router's DHCP table for `raspberrypi`). The Ethernet static IP `192.168.0.250` is the fallback for recovery only  set via `YAHBOOM_FALLBACK_IP`. Rosbridge port: `YAHBOOM_BRIDGE_PORT=9090` (default).

```powershell
git clone https://github.com/sandraschi/yahboom-mcp.git
Set-Location yahboom-mcp
uv sync --extra dev --extra robot-pi

# Start server (stdio for Cursor/Claude; dual for dashboard + MCP)
uv run python -m yahboom_mcp.server --mode stdio
# Or with web dashboard  set YAHBOOM_IP to the robot's WiFi IP:
$env:YAHBOOM_IP = "192.168.0.105"; uv run python -m yahboom_mcp.server --mode dual --port 10792
# Ethernet fallback (recovery/initial setup only):
$env:YAHBOOM_IP = "192.168.0.250"; uv run python -m yahboom_mcp.server --mode dual --port 10792
```

**Raspberry Pi (voice + OLED over SSH):** install the same Python stack on the robot once. The script must be **piped or redirected into** `bash -s` (do not put the file path after `ssh` as a separate argument).

PowerShell (from the repo machine):

```powershell
Get-Content -Raw "D:\Dev\repos\yahboom-mcp\scripts\robot\install_peripherals_pi.sh" | ssh pi@192.168.1.11 "bash -s"
```

(Replace the IP with your robot. Adjust the path if your clone lives elsewhere.)

Or copy and run on the Pi:

```powershell
scp "D:\Dev\repos\yahboom-mcp\scripts\robot\install_peripherals_pi.sh" pi@192.168.1.11:/tmp/
ssh pi@192.168.1.11 "bash /tmp/install_peripherals_pi.sh"
```

(`uv sync --extra robot-pi` only affects your dev PC; the Pi needs its own `pip3` as above.)

##  SOTA Webapp Dashboard

Backend API: [http://localhost:10792](http://localhost:10792) (when running `--mode dual`).  
Dashboard UI: [http://localhost:10893](http://localhost:10893) (Vite dev server; start via `webapp/start.bat` or `start.ps1`).

##  Hardware Diagnostics & Boomy Insight

This project includes a high-performance diagnostic bridge to resolve the Raspberry Pi 5's I2C timing anomalies.

### PTZ Gimbal Wiring (0x41)
For Pan-Tilt-Zoom troubleshooting, use the following sequence:
- **Pins**: GND (Black), VCC (Red), SCL (Yellow), SDA (White).
- **Image**: [PTZ Blueprint](file:///C:/Users/sandr/.gemini/antigravity/brain/e51835f9-38cd-4fa1-8303-53b65f60f6b1/boomy_ptz_wiring_diagram_1774998094869.png) (Local Cache)

### Recovery SOP: SSD Failure
If the Pi 5 encounters a hardware-level power crash due to high-speed SSD substrate:
1. **Unplug SSD** and decommission the RTL9210 bridge.
2. **Revert to MicroSD** baseline @ 192.168.0.250.
3. **Restart Services**: `systemctl --user restart boomy-gateway`.

- **Diagnostic Dashboard**: Access via `/diagnostics` for real-time `dmesg` streaming and I2C health status.

##  Status & Compliance
- [x] FastMCP 3.1 (sampling, prompts)
- [x] SEP-1577 agentic workflow tool
- [x] Multi-MCP Integration (Resonite/HumeReady)
- [x] SOTA 2026 Webapp Visuals
- [x] Federated Fleet Integration
- [x] **Sensory Hub & "Benny-Safe" Avoidance**
- [x] **Physical Button Override**

##  Documentation
For detailed guides on fleet architecture, integration, and status, see the [docs](docs/) directory:
- [Connectivity Guide](docs/CONNECTIVITY.md)  WiFi setup and robot IP discovery.
- [Architecture](docs/architecture.md)  System design and Portmanteau pattern.
- [Pi-less Setup](docs/PI_LESS_SETUP.md)  High-performance PC-as-Brain configuration.
- [Hardware & ROS 2](docs/HARDWARE_AND_ROS2.md)  Pi tiers, ROS 2 interaction, terminal tools, LIDAR integration.
- [Sensory Hub](docs/SENSORY_HUB.md)  Technical details on Ultrasound, Line sensors, and Pi 5 Button mapping.
- [Avoidance Strategy](docs/AVOIDANCE_STRATEGY.md)  "Benny-Safe" reactive navigation and Cliff Guard logic.
- [Raspbot motion troubleshooting](docs/RASPBOT_MOTION_TROUBLESHOOTING.md)  Camera works but no drive; SSH and `/cmd_vel` checks.
- [Webapp 3D Viz](docs/WEBAPP_3D_VIZ.md)  R3F scene, Y-up vs URDF Z-up, wheel/chassis placement.
- [Testing](docs/TESTING.md)  pytest layout, `MockROS2Bridge`, `YAHBOOM_USE_MOCK_BRIDGE`, hardware markers.
- [Embodied AI](docs/EMBODIED_AI.md)  Observe -> LLM -> act loop, snapshot/move API.
- [Neurophilosophy overview](docs/NEUROPHILOSOPHY_OVERVIEW.md)  Damasio, GWT, IIT, enactivism; arxiv papers; link to embodied loop.
- [Boomy Racing Vision](docs/BOOMY_RACING_VISION.md)  Dual-robot competition, "Shazbat!" collision protocol, and FPV racing.
- [AI & Vision Capabilities](docs/AI_CAPABILITIES.md)  Local LLMs and computer vision on RPi 5.
- [Fleet Overview](docs/fleet_overview.md)  Vision for the federated robotics fleet.
- [Integration Guide](docs/integration_guide.md)  Cross-robot workflows.
- [Project Status](docs/status.md)  Roadmap and completion metrics.
- [WiFi Transition Guide](docs/WIFI_TRANSITION.md)  Ethernet-to-AP migration steps.
