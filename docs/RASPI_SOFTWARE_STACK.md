# Boomy's High-Cognition Software Stack (Raspberry Pi 5 16GB)

This document maps Boomy's evolving software substrate, transitioning from a reactive robotics controller to a proactive, edge-compute reasoning hub.

---

## 🏗️ Physical Core (Currently Active)

The "Body" logic that ensures Boomy can move, sense, and protect himself.

| Component | Purpose | Status |
| :--- | :--- | :--- |
| **ROS 2 Humble** | The central nervous system for motor and sensor orchestration. | ✅ Active |
| **Yahboom Peripheral Bridge** | Local SPI/GPIO listener for the 3.5" Touch Dashboard and Sonar. | ✅ Active |
| **Thermal Watchdog** | Critical 1Hz monitoring to prevent SoC damage during fan-less testing. | ✅ Active |
| **Stockfish 16** | Advanced chess engine integrated for mental expansion matches. | ✅ Active |
| **Docker Engine** | Substrate for containerized fleet services (Grafana, Home Assistant). | ✅ Active |

---

## 🧠 Cognitive Layer (Immediate Expansion)

The "Mental" expansion modules planned for deployment today.

| Component | Purpose | Status |
| :--- | :--- | :--- |
| **Code-Server** | Browser-based VSCode instance running directly on Boomy's brain. | 🔄 Next |
| **Piper TTS** | High-fidelity neural voice synthesis for offline local speech. | 🔄 Next |
| **Ollama (Gemma 3)** | Large Language Model for local edge reasoning and "personality." | 🔄 Next |

---

## 👁️ Intelligence Tier (Long-Term Roadmap)

The high-fidelity perception and fleet-integration modules for 2026.

### 🦾 Manipulation & Defense
- **OpenClaw (RoboFang)**: Advanced kinematic planning for high-DOF robotic arms.
- **DefenseClaw**: Proactive security logic using Lidar and Vision for "intruder" tagging.
- **OpenManus**: Humanoid-scale hand/arm coordination logic.

### 👁️ Computer Vision AI
- **Frigate / YOLOv11**: Real-time object classification (identifying "Benny", "Person", "Package").
- **Pose Estimation**: MediaPipe-based tracking to follow or respond to human skeletal gestures.

### 🌐 Fleet Integration
- **MCP Client/Server Hub**: Boomy as a central bridge to other MCP nodes (Plex, Calibre, Resonite).
- **VRChat/OSC Bridge**: Finalizing physical-to-virtual avatar synchronization.
- **Unified Telemetry**: Full Grafana dashboard for real-time sensor history.

---

## 🚦 Operational Constraints
- **RAM Util**: Boomy's 16GB RAM enables 3-4 concurrent AI modules without swap.
- **Thermals**: Heavy AI load requires active cooling. The **Thermal Watchdog** is mandatory during "toasty" missions.
