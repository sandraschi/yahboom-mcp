# Configuration

## Ports (registered in `WEBAPP_PORTS.md`)

| Port | Service |
|------|---------|
| 10892 | Yahboom MCP backend (Unified Gateway: REST + MCP SSE) |
| 10893 | Web dashboard frontend (Vite dev) |

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `YAHBOOM_IP` | `192.168.1.11` | Robot (Raspberry Pi) IP |
| `YAHBOOM_FALLBACK_IP` | unset | Ethernet recovery IP (e.g. `192.168.0.250`) |
| `YAHBOOM_BRIDGE_PORT` | `9090` | ROSBridge websocket port on the robot |
| `YAHBOOM_ESP32_PORT` | `2323` | Direct ESP32 serial-to-TCP port |
| `YAHBOOM_CONNECTION` | `rosbridge` | `rosbridge` \| `esp32` |
| `YAHBOOM_SSH_USER` / `YAHBOOM_SSH_PASSWORD` / `YAHBOOM_SSH_KEYFILE` | - | SSH access to the Pi for recovery/diagnostics |
| `YAHBOOM_USE_MOCK_BRIDGE` | unset | `1`/`true` to run against the MockROS2Bridge (no hardware) |
| `YAHBOOM_VOICE_DEVICE` | auto (udev scan) | Serial device for the voice module |
| `YAHBOOM_ROS2_CONTAINER` | `yahboom_ros2_final` | Docker container running the ROS 2 driver stack |
| `YAHBOOM_MISSION_TOPIC` | `/boomy/mission` | ROS topic for mission JSON publish |
| `YAHBOOM_GEMINI_API_KEY` | unset | Gemini key for agent mission planning (provider `gemini`) |
| `YAHBOOM_GEMINI_MISSION_MODEL` | `gemini-2.0-flash` | Model used for Gemini mission planning |
| `OLLAMA_BASE_URL` | `http://192.168.1.11:11434` | Ollama endpoint for chat + mission planning |
| `LMSTUDIO_BASE_URL` | `http://localhost:1234` | LM Studio endpoint for chat |
| `DREAME_MAP_URL` | `http://127.0.0.1:10894/api/v1/map` | Dreame D20 Pro floorplan map (standalone dreame-mcp) |
| `MCP_BRIDGE_URLS` | unset | Comma-separated URLs to proxy as MCP bridge providers |
| `YAHBOOM_TAURI` | unset | `1` when running under the Tauri desktop shell |

Copy `.env.example` to `.env` for local overrides. The server also reads `--robot-ip`,
`--mode`, `--port`, and `--debug` CLI flags (see `Development`).

## Transport modes

| Mode | What runs |
|------|-----------|
| `stdio` | MCP over stdio only (Claude Desktop, Cursor) |
| `http` | FastAPI Unified Gateway only (REST + SSE) |
| `dual` (default in `start.ps1`) | Both: REST endpoints + MCP SSE at `/sse` |

## LLM providers

- **Ollama**: `/api/v1/settings/ollama/status`, `/api/v1/settings/ollama/models`
- **LM Studio**: `/api/v1/settings/lmstudio/status`, `/api/v1/settings/lmstudio/models`
- **GPU**: `/api/v1/settings/gpu` (nvidia-smi probe)
- Chat + mission planning route through the provider/model selected via
  `GET/PUT /api/v1/settings/llm`.
