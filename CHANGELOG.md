# Changelog - Yahboom ROS 2 MCP

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-03-04

### Fixed
- **`start.ps1`**: `npm run dev` no longer fails on Windows — wrapped `npm` with `cmd /c` to handle batch-file execution correctly.
- **`server.py`**: Replaced `mcp.app` usage (removed in FastMCP 3.0) with `FastAPI`-first pattern — `FastAPI` instance is created first, then wrapped via `FastMCP.from_fastapi()`.
- **`webapp/src/main.tsx`**: Added missing `BrowserRouter` wrapper; absence caused `Routes`/`NavLink` to throw a missing router-context error on load.
- **`webapp/src/pages/dashboard/Dashboard.tsx`**: Telemetry endpoint returns `{"error": ...}` when ROS bridge is offline. Frontend was calling `.toFixed()` on undefined `battery`/`imu` fields causing an unhandled `TypeError` that unmounted the whole React tree. Fixed with deep optional chaining (`?.`) and validated state setters.

## [1.1.0] - 2026-03-03

### Added
- **Fleet Expansion**: Migrated core robotics documentation from central hub to local `docs/`.
- **Federated Architecture**: Implemented fleet discovery patterns and shared spatial data documentation.
- **PRD & Roadmap**: Established Phase 4-6 roadmap for multi-robot intelligence.
- **Fleet Registry**: Updated `mcp-central-docs` with the 2026 Fleet Registry schema.

## [1.0.0] - 2026-03-03

### Added
- **Project Initialization**: Created workspace with `uv init` and SOTA 2026 scaffold.
- **FastMCP 3.0 Server**: Established core server with lifespan connectivity management.
- **Portmanteau Tool**: Scaffolding for unified `yahboom` tool.
- **Documentation**: SOTA Architecture doc in `mcp-central-docs`.
- **Fleet Registry**: Registered project at port 10792.
