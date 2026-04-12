# Boomy Cognitive Vision (Pi 5 Expansion Roadmap)

The Pi 5 (16GB) elevates Boomy from a "robot in a box" to an "Ego-Centric Autonomous Agent." This roadmap outlines the cognitive and functional modules planned for Boomy's 2026 expansion.

## 🧠 Cognitive Layer (Local AI)
- **Local LLM (Ollama)**: Reasoning about environment data. 
    - *Models*: `gemma3:1b`, `qwen2.5:0.5b`.
    - *Utility*: Explainable robotics ("I paused because the Lidar detected a 20cm obstacle at 45 degrees").
- **Voice Intelligence**:
    - **STT (Whisper.cpp)**: Optimized ARM-native speech-to-text for nearly instant command recognition.
    - **TTS (Piper)**: High-quality, local speech synthesis with custom voice models.

## 👁️ Perception Layer (Vision & Gesture)
- **Gesture Control (MediaPipe)**: Interpreting physical hand signs to drive state transitions (Stay, Follow, Patrol).
- **Object Recognition (YOLOv11/Frigate)**: Classifying "Benny", "Person", "Chair", and "Cliff" for high-fidelity navigation.

## 🛠️ Utility & Fleet Substrate
- **Remote IDE (Code-Server)**: Browser-based VSCode running directly on the Pi 5.
- **Mobile Smart-Home Hub (Home Assistant)**: Boomy as a moving sensor node for Zigbee/Matter networks.
- **System Vitals (Prometheus/Grafana)**: Real-time mission telemetry and thermal monitoring dashboarded at `boomy:3000`.

## 🎮 Competition & Social
- **Stockfish Bridge**: High-resolution touch-chess logic integrated into the 3.5" dashboard.
- **VRChat/OSC Link**: Synchronizing Boomy's hardware with a virtual avatar's state.
