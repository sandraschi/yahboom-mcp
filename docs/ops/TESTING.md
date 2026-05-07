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
| `YAHBOOM_USE_MOCK_BRIDGE` | Set to `1` / `true` / `yes` / **`on`** so the server lifespan uses **`MockROS2Bridge`** instead of **`ROS2Bridge`**, skips real **SSH** and **VideoBridge**, and avoids hitting the Pi. Tests set this in `tests/conftest.py` before the app is imported. |
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

## Webapp (Biome)

From `webapp/`:

```powershell
Set-Location D:\Dev\repos\yahboom-mcp\webapp
npm ci
npm run biome:ci
```

CI-style check (no writes). `npm run biome` applies formatter + safe fixes. **`dist/`** and **`node_modules/`** are ignored in `webapp/biome.json`.

**Zero-warning `biome ci`:** global **`a11y`** recommendations are disabled (**`a11y.recommended`: false**) so accessibility rules do not flood CI with dozens of warnings on the dashboard. **`correctness.useExhaustiveDependencies`** and **`correctness.noUnusedVariables`**, and **`suspicious.noArrayIndexKey`**, **`noExplicitAny`**, **`noAssignInExpressions`**, are **off** so the remaining recommended set runs without warnings. Re-enable individual **`a11y/*`** rules (or **`a11y.recommended`**) when you want to chip away at accessibility with targeted fixes.

## camera_ptz and test order

`yahboom_mcp.operations.camera_ptz` tracks pan/tilt in a **module-level** `_camera_state`. Unit tests that call **`camera_move`** must not assume a clean slate unless they reset it. **`tests/unit/test_all.py`** uses a **`centered_camera_ptz`** fixture (90° / 90°) on the servo camera tests so order and earlier runs cannot leak tilt/pan into assertions.

## Coverage (optional)

```powershell
uv run pytest --cov=yahboom_mcp --cov-report=term-missing
```
