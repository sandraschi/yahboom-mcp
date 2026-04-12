# yahboom-mcp — TODO & Architectural Notes

> Distilled from *Gemini iPad Chat #1* (April 12, 2026).  
> Full chat archived at: `mcp-central-docs/docs/agentic chats/gemini ipad chat #1.md`

---

## 🐛 Known Issues / Immediate Fixes

### PTZ Camera Not Responding (I2C Red Herring)

- [ ] **Stop looking for PTZ servos on Pi's I2C bus** — they are NOT there.
  - PTZ servos are PWM-driven by the **ESP32-S3 co-processor**, not the Pi 5 GPIO.
  - Communication chain: `Pi 5 ROS 2 node → micro_ros_agent (serial) → ESP32 firmware → PWM servo pins`
  - Running `i2cdetect -y 1` on the Pi will not find the gimbal servos. Only the IMU or OLED typically sit on the Pi's I2C bus.

- [ ] **Verify Micro-ROS Agent is running and connected**
  ```bash
  ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0
  ```
  - Baud rate is likely **921600** (Yahboom high-speed serial).
  - If the agent isn't bridging, the Pi is shouting into a void.

- [ ] **Audit PTZ topic name** (non-standard, likely Yahboom-specific)
  ```bash
  ros2 topic list | grep -i ptz
  # or
  ros2 topic list | grep -i camera
  ```

- [ ] **Ensure Docker container has serial device passthrough**
  ```yaml
  # docker-compose.yml
  devices:
    - /dev/ttyUSB0:/dev/ttyUSB0   # Micro-ROS agent to ESP32
  privileged: true                 # or explicit device cgroup rules
  ```

- [ ] **Compile custom Yahboom message types** — standard ROS 2 `sensor_msgs` won't work for Yahboom hardware.
  - Package: `yahboomcar_msgs` (check Yahboom GitHub for the correct package name)
  - Must be sourced in the Docker workspace before the nodes launch.

- [ ] **Hardware bypass test** (isolate hardware vs. ROS mapping)
  - Yahboom usually ships a standalone Python library (`Yahboom_ESP32_Board.py`).
  - Run outside Docker to confirm servos can physically move. If yes → it's a ROS topic/mapping issue.

### Cliff Sensor / Camera Missing After Rebuild

- [ ] Document the "Bricked Boomy Incident" SOP (see below).
- [ ] Verify cliff sensor topic is alive after any OS-level changes.

---

## ⚠️ Hard-Won Lessons — "Bricked Boomy" SOP

> **Context**: During an AG (Gemini 3.1 Flash) session, the model attempted a full Debian + ROS 2 rebuild from scratch. This caused:
> - Loss of camera driver
> - Loss of cliff sensor
> - Factory Yahboom `.so` blobs and specialized kernel tweaks were not preserved

### Guardrails — Add to `CONTRIBUTING.md` and justfile

- [ ] **Strictly forbid "Rebuild from Debian"** unless the following are mirrored first:
  - Yahboom factory `.so` blobs
  - Specialized Yahboom headers and kernel modules
  - The original factory MicroSD image (keep a backup!)

- [ ] **Add a `just recover` command** that resets the workspace to a known-good state (commit hash from last working state).

- [ ] **Hardware-in-the-loop gate before `just push`**:
  ```makefile
  # justfile
  check-hardware:
      @ros2 topic echo /cliff_sensor --once --timeout 3 || (echo "❌ Cliff sensor not alive!" && exit 1)
      @ros2 topic echo /camera/image_raw --once --timeout 3 || (echo "❌ Camera not alive!" && exit 1)
  
  push: check-hardware
      git push
  ```

- [ ] **Model selection note for contributors**: Use Opus 4.6 or local Gemma 4 for sensor-level debugging — avoid large-context models (Flash 3.1) for hardware-specific recovery tasks; they tend toward radical reconstruction over surgical repair.

---

## 🧠 Architecture — Dual-Brain Reference

| Component | Controlling Brain | Communication Method |
|-----------|------------------|---------------------|
| LIDAR (MS200) | Raspberry Pi 5 | USB Serial |
| Camera (USB) | Raspberry Pi 5 | V4L2 (Video for Linux) |
| PTZ Servos | ESP32-S3 | Micro-ROS (Serial bridge) |
| IMU / Motors | ESP32-S3 | Micro-ROS (Serial bridge) |
| Cliff Sensor | ESP32-S3 | Micro-ROS (Serial bridge) |

> The Pi 5 is the **High-Level Brain** (SLAM, path planning, MCP host).  
> The ESP32-S3 is the **Real-Time Actuator** (motors, servos, sensors).

---

## 🤖 Glom-On: Local LLM Integration (Gemma 4)

- [ ] Add "glom-on" Ollama connectivity check to the webapp frontend
  ```javascript
  const checkOllama = async () => {
    try {
      const res = await fetch("http://localhost:11434/api/tags");
      if (!res.ok) throw new Error();
      setOllamaStatus("connected");
    } catch (e) {
      setOllamaStatus("missing");
      toast.warning("Ollama not found. Install it to enable local grounded chat.");
    }
  };
  ```

- [ ] Add grounded system prompt for the in-repo chat (see `mcp-central-docs` for full template):
  - Context: Pi 5 16GB, ROS 2 Humble, Docker, ESP32-S3 co-processor, MS200 LIDAR, USB camera on 2DOF gimbal.
  - Preferred model: `gemma4:e2b` (runs at ~8–12 tok/s on Pi 5 16GB, leaves ~10GB for ROS 2 + Docker).
  - Model autopull if missing:
    ```bash
    curl http://localhost:11434/api/pull -d '{"name": "gemma4:e2b"}'
    ```

- [ ] Implement "Local First" routing in `local-llm-mcp` — standardized across the fleet.

---

## 🌡️ Thermal Governor

> Pi 5 fan is present but likely insufficient under sustained LLM + ROS 2 load. Must watch temp like a hawk.

- [ ] Add thermal monitoring daemon:
  ```bash
  cat /sys/class/hwmon/hwmon0/temp1_input
  # Value is in millidegrees. >75000 = 75°C = throttle territory.
  ```

- [ ] If temp > 75°C, auto-throttle LLM context window to protect ROS 2 real-time nodes.
- [ ] Optional: pipe spoken warning via USB speech hat — *"Sandra, I'm getting too hot."*
- [ ] Track duty cycle of the active cooler fan; log thermal events in the webapp dashboard.

---

## 🎙️ Speech Hat Integration (USB Module)

- [ ] USB speech module can play arbitrary WAV/MP3 — not just canned TTS.
- [ ] Priority use cases:
  - **Overheat warning**: spoken alert before thermal throttle kicks in (more useful than OLED).
  - **Battery low**: spoken warning when power drops below threshold.
  - **Morning alarm**: Boomy navigates to bedroom (using Dustin's map) and plays annoying alarm sound.
  - **Patrol car gag**: siren WAV + red/blue lightstrip oscillation + *"Ausweis bitte!"* for Stammtisch demos.
  - **Dog interaction suite**: bark, whine, wolf howl (see Benny Protocol below).

---

## 🐕 Benny Protocol (GSD Interaction)

- [ ] **No laser pointer module on Boomy** — frustrated prey drive risk (Benny already hunts dark doorways).
- [ ] **Treat dispenser** (ESP32 servo):
  - Gravity-fed hopper inside shroud (reduce scent leak).
  - Spring-loaded servo "ejector" — drops treat to floor 50cm away, not at the robot body.
  - Acoustic conditioning: play a chime 0.5s before drop so Benny looks at floor not at robot.
  - Rate limiting: cooldown period — 3 presses/minute → *"No more snacks, Benny. Go lie down."*
  - `treat_ejector.py` service: ROS 2 service call → ESP32 servo pin.

- [ ] **Paw button interface**:
  - Large arcade buttons (100mm+), GSD-paw proof, debounced GPIO inputs.
  - Intents: `REQUEST_TREAT`, `REQUEST_TOY`, `REQUEST_OUTSIDE`.
  - Button color: Blue = toy, Yellow = treat (GSDs see blue and yellow best; avoid red/green).
  - "Working mode": during focus sessions, buttons software-disabled, lightstrip turns solid red.
  - All interactions acknowledged via speech hat to prevent Benny "disassembling" the button in frustration.

---

## 🖨️ Hardware / Shroud Updates (3D Print)

- [ ] Replace metal shroud (blocks GPIO pins) with 3D-printed version:
  - Open GPIO skyline for display hat and expansion.
  - Vented sides for active cooler airflow.
  - Dedicated recessed bay for USB speech module (side-mount, strain-relieved cable).
  - Speaker grille/venting near speech module.
  - Standoff mounts for 640×320 touch display hat (currently in drawer).
  - Raised LIDAR deck (YDLIDAR, when purchased) with clear 360° field of view.
  - LIDAR rotating assembly enclosed/protected (GSD nose hazard).
  - Touch screen slight recess (GSD snoot-contact protection).

- [ ] Decide on LIDAR hardware:
  - **Option A: YDLIDAR X2L** (~€40–50) — cheapo, 360°, stable ROS 2 drivers. Basic 2D SLAM.
  - **Option B: RPLIDAR A1M8** (~€70–90) — better range (12m), widely supported.
  - **Strategy**: Use **Dustin's** (Dreame) map for global localization; use cheapo LIDAR for reactive local obstacle avoidance only.

---

## 🗺️ Autonomy Roadmap

> Current state: Boomy tethered to Goliath (4090) via Wi-Fi — Goliath does the heavy cognitive lifting.  
> Goal: Full autonomy with entire loop (sense → decide → actuate) running on the Pi 5.

- [ ] Fix all ROS 2 topics so Micro-ROS bridge is fully operational (prerequisite for everything below).
- [ ] Integrate Dustin's (Dreame) map as shared coordinate origin for Nav2 localization.
- [ ] Validate NAV2 stack running natively on Pi 5 16GB.
- [ ] Gemma 4 E2B on Pi 5: replace hardcoded command detection with intent-parsed ROS 2 goal generation.
- [ ] Ship `just recover` and `just check-hardware` commands.

---

*Last updated: 2026-04-12 — Source: Gemini iPad Chat #1*
