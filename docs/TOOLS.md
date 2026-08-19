# Tools

## MCP tools

| Tool | Purpose |
|------|---------|
| `yahboom_tool` | Portmanteau: 30+ hardware ops (motion, sensors, voice, display, lightstrip, camera PTZ, diagnostics, safety, trajectory, audio). Dispatch via `operation=`. |
| `yahboom_demo` | Show-floor demos: chalk drawing (`smiley`, `heart`, `boomy_b`) and talkbot. |
| `yahboom_agentic_workflow` | High-level goal planning via MCP sampling (`ctx.sample`). |
| `yahboom_agent_mission` | NL goal -> structured mission JSON (Ollama / Gemini), optional ROS publish + speech. |
| `yahboom_help_tool` | Multi-level help drill-down (category -> topic). |
| `ros_topic_list` | List active ROS 2 topics and message types. |
| `ros_node_info` | Inspect a ROS 2 node (publishers/subscribers/services). |
| `ros_resync` | Force topic re-discovery and re-subscription. |
| `ros_restart_bringup` | Restart the bringup stack on the robot (nuclear option). |
| `lidar` | Yahboom `/scan` obstacle sectors or Dreame D20 Pro floorplan map. |
| `audio` | Play/store/manage audio via the USB voice module speaker. |
| `query_logs` | Query the in-process log ring buffer. |
| `yahboom_shutdown` | Gracefully shut the server down. |

### `yahboom_tool` operations

`health_check`, `forward`, `backward`, `turn_left`, `turn_right`, `strafe_left`,
`strafe_right`, `stop`, `stop_all`, `read_imu`, `read_encoders`, `read_battery`,
`read_all`, `read_lidar`, `say`, `play`, `play_beep`, `play_file`, `chat_and_say`,
`display`, `clear_display`, `led`, `led_off`, `light_effect`, `patrol_car`,
`camera_up/down/left/right/reset/set_pos/move`, `start_recording`,
`stop_recording`, `list_trajectories`, `config_show`, `inspect_stack`,
`execute_command`, `gripper_set/open/close/status`, `explore`, `explore_and_map`,
`audio_*` sub-ops.

## Prompts

`yahboom_quick_start`, `yahboom_patrol`, `yahboom_diagnostics`,
`yahboom_patrol_apartment`, `yahboom_go_to_recharge`, plus the four skill prompts
(`yahboom_quick_pilot`, `yahboom_patrol_sweep`, `yahboom_emergency_halt`,
`yahboom_diagnostic_triage`).

## REST endpoints (Unified Gateway, port 10892)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health` | Liveness + robot connection state |
| `GET /api/v1/diagnostics` | Tool list, system info (CUA-NSIS smoke) |
| `GET /api/v1/diagnostics/ros/topics` | Topic explorer |
| `POST /api/v1/diagnostics/ros/resync` | Force resync |
| `POST /api/v1/diagnostics/ros/restart` | Restart bringup |
| `GET /api/v1/diagnostics/stack` | ROS nodes + I2C + voice stack |
| `GET /api/v1/diagnostics/logs` | Ring-buffer log tail |
| `GET /api/v1/logs/stream` | SSE live log stream |
| `POST /api/v1/diagnostics/exec` | Sandboxed SSH command (blocked list enforced) |
| `GET /api/v1/telemetry` (+ `/api/v1/sensors`) | Live telemetry |
| `POST /api/v1/control/move` | Velocity command |
| `POST /api/v1/control/tool` | Bridge into `yahboom_tool` |
| `POST /api/v1/control/lightstrip`, `/buzzer`, `/voice` | Peripherals |
| `POST /api/v1/display`, `/clear`, `/scroll`, `/status`, `/write` | OLED |
| `POST /api/v1/voice`, `/voice/play`, `/voice/say` | Voice module |
| `POST /api/v1/tapo/audio/listen|speak|status` | Tapo two-way audio |
| `POST /api/v1/led` | Lightstrip RGB |
| `POST /api/v1/gpio` (GET/POST) | GPIO headlight LEDs |
| `POST /api/v1/emergency` | Emergency strobe/siren sequence |
| `POST /api/v1/reconnect` | Force bridge handshake |
| `POST /api/v1/stop_all` | Global stop |
| `GET /api/v1/missions/status`, `POST /api/v1/missions/run/{id}`, `/stop` | Missions |
| `GET/POST /api/v1/demo*` | Demo lifecycle |
| `GET /stream` | MJPEG camera stream |
| `GET /api/v1/snapshot` | Single JPEG frame |
| `GET /api/v1/slam/map`, `/api/v1/slam/data` | SLAM occupancy grid |
| `GET /api/v1/lidar/dreame-map` | Dreame floorplan proxy |
| `GET /api/v1/settings/llm`, `/settings/ollama/*`, `/settings/lmstudio/*`, `/settings/gpu` | LLM settings + discovery |
| `POST /api/v1/chat` | Chat completion (Ollama / LM Studio) |
| `POST /api/v1/agent/mission` | Agent mission planning |
| `GET /api/capabilities` | Runtime capability introspection |
| `GET /api/skills` | Registered skill listing |
| `GET /api/v1/bridge/proxies` | MCP bridge proxy status |
| `POST /api/shutdown` | Graceful self-termination |
| `GET /docs` | Swagger UI (FastAPI) |

## Webhooks

**N/A** — yahboom-mcp is a hardware-control server with no inbound event sources
from third parties. The equivalent outbound channel is the SSE log stream and
ROS topic subscription; there is no webhook product surface.
