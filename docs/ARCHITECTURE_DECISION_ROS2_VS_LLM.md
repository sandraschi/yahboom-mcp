# Architecture Decision: ROS 2 vs Pure-LLM Control for Boomy

**Date:** 2026-04-04
**Status:** Decision recorded — keep ROS 2, add LLM cognitive layer on top
**Tags:** [yahboom-mcp, architecture, ros2, llm, gemma4, decision, high]

---

## The Question

> Is ROS 2 Humble actually SOTA? Do we need it at all, or should we let Ollama / Gemma 4
> E2B control Boomy directly? ROS feels like pre-AI, old-school technology.

The instinct is directionally correct. The conclusion is: **keep ROS 2, add LLM on top**.
They solve different problems and the combination is stronger than either alone.

---

## What ROS 2 Actually Does

ROS 2 is a real-time hardware abstraction and publish-subscribe messaging bus.
It is not a planning system and has no intelligence. What it provides:

**Deterministic timing.** `/cmd_vel` at 50Hz, encoder callbacks at 100Hz, guaranteed
latency bounds. An LLM inference loop at 7.6 tok/s decode cannot issue a stop command
in 20ms. It cannot catch a cliff edge. ROS 2 can.

**Hardware drivers.** The Yahboom ROSMASTER board contains an STM32F103 MCU running
bare-metal firmware. It speaks a specific UART-over-I2C protocol. The `yahboomcar_bringup`
package is the driver that translates `/cmd_vel` Twist messages into motor PWM values.
Without it, nothing moves regardless of what the LLM decides.

**Sensor pipelines.** Odometry dead-reckoning, quaternion→Euler conversion, LaserScan
sector aggregation — deterministic maths at hardware rates. Not tasks for an LLM.

**Safety.** Emergency stop on cliff detection runs at hardware interrupt latency inside
a ROS 2 node. This must not go through an LLM inference step.

**Ecosystem.** SLAM (Nav2), URDF, coordinate frames (tf2), hardware-tested drivers
for cameras, LIDARs, servos. Decades of robotics engineering distilled into packages.
Replacing this is years of work.

## What ROS 2 Cannot Do

- Understand a scene: "is that Benny or an obstacle?"
- Plan from natural language: "go to the kitchen and come back"
- High-level goal decomposition
- Handle novel situations the programmer didn't anticipate
- Audio in/out, natural language interaction
- Adapt based on context

This is where LLMs belong. ROS 2 is the nervous system. LLMs are the brain.

---

## Is ROS 2 Humble Specifically SOTA?

**Yes, for this hardware, in 2026.**

- Humble is LTS until May 2027
- Best Pi 5 arm64 support of any ROS 2 distro
- Yahboom's Docker image ships Humble — the bringup, drivers, and launch files are all
  tested against it
- ROS 2 Iron and Jazzy exist but have thinner arm64 ecosystem and no Yahboom port

The "old school" feeling comes from ROS 2's build tooling (colcon, ament, DDS) which is
legitimately clunky compared to modern Python packaging. But the alternative isn't
"no ROS" — it's writing your own hardware driver for the STM32, which is months of work
for worse result.

**ROS 2 Humble stays. The architecture decision is what sits above it.**

---

## The 2026 SOTA Architecture

The robotics field has converged on a layered model. This is what Google, Boston Dynamics,
Figure, and the academic community are all converging on:

```
┌─────────────────────────────────────────────────────┐
│  COGNITIVE LAYER                                    │
│                                                     │
│  On-robot:  Gemma 4 E2B via LiteRT-LM (Pi 5)       │
│    • Scene understanding (vision input, native)     │
│    • Audio command parsing (ASR, native)            │
│    • Low-latency local decisions                    │
│    • Offline-capable                                │
│                                                     │
│  On Goliath: Claude / Ollama (Qwen3.5 27B etc.)    │
│    • Complex reasoning, planning, conversation      │
│    • MCP tool orchestration via yahboom-mcp         │
│    • Heavy multimodal tasks                         │
└────────────────────┬────────────────────────────────┘
                     │  Tool calls (JSON/REST)
                     │  via yahboom-mcp FastMCP tools
┌────────────────────▼────────────────────────────────┐
│  BRIDGE LAYER — yahboom-mcp                         │
│                                                     │
│  • Translates LLM tool calls → ROS 2 topics        │
│  • Rate-limits dangerous commands                  │
│  • Safety gates (battery low → refuse patrol)      │
│  • Exposes REST API for both LLM paths             │
│  • Already built (FastMCP 3.1, portmanteau tools)  │
└────────────────────┬────────────────────────────────┘
                     │  /cmd_vel, /servo, /rgblight …
                     │  via ROSBridge WebSocket (port 9090)
┌────────────────────▼────────────────────────────────┐
│  HARDWARE LAYER — ROS 2 Humble                      │
│                                                     │
│  • yahboomcar_bringup (STM32 driver)               │
│  • Deterministic motor control at 50Hz             │
│  • Sensor callbacks at hardware rate               │
│  • Safety: cliff guard, emergency stop             │
│  • Odometry, LIDAR, camera nodes                   │
└─────────────────────────────────────────────────────┘
```

yahboom-mcp is already the bridge layer. The architecture is correct.
**What's missing is the cognitive layer sitting on top.**

---

## Concrete Next Steps: Adding the Cognitive Layer

### Step 1 — LiteRT-LM E2B on the Pi (fast path, offline)

```bash
# On the Pi 5
pip install litert-lm
litert-lm --model gemma4-e2b-it
```

E2B fits in <1.5GB RAM at 4-bit, leaving 14GB+ for ROS 2 and other processes.
Runs at 7.6 tok/s decode on CPU — adequate for command parsing and goal decomposition.
Native audio input: offline voice commands without cloud ASR.
Native vision: feed camera frames, get structured decisions.
Native tool calling: define yahboom-mcp endpoints as LiteRT-LM "skills".

### Step 2 — Define Agent Skills for yahboom-mcp

LiteRT-LM "skills" are structurally identical to MCP tool definitions.
Map the existing yahboom-mcp REST endpoints as skills:

```python
# Sketch — LiteRT-LM skill definition
skills = [
    {
        "name": "move",
        "description": "Move Boomy. linear: m/s (-1 to 1), angular: rad/s (-2 to 2)",
        "endpoint": "http://localhost:10792/api/v1/control/move",
        "params": ["linear", "angular"]
    },
    {
        "name": "set_lights",
        "description": "Set lightstrip. pattern: patrol|rainbow|breathe|fire|off",
        "endpoint": "http://localhost:10792/api/v1/control/lightstrip",
        "params": ["operation", "pattern"]
    },
    {
        "name": "get_telemetry",
        "description": "Get battery, IMU, position, obstacle data",
        "endpoint": "http://localhost:10792/api/v1/telemetry",
        "method": "GET"
    },
    {
        "name": "stop",
        "description": "Emergency stop. Always available.",
        "endpoint": "http://localhost:10792/api/v1/stop_all",
    },
]
```

### Step 3 — Ollama on Goliath as heavy brain

When Goliath is reachable, yahboom-mcp's `yahboom_agentic_workflow` already supports
Claude via MCP. Ollama adds a local-only path: Qwen3.5 27B at ~40 tok/s on the RTX 4090.

The two paths are not competing — Pi E2B handles fast, offline, low-level decisions;
Goliath handles complex planning, conversation, and long-context tasks.

---

## What Does NOT Change

- ROS 2 Humble stays — it is the hardware driver, not the intelligence
- yahboom-mcp stays — it is the bridge, already built correctly
- ROSBridge stays — WebSocket protocol is stable
- The STM32 bringup stays — firmware-level, not replaceable with software

## What Changes

- LiteRT-LM E2B is added as the on-robot cognitive layer
- Agent Skills defined for yahboom-mcp endpoints
- Ollama path wired as the heavy-brain alternative
- The "observe → LLM → act" loop (`EMBODIED_AI.md`) becomes real instead of aspirational

---

## Comparison: ROS 2 vs Pure-LLM

| Concern | ROS 2 | LLM (E2B/Ollama) |
|---|---|---|
| Motor control latency | ~20ms deterministic | ~130ms+ (inference) |
| Hardware driver | Yes (STM32) | No — needs ROS underneath |
| Safety (cliff stop) | Hardware interrupt | Cannot guarantee |
| Scene understanding | No | Yes |
| Natural language | No | Yes |
| Novel situation handling | No | Yes |
| Offline capability | Yes | Yes (E2B on Pi) |
| Sensor fusion | Yes | Partial (needs data) |

Neither replaces the other. They are complementary layers.

---

## References

- Gemma 4 E2B on Pi 5: `mcp-central-docs/robotics/research/GEMMA4_EDGE_ON_RASPBOT.md`
- Current bridge architecture: `yahboom-mcp/docs/FASTMCP3_UNIFIED_GATEWAY.md`
- Embodied AI loop: `yahboom-mcp/docs/EMBODIED_AI.md`
- LiteRT-LM: https://ai.google.dev/edge/litert/models/gemma
- Google Agent Skills: https://developers.googleblog.com/bring-state-of-the-art-agentic-skills-to-the-edge-with-gemma-4/
