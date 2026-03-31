# Changelog - Yahboom ROS 2 MCP

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0-alpha.2] - 2026-03-30

### Fixed
- **Branding Purge**: Removed all incorrect "G1 MISSION" and "Unitree G1" hallucination references across the codebase.
- **Mission Identity**: Standardized on **BOOMY MISSION** for the webapp and correctly identified hardware as **Yahboom Raspbot v2** in all prompts and docs.
- **Roadmap Cleanup**: Sanitized `PRD.md` to prevent recurring branding hallucinations.

## [2.0.0-alpha.1] - 2026-03-29

### Added
- **Boomy Insight Diagnostic Suite**: A comprehensive hardware-level telemetry and recovery layer.
- **SSH Bridge**: Secure `paramiko`-based remote shell for Pi 5 maintenance directly from the webapp.
- **Diagnostics Dashboard**: Real-time view for I2C bus state, kernel log streaming (`dmesg`), and stack health.
- **New MCP Tools**: Registered `inspect_boomy_stack` and `execute_boomy_command`.

### Fixed
- **I2C Expansion Board Stability**: Capped I2C baudrate at **100kHz** via `dtparam` to resolve Raspberry Pi 5 controller timeout failures.
- **Port Allocation**: Standardized webapp frontend at port **10893** following SOTA v12.0 guidelines.

## [1.4.0] - 2026-03-04

### Added
- **Unified Gateway Roadmap**: Defined migration path to FastMCP 3.1 architecture (documented in `docs/FASTMCP3_UNIFIED_GATEWAY.md`).
- **Architecture**: Planned consolidation of MCP and HTTP services into a single FastAPI instance.

## [1.3.0] - 2026-03-04

### Added
- **SOTA 2026 Dashboard**: Successfully consolidated all experimental UI enhancements from `webapp2` back into the primary `webapp`.
- **Infrastructure**: Moved `start.ps1` and `start.bat` into the `webapp/` directory following the standardized project pattern.
- **Unified Gateway**: Validated full compliance with FastMCP 3.1 architecture (consolidated MCP+HTTP).

### Fixed
- **React Runtime**: Resolved "Black Screen" issue by aligning `react` and `react-dom` to version `19.0.0` (Fixed by Windsurf).
- **Consolidation**: Removed redundant `webapp2` experimental directory.

## [1.2.0] - 2026-03-04

### Added
- **Experimental Substrate**: Created `webapp2` to test high-density SOTA visuals (Tailwind/Framer Motion).
- **Architecture**: Implemented `AppLayout` and `Sidebar` patterns for unified fleet command.

### Fixed
- **`start.ps1`**: `npm run dev` no longer fails on Windows — wrapped `npm` with `cmd /c`.

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
