# Hardware Tiers, ROS 2 Interaction & LIDAR

This document covers: the ROSMASTER board (no OS), Pi tiers (minimal vs full), how you interact with ROS 2, optional terminal/shell tools, and how to integrate a small cheap LIDAR.

---

## 1. ROSMASTER board (STM32)

The Yahboom ROSMASTER expansion board uses an **STM32F103RCT6** (ARM Cortex-M3, 72 MHz). It does **not** run Linux or any general-purpose OS.

- **Runs**: Bare-metal firmware or a small RTOS (e.g. FreeRTOS).
- **Handles**: Motor control and PID, encoder capture, 9-axis IMU, PWM/serial servos, CAN/SBUS, LEDs, UART to Pi or ESP32.
- **No**: Filesystem, network stack, or camera/LIDAR drivers on the MCU itself.

The STM32 is the low-level motor/sensor controller; high-level logic (ROS 2, vision, LLM) runs on a Raspberry Pi or on your PC.

---

## 2. Pi tiers: when to use which

| Tier | Hardware | Use case |
|------|----------|----------|
| **Pi-less** | Chassis + ESP32 only | ~$100 bot. PC does all compute; motion/IMU/battery over TCP. No camera, no LIDAR on robot. |
| **Minimal Pi** | Old Pi (Zero 2, 3, 4 with little RAM) | **Camera/PTZ only.** Run camera driver + stream (MJPEG/RTSP or simple API). No need for Pi 5. |
| **Full Pi (e.g. Pi 5)** | Pi 5 (or similar SBC) | ROS 2 + rosbridge on robot, optional **local LLM**, camera, LIDAR. Portable, standalone, or heavy onboard compute. |

**Camera and PTZ require a Raspberry Pi** (or another SBC with USB/CSI). The STM32 does not run camera drivers. In Pi-less (ESP32) mode there is no onboard camera path.

---

## 3. How you interact with ROS 2

### 3.1 SSH + terminal (on the Pi)

- `ssh pi@<robot-ip>`
- Use the ROS 2 CLI: `ros2 topic list`, `ros2 topic echo /odom`, `ros2 run ...`, `ros2 launch ...`
- You start/stop nodes, inspect topics, and debug directly on the robot.

### 3.2 From your PC via rosbridge (what yahboom-mcp uses)

- The Pi runs **rosbridge_suite** (WebSocket server, typically port 9090).
- The MCP server on your PC connects to that WebSocket and uses **roslibpy** to subscribe/publish (e.g. `/odom`, `/cmd_vel`, `/scan`).
- So “interaction” from the app/dashboard is: **PC ↔ rosbridge on Pi ↔ ROS 2 topics**; no SSH from the app.

### 3.3 Optional: ROS 2 terminal/shell tools (future)

To get a better “feel” for ROS 2 without leaving the IDE or dashboard:

- **Option A – SSH runner**: An MCP tool (e.g. `yahboom_ros2_command`) that runs a single command on the robot via SSH (e.g. `ros2 topic list`, `ros2 topic echo /odom --once`). Requires robot IP and SSH user/key. Redundant with a real terminal but convenient for quick checks and learning.
- **Option B – Dashboard panel**: A “ROS 2” panel in the webapp that runs such commands (e.g. text field + “Run”) and shows stdout/stderr.

Implementation options: run commands **over SSH on the robot** (needs Pi + SSH access) or **locally** (only if ROS 2 is installed on the PC and shares the same DDS network with the robot).

---

## 4. Integrating a small cheap LIDAR

### 4.1 With a Raspberry Pi on the robot

- Most small cheap LIDARs (e.g. RPLidar A1/A2, YDLidar) are **USB**. Plug into the Pi and run a ROS 2 driver there (e.g. `rplidar_ros2`). The driver publishes `sensor_msgs/LaserScan` on `/scan`.
- **Yahboom-mcp already uses this**: when connected via rosbridge, it subscribes to `/scan` and exposes LIDAR in telemetry and tools. No change needed in yahboom-mcp.
- **Steps**: Add the LIDAR to your ROS 2 launch file on the Pi; ensure `/scan` is published; the MCP server and dashboard consume it automatically.

### 4.2 Without a Pi (ESP32-only, Pi-less)

The STM32 does not run a LIDAR driver; the ESP32 bridge does not speak LIDAR. Options:

| Option | Description |
|--------|-------------|
| **Minimal Pi for LIDAR (+ camera)** | Add a low-cost Pi just for USB LIDAR (and optionally camera). Run ROS 2 driver on the Pi; connect PC via rosbridge. Same as “with Pi” above. |
| **Serial LIDAR + ESP32** | Some LIDARs (e.g. TF-mini, or units with simple serial protocols) can be read by an MCU. Custom ESP32 firmware could read serial and send e.g. `SCAN,...` in the ESP32 protocol. Requires protocol work and a LIDAR that exposes serial (not all cheap ones do). |
| **LIDAR on the PC** | If the robot is close and the LIDAR is USB, run the driver on the PC. “Access” is from the PC; the robot does not carry the LIDAR. |

**Summary**: With a Pi, a small cheap USB LIDAR is straightforward and already integrated via `/scan`. Without a Pi, you either add a minimal Pi for LIDAR/camera, use a serial LIDAR with custom ESP32 firmware, or run the LIDAR on the PC.

---

## 5. See also

- [Pi-less Setup](PI_LESS_SETUP.md) — PC-as-brain, ESP32 bridge, ~$100 bot.
- [Connectivity Guide](CONNECTIVITY.md) — WiFi and robot IP.
- [AI & Vision Capabilities](AI_CAPABILITIES.md) — Local LLMs and vision on Pi 5.
