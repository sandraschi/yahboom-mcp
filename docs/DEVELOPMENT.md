# Development

## Setup

```powershell
just bootstrap   # uv sync --extra dev + pre-commit install + webapp npm ci
```

Requires `uv`, `just`, and Node (webapp). Python `>=3.12` via `.python-version`.

## Layout

```
src/yahboom_mcp/        # Python package (FastMCP + FastAPI Unified Gateway)
  server.py             # app wiring, REST routes, MCP tools, main()
  portmanteau.py        # yahboom_tool dispatch (30+ hardware ops)
  prompts.py            # @mcp.prompt() templates
  agentic.py            # yahboom_agentic_workflow (ctx.sample)
  agent_mission.py      # LLM mission planner (Ollama / Gemini)
  operations/           # per-domain executors (motion, sensors, voice, ...)
  core/                 # bridges (ros2, ssh, esp32, video)
  skills/               # prompt-based operation skills
  stack_probe.py        # Docker driver-stack health probe
webapp/                 # React + Vite + Tailwind dashboard (port 10893)
native/                 # Tauri 2 NSIS desktop shell (embedded backend)
ros2/                   # ROS 2 launch/config artifacts for the Pi
scripts/                # fleet + hardware utilities
tests/                  # pytest suite (unit / integration / e2e / hardware)
```

## Commands

```powershell
just serve        # start server (dual, port 10892)
just stdio        # MCP stdio mode
just web          # start webapp
just test         # full pytest
just test-unit    # tests/unit only
just lint         # ruff + tsc + biome
just fix          # ruff --fix + biome check --write
just gates        # (fleet.just) lint + format + typecheck + tests
```

## Onboarding

**Onboarding: N/A** — this server controls a physical robot (Yahboom Raspbot v2).
There is no software wrappee or online account to create. Setup instead requires
the robot hardware, a Raspberry Pi running ROS 2 Humble + rosbridge_suite, and
network reachability. See `docs/ONBOARDING.md` for the hardware bring-up path.

## Testing conventions

- Unit tests run against the `MockROS2Bridge` (set `YAHBOOM_USE_MOCK_BRIDGE` or use
  the fixture in `tests/conftest.py`).
- `e2e` / `needs_robot` markers require a physical robot (`YAHBOOM_E2E=1`).
- Hardware tests live under `tests/hardware/` and are excluded from default runs.
- Coverage gate: `--cov-fail-under=30` via `[tool.coverage.report]`.

## Python gates (five-gate)

```powershell
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run pyright src/
uv run pytest tests/unit tests/integration
```
