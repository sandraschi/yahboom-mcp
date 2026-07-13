# yahboom-mcp BUILD_LOG

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
