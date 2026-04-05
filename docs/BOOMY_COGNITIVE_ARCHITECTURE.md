# Boomy Cognitive Architecture: Two-Brain Model

**Date:** 2026-04-04
**Status:** Design document
**Tags:** [yahboom-mcp, boomy, gemma4, litert-lm, ollama, cognitive, architecture, high]
**Related:** `BOOMY_AUTONOMOUS_INTELLIGENCE.md`, `ARCHITECTURE_DECISION_ROS2_VS_LLM.md`

---

## The Two-Brain Model

Boomy has two inference engines that operate simultaneously or as fallbacks:

```
┌─────────────────────────────────────────────────────────────────────┐
│  BRAIN A: REFLEX BRAIN (always on, on-robot)                        │
│                                                                     │
│  Hardware: Pi 5, 16GB RAM                                           │
│  Model:    Gemma 4 E2B via LiteRT-LM                                │
│  RAM use:  <1.5GB (4-bit quantized)                                 │
│  Speed:    7.6 tok/s decode, 133 tok/s prefill                      │
│  Latency:  ~500ms for short commands                                │
│  Context:  128K tokens                                              │
│  Offline:  Yes — no network dependency                              │
│                                                                     │
│  Handles:                                                           │
│  • Audio command parsing (native ASR input)                         │
│  • Visual scene analysis (native vision input)                      │
│  • WIGO reasoning and reporting                                     │
│  • Demo mode narration                                              │
│  • Low-latency decisions: "is the path clear?"                      │
│  • Kaffeehaus demo E2B describes what it sees                       │
│                                                                     │
│  Does NOT handle:                                                   │
│  • Motor control (too slow for safety-critical timing)              │
│  • Complex multi-step planning (limited quality vs Goliath)         │
│  • Long conversations (7.6 tok/s feels slow to a human)            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    when Goliath reachable
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│  BRAIN B: STRATEGIC BRAIN (when available, on Goliath)              │
│                                                                     │
│  Hardware: Goliath — RTX 4090, 64GB RAM                             │
│  Models:   Claude (via MCP), Qwen3.5 27B via Ollama (~40 tok/s)    │
│            or Gemma 4 26B MoE (~fast, 3.8B active params)          │
│  Latency:  ~200ms for Ollama, variable for Claude                   │
│                                                                     │
│  Handles:                                                           │
│  • Complex reasoning and planning                                   │
│  • Long-context tasks (256K tokens at 26B)                         │
│  • Tool orchestration across the entire MCP fleet                  │
│  • Creative or high-quality language generation                     │
│  • Multi-robot coordination (Dreame, future robots)                 │
│  • Fine-grained decision making with full context                   │
└─────────────────────────────────────────────────────────────────────┘
```

Both brains issue commands through the same interface: `yahboom-mcp` REST API and
FastMCP tools. The hardware layer (ROS 2) does not know or care which brain is upstream.

---

## LiteRT-LM Integration Plan

### Installation on Pi 5

```bash
# SSH into Pi
ssh pi@<robot-wifi-ip>

# Install LiteRT-LM
pip3 install litert-lm

# Download E2B model (approx 1.2GB)
litert-lm --model gemma4-e2b-it --download-only

# Test basic inference
litert-lm --model gemma4-e2b-it --prompt "Say hello in German."
# Expected: "Hallo!"

# Test with tool calling
litert-lm --model gemma4-e2b-it \
  --prompt "What direction should I move to avoid an obstacle 0.3m ahead?" \
  --tools '[{"name":"move","description":"Move the robot"}]'
```

### Running as a Service

LiteRT-LM exposes an OpenAI-compatible API when run with `--server`:

```bash
# Start inference server on Pi
litert-lm serve --model gemma4-e2b-it --port 8080 --host 0.0.0.0

# Test from Goliath or Windows
curl http://<robot-ip>:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma4-e2b-it","messages":[{"role":"user","content":"Hallo!"}]}'
```

Systemd service (`/etc/systemd/system/litert-lm.service`):
```ini
[Unit]
Description=LiteRT-LM Gemma 4 E2B Inference Server
After=network.target

[Service]
ExecStart=/home/pi/.local/bin/litert-lm serve --model gemma4-e2b-it --port 8080
Restart=always
RestartSec=10
User=pi

[Install]
WantedBy=multi-user.target
```

### Skill Definitions

LiteRT-LM skills are JSON tool definitions. Define once, reuse across all autonomous modes:

```json
[
  {
    "name": "move",
    "description": "Move Boomy. linear_x: forward/backward m/s (-0.5 to 0.5). angular_z: rotation rad/s (-1.5 to 1.5). linear_y: strafe m/s (-0.5 to 0.5).",
    "parameters": {
      "type": "object",
      "properties": {
        "linear_x":  {"type": "number", "description": "Forward (+) or backward (-)"},
        "angular_z": {"type": "number", "description": "Left (+) or right (-)"},
        "linear_y":  {"type": "number", "description": "Strafe left (+) or right (-)"}
      }
    },
    "endpoint": "POST http://localhost:10792/api/v1/control/move"
  },
  {
    "name": "stop",
    "description": "Emergency stop. Call this immediately if any danger is detected.",
    "endpoint": "POST http://localhost:10792/api/v1/stop_all"
  },
  {
    "name": "set_lights",
    "description": "Control chassis LEDs. operation: 'set' for static colour (r,g,b 0-255), 'pattern' for effect name, 'off' to turn off. Patterns: patrol, rainbow, breathe, fire.",
    "parameters": {
      "type": "object",
      "properties": {
        "operation": {"type": "string", "enum": ["set", "pattern", "off"]},
        "r": {"type": "integer"}, "g": {"type": "integer"}, "b": {"type": "integer"},
        "pattern": {"type": "string", "enum": ["patrol", "rainbow", "breathe", "fire"]}
      },
      "required": ["operation"]
    },
    "endpoint": "POST http://localhost:10792/api/v1/control/lightstrip"
  },
  {
    "name": "say",
    "description": "Speak text aloud via the voice module. Use German by default.",
    "parameters": {
      "type": "object",
      "properties": {"text": {"type": "string"}},
      "required": ["text"]
    },
    "endpoint": "POST http://localhost:10792/api/v1/voice"
  },
  {
    "name": "get_telemetry",
    "description": "Get current robot state: battery %, position, obstacles, IMU heading.",
    "endpoint": "GET http://localhost:10792/api/v1/telemetry"
  },
  {
    "name": "capture_and_describe",
    "description": "Capture a camera frame and return a description of what is visible.",
    "endpoint": "GET http://localhost:10792/api/v1/snapshot"
  },
  {
    "name": "write_display",
    "description": "Write text to the OLED display. param1: text, param2: line number (0-3).",
    "endpoint": "POST http://localhost:10792/api/v1/display/write"
  }
]
```

### The Observe → Think → Act Loop

This is the core pattern for all autonomous E2B behaviour:

```python
# /home/pi/boomy_agent.py
# The main autonomous loop when in LOCAL_AI or OFFLINE_AI state

import httpx
import asyncio
import json

LITERT_URL  = "http://localhost:8080/v1/chat/completions"
MCP_URL     = "http://localhost:10792"
SKILLS_FILE = "/home/pi/boomy_skills.json"

SYSTEM_PROMPT = """
Du bist Boomy, ein autonomer Roboter im Wiener 9. Bezirk.
Du sprichst Deutsch. Du bist freundlich, kompetent und ehrlich.

Deine Aufgaben (wenn nicht anders angegeben):
- Patrouilliere sicher durch den Raum
- Erkenne Hindernisse und weiche ihnen aus
- Beobachte die Umgebung auf Ungewöhnliches
- Melde Probleme via Stimme und Display

Sicherheitsregeln (niemals überschreiten):
- Fahre niemals schneller als 0.3 m/s in Innenräumen
- Wenn sonar < 0.35m: sofort stoppen und zurückfahren
- Wenn Akku < 15%: zur Ladestation navigieren und warten
- Im Zweifel: stoppen und fragen

Wenn du eine Aufgabe ausführst, nutze die verfügbaren Tools.
"""

async def observe():
    """Get current robot state."""
    async with httpx.AsyncClient() as client:
        tele = await client.get(f"{MCP_URL}/api/v1/telemetry")
        snap = await client.get(f"{MCP_URL}/api/v1/snapshot")
    return {
        "telemetry": tele.json(),
        "has_image": snap.status_code == 200
    }

async def think(observation: dict, goal: str) -> dict:
    """Ask E2B what to do next."""
    with open(SKILLS_FILE) as f:
        skills = json.load(f)

    obs_text = json.dumps(observation["telemetry"], ensure_ascii=False)
    prompt = f"Aktueller Zustand: {obs_text}\n\nAufgabe: {goal}"

    payload = {
        "model": "gemma4-e2b-it",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        "tools": skills,
        "max_tokens": 512,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(LITERT_URL, json=payload)
    return r.json()

async def act(llm_response: dict):
    """Execute tool calls from E2B response."""
    choices = llm_response.get("choices", [])
    if not choices:
        return

    msg = choices[0].get("message", {})
    tool_calls = msg.get("tool_calls", [])

    async with httpx.AsyncClient() as client:
        for tc in tool_calls:
            fn   = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])
            # Resolve skill endpoint
            # (simplified — production code reads from skills.json)
            if fn == "move":
                await client.post(
                    f"{MCP_URL}/api/v1/control/move",
                    params={"linear": args.get("linear_x", 0),
                            "angular": args.get("angular_z", 0)}
                )
            elif fn == "stop":
                await client.post(f"{MCP_URL}/api/v1/stop_all")
            elif fn == "say":
                await client.post(f"{MCP_URL}/api/v1/voice",
                                  json={"text": args["text"]})
            elif fn == "set_lights":
                await client.post(f"{MCP_URL}/api/v1/control/lightstrip",
                                  json=args)
            # ... etc for all skills

async def autonomous_loop(goal: str = "Patrouilliere sicher durch den Raum."):
    """Main loop: observe → think → act, every 2 seconds."""
    print(f"Starting autonomous loop. Goal: {goal}")
    while True:
        try:
            obs    = await observe()
            result = await think(obs, goal)
            await act(result)
        except Exception as e:
            print(f"Loop error: {e}")
        await asyncio.sleep(2.0)

if __name__ == "__main__":
    asyncio.run(autonomous_loop())
```

---

## Vision Pipeline

E2B natively accepts image input. The pipeline for visual scene analysis:

```python
import cv2
import base64
import httpx

def capture_frame_b64() -> str:
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return base64.b64encode(buf.tobytes()).decode()

async def describe_scene(question: str) -> str:
    frame_b64 = capture_frame_b64()
    if not frame_b64:
        return "Kamera nicht verfügbar."

    payload = {
        "model": "gemma4-e2b-it",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{frame_b64}"}},
                {"type": "text", "text": question},
            ]
        }],
        "max_tokens": 200,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(LITERT_URL, json=payload)
    return r.json()["choices"][0]["message"]["content"]

# Usage:
# await describe_scene("Ist die Haustür offen oder geschlossen?")
# await describe_scene("Siehst du Benny, den Hund?")
# await describe_scene("Gibt es etwas Ungewöhnliches oder Gefährliches im Bild?")
# await describe_scene("Beschreibe den Raum in einem Satz auf Deutsch.")
```

---

## Audio Pipeline (ASR → Command → Action)

E2B has native audio input. The wake-word → command → action pipeline:

```
[Microphone] → [Wake word detection] → [30s audio capture]
    → [E2B ASR + intent parsing] → [Tool call] → [ROS 2 action]

Wake words: "Boomy", "Hey Boomy", "Roboter"

Example commands E2B should handle:
  "Boomy, fahr vorwärts"          → move(linear_x=0.2)
  "Boomy, stopp"                  → stop()
  "Boomy, was siehst du?"         → describe_scene("Was siehst du?") → say()
  "Boomy, demo mode"              → demo.run_demo()
  "Boomy, wie ist dein Akku?"     → get_telemetry() → say battery level
  "Boomy, patrouilliere"          → autonomous_loop(goal="patrol")
  "Boomy, geh zur Küche"          → autonomous_loop(goal="navigate to kitchen")
```

Audio input processing with LiteRT-LM (max 30s per clip):
```python
import sounddevice as sd
import numpy as np
import tempfile
import soundfile as sf

def record_command(duration=5, samplerate=16000) -> str:
    """Record audio and return as base64 WAV for E2B."""
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate,
                   channels=1, dtype='int16')
    sd.wait()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, samplerate)
        with open(f.name, "rb") as wav:
            return base64.b64encode(wav.read()).decode()
```

---

## Integration with yahboom-mcp

The autonomous agent (`boomy_agent.py`) and yahboom-mcp are siblings, not nested.
Both run on the Pi. They share the same hardware through the REST API:

```
boomy_agent.py          →  POST http://localhost:10792/...  →  yahboom-mcp
boomy_watchdog.py       →  POST http://localhost:10792/...  →  yahboom-mcp
litert-lm (serve mode)  →  (called by boomy_agent.py)
                                         ↓
                                    yahboom-mcp
                                         ↓
                                  ROSBridge (port 9090)
                                         ↓
                                    ROS 2 Humble
                                         ↓
                                    STM32 / hardware
```

yahboom-mcp does not need to know about LiteRT-LM. It just receives REST calls.
LiteRT-LM does not need to know about ROS 2. It just issues tool calls.

When Goliath is available, Claude or Ollama can also issue the same REST calls.
The interface is stable. The brain can be swapped without changing the bridge.

---

## Capability Roadmap

| Capability | State | Requires |
|---|---|---|
| Voice command (German) | Planned | LiteRT-LM + mic |
| Scene description | Planned | LiteRT-LM + camera fix |
| Door detection | Planned | Camera + E2B + servo calibration |
| Autonomous patrol | Planned | Sensors working + E2B loop |
| Goliath LED check | Planned | Camera + servo calibration |
| Environment anomaly | Planned | Camera + E2B |
| WIGO mode | Planned | All above |
| Kaffeehaus demo | Planned | Voice + lights + camera |
| Battery dock-seek | Future | ArUco tag or colour marker at dock |
| SLAM / room map | Future | LIDAR add-on |
| Person recognition | Future | Fine-tuned vision model or YOLOv8 |
| Multi-room navigation | Future | SLAM + room labels |

---

## Why This Works Without Fine-Tuning

Gemma 4 E2B is instruction-tuned and supports structured tool calling natively.
Most of Boomy's tasks can be accomplished with good system prompts and zero fine-tuning:

- **Vision prompts are specific:** "Is the door open or closed?" has a constrained answer space.
- **Tool calls are grounded:** E2B doesn't need to hallucinate actions — it picks from a defined tool list.
- **German works natively:** E2B is trained on 140+ languages including German.
- **Error recovery is built-in:** the observe→think→act loop retries on failure.

Fine-tuning becomes relevant when:
- You want specific personality traits to be rock-solid (demo dialogue)
- You want Benny-specific recognition (vs generic dog detection)
- You want room-specific navigation (kitchen vs living room)

For now, prompt engineering covers everything needed for phases A-D.
