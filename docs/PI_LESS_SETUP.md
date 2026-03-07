# Pi-less Setup: PC-as-Brain (Raspbot v2 for ~$100)

Run the Yahboom Raspbot v2 **without the Raspberry Pi**. The chassis + ROSMASTER board + ESP32 WiFi bridge keeps the robot under roughly **$100**; your PC runs the MCP server, ROS 2 (optional), and all AI/vision.

---

## 1. Why Pi-less?

| Setup | Cost | Use case |
|-------|------|----------|
| **With Pi 5** | Chassis + Pi (~$100 extra) | Autonomous, portable, full camera/LIDAR on robot. |
| **Pi-less (ESP32 bridge)** | Chassis + ESP32 (~$5) | **~$100 total bot.** Fleet in one room, PC does all compute; WiFi link to robot. |

**Best for**: Fleet of cheap bots in a single space with good WiFi; one powerful PC runs yahboom-mcp for all of them.

---

## 2. Hardware

- **Raspbot v2 chassis** (mecanum wheels, motors, ROSMASTER/STM32 controller board).
- **ESP32** (e.g. ESP32-WROOM, ~$5) with **3.3V serial** to the controller’s serial header (TX/RX/GND). Check your board’s pinout; often a 4-pin serial connector.
- **Power**: ESP32 from USB or from robot 5V/3.3V if available.
- **No Raspberry Pi**, no camera/LIDAR on robot unless you add them separately (see Limitations).

### Wiring (ESP32 ↔ ROSMASTER)

| ESP32      | ROSMASTER board |
|------------|------------------|
| TX (GPIO17) | RX (serial in)   |
| RX (GPIO16) | TX (serial out)  |
| GND         | GND              |

Use 3.3V logic; do not connect 5V to ESP32 pins.

---

## 3. ESP32 firmware options

### Option A: Transparent bridge (esp-link style)

- Flash **esp-link** or any “TCP to serial” firmware.
- PC opens a TCP connection to the ESP32’s IP (e.g. port **23**); bytes sent go to the board’s serial, bytes from the board come back.
- The MCP server then must speak the **ROSMASTER board’s native serial protocol** (vendor-specific). If you have the protocol doc, we can add a parser; otherwise use Option B.

### Option B: Protocol bridge (recommended)

- Flash a **custom ESP32 sketch** that:
  - Talks to the ROSMASTER over serial (using the board’s existing protocol or simple custom commands).
  - Talks to the PC over TCP using the **yahboom-mcp text protocol** below.
- The MCP server uses the same protocol; no need to implement the board’s native protocol on the PC.

---

## 4. Yahboom-MCP ↔ ESP32 protocol (Option B)

Connection: TCP to `ESP32_IP:port` (default port **2323**). Line-based text, UTF-8, newline `\n`.

### PC → robot (commands)

| Line | Meaning |
|------|--------|
| `CMD,{linear_x},{linear_y},{angular_z}\n` | Twist: linear x/y (m/s), angular z (rad/s). Example: `CMD,0.2,0.0,0.0\n` |

Sent when velocity changes (e.g. from MCP tools or dashboard).

### Robot → PC (telemetry)

ESP32 sends one line per sensor update (order and frequency up to the sketch):

| Line | Meaning |
|------|--------|
| `IMU,{heading},{pitch},{roll},{yaw}\n` | Degrees (float). |
| `BAT,{percentage},{voltage}\n` | Battery 0–100, voltage (float). |
| `ODOM,{x},{y},{z},{linear},{angular}\n` | Position (m), linear velocity (m/s), angular (rad/s). |

Example:

```
IMU,45.2,0.1,-0.3,-45.2
BAT,82,11.8
ODOM,0.1,0.0,0.0,0.0,0.0
```

The MCP server parses these into the same internal state as the ROS 2 bridge, so tools and the dashboard work unchanged.

---

## 5. Enabling the ESP32 bridge

Set environment variables and (re)start the server:

| Variable | Meaning | Example |
|----------|---------|--------|
| `YAHBOOM_CONNECTION` | `rosbridge` (default) or `esp32` | `esp32` |
| `YAHBOOM_IP` | Robot or ESP32 IP | `192.168.1.20` |
| `YAHBOOM_BRIDGE_PORT` | Rosbridge port (when `rosbridge`) | `9090` |
| `YAHBOOM_ESP32_PORT` | TCP port for ESP32 (when `esp32`) | `2323` |

Example (PowerShell):

```powershell
$env:YAHBOOM_CONNECTION = "esp32"
$env:YAHBOOM_IP = "192.168.1.20"
$env:YAHBOOM_ESP32_PORT = "2323"
.\webapp\start.ps1
```

Or use the start script (Pi-less in one command):

```powershell
.\webapp\start.ps1 -RobotIP 192.168.1.11 -Connection esp32
```

Optional: `-ESP32Port 2323` (default 2323). With RasPi/rosbridge use `-RobotIP` and `-BridgePort 9090` and omit `-Connection`.

---

## 6. Software architecture (PC-side)

```
┌─────────────────────────────────────────────────────────┐
│  PC (yahboom-mcp)                                        │
│  ┌──────────────┐   ┌─────────────────────────────────┐  │
│  │ MCP / REST   │──▶│ Bridge (ROS2Bridge or ESP32Bridge)│  │
│  │ tools, API   │   └─────────────────────────────────┘  │
│  └──────────────┘              │                         │
└────────────────────────────────│─────────────────────────┘
                                 │ TCP (esp32) or WebSocket (rosbridge)
                                 ▼
                    ┌────────────────────────┐
                    │ ESP32 (WiFi serial)    │  or  Raspberry Pi (rosbridge)
                    │ or RPi + rosbridge     │
                    └────────────┬───────────┘
                                 │ Serial
                                 ▼
                    ┌────────────────────────┐
                    │ ROSMASTER / STM32      │
                    │ Motors, IMU, battery   │
                    └────────────────────────┘
```

With `YAHBOOM_CONNECTION=esp32`, the server uses `ESP32Bridge` and does not need ROS 2 or rosbridge on the robot.

---

## 7. Limitations (Pi-less)

| Feature | Pi-less | Note |
|--------|---------|------|
| **Motion** | Yes | Via CMD lines over ESP32. |
| **IMU / battery / odom** | Yes | If ESP32 sketch sends IMU,BAT,ODOM lines. |
| **Camera** | No | Add IP camera or ESP32-CAM and ingest on PC. |
| **LIDAR** | No | Would need LIDAR–Ethernet/WiFi bridge. |

---

## 8. ESP32 sketch (stub for Option B)

A minimal Arduino/ESP32 sketch should:

1. Connect to WiFi (or create hotspot).
2. Listen for TCP on port 2323 (or your `YAHBOOM_ESP32_PORT`).
3. On connect: read lines; if line starts with `CMD,`, parse three floats and send the equivalent to the ROSMASTER over serial (format depends on your board).
4. In loop: read serial from the board; when you have a full IMU/battery/odom packet, format and print one `IMU,...`, `BAT,...`, or `ODOM,...` line to the TCP client.

Example (pseudo):

```cpp
// Parse: CMD,lx,ly,az
// Send to board over Serial2 (e.g. custom protocol or simple "V,lx,ly,az\n")
// Read Serial2; when you have data, send "IMU,..." or "BAT,..." or "ODOM,..." to WiFi client
```

We do not ship the sketch in this repo; implement or adapt from your board’s serial protocol.

---

## 9. When to use which

- **Pi-less + ESP32**: Cheapest (~$100 bot), good for fleet in one room with strong WiFi; camera/LIDAR only via extra hardware.
- **With Pi**: Full onboard stack, camera, LIDAR, rosbridge; better for mobile or standalone demos.

For Pi tiers (minimal Pi for cam/PTZ vs Pi 5 for ROS 2 + LLM), ROS 2 interaction (SSH vs rosbridge), optional terminal tools, and LIDAR integration details, see [Hardware & ROS 2](HARDWARE_AND_ROS2.md).
