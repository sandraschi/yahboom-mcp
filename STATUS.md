# Project Status: Yahboom Raspbot v2 (Boomy)

**Current SOTA:** v16.12  
**Operational Status:** Industrial Beta (Sync Phase)  
**Last Updated:** 2026-04-13

## 🌐 Connectivity & Infrastructure

| Component | Port | Status | Note |
| :--- | :--- | :--- | :--- |
| **Backend (FastAPI)** | `10892` | **ACTIVE** | Unified MCP + REST Gateway |
| **Dashboard (Vite)** | `10893` | **ACTIVE** | Proxied to 10892 |
| **DDS/ROS 2 Bridge** | `9090` | **STANDBY** | WebSocket Bridge to Pi 5 |
| **CLI (Justfile)** | `10892` | **SYNCED** | Root project default |

## 🕹️ Dashboard Health

- **Telemetry**: Active (Heartbeat + Health probes synchronized).
- **Peripherals**: 
    - **Patrol Car Pattern**: Restored and validated.
    - **Sound/Voice**: Serial auto-detection active.
- **3D Visualization**: 
    - **Status**: **v0.1 Pre-Alpha** (Work in Progress).
    - **Geometry**: Axis-aligned (Y-up), elevated (0.0325m), wheels correctly mounted.
    - **Assets**: Currently using X3 proxy meshes pending Raspbot v2 STLs.

## 🚢 Fleet Roadmap

- **Core Hardware**: Yahboom Raspbot v2 (Boomy).
    - **Weight**: 1.0 kg.
    - **Cost**: ~$300 (w/ Pi 5 16GB).
- **Scaling Path**: **ROSMASTER X3 PLUS** (Jetson Orin NX + LiDAR + 6-DOF Arm) documented in `docs/fleet/`.
- **Target 2026**: **Noetix Bumi Android** (Autumn Project). Currently in **Virtual Twin** development phase.

## 🛡️ Reliability Headers

- **Port Paradox**: Resolved (All components moved from 10792 -> 10892).
- **Process Guard**: `start.ps1` hardened with automatic port squatter cleanup.
- **Documentation**: All READMEs and guides synced to v16.12.
