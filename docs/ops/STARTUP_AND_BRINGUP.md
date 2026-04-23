# Startup, bringup, and how Goliath talks to the Raspbot

**Canonical copy (next to code):** this file lives in `yahboom-mcp`. **MCP Central Docs** keeps a **full-text copy** for RAG and semantic search in the fleet docs webapp: `mcp-central-docs/docs/robotics/yahboom/STARTUP_AND_BRINGUP.md` — update both when operator steps or env vars change. Stack probe reference: `mcp-central-docs/docs/robotics/yahboom/STACK_HEALTH_PROBE.md` (full **`health.stack`** field list there for search).

---

## 1. Three things people confuse: ROS 2, rosbridge (software), and USB hardware under the Pi

| Layer | What it is | Where it runs |
|------|-------------|---------------|
| **ROS 2** | DDS-based graph: drivers, `cmd_vel`, sensors, `Mcnamu_driver`, camera nodes, etc. | Raspberry Pi (often **inside Docker**). |
| **rosbridge_suite** (`rosbridge_server`) | **Software** WebSocket server (classically port **9090**) that translates between the ROS 2 graph and JSON/WebSocket clients. | Same machine as ROS 2 (Pi / container). **Not** a separate PCB. |
| **Lower controller hardware** | Yahboom’s **motor/sensor controller tier** sits **under** the Raspberry Pi in the stack and talks to the Pi over **USB** (serial). It is part of the robot’s physical architecture and shows up as `/dev/ttyUSB*` etc. Operators sometimes mis-speak and call this “the rosbridge board” — it is **not** the WebSocket `rosbridge_server`. In engineering docs we call this the **ROSMASTER / driver plane**; the WebSocket layer is **rosbridge_suite** on the Pi. |

**MCU vs Micro-ROS vs rosbridge (short):** the **MCU** is the processor **on that lower board** (e.g. ESP32-S3). **Micro-ROS** is the **serial** path **MCU ↔ Pi** into DDS. **Rosbridge** is **separate software on the Pi** for **PC ↔ Pi** over **WebSocket**. None of those three are interchangeable — see **[RASPBOT_V2_HARDWARE_STACK.md §1](../hardware/RASPBOT_V2_HARDWARE_STACK.md#1-terms-and-layers-read-this-first)** and **§9.3**.

**Goliath (your PC)** runs **yahboom-mcp**. It opens:

1. **TCP/WebSocket to `YAHBOOM_IP:YAHBOOM_BRIDGE_PORT` (default 9090)** → hits **rosbridge_suite** on the Pi → same ROS 2 graph as onboard nodes.  
2. **SSH** to the same IP → OLED, voice, `docker exec`, diagnostics, and **remote bringup** commands.

If the robot is **off**, or Goliath is **not** on the Raspbot Wi‑Fi AP **and** no **Ethernet** path exists, **both** SSH and rosbridge fail: the dashboard shows **no robot path**; no script on Goliath can power the Pi or join Wi‑Fi for you.

---

## 2. End-to-end boot order (what has to happen)

1. **Power** — Raspbot on; Pi boots; Docker engine starts (if enabled).  
2. **Network** — Goliath can reach the Pi (AP, home LAN, or direct Ethernet).  
3. **Docker container** (typical Yahboom image) — e.g. `yahboom_ros2` / `yahboom_ros2_final` running with ROS workspace mounted.  
4. **ROS 2 bringup** — `ros2 launch yahboomcar_bringup yahboomcar_bringup.launch.py` (drivers, topics).  
5. **rosbridge** — `ros2 launch rosbridge_server rosbridge_websocket_launch.xml` so **Goliath’s `ROS2Bridge`** (`roslibpy`) can attach.  
6. **yahboom-mcp on Goliath** — `webapp/start.ps1` or `uv run python -m yahboom_mcp.server --mode dual --port 10892`; webapp on **10893** proxies `/api` to **10892**.

Until steps 1–2 succeed, steps 3–6 are irrelevant from the operator’s point of view.

---

## 3. How Docker and bringup are started on the Pi

The repo does **not** auto-provision the SD image. On a configured robot, common patterns are:

### 3.1 Optional: full stack via systemd + Docker (`setup-autostart.sh`)

Script: `scripts/robot/setup-autostart.sh` (run **once** on the Pi with `sudo`). It:

- Sets `docker update --restart always <container>` so Docker restarts the ROS container.  
- Installs `/usr/local/bin/yahboom-launch.sh`, which waits for Docker, waits until the container is running, then `docker exec` runs **rosbridge** in the background and **yahboomcar_bringup** in the foreground.  
- Installs **`yahboom-robot.service`** (`systemctl enable`).

See the script for exact container name (`yahboom_ros2` in that file).

### 3.2 Optional: rosbridge only on the host (`install-rosbridge-at-boot.sh`)

Script: `scripts/robot/install-rosbridge-at-boot.sh` — systemd **`rosbridge.service`** running `ros2 launch rosbridge_server ...` on the **host** (outside Docker). Use one strategy consistently with your image.

### 3.3 What yahboom-mcp does over SSH when the bridge connects

`ROS2Bridge._ensure_ros_running()` (see `core/ros2_bridge.py`) can SSH to the Pi, inspect `ros2 node list` inside the container, and if critical drivers are missing, fire a **detached** `ros2 launch yahboomcar_bringup ...` inside Docker **before** finishing the WebSocket handshake. Container names in code may show `yahboom_ros2_final` vs `yahboom_ros2` — **your image must match** what the server calls.

---

## 4. Restart from the webapp (after SSH works)

| Action | Endpoint / UI | Effect |
|--------|----------------|--------|
| **Reconnect** (dashboard) | `POST /api/v1/reconnect` | Retries **rosbridge** handshake from Goliath; on success, resyncs video/peripherals. Does **not** start Docker or power the Pi. |
| **Hard Reset** (Diagnostic Hub) | `POST /api/v1/diagnostics/ros/restart` | `docker exec -d ... ros2 launch yahboomcar_bringup ...` on the Pi (**requires SSH**). |
| **System Re-Sync** | `POST /api/v1/diagnostics/ros/resync` | Metadata / topic resync on the bridge side. |
| **Agent mission (LLM)** | `POST /api/v1/agent/mission` **or MCP** `yahboom_agent_mission` | Same planner and publish path. HTTP body: `{ "goal": "…", "provider": "auto"|"ollama"|"gemini", "publish_to_ros": true, "speak": false }`. Returns structured **JSON plan**; optionally publishes on **`std_msgs/String`** default **`/boomy/mission`** (`YAHBOOM_MISSION_TOPIC`). **Ollama** (Settings model) and/or **`YAHBOOM_GEMINI_API_KEY`** + **`YAHBOOM_GEMINI_MISSION_MODEL`**. **Pi:** **`ros2/boomy_mission_executor`** subscribes and drives **`/cmd_vel`**, optional Nav2 and **`/boomy/detections_json`**. Full detail: **[AGENT_MISSION_AND_MCP.md](AGENT_MISSION_AND_MCP.md)**. |

If **SSH is down**, Hard Reset cannot run. Fix power + network first.

---

## 5. Webapp: where status appears

| Surface | Route | Purpose |
|---------|--------|---------|
| **Dashboard (first page)** | `/dashboard` | **Basic** robot link: gateway reachability, target IP, ROS / SSH / video summary, operator guidance when the robot is off or unreachable (power, Raspbot AP vs Ethernet, then Reconnect / Diagnostics). Includes the **stack health** table when **`GET /api/v1/health`** returns a **`stack`** object. |
| **Diagnostic Hub (“status detail”)** | `/diagnostics` | **Deep** ROS context: node list via SSH, native topic explorer, resync / hard reset, SSH shell. Same **stack health** table as the dashboard when **`stack`** is present. |
| **Server logs** | `/logs` | Live **yahboom-mcp** log stream (SSE) for Goliath-side errors. |

### 5.1 Stack health probe and container logs in the UI

The server periodically probes the Pi over **SSH** (Docker **`inspect`**, optional **`docker logs --tail`**, `docker ps` preview, `ros2 node list` inside the container for the driver graph) and merges TCP/WebSocket hints into **`health.stack`**. Operators see **layers** (Goliath → robot, SSH, Pi, Docker, ROS container, graph, rosbridge, cmd_vel, video), **run history** (never started vs started then exited vs **restart loop**), **remediation** lines, and—when the ROS container is **not** healthy—a **Docker log preview** (redacted, size-capped).

Configure container name and probe/log limits on **Goliath** (where **`yahboom-mcp`** runs): **`YAHBOOM_ROS2_CONTAINER`**, **`YAHBOOM_STACK_PROBE_SECS`**, **`YAHBOOM_DOCKER_LOGS_TAIL`**, **`YAHBOOM_DOCKER_LOGS_MAX_CHARS`**. Full reference: **[STACK_HEALTH_PROBE.md](STACK_HEALTH_PROBE.md)**.

---

## 6. Starting the stack from Goliath

```powershell
cd D:\Dev\repos\yahboom-mcp\webapp
.\start.ps1 -RobotIP <PI_IP>   # optional: -BridgePort 9090 -FallbackIP ...
```

This sets `YAHBOOM_*`, runs `uv sync`, starts **yahboom-mcp** on **127.0.0.1:10892** (`--mode dual`), and **Vite** on **10893** with proxy to the backend.

---

## 7. Related docs

- [`RASPBOT_V2_HARDWARE_STACK.md`](../hardware/RASPBOT_V2_HARDWARE_STACK.md) — Chassis, motors, sensors, expansion board, Pi ports, battery, switch.
- [`ROSBRIDGE.md`](../hardware/ROSBRIDGE.md) — `ROS2Bridge`, topics, env vars.  
- [`ROSBRIDGE_AT_BOOT.md`](ROSBRIDGE_AT_BOOT.md) — one-time rosbridge systemd on the Pi.  
- [`installation.md`](installation.md) — dev prerequisites and launch modes.  
- [`STACK_HEALTH_PROBE.md`](STACK_HEALTH_PROBE.md) — **`health.stack`**, lifecycle, restart loop UI, Docker log preview env vars.  
- [`../hardware/ROSMASTER_ESP32.md`](../hardware/ROSMASTER_ESP32.md) — ESP32 / serial co-processor (related USB/serial story).
