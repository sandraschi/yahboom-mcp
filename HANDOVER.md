# Handover — yahboom-mcp (Boomy Raspbot v2)

**Session**: 2026-05-07 (16h epic)
**Operator**: Sandra
**Next action**: Convert STEP → STL for Viz.tsx, connect speaker to 3.5mm jack

---

## Running Services (Pi 192.168.1.11)

| Service | Status | Port | Notes |
|---------|--------|------|-------|
| Docker: yahboom_ros2_final | Running | host network | Driver + rosbridge + mission executor + detection bridge |
| Docker: yahboom_rosbridge_sidecar | Stopped | — | Replaced by container rosbridge |
| Docker: micro_ros_sidecar | Exited | — | ESP32 micro-ROS agent, serial protocol mismatch |
| raspbot.pyc demo | Running | **6001** | MJPEG camera stream + direct hardware access |
| Ollama | Running | **11434** (0.0.0.0) | Gemma3:1b, mission planning |
| Host rosbridge | **DISABLED** | — | `yahboom-robot.service` masked, `systemctl disabled` |
| MCP Server (PC) | Running | **10892** | Started manually in pwsh window |
| Vite webapp (PC) | Running | **10893** | Started manually |

### Container rosbridge
- Runs INSIDE yahboom_ros2_final (host networking)
- Has all workspace packages (`yahboomcar_msgs`)
- Started via: `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`
- `client_count` now shows connected clients (was 0 with host rosbridge)
- All topic publish/subscribe works through DDS

### Container entrypoints (NOT in git — Pi memory only)

These files were created inside the container and are NOT backed up:

| File | Content |
|------|---------|
| `/entrypoint.sh` | 3-line script starting rosbridge, bringup, mission_executor, detection_bridge |
| `/start_all.sh` | Same as entrypoint |
| `/minimal_mission_executor.py` | **IN GIT** at repo root — redeploy via deploy_pi.sh |
| `/detection_bridge.py` | **IN GIT** at `vision_bridge.py` — redeploy via deploy_pi.sh |

To recreate a fresh Pi, run: `./scripts/deploy_pi.sh 192.168.1.11 pi`

---

## Key Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **SSH `docker exec ros2 topic pub` for cmd_vel** | rosbridge didn't forward — THIS IS NOW REVERTED. Rosbridge works after killing host service |
| **SSH `Raspbot_Lib.Ctrl_WQ2812_brightness_ALL()` for lightstrip** | Was workaround — **NOW REVERTED**. Rosbridge works, standard roslibpy publish restored |
| **SSH `Raspbot_Lib.Ctrl_Servo()` for PTZ** | Was workaround — **NOW REVERTED** to roslibpy primary, SSH kept as fallback |
| **`smbus2` + PIL for OLED** | Permanent — luma.oled dependency eliminated, OLED works with zero deps |
| **Host rosbridge killed + masked** | Container rosbridge now serves port 9090 with all packages |
| **roslibpy downgraded 2.0.0 → 1.0.0** | Required for Humble-compatible rosbridge protocol |

---

## Known Hardware Limitations

| Issue | Status | Fix |
|-------|--------|-----|
| **No IMU/battery** | STM32 firmware doesn't expose | External INA219 (battery) + MPU6050 (IMU) via I2C |
| **PTZ servos** | I2C commands succeed, servos may lack power | Check physical servo wiring + external power |
| **Voice CSK4002 speaker** | USB audio goes to 3.5mm jack, SPK header needs pre-recorded phrases | Move speaker to 3.5mm jack |
| **CSK4002 phrase IDs** | Not known for this firmware batch | Try IDs 1-85 manually |

---

## Webapp Pages

| Page | Path | Purpose |
|------|------|---------|
| Dashboard | `/dashboard` | Camera, WASD drive, PTZ, lightstrip, voice |
| Status | `/status` | Connection health, telemetry, stack diagnostics |
| Missions | `/missions` | Natural-language goals, sample missions, report-back |
| Mission Control | `/mission-control` | Telemetry-focused view |
| Diagnostic Hub | `/diagnostics` | ROS topics/nodes, SSH shell, stack table |
| Server Logs | `/logs` | Live SSE stream with filter, export, sort |
| Help | `/help` | 8 tabs incl. ROS 2 and Missions |
| Visualization | `/viz` | 3D Three.js — auto-discovers STL files |

---

## Mission Executor

File: `minimal_mission_executor.py` (running inside container)

- Subscribes `/boomy/mission` (JSON from Ollama planner)
- Publishes `/cmd_vel` (sinusoidal search pattern)
- Publishes `/boomy/mission_status` (JSON with was_blocked flag)
- Publishes `/buzzer` (Bool beep on completion/target found)
- Subscribes `/ultrasonic` (obstacle avoidance, threshold 25cm)
- Subscribes `/boomy/detections_json` (SSD MobileNet → label matching)

---

## Detection Bridge

File: `vision_bridge.py` → `/detection_bridge.py` in container

- SSD MobileNet v2 COCO (90 classes: dog, person, cat, bowl, etc.)
- Reads MJPEG from raspbot.pyc demo at `http://192.168.1.11:6001/video_feed`
- Publishes to `/boomy/detections_json` at ~0.5 FPS
- Confidence threshold: 0.45

---

## Next Actions (priority order)

1. **Convert STEP to STL** — Open FreeCAD GUI → File → Open → `Raspbot-V2.STEP` → Ctrl+A → Export → `webapp/public/assets/meshes/boomy_complete.stl`
2. **Check Viz.tsx** — Auto-discovery loads the STL; verify at `http://localhost:10893/viz`
3. **Speaker** — Move speaker wire from CSK4002 SPK header to 3.5mm jack, or connect external speaker
4. **Bumi purchase** — Contact sales@noetixrobotics.com
5. **QCAD MCP** — Start implementation from `qcad-mcp/ARCHITECTURE.md`
