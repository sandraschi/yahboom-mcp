# Gemma 4 E2B/E4B — On-Device LLM for Raspbot V2

**Date:** 2026-04-04
**Tags:** [yahboom-mcp, raspbot, gemma4, litert-lm, on-device-llm, edge-ai, pi5, medium]

---

## Hardware Fit

Raspbot V2 runs **Pi 5 with 16GB RAM**. Both Gemma 4 edge models fit:

| Model | 4-bit RAM  | Capabilities                          |
|-------|-----------|---------------------------------------|
| E2B   | <1.5GB    | Text, vision, **audio input**, tools  |
| E4B   | ~5GB      | Text, vision, **audio input**, tools  |

Google's own Pi 5 benchmark: **133 tok/s prefill, 7.6 tok/s decode** for E2B on CPU.
At 7.6 tok/s decode, command parsing and agentic decision steps are feasible in real time.

---

## What Makes This Interesting for Raspbot

- **Audio input (ASR)** natively in E2B and E4B — offline voice commands without cloud
- **Vision** — bounding box output, OCR, scene understanding from camera frames
- **Native function calling** — maps directly to MCP tool calls / Agent Skills pattern
- **128K context** — can hold full session history on-device
- **Fully offline** — no dependency on Goliath or network

This is the first model family where a Pi 5 can run ASR + vision + tool-calling + agentic
planning simultaneously in under 2GB RAM.

---

## Quick Start on Pi 5

```bash
# Option 1: LiteRT-LM (Google's optimized runtime, recommended)
pip install litert-lm
litert-lm --model gemma4-e2b-it

# Option 2: Ollama (simpler, less optimized)
ollama run gemma4:e2b
```

LiteRT-LM is optimized for XNNPack CPU acceleration and supports tool calling
(same mechanism as Google AI Edge Gallery "Agent Skills").

---

## Integration Architecture

```
[Mic] → ASR (E2B native) ┐
[Camera] → Vision (E2B)  ┤→ [LiteRT-LM on Pi 5] → [ROS2 actions] → [Hardware]
[Text cmd]               ┘         ↕ (when available)
                         [Goliath via FastMCP gateway]
```

Existing yahboom-mcp MCP tools (move, scan, avoid, sensor_read) can be exposed as
LiteRT-LM "skills" — the Agent Skills pattern is structurally identical to MCP tool calling.

---

## Proposed Use Cases

1. **Offline voice control** — E2B audio input → parse command → ROS2 action, no cloud
2. **Visual navigation assist** — camera frame → bounding boxes → obstacle avoidance
3. **Offline fallback brain** — autonomous behaviour when Goliath unreachable (travel etc.)
4. **Japanese-language commands** — native 140+ language support, no translation layer

---

## Next Steps

- [ ] `pip install litert-lm` on Pi 5, verify install and E2B inference
- [ ] Test audio pipeline: Raspbot mic → LiteRT-LM ASR → command string
- [ ] Benchmark E4B 4-bit vs E2B on Pi 5 for quality/latency tradeoff
- [ ] Prototype one skill: "navigate to obstacle and stop" via LiteRT-LM tool call
- [ ] Explore wrapping LiteRT-LM skills as yahboom-mcp FastMCP tools (bidirectional)

---

## Further Reading

- `docs/BOOMY_AUTONOMOUS_INTELLIGENCE.md` — WIGO mode, Kaffeehaus demo, scenario plan
- `docs/BOOMY_COGNITIVE_ARCHITECTURE.md` — two-brain model, LiteRT-LM skill definitions
- `docs/ARCHITECTURE_DECISION_ROS2_VS_LLM.md` — ROS 2 stays, LLMs on top
- Google AI Edge blog: https://developers.googleblog.com/bring-state-of-the-art-agentic-skills-to-the-edge-with-gemma-4/
- LiteRT-LM HuggingFace: https://huggingface.co/litert-community/gemma-4-E4B-it-litert-lm
