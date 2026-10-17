# yahboom-mcp BUILD_LOG

## 2026-10-17 - v2.5.0 stable release build

Built from clean tree (all release-prep commits landed, `git status` clean).
Toolchain: `just build-native` (build-sidecar PyInstaller exe + Tauri NSIS).

### Problems found and fixed before/during the build
- **Operator port collision**: `backend.rs` + `build.ps1` used 11246, already
  owned by democraft-mcp's BackendPort. Moved operator pair to 11247/11248
  (verified free in WEBAPP_PORTS.md + all fleet-start configs), registered
  both `yahboom-mcp-native` rows, updated `VITE_API_BASE` + backend.rs comment.
- **tauri.conf.json version 0.1.0** (stale since first scaffold) → 2.5.0 to
  match tag == manifest == pyproject per RELEASE_TIERS contract.
- **NSIS registration gap**: hooks.nsh had no mcp-clients include; vendored
  fleet `mcp-clients.nsh` + `install-mcp-clients.ps1`, wired register/
  unregister macros, added ps1 to tauri resources.
- **MCPB pollution abort**: first pack failed — timestamped `.bak` files under
  `mcpb/` were staged into the bundle; cleared (gitignored anyway) and repacked
  clean (163 KB, launch-check OK).
- **e2e unrunnable**: `@playwright/test` was never a devDependency; added,
  fixed `/health` → `/api/v1/health`, dual webServer (backend + frontend);
  2/2 green.
- **Pre-commit biome hook vs e2e artifacts**: playwright `test-results/`
  tripped `biome ci`; deleted + gitignored `webapp/test-results/` and
  `webapp/playwright-report/`.
- **Vendored smoke script ruff failure**: `scripts/smoke_stdio.py` (canonical
  copy) failed RUF005 under repo gate; applied the unpack fix + vendor note.
- **Rebuild required after request-log**: the first installer was built before
  `GET /api/v1/request-log` existed in the sidecar; CUA backend-receipt proof
  needs it in the shipped binary, so `just build-native` was re-run after the
  final src commit. Only the second installer ships.

### Verification (this build)
- Gates: ruff, ruff-format, pyright 0/0/0, pytest 100 passed / 28 skipped,
  tsc, biome 50 files clean.
- stdio handshake (`scripts/smoke_stdio.py`): ok. Frozen HTTP smoke on :11892:
  200 with robot_connection shape.
- MCPB: import isolation, AST, pollution, launch-check all pass (canonical
  `scripts/mcpb-pack.ps1`).
- CUA NSIS smoke: see `cua-reports/cua-result.json` (written by
  `just cua-nsis-test` on the shipped installer).

## 2026-06-25 — SOTA compliance sweep

### Changes
- Created `.env.example` from `.env` template (stripped secrets, blank placeholders)
- Fixed `native/build.ps1` to bundle `.env.example` instead of `.env`
- Fixed `native/tauri.conf.json` resources to reference `.env.example`
- Added `@tauri-apps/api` and `zustand` to webapp dependencies
- Added `webapp/src/lib/store.ts` — Zustand backend state store
- Added `webapp/src/lib/use-zoom.ts` — Ctrl+Scroll zoom hook
- Wired backend-status event listener in AppLayout
- Added restart-backend button (Tauri invoke) to AppLayout + Dashboard
- Added data-testid attributes: dashboard, backend-dot, kpi-server, kpi-tools, kpi-robot
- Added exponential backoff [1,2,4,8,16]s to Dashboard health polling
- Added `GET /api/v1/diagnostics` endpoint to backend
- Fixed `glama.json` fastmcp version 3.2.0 → 3.4.2
- Enhanced `native/build.ps1` with API_BASE port verification, 5MB size gate, frozen binary smoke test
- Added POSTINSTALL section to `native/windows/hooks.nsh`

### Open issues
- None — all fleet gaps closed.

## Build Failure - 2026-08-26 15:30:13

### Smoke FAILED
Port: 10892
timeout: port 10892 never opened after 30s
