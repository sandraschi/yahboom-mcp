# Raspbot v2 — Camera works, robot does not move

## What “camera works” really means

If the **front camera video** appears in the Yahboom **iPhone app** (or another viewer) over the LAN, you are **nearly there** at the system level:

- The **Raspberry Pi** is powered, networked (Ethernet or WiFi), and running software that can **capture and stream** video.
- The **Pi is correctly stacked on the ROSMASTER** expansion board in the sense that the overall Yahboom image and services are operational enough for the **vision path**.
- It does **not** automatically prove that **motor control**, **ROS 2 base drivers**, or **rosbridge** are healthy. Video and motion use **different software paths**.

Treat “video OK, no drive” as: **sensors/streaming up; actuation or command path not verified**.

## Why motion can fail while video works

| Layer | Typical role | Symptom if broken |
|--------|----------------|-------------------|
| Camera / stream | MJPEG, HTTP, or app-specific server | Video works |
| ROS 2 base driver | Subscribes to `/cmd_vel`, talks to STM32 on ROSMASTER | No movement |
| rosbridge | WebSocket (often 9090; some images use 6000 on hotspot) | MCP / PC tools cannot command; app may still show video |
| Phone app | May stream video over **non-ROS** APIs while sending drive commands elsewhere | Video yes, drive no if app or topic mismatch |

This MCP server publishes velocity to **`/cmd_vel`** via **rosbridge** (see `src/yahboom_mcp/core/ros2_bridge.py`). Remote control from the dashboard requires **rosbridge on the robot**, correct **`YAHBOOM_IP`** and **`YAHBOOM_BRIDGE_PORT`**, and a **subscriber on `/cmd_vel`** on the Pi.

## SSH diagnostics (on the Raspberry Pi)

SSH in (replace with your router’s IP and user, often `pi`):

```text
ssh pi@<robot-ip>
```

Then on the Pi (ROS 2 Humble assumed):

```bash
source /opt/ros/humble/setup.bash
```

### 1. Topics and subscribers

```bash
ros2 topic list
ros2 topic info /cmd_vel
```

- If **`/cmd_vel` has zero subscribers**, nothing is consuming velocity commands: base bringup may not be running, or the stack uses a **remapped** topic name.

```bash
ros2 node list
```

Expect Yahboom-related nodes. An almost empty list usually means the robot stack did not start.

### 2. Direct motion test (bypasses phone and MCP)

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.15, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

- **Wheels move** → Driver and hardware likely OK; debug **rosbridge**, **app**, or **PC** connection.
- **No movement** → Check **power**, **physical e-stop**, **UART/STM32 link**, and **Yahboom launch** files that start the motor node.

### 3. Does the app send ROS commands?

While you command “forward” in the app:

```bash
ros2 topic echo /cmd_vel
```

- **No messages** → App may not be publishing to `/cmd_vel`, or uses another control channel.
- **Messages but no motion** → Remapping, driver state, or hardware.

### 4. Rosbridge port from the PC

On **Windows** (PowerShell), test reachability to the bridge port (default **9090**; try **6000** on some hotspot setups):

```powershell
Test-NetConnection -ComputerName <robot-ip> -Port 9090
```

On the Pi, confirm a listener (tool may vary):

```bash
sudo ss -tlnp
```

Look for **9090** or **6000**.

## Related docs

- [CONNECTIVITY.md](CONNECTIVITY.md) — IP discovery, `YAHBOOM_IP`, rosbridge at boot.
- [HARDWARE_AND_ROS2.md](HARDWARE_AND_ROS2.md) — ROSMASTER vs Pi, SSH + `ros2` CLI, rosbridge architecture.
- [ROSBRIDGE_AT_BOOT.md](ROSBRIDGE_AT_BOOT.md) — if rosbridge is not running after reboot.

## Summary

**Camera working over the network is strong evidence the Pi + ROSMASTER stack and Yahboom software are largely correct for perception and streaming.** Remaining work for full teleop is to confirm **ROS 2 motion nodes**, **`/cmd_vel` subscription**, and **rosbridge** (plus correct ports from your PC or MCP server).
