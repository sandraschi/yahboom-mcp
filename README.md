# Yahboom Raspbot v2 (Boomy) — MCP Server, Webapp & Documentation

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://biomejs.dev"><img src="https://img.shields.io/badge/Linted_with-Biome-60a5fa?style=flat-square&logo=biome&logoColor=white" alt="Biome"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

[![CI](https://github.com/sandraschi/yahboom-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sandraschi/yahboom-mcp/actions/workflows/ci.yml)
[![FastMCP 3.2](https://img.shields.io/badge/FastMCP-3.2.0-6366f1?style=flat-square&logo=python&logoColor=white)](https://github.com/jlowin/fastmcp)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![ROS 2 Humble](https://img.shields.io/badge/ROS_2-Humble-22314E?style=flat-square&logo=ros&logoColor=white)](https://docs.ros.org/en/humble/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Biome](https://img.shields.io/badge/linted-Biome-60a5fa?style=flat-square&logo=biome&logoColor=white)](https://biomejs.dev/)
[![License](https://img.shields.io/github/license/sandraschi/yahboom-mcp?style=flat-square)](https://github.com/sandraschi/yahboom-mcp/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/sandraschi/yahboom-mcp?style=flat-square&logo=github)](https://github.com/sandraschi/yahboom-mcp/stargazers)
[![Last commit](https://img.shields.io/github/last-commit/sandraschi/yahboom-mcp?style=flat-square)](https://github.com/sandraschi/yahboom-mcp/commits/main)
[![Ollama](https://img.shields.io/badge/Ollama-ready-5a5aff?style=flat-square&logo=ollama)](https://ollama.com/)
[![LM Studio](https://img.shields.io/badge/LM_Studio-ready-8b5cf6?style=flat-square)](https://lmstudio.ai/)
[![Topics](https://img.shields.io/badge/topics-robot%20%7C%20autonomous%20%7C%20lidar%20%7C%20agentic_ai-f97316?style=flat-square)](https://github.com/sandraschi/yahboom-mcp)

![Boomy Hero Shot](assets/boomy_hero.png)

## Quick Start

```powershell
git clone https://github.com/sandraschi/yahboom-mcp
cd yahboom-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:

## Overview

**Boomy** is a **Yahboom Raspbot v2** (Mecanum Version) robot car. Weighing in at approximately **1.0 kg** and costing roughly **$300** (fully loaded with a Raspberry Pi 5 16GB), it provides a unified platform for testing sensor integration, ROS 2 orchestration, and agentic (AI-driven) robotics. It's also great fun for kids of all ages.

### The Manufacturer: Yahboom
[Yahboom](https://www.yahboom.net/) is a prominent player in the Chinese robotics and STEM education industry. They offer a diverse range of hardware platforms:
*   **Market Range**: From entry-level $50 DIY kits to advanced $2,000+ STEM robots with precision mechanical arms.
*   **Industry Position**: They specialize in accessible hardware for education and prototyping, positioned below enterprise-grade platforms such as Unitree or Noetix.
*   **Developer Ecosystem**: Yahboom maintains a strong commitment to a **FOSS (Free and Open Source Software)** stack and provides active GitHub support for developers.

---

## 🏗️ Hardware Architecture

Boomy utilizes a "Double-Stack" controller model to bridge real-time physical reliability with high-level cognitive tasks:

1.  **Rosmaster (ESP32 / Micro-ROS)**: Small-form-factor hardware controller for low-latency motor control, ultrasonic pinging, and line-sensor processing.
2.  **Raspberry Pi 5 (Optional / Gateway)**: The main brain for standalone operation.

### 🚀 The "Zero-Host" Swarm Config
For scaled deployments, Boomy can operate in a **Pi-less Swarm** mode:
- **Setup**: Remove the Raspberry Pi; replace with a WiFi-to-Ethernet/UART bridge ($15).
- **Control**: Centralized orchestration via a remote **Mothership** (PC with RTX 4090).
- **Scaling**: Deploy 3+ units for the price of a single Pi-hosted robot.

---

## 🕹️ Interface Separation

This project clearly distinguishes between human-operable controls and machine-optimized interfaces:

*   **Human Interface**: A browser-based **Web Dashboard** (React/Vite) designed for manual telemetry observation, peripheral control (lights, OLED), and human-robot interaction.
*   **Machine Interface**: A standards-compliant **MCP Server** (Model Context Protocol) designed for AI agents and MCP clients to programmatic control Boomy as a tool within a larger fleet.

---

## 📂 Documentation Pillars

| Pillar | Focus | Key Topics |
| :--- | :--- | :--- |
| **[Autonomous Missions](docs/ops/AUTONOMOUS_MISSIONS.md)** | **v2.4.0 — Ollama → ROS** | Natural-language goals → LLM planning → ROS execution; vision detection (SSD MobileNet v2); ultrasonic obstacle avoidance; "find our dog" walkthrough. |
| **[Startup & bringup](docs/ops/STARTUP_AND_BRINGUP.md)** | **Start here (robot + Goliath)** | ROS 2 vs **rosbridge_suite** (software) vs USB controller tier under the Pi; boot order; Docker/systemd on the Pi; what the webapp can restart; dashboard vs diagnostics. |
| **[Agent missions & MCP](docs/ops/AGENT_MISSION_AND_MCP.md)** | **LLM → Pi missions** | **`yahboom_agent_mission`** (MCP) and **`POST /api/v1/agent/mission`** (HTTP); **`MissionPlanV1`**; env vars; **`boomy_mission_executor`**; Nav2 and **`/boomy/detections_json`**; troubleshooting vs **`yahboom_agentic_workflow`**. |
| **[Rosmaster Architecture](docs/hardware/ROSMASTER_ARCHITECTURE.md)** | **Dual-bus analysis** | I2C (0x2b) for motors/sensors, UART for IMU/battery; register map; container layout; micro-ROS analysis. |
| **[Stack health probe](docs/ops/STACK_HEALTH_PROBE.md)** | **`health.stack`** | TTL SSH/TCP probes, **`YAHBOOM_ROS2_CONTAINER`**, lifecycle (never started vs exited vs **restart loop**), optional **`docker logs`** preview (redacted). |
| **[Setup & Installation](docs/ops/installation.md)** | Dev install | `uv`, modes, baseline env vars. |
| **[Software & Logic](docs/core/)** | Architecture | System design, ROS 2 node graphs, and state management. |
| **[Hardware & Pinouts](docs/hardware/)** | Physical Layer | Wiring diagrams, I2C addresses, and sensor technical specs. |
| **[Raspbot v2 hardware stack](docs/hardware/RASPBOT_V2_HARDWARE_STACK.md)** | **Boomy chassis** | Chassis, mecanum, motors, lightstrip, PTZ, camera, IMU, ultrasonic, line/cliff, **expansion board vs rosbridge software**, Pi ports, I2C, battery, switch. |
| **[ROS 2 Bridge](docs/hardware/ROSBRIDGE.md)** | Connectivity | Bridge architecture, topic map, state cache, env vars, known bugs. |
| **[Voice & Audio](docs/hardware/VOICE_AUDIO.md)** | Sound System | CSK4002 module protocol, espeak-ng TTS, chatrobot architecture. |
| **[Multi-Robot Integration](docs/fleet/)** | Ecosystem | Federated fleet standards and cross-robot communication protocols. |

---

### Webapp status surfaces

- **Dashboard (`/dashboard`)** — First page: basic **robot link** (gateway, target IP, ROS · SSH · video) and operator hints when the Raspbot is off or Goliath has no AP/Ethernet path.
- **Diagnostic Hub (`/diagnostics`)** — Detail: ROS topic explorer, node list, resync / hard reset, SSH shell, **stack health** table (same **`stack`** payload as the dashboard when available).
- **Server logs (`/logs`)** — Live **yahboom-mcp** log stream (SSE) on Goliath.

---

*Historical status logs and legacy research are preserved in the [docs/archive/](docs/archive/) directory.*


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 2026** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting.
- **MCP**: [FastMCP 3.2](https://github.com/jlowin/fastmcp) with Unified Gateway, portmanteau tools, skills, and agentic sampling.
- **LLM Providers**: Auto-discovery of [Ollama](https://ollama.com/) (`:11434`) and [LM Studio](https://lmstudio.ai/) (`:1234`). GPU metrics via nvidia-smi.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
