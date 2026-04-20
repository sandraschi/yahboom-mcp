# Implementation Plan: Gemma 4 Local AI (Raspbot v2)

This document outlines the technical roadmap for deploying the **SOTA 2026 Local AI stack** on the Raspberry Pi 5 (16GB) "Boomy" platform.

## 1. Local LLM Deployment (Tier 2)

### Ollama Setup
- **Model**: `gemma-4-e2b` (Recommended for speed) or `gemma-4-e4b` (Recommended for reasoning depth).
- **Quantization**: 4-bit (GGUF/Ollama default).
- **Optimization**:
    - Set `num_ctx 4096` to preserve memory and speed up processing.
    - Set `num_predict 512` for concise, actionable intents.

### API Bridge
- Ensure Ollama is listening on `0.0.0.0:11434` for internal mesh access.

## 2. Wake Word Integration (Tier 1)

### openwakeword Deployment
- **Library**: `pip install openwakeword`.
- **System Service**: Create `/etc/systemd/system/wakeword.service`.
- **Logic**: 
    - Continuous audio capture via `pyaudio` or `sounddevice`.
    - On detection, send a trigger to the `yahboom-mcp` via local REST or a shared file flag.
    - Suppress sensing while the car is moving to avoid motor noise false-triggers.

## 3. The Actuator Bridge

### LLM Intent Mapping
The LLM response should be requested in a structured JSON format. 
Example Intent:
```json
{
  "action": "patrol",
  "parameters": { "speed": 0.5, "duration": 60 },
  "reasoning": "User requested area security check."
}
```

### ROS 2 Mapping
- **Node**: Implement `agent_bridge_node.py`.
- **Behavior**:
    - Subscribes to agentic intent tool calls.
    - Publishes to `/cmd_vel` for movement.
    - Publishes to `/yahboom_lights` for status feedback (e.g., Pulse Blue = Thinking, Pulse Green = Executing).

## 4. Implementation TODO Checklist
- [ ] Install Ollama + Pull Gemma 4 E2B.
- [ ] Set up `openwakeword` and verify sensitivity with RPi 5 internal audio.
- [ ] Implement `local_ai_inference` tool in `yahboom-mcp`.
- [ ] Build the JSON intent parser and map to ROS 2 behavioral nodes.
- [ ] Validate "Spatial Grounding" via World Labs telemetry.

---
*Target Completion: May 2026*
