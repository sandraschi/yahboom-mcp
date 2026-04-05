# The Cognitive Pi 5: Boomy's Expansion Manual (2026 Edition)

The Raspberry Pi 5 (16GB) is Boomy's "High-Cognition Substrate." This manual details the transition from a standard robotics controller to a mobilized, edge-compute reasoning hub.

## 🏢 Hardware Specs: The "Mini-PC" Power
- **CPU**: Quad-core ARM Cortex-A76 @ 2.4GHz.
- **Memory**: 16GB LPDDR4X (Enables large Docker stacks and LLM context windows).
- **PCIe Gen 3**: Support for high-speed NVMe storage for deep learning models.
- **Dual 4K Micro-HDMI**: Driving the 3.5" dashboard while maintaining secondary telemetry screens.

---

## 🧠 Cognitive Tier: Local Intelligence & Reasoning

### 1. Edge-LLM Reasoning (Ollama)
The Pi 5 16GB can run sub-2B parameter models with impressive latency.
- **Model**: `gemma3:1b` or `qwen2.5:0.5b`.
- **Utility**: Explainable Robotics.
    - *Query*: "Boomy, status summary."
    - *Response*: "Detected low battery (11.2V) and high CPU temp (62C). Navigating to cooling zone."
- **Install**: `curl -fsSL https://ollama.com/install.sh | sh`

### 2. Natural Voice (Whisper.cpp + Piper)
Low-latency speech interactions that feel "human."
- **STT**: `whisper.cpp` (Optimized for ARMv8 Neon). Nearly instant command transcription.
- **TTS**: `Piper`. Neural-sounding local voices (no "robot" monotone).
- **Utility**: Full conversational control without cloud dependency.

---

## 👁️ Perception Tier: Advanced Vision & Gestures

### 1. Gesture Control (MediaPipe)
- **Utility**: Control Boomy's state transitions with physical hand signs.
- **Grok Pattern**: Thumbs up (Resume), Open Palm (Stop), Pointing (Directional Command).

### 2. Security & Patrol (Frigate / YOLOv11)
- **Utility**: Real-time object classification (Benny, Person, Package).
- **Integration**: Boomy acts as a mobile security guard, sending snapshots to your phone when an anomaly is detected.

---

## 🛠️ Professional Utility & Dev Substrate

### 1. Remote IDE (Code-Server)
- **Utility**: A full VSCode instance running on Boomy. 
- **Workflow**: Browse to `http://boomy:8080` from your laptop. Edit python bridge code and mission logic directly in a professional IDE while Boomy is at your feet.
- **Install**: `curl -fsSL https://code-server.dev/install.sh | sh`

### 2. Mobile Hub (Home Assistant Docker)
- **Utility**: Boomy as a moving Zigbee/Matter bridge.
- **Use Case**: Boomy detects a "Cold Spot" in the hallway and adjusts the Nest thermostat via local API.

---

## 🏰 Mental Matches: The "Chess" Head
- **Stockfish 16**: Deployed on-robot for high-stakes matches on the 3.5" LCD.
- **Stylus Interaction**: Use the XPT2046 touch screen to drag-and-drop pieces directly on the robot's "head."

---

## 🚦 Operational Constraints (Thermal)
> [!CAUTION]
> **PI 5 THERMALS (FAN-LESS)**
> The Pi 5 16GB generates significant heat during LLM inference or Code-Server loads. The **Thermal Watchdog** is mandatory.
> - **Soft Throttle (74°C)**: Automatic LED shutdown and refresh reduction.
> - **Hard Throttle (79°C)**: Mission Termination.

## 🚀 Recommended Deployment Order
1. **Thermal Watchdog** (✅ DEPLOYED)
2. **Code-Server** (For seamless remote development)
3. **Piper TTS** (For Boomy's initial vocal "vibe")
4. **Ollama** (For the High-Cognition Brain)
