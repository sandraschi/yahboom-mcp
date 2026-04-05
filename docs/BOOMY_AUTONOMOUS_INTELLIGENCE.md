# Boomy Autonomous Intelligence: Architecture & Scenario Plan

**Date:** 2026-04-04
**Status:** Design document — implementation roadmap
**Tags:** [yahboom-mcp, boomy, autonomous, gemma4, litert-lm, architecture, design, high]
**Related:** `ARCHITECTURE_DECISION_ROS2_VS_LLM.md`, `GEMMA4_EDGE_ON_RASPBOT.md`

---

## Vision

Boomy is not a remote-controlled toy. Boomy is an autonomous agent that happens to accept
remote supervision when it's available. The guiding principle:

> **Connectivity to Goliath is a convenience, not a dependency.**
> Boomy must degrade gracefully through every level of connectivity loss,
> down to fully autonomous local operation with on-device intelligence.

This document covers:
1. The connectivity state machine
2. The autonomous "What is going on?" mode
3. Scenario-specific behaviour (front door, server status, environment sensing)
4. The Kaffeehaus demo mode
5. Implementation plan

---

## Part 1 — Connectivity State Machine

Boomy's runtime has four connectivity states. Transitions are detected by a background
watchdog running every 10 seconds.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONNECTIVITY STATES                          │
│                                                                 │
│  STATE 0: FULL                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Goliath reachable + yahboom-mcp connected + internet OK  │   │
│  │ → Full Claude/Ollama intelligence via MCP               │   │
│  │ → All tools available                                   │   │
│  │ → LED: slow blue breathe                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│            ↓ yahboom-mcp timeout (30s)                          │
│  STATE 1: LOCAL_AI                                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Goliath unreachable, WiFi still up, internet may work   │   │
│  │ → Gemma 4 E2B via LiteRT-LM takes over                 │   │
│  │ → All local hardware tools still available              │   │
│  │ → Reduced reasoning quality, no long-context tasks      │   │
│  │ → LED: slow green breathe                               │   │
│  │ → Voice: "Verbindung zu Goliath verloren. Lokalmodus."  │   │
│  └──────────────────────────────────────────────────────────┘   │
│            ↓ WiFi disconnect / DHCP timeout                     │
│  STATE 2: OFFLINE_AI                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ No network at all                                        │   │
│  │ → E2B still runs (no internet needed)                   │   │
│  │ → Switches to WIGO mode (see Part 2)                    │   │
│  │ → LED: amber pulse                                      │   │
│  │ → Voice: "Netzwerk nicht gefunden. Ich schaue mich um." │   │
│  └──────────────────────────────────────────────────────────┘   │
│            ↓ E2B inference fails or LiteRT-LM crash            │
│  STATE 3: HARDWARE_ONLY                                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ All AI unavailable — ROS 2 still runs                   │   │
│  │ → Pre-programmed safety patrol only (no LLM)            │   │
│  │ → Cliff guard, obstacle avoidance active                │   │
│  │ → LED: red slow pulse                                   │   │
│  │ → OLED: "SAFE MODE — AI OFFLINE"                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Watchdog Implementation

The connectivity watchdog runs as a systemd service on the Pi, independent of Docker
and ROS 2. It owns the state machine and triggers mode transitions.

```python
# /home/pi/boomy_watchdog.py — runs as systemd service
# Checks every 10s:
#   1. Can reach Goliath MCP at YAHBOOM_MCP_URL?
#   2. Can reach internet (1.1.1.1)?
#   3. Is E2B inference server responding?
# Updates /run/boomy/state (tmpfs, survives ROS restart, not reboot)
# Triggers mode transitions and LED/voice notifications
```

State is written to `/run/boomy/state` — a tmpfs file readable by all processes.
LiteRT-LM skill scripts check this file before deciding which action path to take.

---

## Part 2 — WIGO Mode ("What Is Going On?")

WIGO mode activates when Boomy detects connectivity loss (State 2 or 3).
It is Boomy's autonomous diagnostic and environmental awareness routine.

### WIGO Sequence

```
TRIGGER: Goliath unreachable for >30s
         OR WiFi lost
         OR manual button press (top KEY button)

STEP 1: ANNOUNCE
  → Voice: "Verbindung verloren. Ich schaue mich um."
  → LED: amber patrol pattern (slow flash)
  → OLED: "WIGO MODE" + timestamp

STEP 2: NETWORK PROBE (30 seconds)
  → ping 192.168.0.1 (router)  — is WiFi connected at all?
  → ping 1.1.1.1                — is internet reachable?
  → ping 192.168.0.105          — is Goliath up? (Boomy's own IP = different)
  → HTTP GET http://goliath:10792/api/v1/health  — is yahboom-mcp running?
  → Record results in /run/boomy/wigo_report.json

STEP 3: LED STATUS VISUAL CHECK
  → Pan camera toward Goliath's usual location (known fixed position)
  → Capture frame via cv2 or LiteRT-LM vision
  → Ask E2B: "Are there any indicator lights visible? What colour?"
  → If Goliath LEDs visible and correct colour: "Server scheint aktiv."
  → If dark/off: "Server-LEDs nicht sichtbar. Eventuell ausgefallen."
  → If ambiguous: log frame to /run/boomy/wigo_frames/

STEP 4: ENVIRONMENT SCAN
  → 360° slow rotation, capturing frames every 45°
  → For each frame, E2B vision analysis:
    - Is the front door open or closed?
    - Is anyone in the room?
    - Unusual objects / fire / water on floor?
    - Lighting conditions (day/night estimate)
  → Write structured JSON report to /run/boomy/env_report.json

STEP 5: SELF-ASSESSMENT
  → Check own battery level
  → Check CPU temp
  → Check RAM usage
  → Check ROS 2 node health
  → Write to /run/boomy/self_report.json

STEP 6: DECISION
  ┌─────────────────────────────────────────────────────────────┐
  │ IF router reachable BUT Goliath down:                       │
  │   → "Router erreichbar, Goliath antwortet nicht."          │
  │   → Wait 2 minutes, retry                                  │
  │   → After 3 retries: safe park + sleep (save battery)      │
  │                                                             │
  │ IF internet reachable:                                      │
  │   → Could theoretically reach cloud API (future)           │
  │   → Currently: log connectivity, continue local mode       │
  │                                                             │
  │ IF nothing reachable:                                       │
  │   → Full offline mode                                       │
  │   → Switch to autonomous patrol (if battery > 30%)         │
  │   → Or safe park (if battery < 30%)                        │
  │                                                             │
  │ IF danger detected (fire, flood, intruder):                 │
  │   → Emergency protocol (see Part 3)                        │
  └─────────────────────────────────────────────────────────────┘

STEP 7: REPORT
  → Compile full WIGO report
  → Write to /home/pi/boomy_logs/wigo_{timestamp}.json
  → OLED: summary (IP status, environment, battery)
  → If connectivity restored during WIGO: announce and exit mode
```

### WIGO Report Format

```json
{
  "timestamp": "2026-04-04T14:32:00Z",
  "trigger": "goliath_timeout",
  "network": {
    "router": true,
    "internet": false,
    "goliath_ping": false,
    "goliath_api": false
  },
  "environment": {
    "front_door": "closed",
    "persons_detected": 0,
    "lighting": "daylight",
    "anomalies": [],
    "frame_count": 8
  },
  "self": {
    "battery_pct": 74,
    "cpu_temp_c": 52.3,
    "ram_used_pct": 41,
    "ros2_nodes_ok": true
  },
  "decision": "wait_and_retry",
  "retry_count": 1
}
```

---

## Part 3 — Specific Autonomous Scenarios

### Scenario A: "Is the front door open?"

**Trigger:** WIGO scan OR periodic scheduled check (every 30 min when in autonomous mode)

**Implementation:**
```python
# On Pi, using LiteRT-LM vision
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
# Pan servo to front-door-facing position (calibrated once, stored in config)
await servo_set(pan=DOOR_PAN_ANGLE, tilt=DOOR_TILT_ANGLE)
time.sleep(1.0)  # settle
ret, frame = cap.read()

# Ask E2B with vision input
result = litert_lm.infer(
    model="gemma4-e2b",
    image=frame,
    prompt="Is the door in this image open, closed, or unclear? "
           "Answer with one word: open, closed, or unclear.",
    max_tokens=10
)
door_state = result.strip().lower()
```

**Actions:**
- Door open + no person detected + night: "Haustür ist offen!" → LED red flash → voice alert
- Door open + person detected: log as expected (someone coming/going)
- Door closed: log as normal, continue

**Config file** (`/home/pi/boomy_config.json`):
```json
{
  "door_check": {
    "enabled": true,
    "interval_minutes": 30,
    "servo_pan": 45,
    "servo_tilt": 75,
    "alert_if_open_and_night": true
  }
}
```

### Scenario B: "Is Goliath's server LED visible?"

**Trigger:** WIGO Step 3

**Implementation:**
- Goliath has a known physical location. Calibrate once: drive Boomy to a fixed spot,
  pan/tilt to point at Goliath's LED indicators, save angles to config.
- Capture frame, pass to E2B: "Describe any coloured lights visible. Are there blue,
  green, or red LEDs? How many?"
- Parse response to determine server state.

**Fallback:** If camera not working, check via network probe alone.

### Scenario C: Environment Anomaly Detection

**Periodic scan** every 2 hours during autonomous operation:
- Rotate 360°, capture 8 frames
- E2B prompt per frame: "List any objects or conditions that seem unusual, dangerous,
  or out of place. Be specific. If nothing unusual, say 'normal'."
- If any frame returns non-normal: log + voice alert + send to OLED

**Specific detections to train for (via E2B prompting, no fine-tuning needed):**
- Water on floor ("Wasser am Boden erkannt!")
- Smoke / unusual haze
- Open window (relevant if Benny might escape)
- Benny in a restricted area
- Unknown person (when autonomous and doors locked)
- Fallen object blocking path

### Scenario E: "Hey Sandra, ich habe die Verbindung verloren"

This is the most important immediate behaviour. When connectivity to Goliath drops:

**Voice dialogue:**
```
Boomy: "Hey Sandra, ich habe die Verbindung zum PC verloren. Was soll ich tun?"
```

**E2B ASR listens** for up to 30 seconds. Understood commands:

| What Sandra says | What Boomy does |
|---|---|
| "Geh in die Küche und warte" | Navigates toward kitchen area, stops, enters wait mode |
| "Komm zu mir" | Activates person-following or moves toward Sandra's voice |
| "Bleib wo du bist" | Stays put, enters monitoring mode |
| "Patrouilliere" | Enters autonomous patrol |
| "Lad dich auf" / "Geh zur Ladestation" | Dock-seek mode |
| "Alles gut, ich schaue es an" | Acknowledge, enter standby |
| (no response after 30s) | Runs WIGO mode, parks safely |

**Implementation in boomy_watchdog.py:**
```python
async def handle_connectivity_loss():
    # Announce
    await voice.execute(operation="say",
        param1="Hey Sandra, ich habe die Verbindung zum PC verloren. Was soll ich tun?")

    # Listen for 30s via E2B ASR
    command = await asr_listen(timeout=30)

    if command:
        intent = await e2b_parse_intent(command, language="de")
        await execute_intent(intent)
    else:
        # No response — run WIGO and park
        await voice.execute(operation="say",
            param1="Keine Antwort. Ich schaue mich um und warte.")
        await run_wigo()
```

**Future: "Bring mir ein Bier"**

When a gripper arm is fitted this extends naturally:
```
Sandra: "Boomy, bring mir ein Bier"
E2B intent: {action: fetch, object: beer, recipient: Sandra}
  → navigate to fridge area (known position in map)
  → vision: identify beer can/bottle
  → gripper: open → position → close
  → navigate back to Sandra (face detection or audio localisation)
  → gripper: release
  → "Bitte schön, Sandra!"
```

The dialogue parsing and intent extraction work today with E2B.
The actuator (gripper) is the missing hardware piece.

Boomy must manage its own energy autonomously.

```
Battery > 60%: Full autonomous operation
Battery 30-60%: Reduced patrol, limit speed
Battery 15-30%: OLED warning + voice "Akku niedrig" + navigate to dock area
Battery < 15%: Emergency park + sleep
  → Park at safe spot (near wall, out of traffic)
  → LED slow red pulse
  → Voice: "Akku kritisch. Ich warte auf Aufladung."
  → All non-essential processes suspended
```

**Dock navigation** (pre-AI, ROS 2 level):
- A physical marker (ArUco tag or coloured tape) at the dock
- Camera-based dock detection when battery low
- Navigate to within 30cm, stop

---

## Part 4 — Kaffeehaus Demo Mode

**Concept:** A scripted but intelligent demonstration mode. Triggered by:
- Double-press the top KEY button
- `yahboom(operation="demo_mode")` MCP tool call
- REST: `POST /api/v1/demo/start`

This is Boomy's showpiece. It runs fully on-device (E2B) and does not require Goliath.

### Demo Script — "Guten Tag" Sequence

```
PHASE 0: BOOT ANIMATION (3 seconds)
  → Rainbow lightstrip sweep
  → Servo: slow left-right head scan
  → OLED: "BOOMY v2 — DEMO MODE"

PHASE 1: GREETING
  → Stop centre, LEDs: warm white breathe
  → Voice (German): "Guten Tag! Ich bin Boomy, Ihr autonomer Assistent."
  →                  "Wie kann ich Ihnen zeigen, was ich kann?"
  → Tilt camera up slightly (attentive posture)
  → Wait 2 seconds

PHASE 2: SELF-INTRODUCTION
  → LED: blue
  → Voice: "Ich fahre auf vier Mecanum-Rädern — das bedeutet, ich kann mich
            in alle Richtungen bewegen, auch seitwärts."
  → DEMONSTRATE: strafe left 0.5s, strafe right 0.5s, 360° spin
  → LED: green flash on completion

PHASE 3: SENSOR DEMO
  → LED: cyan
  → Voice: "Ich kann meine Umgebung wahrnehmen."
  → Pan camera left-right-center (looking around)
  → Voice: "Meine Kamera sieht, ob Türen offen oder Personen anwesend sind."
  → Capture frame, run E2B: "What do you see in this room? One sentence."
  → Voice: read E2B response aloud (in German if possible)

PHASE 4: OBSTACLE AVOIDANCE DEMO
  → LED: orange
  → Voice: "Ich erkenne Hindernisse und weiche ihnen aus."
  → Drive forward slowly
  → If sonar < 0.4m: stop + back up + turn
  → Voice: "Hindernis erkannt — ich weiche aus."
  → Return to start position

PHASE 5: LIGHTSTRIP SHOWCASE
  → Voice: "Ich habe auch dekorative Beleuchtung."
  → Sequence: patrol → rainbow (5s each) → breathe → off
  → Voice: "Streifenlicht-Effekte für jeden Anlass."

PHASE 6: CLOSING
  → LED: warm white breathe
  → Voice: "Das war eine kurze Vorführung meiner Fähigkeiten."
  →        "Ich kann autonom patrouillieren, Türen überwachen,"
  →        "Personen erkennen, und vieles mehr."
  →        "Danke für Ihre Aufmerksamkeit!"
  → Slow bow: tilt camera down, pause, tilt back up
  → OLED: "DEMO COMPLETE — DANKE!"
  → LED: off after 5 seconds
  → Return to previous mode
```

### Demo Mode — Technical Implementation

```python
# src/yahboom_mcp/operations/demo.py
import asyncio
from . import motion, lightstrip, voice
from .camera_ptz import camera_set_pos

async def run_demo(bridge, ssh):
    """Full Kaffeehaus demo sequence."""

    async def say(text: str):
        await voice.execute(operation="say", param1=text)
        # Estimate duration: ~60 chars/second for German TTS
        await asyncio.sleep(max(1.5, len(text) / 60))

    async def led(pattern: str | None = None, r=0, g=0, b=0):
        if pattern:
            await lightstrip.execute(operation="pattern", param1=pattern)
        else:
            await lightstrip.execute(operation="set", param1=r, param2=g, param3=b)

    async def stop():
        await bridge.publish_velocity(0, 0)
        await asyncio.sleep(0.3)

    # Phase 0: Boot animation
    await led("rainbow")
    await camera_set_pos(bridge, 45, 90, ssh_bridge=ssh)
    await asyncio.sleep(0.5)
    await camera_set_pos(bridge, 135, 90, ssh_bridge=ssh)
    await asyncio.sleep(0.5)
    await camera_set_pos(bridge, 90, 90, ssh_bridge=ssh)
    await asyncio.sleep(1.0)

    # Phase 1: Greeting
    await led(r=200, g=180, b=150)  # warm white
    await say("Guten Tag! Ich bin Boomy, Ihr autonomer Assistent. "
              "Wie kann ich Ihnen zeigen, was ich kann?")
    await camera_set_pos(bridge, 90, 75, ssh_bridge=ssh)  # slight tilt up
    await asyncio.sleep(2)

    # Phase 2: Movement demo
    await led(r=0, g=0, b=255)
    await say("Ich fahre auf vier Mecanum-Rädern — "
              "das bedeutet, ich kann mich in alle Richtungen bewegen, "
              "auch seitwärts.")
    await bridge.publish_velocity(linear_x=0, angular_z=0, linear_y=0.25)
    await asyncio.sleep(1.2)
    await bridge.publish_velocity(linear_x=0, angular_z=0, linear_y=-0.25)
    await asyncio.sleep(1.2)
    await bridge.publish_velocity(linear_x=0, angular_z=0.6, linear_y=0)
    await asyncio.sleep(5.2)  # ~360° at 0.6 rad/s
    await stop()
    await led(r=0, g=255, b=0)
    await asyncio.sleep(0.5)

    # Phase 3: Sensor / vision demo
    await led(r=0, g=200, b=200)
    await say("Ich kann meine Umgebung wahrnehmen.")
    await camera_set_pos(bridge, 45, 80, ssh_bridge=ssh)
    await asyncio.sleep(0.8)
    await camera_set_pos(bridge, 135, 80, ssh_bridge=ssh)
    await asyncio.sleep(0.8)
    await camera_set_pos(bridge, 90, 80, ssh_bridge=ssh)
    await say("Meine Kamera sieht, ob Türen offen oder Personen anwesend sind.")

    # Phase 4: Obstacle avoidance
    await led(r=255, g=100, b=0)
    await say("Ich erkenne Hindernisse und weiche ihnen aus.")
    sonar = bridge.state.get("ir_proximity") or 2.0
    if sonar > 0.5:
        await bridge.publish_velocity(linear_x=0.15, angular_z=0)
        await asyncio.sleep(1.5)
    await stop()
    await say("Hindernis erkannt — ich weiche aus.")
    await bridge.publish_velocity(linear_x=-0.15, angular_z=0)
    await asyncio.sleep(1.0)
    await stop()

    # Phase 5: Lightstrip showcase
    for pattern, label, duration in [
        ("patrol", "Patrouillenmuster", 4),
        ("rainbow", "Regenbogeneffekt", 4),
        ("breathe", "Atemeffekt", 4),
    ]:
        await lightstrip.execute(operation="pattern", param1=pattern)
        await asyncio.sleep(duration)
    await lightstrip.execute(operation="off")
    await say("Streifen-Licht-Effekte für jeden Anlass.")

    # Phase 6: Closing
    await led(r=200, g=180, b=150)
    await say("Das war eine kurze Vorführung meiner Fähigkeiten. "
              "Ich kann autonom patrouillieren, Türen überwachen, "
              "Personen erkennen, und vieles mehr. "
              "Danke für Ihre Aufmerksamkeit!")
    await camera_set_pos(bridge, 90, 110, ssh_bridge=ssh)  # bow
    await asyncio.sleep(1.5)
    await camera_set_pos(bridge, 90, 90, ssh_bridge=ssh)
    await asyncio.sleep(5)
    await lightstrip.execute(operation="off")
```

### MCP Tool Registration

```python
# In server.py — register demo as a tool and endpoint
@app.post("/api/v1/demo/start")
async def start_demo():
    bridge = _state.get("bridge")
    ssh    = _state.get("ssh")
    if not bridge or not bridge.connected:
        return {"success": False, "error": "Bridge not connected"}
    asyncio.create_task(demo.run_demo(bridge, ssh))
    return {"success": True, "message": "Demo started"}

@app.post("/api/v1/demo/stop")
async def stop_demo():
    # Cancel demo task, stop all motion, lights off
    ...
```

---

## Part 5 — Autonomous Patrol Mode

When in LOCAL_AI or OFFLINE_AI state, Boomy switches to autonomous patrol.
This is more sophisticated than the E2E test patrol — it uses sensor feedback.

### Patrol Logic

```
PATROL TICK (every 500ms):
  1. Read sonar distance
  2. If sonar < 0.35m: AVOID (back up, turn random direction)
  3. If sonar < 0.60m: SLOW (reduce speed 50%)
  4. Else: FORWARD at nominal speed
  5. Every 30s: random direction change (prevents wall-hugging loops)
  6. Every 5min: stop, 360° scan, log environment snapshot
  7. Every 15min: check battery → if < 30%, dock-seek mode
```

### Patrol Zones (future — requires SLAM)

Once LIDAR is fitted, zones can be defined as named areas in the map:
- Living room, kitchen, hallway, front door
- Boomy can patrol a defined route rather than random walk
- Report: "Küche: normal. Haustür: geschlossen. Wohnzimmer: 1 Person."

---

## Part 6 — Implementation Plan

### Phase A — Foundation (1-2 days, mostly Pi-side)

1. Fix sensors (see `ASSESSMENT_2026.md` P0 tasks) — need IMU/battery/odom for autonomous op
2. Install LiteRT-LM E2B on Pi 5
3. Write `boomy_watchdog.py` systemd service
4. Implement connectivity state machine
5. Test LED + voice notifications per state

### Phase B — WIGO Mode (2-3 days)

6. Implement WIGO sequence as `operations/wigo.py`
7. Network probe functions
8. Camera capture + E2B vision query
9. WIGO report JSON writer
10. Register as MCP tool + `/api/v1/wigo/run` endpoint

### Phase C — Scenario Intelligence (3-5 days)

11. Door detection (camera + E2B + servo positioning)
12. Goliath LED visual check (servo calibration + E2B)
13. Environment anomaly detection
14. Battery management + dock-seek
15. Config file schema + `/home/pi/boomy_config.json`

### Phase D — Demo Mode (1-2 days)

16. `operations/demo.py` — full Kaffeehaus sequence
17. MCP tool `demo_mode` + REST endpoint
18. Webapp button "Start Demo" on Workflows page
19. Test full sequence, tune timing
20. Add more E2E test: `test_e2e_demo_mode.py`

### Phase E — Autonomous Patrol (2-3 days)

21. `operations/autonomous_patrol.py` — sensor-reactive patrol
22. Patrol mode state machine
23. Environment snapshot on schedule
24. OLED updates during patrol
25. Connect to WIGO: if anomaly detected during patrol, run full WIGO

### Total estimate: 9-15 days of focused Pi-side work

The heavy lifting is all on the Pi once sensors are working. Most of the Goliath-side
code (yahboom-mcp, FastMCP tools, REST endpoints) is already in place.

---

## Part 7 — Language & Personality Notes

Boomy speaks primarily **German** in the Vienna apartment context. The voice module
should have German as default language. Key phrases to use:

| Situation | German phrase |
|---|---|
| Startup | "Guten Morgen. Ich bin bereit." |
| Connectivity lost | "Verbindung verloren. Ich schaue mich um." |
| WIGO start | "Was ist hier los? Ich prüfe die Lage." |
| Door open at night | "Achtung! Die Haustür ist offen." |
| Battery low | "Mein Akku ist fast leer. Ich brauche Strom." |
| Obstacle | "Hindernis erkannt. Ich weiche aus." |
| Demo greeting | "Guten Tag! Wie kann ich Ihnen zeigen, was ich kann?" |
| Demo goodbye | "Danke für Ihre Aufmerksamkeit!" |
| Benny detected | "Hallo, Benny! Braver Hund." |
| All clear | "Alles in Ordnung. Ich setze die Patrouille fort." |
| Error | "Entschuldigung. Ein Fehler ist aufgetreten." |

**Personality:** Boomy is friendly, slightly formal (Sie-form with strangers, du-form
with Benny), competent, and self-aware. Does not pretend to have capabilities it lacks.
Reports status honestly. Has a dry sense of humour when appropriate.

---

## Appendix — File Locations

| File | Purpose |
|---|---|
| `/home/pi/boomy_watchdog.py` | Connectivity state machine daemon |
| `/home/pi/boomy_config.json` | Scenario config (door angles, zones, etc.) |
| `/run/boomy/state` | Current connectivity state (tmpfs) |
| `/run/boomy/wigo_report.json` | Latest WIGO report (tmpfs) |
| `/home/pi/boomy_logs/` | Persistent logs, WIGO reports |
| `/home/pi/boomy_frames/` | Saved frames from anomaly detection |
| `src/yahboom_mcp/operations/wigo.py` | WIGO mode implementation |
| `src/yahboom_mcp/operations/demo.py` | Kaffeehaus demo implementation |
| `src/yahboom_mcp/operations/autonomous.py` | Autonomous patrol implementation |
