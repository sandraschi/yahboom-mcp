# Yahboom Raspbot v2 (Boomy) - MCP Server, Webapp & Documentation

![Boomy Hero Shot](assets/boomy_hero.png)

## Overview

**Boomy** is a small-scale demonstration robot car based on the **Yahboom Raspbot v2** (Mecanum Version). This project provides a unified control gateway for testing sensor integration, ROS 2 orchestration, and agentic (AI-driven) robotics.

### The Manufacturer: Yahboom
[Yahboom](https://www.yahboom.net/) is a prominent player in the Chinese robotics and STEM education industry. They offer a diverse range of hardware platforms:
*   **Market Range**: From entry-level $50 DIY kits to advanced $2,000+ STEM robots with precision mechanical arms.
*   **Industry Position**: They specialize in accessible hardware for education and prototyping, positioned below enterprise-grade platforms such as Unitree or Noetix.
*   **Developer Ecosystem**: Yahboom maintains a strong commitment to a **FOSS (Free and Open Source Software)** stack and provides active GitHub support for developers.

---

## 🏗️ Hardware Architecture

Boomy utilizes a "Double-Stack" controller model to bridge real-time physical reliability with high-level cognitive tasks:

1.  **Rosmaster (ESP32 / Micro-ROS)**: Small-form-factor hardware controller for low-latency motor control, ultrasonic pinging, and line-sensor processing.
2.  **Raspberry Pi 5 (ROS 2 Humble / Gateway)**: The main brain, handling vision processing, networking, and the orchestration of the agentic gateway.

---

## 🕹️ Interface Separation

This project clearly distinguishes between human-operable controls and machine-optimized interfaces:

*   **Human Interface**: A browser-based **Web Dashboard** (React/Vite) designed for manual telemetry observation, peripheral control (lights, OLED), and human-robot interaction.
*   **Machine Interface**: A standards-compliant **MCP Server** (Model Context Protocol) designed for AI agents and MCP clients to programmatic control Boomy as a tool within a larger fleet.

---

## 📂 Documentation Pillars

| Pillar | Focus | Key Topics |
| :--- | :--- | :--- |
| **[Setup & Installation](docs/ops/installation.md)** | Start Here | Launch commands, `uv run` usage, and baseline configuration. |
| **[Software & Logic](docs/core/)** | Architecture | System design, ROS 2 node graphs, and state management. |
| **[Hardware & Pinouts](docs/hardware/)** | Physical Layer | Wiring diagrams, I2C addresses, and sensor technical specs. |
| **[Multi-Robot Integration](docs/fleet/)** | Ecosystem | Federated fleet standards and cross-robot communication protocols. |

---

*Historical status logs and legacy research are preserved in the [docs/archive/](docs/archive/) directory.*
