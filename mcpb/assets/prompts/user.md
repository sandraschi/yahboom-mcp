# yahboom-mcp — Operator Guide

This guide teaches a human or agent operator to bring up the Yahboom Raspbot v2
("Boomy"), drive it from chat or the dashboard, and recover it when something
breaks. Backend runs on port **10892**, dashboard on **10893**. All chat control
flows through the MCP tools; the dashboard mirrors them for manual use.

## 1. Quick start (15 minutes)

1. Power the robot and join it to your LAN (AP mode works for first contact;
   infrastructure Wi-Fi for daily use). Note the Pi IP (default `192.168.1.11`).
2. On the robot (or its factory image), start rosbridge:
   `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`, and confirm
   the `yahboom_ros2_final` container is up (`docker ps`).
3. On your PC: `git clone https://github.com/sandraschi/yahboom-mcp`,
   `uv sync --extra dev`, copy `.env.example` to `.env`, set `YAHBOOM_IP`.
4. Launch: `.\start.ps1` (dual mode) or `uv run python -m yahboom_mcp.server
   --mode dual --port 10892`. Open `http://localhost:10893`.
5. First tool call, always: `yahboom_tool(operation="health_check")`. Green
   across ROS/SSH/video means you may drive. No hardware? Set
   `YAHBOOM_USE_MOCK_BRIDGE=1` and practice the whole guide risk-free.
6. Claude Desktop users: drag `yahboom-mcp-v2.5.0.mcpb` from GitHub Releases
   into the app (see INSTALL.md Option A), then set `YAHBOOM_IP` in the server
   env block.

## 2. Tutorials

### T1. Your first drive (2 min, open floor)

Call `health_check`, then `read_battery` (want > 20%). Drive:
`yahboom_tool(operation="forward", param1=0.3)` — wait three seconds —
`yahboom_tool(operation="stop")`. Read `read_imu` for the new heading. That is
the whole loop: check, move, stop, verify. Repeat with `turn_left`
(param1=0.5 rad/s) and `strafe_left` (param1=0.2 m/s) to feel holonomic motion.

### T2. Battery-aware patrol

Before any patrol, gate on battery: `read_battery` under 20% means charge
first. Healthy? Call `yahboom_agentic_workflow(goal="Patrol a 2 m square:
forward 2 s, turn left 90 degrees, repeat 4 times, stop, report battery")`.
The planner sequences health, moves, LIDAR glances, and the final stop. Watch
progress in Dashboard Mission Control and `/api/v1/logs/stream`.

### T3. Obstacle check with LIDAR

`lidar(operation="read", source="yahboom")` returns 8 sectors with distances.
Drive only into sectors reading clear beyond 0.8 m. For the raw point cloud use
`read_raw`. If you also run dreame-mcp, `lidar(operation="read_dreame_map",
source="dreame")` overlays the D20 Pro floorplan — compare both before
trusting one.

### T4. Camera PTZ tour

`camera_reset`, then `camera_left`, `camera_up`, `camera_right`, `camera_down`
in sequence with a `/api/v1/snapshot` after each to confirm framing. `set_pos`
takes a preset; `move` takes deltas. If snapshots return 204, no frame has
arrived yet — check video bridge state, not the camera.

### T5. OLED messages

`display` writes a line (`clear_display` wipes). Typical use: show status
(`display`, param1="PATROL 2/4 · BAT 78%") so bystanders see state. Scrolling
text uses `POST /api/v1/scroll`; probe with `/api/v1/status` first (I2C probe).

### T6. Lightstrip and buzzer

`led` sets RGB (e.g. red 255,0,0 for stop; green for go), `led_off` clears,
`light_effect` runs a named pattern, `patrol_car` arms the patrol preset.
Pair with `play(operation="play", ...)` siren ID for an attention sequence, or
`POST /api/v1/emergency` for the full strobe+siren background loop (toggle off
the same way).

### T7. Voice and audio

`say` speaks TTS through the voice module; `play(operation="sound",
file_name="ding")` fires one of 17 built-ins. For custom clips: `audio`
`store` a local mp3 to `~/boomy_audio/`, then `play_stored` by name;
`list_stored`/`delete_stored`/`stop` manage the shelf. Tapo camera two-way:
`POST /api/v1/tapo/audio/listen` transcribes via faster-whisper,
`.../speak` plays TTS out the Pi speaker. Voice-module not found? The server
scans `/dev/ttyUSB*` by VID:PID — set `YAHBOOM_VOICE_DEVICE=/dev/ttyUSBn` or
install the `/dev/ttyVOICE` udev symlink (docs/hardware/HARDWARE_DIAGNOSIS_VOICE_I2C.md).

### T8. Record and replay a trajectory

`start_recording`, drive your path manually (dashboard Mission Control or
single tool calls), `stop_recording` with a name. `list_trajectories` shows
saved runs; missions can replay them. Keep runs short (< 60 s) until odometry
trust is established via `read_encoders` drift checks.

### T9. LLM mission ("find our dog" pattern)

`yahboom_agent_mission(goal="Find the dog in the living room, approach slowly,
stop 1 m away, say hello", publish_to_ros=true, speak=true)`. The planner
returns structured JSON (intent, behavior, target, optional nav2 goal),
publishes it on `/boomy/mission` for the on-Pi executor, and speaks feedback.
Provider `auto` prefers Gemini (needs `YAHBOOM_GEMINI_API_KEY`) else Ollama
(default endpoint is the Pi itself at :11434 — set `OLLAMA_BASE_URL` for a
bigger host model). Watch `/api/v1/missions/status`.

### T10. ROS graph inspection

`ros_topic_list()` shows live topics + types; `ros_node_info(node)` shows
publishers/subscribers/services for one node. Stale list? `ros_resync()`
re-discovers and resubscribes. The dashboard Diagnostics page renders the same
data with resync/restart buttons and an SSH shell.

### T11. SSH recovery without leaving chat

`execute_command` runs read-mostly commands (`docker ps`, `ros2 node list`,
`hostname -I`, `docker logs --tail`). Blocked tokens (rm, mkfs, dd, shutdown,
reboot, passwd, device redirects) return 403 — this is deliberate. For full
shell, use the dashboard SSH panel or your own terminal with
`YAHBOOM_SSH_USER`.

### T12. Demos for visitors

`yahboom_demo` chalk drawing (`demo_draw` pattern `smiley`/`heart`/`boomy_b`;
needs flat floor + chalk holder) and talkbot (`demo_talkbot`: approach, PTZ
wiggle, spoken greeting). Always `..._stop` + `stop` when the audience leaves.
Check `demo_draw_status`/`demo_talkbot_status` before assuming idle.

## 3. REST endpoint examples (curl against :10892)

- Health: `curl http://localhost:10892/api/v1/health`
- Telemetry: `curl http://localhost:10892/api/v1/telemetry`
- Move: `curl -X POST "http://localhost:10892/api/v1/control/move?linear=0.2&angular=0.0"`
- Tool bridge: `curl -X POST http://localhost:10892/api/v1/control/tool -H "Content-Type: application/json" -d '{"operation":"read_battery"}'`
- Snapshot: `curl http://localhost:10892/api/v1/snapshot -o frame.jpg` (204 = empty)
- MJPEG: open `http://localhost:10892/stream` in a browser
- Logs: `curl http://localhost:10892/api/v1/logs/stream` (SSE)
- Skills: `curl http://localhost:10892/api/skills`
- Capabilities: `curl http://localhost:10892/api/capabilities`
- Chat: `curl -X POST http://localhost:10892/api/v1/chat -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"battery status?"}],"personality":"operator"}'` (needs a model selected in Settings)
- Mission: `curl -X POST http://localhost:10892/api/v1/agent/mission -H "Content-Type: application/json" -d '{"goal":"patrol the hallway","publish_to_ros":false}'`
- SLAM map: `curl http://localhost:10892/api/v1/slam/map -o map.png` (needs slam_toolbox on the robot)
- Swagger: `http://localhost:10892/docs`

## 4. Configuration cheat sheet

Robot link: `YAHBOOM_IP`, `YAHBOOM_FALLBACK_IP`, `YAHBOOM_BRIDGE_PORT` (9090),
`YAHBOOM_ESP32_PORT` (2323), `YAHBOOM_CONNECTION` (rosbridge|esp32),
`YAHBOOM_ROS2_CONTAINER` (yahboom_ros2_final), `YAHBOOM_USE_MOCK_BRIDGE`.
Access: `YAHBOOM_SSH_USER/PASSWORD/KEYFILE`, `YAHBOOM_VOICE_DEVICE`.
Missions/LLM: `YAHBOOM_MISSION_TOPIC` (/boomy/mission), `YAHBOOM_GEMINI_API_KEY`,
`YAHBOOM_GEMINI_MISSION_MODEL`, `OLLAMA_BASE_URL`, `LMSTUDIO_BASE_URL`.
Maps/federation: `DREAME_MAP_URL`, `MCP_BRIDGE_URLS`, `YAHBOOM_TAURI`. CLI:
`--mode stdio|http|dual`, `--port`, `--robot-ip`, `--debug`. Full table with
defaults: `docs/CONFIGURATION.md`.

## 5. Troubleshooting

- **health_check red on ROS**: `inspect_stack` names the dead layer. TCP dead →
  robot IP changed or Wi-Fi dropped (try fallback IP). SSH up but ROS down →
  `docker ps` on the Pi; container exited → restart it; restart-loop → read
  `docker logs` (redacted preview via stack probe). Topics stale → `ros_resync`.
  Nothing helps → `ros_restart_bringup` (warn first, ~30 s outage).
- **Robot drives but odometry drifts**: cross-check `read_encoders` vs
  `read_imu` heading after a 360° turn; resync; keep trajectories short.
- **No video / snapshot 204**: bridge cache empty — wait 5 s and retry; then
  video bridge state; then SSH OpenCV fallback (`GET /api/v1/snapshot` chains
  all three automatically).
- **Voice module missing**: USB reseat, `get_voice_status` I2C probe,
  `YAHBOOM_VOICE_DEVICE` override, udev symlink doc.
- **Chat says no model**: Settings → LLM → Test provider → pick model → chat
  retries. `GET /api/v1/settings/ollama/status` tells reachability first.
- **Dashboard shows Connecting…**: backend still booting (uv sync on start) —
  wait + retry; check `:10892/api/v1/health` directly. A foreign-Origin browser
  tab needs same-origin URLs (the app uses relative `/api` + Vite proxy, Tauri
  builds use `VITE_API_BASE`) — do not "fix" by widening CORS.
- **Agentic workflow stalls**: needs a sampling-capable client (Cursor/Claude
  Desktop with sampling); otherwise use single tool calls or the dashboard.
- **Port already bound**: `start.ps1` clears zombies; `fleet-start.config.ps1`
  holds 10892/10893 — never hardcode elsewhere.

## 6. FAQ

**Do I need the physical robot?** No — mock bridge runs the whole guide.
**ROS or ESP32 link?** ROS for sensing/missions, ESP32 for raw low-latency
velocity, mock for practice. **Can two clients drive at once?** Technically yes
— coordinate; `stop_all` is the shared panic button. **Where do trajectories
live?** Listed by `list_trajectories`; record short, replay supervised.
**Does chat have MCP tools?** No — dashboard chat is advisory (skills +
preprompt); execution happens in MCP clients or Mission Control.
**Which model for missions?** Host-scale Ollama or Gemini; the Pi's Gemma3:1b
suits chat, not planning. **How do I update?** `git pull`, `uv sync`,
restart; dashboard prompts on version skew. **Is my API key safe?** Keys live
server-side env only — the webapp talks to the backend proxy, never to
provider endpoints directly.

## 10. Dashboard page-by-page (what each screen is for)

**Dashboard**: link hero (gateway to Pi path with ROS/SSH/video dots), KPI
cards (server, robot, tools), stack chips, onboarding cue when offline.
**Mission Control**: drive pad, speed sliders, telemetry tiles, trajectory
record buttons. **Missions**: plan list, run/stop, live status. **Status**:
bringup detail (container, nodes, versions). **Peripherals**: LED picker,
buzzer, voice say/play, OLED writer, GPIO toggles. **Workflows**: one-click
agentic presets (patrol square, room sweep, return-to-dock). **Diagnostics**:
topic explorer, node inspector, resync/restart buttons, SSH shell, stack
table, sandbox exec box. **Logs**: SSE tail with level filter plus export.
**Chat**: skill-first companion, personalities, history, export. **Tools**:
every MCP op with params plus try-it. **Apps**: fleet siblings (speech,
dreame) with jump links. **LLM**: Ollama/LM Studio cards, Test buttons, model
dropdowns, GPU readout. **Settings**: connection (IP, ports, container),
mission topic, voice device. **Onboarding**: bring-up checklist with sanity
commands. **Help**: endpoint reference, MCP snippets, port table. **Viz**: 3D
robot plus camera frustum. **Map / SLAM / LidarMap / LidarAddon**: occupancy
grid, pose trail, scan overlay, Dreame comparison. **Movement**: fine jog
controls. **Sensors**: IMU/encoder/battery charts. **Voice / VoiceUpgrade**:
module status, say/play, firmware notes. **Audio**: shelf manager
(store/play/delete). **Analytics**: drive-time and distance summaries.

## 11. Advanced tutorials (level 3)

### T21. Voice module upgrade path

`get_voice_status` baseline (firmware, VID:PID). If the CSK4002 mishears,
first reposition (mic facing the room, away from wheel noise), then the
VoiceUpgrade page firmware notes, then pin `YAHBOOM_VOICE_DEVICE` so a reboot
never reorders `/dev/ttyUSBn`. Regression test: the T17 phrase set — all
three must transcribe before you call it fixed.

### T22. Rosbridge at boot (Pi side)

Install `scripts/robot/install-rosbridge-at-boot.sh` over SSH so rosbridge
plus drivers survive power cycles (docs/ops/ROSBRIDGE_AT_BOOT.md). Verify with
a cold boot: power off, wait 30 s, power on, `docker ps` at +90 s, dashboard
green at +120 s. If the container restart-loops, `docker logs` names the
missing device (usually camera index shift after USB reseat — fix with a udev
rule, not a reboot habit).

### T23. Dreame standalone pairing

Run dreame-mcp (10894/10895), set `DREAME_MAP_URL`, restart yahboom-mcp.
`lidar(source="dreame")` should return the floorplan; overlay it in LidarAddon
and drive the T16 comparison. Dreame down? Yahboom reads keep working — the
proxy fails soft by design. Document which map you trusted per run.

### T24. Multi-robot notes (fleet of Boomys)

One server instance per robot (separate `YAHBOOM_IP`, separate ports — claim
new pairs, never share 10892). Name each instance (`boomy-1`, `boomy-2`) in
its `.env` and dashboard title. Missions stay per-robot; cross-robot
choreography goes through the agentic workflow in an MCP client that sees both
servers. Shared `stop_all` discipline: announce before anyone drives.

### T25. Pi image upgrade without tears

Snapshot first: export trajectories (`list_trajectories` names), maps (SLAM
PNGs), and your `.env`. Flash, reinstall Docker plus pull
`yahboomtechnology/ros-humble`, restore the container name
(`YAHBOOM_ROS2_CONTAINER` must match), rerun the T22 boot install, then the
T20 mock plan on hardware. Total downtime about 1 h; most of it is the image
pull.

### T26. Talkbot show routine (5-minute set)

`demo_talkbot` greeting → `display` "HELLO" → `light_effect` rainbow →
`camera` slow pan via `camera_left`/`camera_right` with snapshots on the Viz
page → `play` applause → `say` goodbye → `stop_all`. Rehearse twice in mock
mode; live audiences forgive slowness, not runaways.

## 12. Glossary

**Bringup**: the ROS 2 launch set (drivers plus rosbridge) inside the
container. **Rosmaster**: ESP32 low-level controller (motors, ping, line
sensors). **Holonomic**: mecanum drive — lateral strafing without turning.
**Stack probe**: layered TCP/SSH/Pi/Docker/ROS health snapshot. **Resync**:
topic re-discovery plus resubscribe. **Mock bridge**: scripted no-hardware
backend. **MissionPlanV1**: validated mission JSON schema. **Nav2 goal**:
x/y/theta navigation target. **Preprompt**: system text prepended to chat
(base plus skills plus persona). **Ring buffer**: in-memory rotating log store
(`query_logs`). **Sidecar**: PyInstaller backend exe shipped inside the Tauri
app. **Portmanteau**: one tool routing many operations via an `operation`
enum. **Skill-first**: chat answers grounded in registered skill texts.
**Tailscale**: mesh VPN reaching the dashboard off-LAN. **Udev symlink**:
stable `/dev` name for USB devices across reboots. **VID:PID**: USB
vendor/product ID pair used to find the voice module. **slam_toolbox**: ROS 2
mapping stack producing the occupancy grid.

## 13. First-week practice curriculum (mock bridge, 30 min/day)

**Day 1**: T1 three times until stop-after-move is reflex. **Day 2**: T3 —
call sectors with eyes closed, then verify by driving. **Day 3**: T2 square
patrol via agentic workflow, then the same square by hand (feel the planning
gap). **Day 4**: T5+T6 — OLED plus lightstrip status language you will reuse
forever. **Day 5**: T9 find-the-chair (mock target), watch the plan JSON, then
T18 abort drill twice. **Day 6**: T10+T11 — break the mock graph (ask how),
resync, recover via SSH commands. **Day 7**: T14 emergency drill timed, then
T26 talkbot routine start to finish. Graduate to hardware with T1 only.

## 14. Pre-drive checklist (print this)

1. `health_check` green on ROS/SSH/video. 2. Battery above 20% (`read_battery`
   number, not memory). 3. LIDAR sectors ahead clear (`read`). 4. Floor clear
   of cables, pets, toes. 5. `stop_all` reachable (chat open or dashboard
   Mission Control). 6. Trajectory recorder off unless intended. 7. Bystanders
   warned for siren/light effects. 8. Know your abort: mission stop, then
   `stop`, then `stop_all`. Skip any line and you are testing luck, not the
   robot.

## 15. More FAQ (second round)

**Why does the robot spin instead of strafing?** Mecanum wheels mounted
wrong-handed (X vs O configuration) — check the hardware stack doc before
blaming software. **IMU heading drifts indoors?** Magnetic interference from
motors/speakers — calibrate away from the chassis, and cross-check with
encoders. **Can I limit speed for kids?** Drive 0.1-0.2 m/s params and keep
`stop_all` yourself; there is no separate kid mode. **Dashboard on HTTPS?**
LAN plain HTTP is the supported shape; use Tailscale for remote rather than
exposing ports. **How many trajectories fit?** Dozens of short runs; name them
by room and date (`kitchen_2026-10-16`) or the list becomes archaeology.
**Rosbridge port conflict?** Only one server per robot IP:port — a second
`start.ps1` steals nothing but confuses everything; check `fleet-status` for
zombies. **What voids the warranty?** Physical mods (gripper force, voltage
hacks) — software cannot void it, but `execute_command` blocks the dangerous
nouns anyway. **Where is the project roadmap?** GitHub issues plus
`docs/releases/`; missions replay and server-side map export are the
most-asked next features.

## 16. Copy-paste scenario scripts (chat-ready)

**Morning check**: "health_check, then battery and IMU. Report all three
numbers." **Room sweep**: "Agentic workflow: sweep the living room clockwise,
LIDAR-gated, stop on sectors under half a meter, return to start, report
battery." **Guest demo**: "Talkbot greeting, OLED HELLO, rainbow effect, slow
camera pan, applause, goodbye, stop_all." **Low battery**: "read_battery —
if under 20, shortest path to dock, stop, display CHARGING." **Lost link**:
"inspect_stack, name the dead layer, resync once, report." Each script fits
one chat message; the agentic workflow executes multi-step ones.

## 17. Maintenance calendar

**Daily**: charge to full, wipe camera lens, `health_check` before first
drive. **Weekly**: T14 emergency drill, trajectory list prune, `docker logs`
glance for restart loops, Wi-Fi signal check (`iw` link above -65 dBm).
**Monthly**: wheel/encoder drift test (360° turn, compare IMU vs encoders),
gripper (if fitted) open/close cycle count, voice-phrase regression (T17
set), backup maps + trajectories + `.env` off-robot. **Quarterly**: Pi OS
patches, `uv sync` + full gate run on the server repo, review open GitHub
issues for your symptoms before inventing new ones. **Yearly**: battery
capacity test (full discharge timed vs new baseline — replace under 70%),
mecanum roller wear inspection, re-torque chassis screws. A maintained Boomy
lasts years; a neglected one eats LIDAR bearings and batteries.

## 18. Command reference card (every op in one place)

Motion: `forward` (m/s + optional seconds), `backward`, `turn_left`/`turn_right`
(rad/s), `strafe_left`/`strafe_right` (m/s lateral), `stop`, `stop_all`.
Sensors: `read_imu` (heading/pitch/roll), `read_encoders` (ticks),
`read_battery` (percent + volts), `read_all` (everything), `read_lidar`
(sectors). Voice: `say` (text), `play` (17 built-ins by name), `play_beep`,
`play_file` (local path), `chat_and_say` (LLM + voice), `audio_store`,
`audio_play_stored`, `audio_list_stored`, `audio_stop`. Display: `display`
(text + line), `clear_display`. Light: `led` (R/G/B), `led_off`,
`light_effect` (pattern), `patrol_car`. Camera: `camera_up/down/left/right/
reset/set_pos/move`. Paths: `start_recording`, `stop_recording` (name),
`list_trajectories`. Robot programs: `explore`, `explore_and_map`. Gripper:
`set/open/close/status`. Health: `health_check`, `config_show`,
`inspect_stack`, `execute_command` (sandboxed). LIDAR tool: `read`, `read_raw`,
`read_dreame_map` × source `yahboom/dreame/auto`. Audio tool: `play`, `sound`,
`store`, `play_stored`, `list_stored`, `delete_stored`, `stop`. ROS tools:
`ros_topic_list`, `ros_node_info`, `ros_resync`, `ros_restart_bringup`.
Missions: `yahboom_agent_mission` (goal/provider/publish/speak),
`yahboom_agentic_workflow` (goal). Demos: draw (`smiley/heart/boomy_b`) +
talkbot, each with status/stop. Help: `yahboom_help_tool` (7 categories).
Logs: `query_logs` (source/level/search/limit). Lifecycle:
`yahboom_shutdown`. Cards: `show_robot_status_card`. Prompts: quick_start,
patrol, diagnostics, patrol_apartment, go_to_recharge + 4 skills. HTTP: health,
telemetry, control/move, control/tool, display/*, voice/*, tapo/*, led, gpio,
emergency, reconnect, stop_all, missions/*, demo*, stream, snapshot,
slam/map, slam/data, lidar/dreame-map, settings/llm, settings/ollama/*,
settings/lmstudio/*, settings/gpu, chat, agent/mission, capabilities, skills,
bridge/proxies, shutdown, docs. Learn this card and the whole server fits in
your head.

## 19. Worked session transcript (boot to shutdown, annotated)

`health_check` → ROS green, battery 82%, video active. `read_lidar`: all
sectors beyond 1.5 m — clear. `forward` 0.3 for 3 s → `stop` → `read_imu`:
heading swung 2° (floor friction, normal). `display` "LOOP 1/4" →
`light_effect` patrol preset → `turn_left` 0.5 for 2 s → `stop` →
`read_battery`: 80%. `camera_left` → snapshot shows the doorway; `camera_reset`.
`say` "Loop one complete" → `play` ding. Repeat the loop three more times
(T2 pattern), then `read_all`: battery 71%, encoders symmetric, IMU level.
`start_recording` → drive the loop once more → `stop_recording` "loop_demo".
`list_trajectories` confirms it saved. `display` "DONE" → `led_off` →
`clear_display`. `query_logs` (limit 5) shows no errors. `yahboom_shutdown`
only if you are done for the day — otherwise leave the server up; idle cost
is nil and the next session starts at T1, not at boot. Total: 20 minutes,
zero surprises, one reusable trajectory. That is what a clean session feels
like — boring, logged, repeatable.

## 20. Error phrasebook (exact strings, exact moves)

"bridge not initialized" → robot link never came up; check `YAHBOOM_IP` and
rerun `health_check`. "SSH Not Connected" → credentials or Wi-Fi; verify the
Pi on LAN, then reconnect. "No model selected" → Settings → LLM → Test →
pick → retry chat. "Ollama unreachable" → host asleep or URL wrong; the
settings status endpoint proves reachability before you blame the model. "Model
returned invalid JSON" → mission goal too vague; add a concrete target and
retry once. "Command blocked" → sandbox refusal (403); use the dashboard SSH
panel for anything beyond read-mostly. "topics stale" → `ros_resync`, wait
10 s, re-list. "container exited" → SSH `docker ps -a`, restart the bringup
container, watch logs for the missing device. "204 No Content" on snapshot →
not an error; the frame cache is empty right after boot. "voice module not
found" → USB reseat, then `YAHBOOM_VOICE_DEVICE` override. "battery critical"
→ stop everything, dock now, debrief later. When in doubt: health, inspect,
resync, restart — one ladder, then hands-on hardware.

## 21. About this bundle (version notes)

Bundle `yahboom-mcp` for server v2.5.0: 13 MCP tools plus prompts, skills,
and Prefab cards; stdio entry `python -m yahboom_mcp`; backend 10892,
dashboard 10893. New in this revision: skill-first chat (skills merged into
the system prompt with persona), robot status Prefab card, shared error
helper with traceback logging, `${__dirname}`-only manifest variables, and
the onboarding cue on the dashboard. Requires Python 3.12+ via uv; robot
optional (mock bridge included). Report issues to sandraschi/yahboom-mcp
with stack output and log slices attached.

## 7. More tutorials (level 2)

### T13. Gripper pick-and-place (if fitted)

`gripper_status` first (is anything held?). `gripper_open`, drive to the
object with LIDAR-gated creep (`forward` 0.1 m/s, stop on sector < 0.4 m),
`gripper_close`, lift check via `gripper_status`, drive back, `gripper_open`.
Never close on unknown resistance — the Raspbot gripper has no force feedback.

### T14. Emergency drill (do this monthly)

With the robot on open floor: `forward` 0.3, then `stop_all` mid-motion.
Verify halt under half a second via `read_encoders` (ticks frozen). Then
`POST /api/v1/emergency` with `{"active": true}` — strobe plus siren should
run; `{"active": false}` silences. Log the drill date; a stale drill is how
surprises happen.

### T15. SLAM mapping session

Needs `slam_toolbox` on the robot. Drive slowly (`explore` supervised or manual
0.15 m/s loops) while `GET /api/v1/slam/data` streams grid plus pose plus scan
overlay to the SLAM page. Save with `GET /api/v1/slam/map` to PNG when loop
closure looks tight (walls overlap, no doubling). Bad map? Fast driving and
featureless corridors are the usual causes — slow down, add objects.

### T16. Dreame vs Yahboom map comparison

With dreame-mcp running, open LidarAddon: Yahboom `/scan` sectors beside the
Dreame floorplan. Walk the robot 2 m and watch both update — agreement means
both localized; divergence means one drifted (usually the cheaper odometry).
`read_dreame_map` vs `read` timestamps tell which is staler.

### T17. Tapo listening session

Quiet room: `POST /api/v1/tapo/audio/listen` captures RTSP mic audio and
transcribes via faster-whisper. Speak a command phrase, confirm the text, then
`speak` the acknowledgement out the Pi speaker. Latency over 5 s usually means
the Whisper model is cold-loading — the second run is fast.

### T18. Multi-room mission with nav2 goal

In `yahboom_agent_mission`, include a concrete target ("kitchen doorway, 3 m
ahead of dock") so the planner emits a nav2 goal, not just behaviors. Publish
with `publish_to_ros=true` and watch `/boomy/mission` echo in
`/api/v1/missions/status`. Abort path: `POST /api/v1/missions/stop` then
`stop_all` — practice the abort before you need it.

### T19. Dashboard tour (every page in 10 minutes)

Dashboard (link hero + KPIs) → Mission Control (drive 1 m) → Peripherals (LED
red, beep, OLED "HI") → Diagnostics (topic list, one resync) → Logs (watch a
drive scroll by) → Chat (ask "battery status?") → LLM (Test Ollama) → Tools
(find `read_lidar`) → Onboarding (read the bring-up list even if done) → Help
(copy the Claude Desktop snippet). If any page hangs on a spinner, the backend
is mid-boot — wait 30 s, retry once, then check `:10892/api/v1/health`.

### T20. Mock-bridge practice plan (no hardware week)

Set `YAHBOOM_USE_MOCK_BRIDGE=1`, restart, and run T1–T12 end to end: every op
responds with scripted data. Graduate when you can do T2 + T9 + T14 without
looking at this guide. Unset the flag and re-run T1 on hardware — the only
difference should be real sensor numbers.

## 8. Extended troubleshooting

- **Topics list empty but bridge connected**: rosapi not yet discovered — wait
  10 s, `ros_resync`, re-list. Still empty: the container's rosbridge may serve
  a different port — check `YAHBOOM_BRIDGE_PORT` against the compose file.
- **Encoders frozen mid-drive**: ESP32 link dropped (check `inspect_stack` TCP
  layer) or wheels lifted. Re-seat, re-check, resume.
- **OLED shows garbage**: I2C clock stretch on long cables — `clear_display`,
  rewrite shorter text; persistent garbage means 5 V rail sag (charge battery).
- **Lightstrip one color stuck**: `led_off` then set again; a stuck channel
  after power cycle is a hardware fault, not software.
- **Tapo listen hears nothing**: RTSP credentials changed camera-side —
  re-check `.../status` connectivity first, then mic gain in the Tapo app.
- **Mission publishes but robot idles**: executor not subscribed — verify
  `YAHBOOM_MISSION_TOPIC` matches the Pi executor's topic (`/boomy/mission`
  default both sides) and the executor process is alive via SSH.
- **Chat answers generically**: no model selected (Settings) or skills failed
  to load (`GET /api/skills` should list 4) — the system prompt degrades
  gracefully, but quality drops without skills plus persona.
- **After Pi reboot nothing works**: Docker autostart may lag rosbridge by a
  minute; `docker ps` until `yahboom_ros2_final` is healthy, then resync.

## 9. Extended FAQ

**Can I drive from my phone?** Open the dashboard URL (Tailscale or LAN) —
Mission Control is touch-usable; no app needed. **Two operators at once?**
Last command wins; use `stop_all` liberally and coordinate over chat.
**How loud is the siren?** Loud enough for a workshop — warn the room before
T6/T14. **Does it work outdoors?** LIDAR yes, camera exposure struggles in
direct sun, Wi-Fi range is the real limit — stay within AP sight.
**What breaks most often?** Wi-Fi roaming (static DHCP lease fixes most of
it), followed by discharged batteries sagging the 5 V rail. **Can missions run
offline?** Ollama on LAN yes; Gemini needs internet. **How do I back up maps
and trajectories?** Copy the robot-side map saves plus `list_trajectories`
names into your own notes; server-side export is on the roadmap. **Is there a
speed limit?** Software caps at safe indoor values — verify with `config_show`
before gymnasiums. **Kid-safe?** Supervised, open floor, `stop_all` in hand,
under 0.2 m/s — the talkbot demo is the recommended first contact.
