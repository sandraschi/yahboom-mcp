# Boomy: Yahboom Raspbot v2 Industrial-Agentic Gateway

![Boomy Hero Shot](assets/boomy_hero.png)

## Overview

**Boomy** is a small-scale demonstration robot car designed as a high-fidelity platform for agentic orchestration and Embodied AI development. While compact, the platform bridges the gap between hobbyist hobbyists and industrial robotics through its sophisticated hardware-software integration.

At its core, Boomy leverages the **Yahboom Raspbot v2** (Mecanum Version) hardware, industrialized with a custom MCP (Model Context Protocol) gateway for seamless LLM-to-Robot interaction.

---

## 🏗️ Hardware Architecture: The "Double-Stack" Model

Boomy operates on a sophisticated dual-controller substrate to ensure both real-time physical reliability and high-level cognitive intelligence:

1.  **Rosmaster (ESP32 / Micro-ROS)**:
    *   **Function**: Low-level hardware abstraction and real-time motion control.
    *   **Capabilities**: 4x Mecanum wheel PWM control, line-sensor processing, ultrasound pinging, and I2C peripheral management.
    *   **Protocol**: Interacts with the main brain via Micro-ROS over a high-speed serial bridge.

2.  **Raspberry Pi 5 (ROS 2 Humble / Agentic Gateway)**:
    *   **Function**: High-level cognition, vision processing, and MCP federation.
    *   **Capabilities**: Runs the ROS 2 Humble node graph, the local Ollama/Gemma intelligence node, and the Python-based FastMCP bridge.
    *   **Vision**: Front-mounted dual-servo **Pan-Tilt-Zoom (PTZ)** camera module for autonomous tracking and visual verification.

---

## 🛠️ Sensory Substrate & Actuation

Beyond its drivetrain, Boomy is equipped with a professional-grade sensory array:

*   **Omnidirectional Mobility**: 4x Mecanum wheels enabling strafing, rotation, and complex 360° navigation.
*   **Visual Intelligence**: PTZ camera arm with 180° pan/tilt range for dynamic environment scanning.
*   **Proximity Fusion**: Ultrasonic "eyes" for reactive obstacle avoidance and line-tracking sensors for cliff-guard safety.
*   **Peripheral Zen**: Top-mounted OLED telemetry display and an RGB status lightstrip for human-robot visual feedback.

---

## 📂 Documentation Pillars

The documentation is organized into four logical pillars to support rapid technical navigation:

| Pillar | Focus | Key Topics |
| :--- | :--- | :--- |
| **[Architecture & Logic](docs/core/)** | Core Cognition | System design, State machines, Neurophilosophy, Embodied AI. |
| **[Hardware Technicals](docs/hardware/)** | Physical Substrate | Pinouts, Wiring, I2C Bridges, Mecanum logic, PTZ Servos. |
| **[Operations & Deployment](docs/ops/)** | Lifecycle Management | Connectivity, WiFi Transition, OS Stack, Testing & Diagnostics. |
| **[Fleet & Federation](docs/fleet/)** | Ecosystem | Multi-robot orchestration, Dreame-MCP integration, Racing Vision. |

---

## 🚀 Getting Started

### 1. Connection Baseline
Boomy primarily communicates over WiFi via ROSBridge.
```powershell
# Set robot IP and launch the dual-mode gateway
$env:YAHBOOM_IP = "192.168.1.XX"
uv run python -m yahboom_mcp.server --mode dual --port 10792
```

### 2. SOTA Webapp Hub
Access the professional **Peripheral Zen** control plane:
*   **UI Dashboard**: `http://localhost:10893` (Vite dev server)
*   **Documentation Library**: Detailed guides are available in the [docs/](docs/) directory.

---

## 🏁 Project Status & Compliance
- [x] **FastMCP 3.1+** (Sampling, Prompts, Skills)
- [x] **Double-Stack Hardware Bridge** (ESP32 + Pi 5)
- [x] **Mecanum Omnidirectional Control**
- [x] **PTZ Camera & Global Shutter Vision**
- [x] **Industrial documentation hierarchy**

*Historical logs and legacy assessments are preserved in the [docs/archive/](docs/archive/) directory.*
