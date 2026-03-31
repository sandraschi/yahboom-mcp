# Testing — mock bridge, CI, optional hardware

## Install dev dependencies

```powershell
Set-Location D:\Dev\repos\yahboom-mcp
uv sync --extra dev
```

## Layout

| Path | Role |
|------|------|
| `tests/unit/` | Fast tests: math helpers, portmanteau with injected mock bridge |
| `tests/integration/` | FastAPI `TestClient` against the app with **`YAHBOOM_USE_MOCK_BRIDGE`** |
| `tests/hardware/` | Optional TCP check to **`YAHBOOM_IP`:`YAHBOOM_BRIDGE_PORT`** (rosbridge) |
| `src/yahboom_mcp/testing/mock_bridge.py` | **`MockROS2Bridge`** — no roslibpy network |

## Environment variables

| Variable | Purpose |
|----------|---------|
| `YAHBOOM_USE_MOCK_BRIDGE` | Set to `1` / `true` / `yes` so the server lifespan uses **`MockROS2Bridge`** instead of **`ROS2Bridge`**. Tests default this via `tests/conftest.py` before importing the app. |
| `YAHBOOM_E2E` | Set to `1` to **un-skip** `@pytest.mark.real_robot` tests (lab / physical bot on the LAN). |

## Pytest markers

Configured in `pyproject.toml` under `[tool.pytest.ini_options]`:

- **`unit`** — no I/O
- **`mock`** — mock bridge / fakes
- **`integration`** — ASGI / HTTP
- **`real_robot`** — skipped unless `YAHBOOM_E2E=1`
- **`slow`** — optional long runs

## Commands

```powershell
uv run pytest
uv run pytest tests\unit
uv run pytest -m "not real_robot"
uv run pytest tests\hardware -m real_robot
```

For hardware smoke tests (rosbridge port open), set **`YAHBOOM_E2E=1`** and **`YAHBOOM_IP`** (and **`YAHBOOM_BRIDGE_PORT`** if not 9090).

## Coverage (optional)

```powershell
uv run pytest --cov=yahboom_mcp --cov-report=term-missing
```
