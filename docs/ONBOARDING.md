# Onboarding — Boomy (Yahboom Raspbot v2)

This MCP server controls a **physical robot**. There is no software wrappee or
online account - onboarding means bringing the hardware up so the server has
something to talk to.

## What you need

- **Yahboom Raspbot v2** (mecanum edition), battery charged and switch on.
- **Raspberry Pi 5** running **ROS 2 Humble** with **rosbridge_suite** (or use
  the Pi-less Swarm config: WiFi-to-Ethernet/UART bridge + a Mothership PC).
- Network path from the host running the MCP server to the Pi
  (same LAN, or the Raspbot hotspot `raspbot` / password `12345678`).

## Bring-up checklist

1. **Power** the robot; confirm the Pi boots and `rosbridge_server` is listening
   on port `9090` (or `6000` for the hotspot profile).
2. **Determine the IP**: `YAHBOOM_IP` defaults to `192.168.1.11`. Set it in
   `.env` (from `.env.example`) or via `--robot-ip`.
3. **Start the server**: `just serve` (or `start.ps1`). The web dashboard runs
   on `http://localhost:10893`.
4. **Sanity check**:
   - `GET http://localhost:10892/api/v1/health` -> `robot_connection.ros == "connected"`.
   - Dashboard: **Backend** dot green, robot link shows ROS/SSH/video status.
   - Try `yahboom_tool(operation="health_check")` from an MCP client.
5. **Optional extras**: voice module (`/dev/ttyVOICE` or `YAHBOOM_VOICE_DEVICE`),
   OLED display, Dreame floorplan (`DREAME_MAP_URL`), LLM providers
   (Ollama / LM Studio / Gemini key for agent missions).

## Costs / notes

- Hardware cost ~$300 fully loaded (Pi 5 16 GB). No subscription or cloud cost.
- Firmware/driver stack runs in a Docker container on the Pi
  (`yahboom_ros2_final`, override with `YAHBOOM_ROS2_CONTAINER`).
- Don't run missions on a low battery (`<20%`) - see
  `docs/ops/AUTONOMOUS_MISSIONS.md`.

## Common pitfalls

- Hotspot SSID vs LAN: the server must reach the Pi's IP; the hotspot assigns
  `192.168.1.11` (port `6000`), a home router usually gives a DHCP IP (port `9090`).
- rosbridge inside Docker: the `rosbridge_websocket` node must be in the driver
  graph or web telemetry will be empty even though ROS itself runs.
- First-time vision: wait for the VideoBridge to produce frames before judging
  the camera.

## Reference docs

- `docs/ops/STARTUP_AND_BRINGUP.md` — boot order, bringup, dashboard vs diagnostics
- `docs/ops/AGENT_MISSION_AND_MCP.md` — missions and agent workflows
- `docs/hardware/RASPBOT_V2_HARDWARE_STACK.md` — chassis and sensor details
