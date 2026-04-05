# yahboom-mcp Deep Assessment

**Date:** 2026-04-04
**Assessor:** Claude Sonnet 4.6 (via MCP / Claude Desktop)
**Version assessed:** 2.0.0-alpha.2 (current HEAD)
**Supersedes:** ASSESSMENT_2026.md (2026-03-04, Cascade AI — grade inflation, pre-hardware-test)
**Tags:** [yahboom-mcp, raspbot, assessment, status, high]

---

## Ground Truth: What Actually Works

Based on code review, STATUS_HANDOFF.md, and direct hardware feedback (2026-04-04):

| Subsystem | Status | Notes |
|---|---|---|
| Wheel control (cmd_vel) | ✅ Working | Mecanum, all directions incl. strafe |
| RGB lightstrip | ✅ Working | `/rgblight` topic, topic wired in `_setup_topics` |
| MCP server (stdio/dual) | ✅ Working | FastMCP 3.1, portmanteau tool, agentic workflow |
| Webapp frontend | ✅ Working | React 19, Vite, ports 10892/10893 |
| SSH bridge | ✅ Working | paramiko, used for diagnostics and bringup |
| ROSBridge connection | ✅ Working | roslibpy, watchdog, dual-host handshake |
| Camera streaming | ❌ Broken | `/image_raw/compressed` subscribes but no data flows |
| Sensor reading (IMU/battery/odom) | ❌ Broken | Topics list as active, `echo` returns null/empty |
| Network (eth/wifi priority) | ❌ Broken | Ethernet and WiFi routing fight; WiFi should be primary |
| PTZ gimbal | ❌ Not implemented | `servo_topic` wired but no working commands confirmed |
| Sonar / line sensor | ❓ Unverified | Callbacks written, topic existence unconfirmed on hardware |
| LIDAR | ❓ Not fitted | Optional add-on; `/scan` subscriber ready but nothing to receive |

---

## Architecture Assessment

The architecture is sound. The code is clean and professionally structured. The problems are
not architectural — they are integration and infrastructure issues at the hardware/OS/network
boundary. This is an important distinction: fixing them does not require rewriting anything.

**What's solid:**

`ros2_bridge.py` is well-written. Quaternion-to-Euler conversion is correct. The
`_scan_to_obstacle_summary()` 8-sector collapse is reasonable. Sensor callbacks are clean.
`get_full_telemetry()` handles None gracefully. The dual-host connection handshake
(primary + fallback) is a good pattern. The watchdog reconnect loop is appropriate.

`video_bridge.py` handles CompressedImage, raw image (rgb8/bgr8/mono8/yuv422), and MJPEG
streaming cleanly. The logic is correct. The problem is upstream — the topic has no data.

The portmanteau tool pattern, FastMCP 3.1 integration, and SEP-1577 agentic workflow are
all implemented correctly at the code level.

**What's over-documented relative to reality:**

The March 2026 Cascade assessment (ASSESSMENT_2026.md, PRODUCTION_READINESS.md) awarded
grade A/A+ and "85% production ready" based on code review only — before the hardware was
fully tested. That was wrong. Sensors not working and camera not working are not minor gaps.
The actual operational completeness is closer to 40-50% of the intended capability.

---

## Problem Analysis

### 1. Sensor Blackout (IMU, Battery, Odometry)

**Symptom:** `ros2 topic list` shows `/imu/data`, `/battery_state`, `/odom` as active.
`ros2 topic echo` returns empty or null values.

**Root cause (most likely):** The `Rosmaster_Lib.py` UART-over-I2C protocol between the STM32
MCU (address `0x2b`) and the Pi is not being correctly parsed by the patched
`Mcnamu_driver.py`. The driver creates receive threads but the checksum/packet framing isn't
satisfying the ROS 2 message constructors, so the topics exist but publish garbage or nothing.

**Secondary possibility:** I2C instability. The board is capped at 100kHz via `dtparam`
(correctly done), but oxidised or loose cabling at the MCU junction causes 100% packet loss
despite `i2cdetect` seeing `0x2b`.

**What needs doing:**
- Verify actual byte stream from STM32 with a raw I2C trace or logic analyser capture
- Diff `Mcnamu_driver_patched.py` (repo root) against `Rosmaster_Lib.py` to find the
  missing packet structure
- Re-seat I2C cables physically before debugging further in software

### 2. Camera Streaming

**Symptom:** `/dev/video0` exists inside the Docker container. Topic `/image_raw/compressed`
is subscribed to but `VideoBridge` receives no frames (`frame_count` stays 0).

**Root cause:** The `usb_cam` (or equivalent ROS 2 camera node) is not running inside the
container, or is not publishing to `/image_raw/compressed`. The device is mapped but the
node was never started. This is a ROS 2 bringup gap, not a code bug.

**What needs doing:**
- SSH into the container: `docker exec -it yahboom_ros2 bash`
- Check: `ros2 node list` — is there a camera node?
- If not: `ros2 run usb_cam usb_cam_node_exe --ros-args -p video_device:=/dev/video0`
- Verify: `ros2 topic echo /image_raw/compressed --once` — does data come out?
- If the Yahboom bringup launch doesn't include the camera node, add it

Alternative: use direct MJPEG via `cv2.VideoCapture(0)` on the Pi (no ROS layer),
served over HTTP. This bypasses the ROS camera pipeline entirely and is more robust
for a simple feed. The `VideoBridge` could be extended with a direct-capture mode.

### 3. Network: Ethernet vs WiFi Priority

**Situation:** The Pi 5 has both ethernet (static `192.168.0.250`) and WiFi connected.
They fight for routing because both interfaces are up simultaneously. The MCP server
README still shows ethernet as the default IP. Ethernet was only for initial bringup.

**WiFi should be the operational interface.** Ethernet should be disabled or deprioritised
in normal operation.

**Fix on the Pi:**

```bash
# Check current routing table
ip route show

# If both routes compete, set WiFi metric lower (higher priority)
# Via NetworkManager (preferred on Ubuntu/Pi OS):
nmcli connection modify "Wired connection 1" ipv4.route-metric 200
nmcli connection modify "YourWiFiSSID" ipv4.route-metric 100
nmcli connection up "YourWiFiSSID"

# Or disable ethernet entirely when not needed:
nmcli connection down "Wired connection 1"
# Or: ip link set eth0 down
```

**Fix in yahboom-mcp:**

The default `YAHBOOM_IP` in `README.md` and `.env` examples must change from `192.168.0.250`
(ethernet static) to the WiFi IP (check router DHCP, or assign a static WiFi lease).

The `ROS2Bridge` dual-host handshake already supports a fallback — this should be
configured as WiFi primary, ethernet fallback (not the other way around).

```python
# Intended configuration after fix:
bridge = ROS2Bridge(
    host="<WIFI_IP>",           # primary: WiFi
    fallback_host="192.168.0.250"  # fallback: ethernet for recovery only
)
```

Document the WiFi IP in `CONNECTIVITY.md`. The current `CONNECTIVITY.md` still has
"Yahboom G1" in the title (wrong robot — it's a Raspbot v2) and the old IP throughout.

---

## Documentation Issues

Several docs are out of date or contain wrong information:

- `CONNECTIVITY.md` — title says "Yahboom G1" (should be Raspbot v2)
- `CONNECTIVITY.md` — no mention of ethernet/WiFi priority conflict
- `ASSESSMENT_2026.md` (old) — grade inflation, written before hardware test
- `PRODUCTION_READINESS.md` — "✅ Hardware Integration: Production Ready" — not accurate
- `README.md` — default IP `192.168.0.250` is ethernet, should be WiFi
- `docs/status.md` — likely stale (not reviewed but the pattern holds)
- `WIFI_TRANSITION.md` — describes the AP mode scenario (robot creates its own AP);
  the actual scenario is robot on home WiFi, which is a different configuration

---

## What Needs Doing (Prioritised)

### DONE (2026-04-04)

- [x] **`monitor_connection` TypeError** — `timeout_sec` → `timeout` kwarg fixed in `ros2_bridge.py`
- [x] **WiFi-first defaults** — `server.py` lifespan now uses `YAHBOOM_IP` defaulting to WiFi,
      `YAHBOOM_FALLBACK_IP` defaults to ethernet `192.168.0.250`
- [x] **README.md** — updated default IP and startup examples to show WiFi-first pattern
- [x] **CONNECTIVITY.md** — full rewrite: correct robot name (Raspbot v2 not G1), WiFi-primary
      architecture, NetworkManager metric fix commands, static DHCP lease instructions,
      full troubleshooting section
- [x] **`video_bridge.py`** — added direct `cv2.VideoCapture` fallback mode: if no ROS frames
      arrive within 10s, automatically switches to direct device capture. Also `YAHBOOM_CAMERA_DIRECT=1`
      env var to force direct mode. Fixes camera without requiring ROS camera node.
- [x] **`scripts/diagnose_sensors.sh`** — Pi-side diagnostic: I2C bus probe, node list,
      per-topic echo test, publish rate check, camera device check, dmesg I2C errors
- [x] **`scripts/start_camera.sh`** — Pi-side camera bringup: tries `usb_cam` then `v4l2_camera`,
      handles device-not-found gracefully, verifies topic after start
- [x] **`scripts/fix_network_priority.sh`** — Pi-side NetworkManager metric fix: WiFi=100,
      Ethernet=200, prints the WiFi IP and the env vars to set on Windows

- [x] **`lightstrip.py`** — patrol car, rainbow, breathe, fire patterns; async task, clean cancel
- [x] **`camera_ptz.py`** — 3-tier servo publish (bridge → ROS topic → SSH/I2C fallback); angle clamping; ssh_bridge passed through
- [x] **`display.py`** — rewrite: luma-only, shlex-safe, `get_status` probes I2C then pings luma, `scroll` fixed
- [x] **`voice.py`** — rewrite: USB VID:PID detection, device fallback scan, fixed base64 encoding bug, clean `_serial_cmd` helper
- [x] **Test scaffold** — `conftest.py` with `mock_ssh` + `mock_bridge_with_servo`; 30 unit tests in `tests/unit/test_all.py`; full E2E suite in `tests/e2e/test_patrol.py` including square patrol
- [x] **`pyproject.toml`** — `pytest-timeout`, `e2e` marker
- [x] **`CHANGELOG.md`** — v2.1.0 entry documenting all changes

### P0 — Still needed (hardware side)

- [ ] SSH into Pi, run `scripts/diagnose_sensors.sh`, paste output → fix I2C/UART protocol in `Mcnamu_driver_patched.py`
- [ ] Run `scripts/fix_network_priority.sh`, note WiFi IP, update `YAHBOOM_IP`
- [ ] Physically re-seat MCU I2C cables
- [ ] Start camera node: `bash scripts/start_camera.sh` on Pi
- [ ] Probe display: `yahboom(operation="display", param1="get_status")` → check I2C address
- [ ] Probe voice: `yahboom(operation="voice_status")` → check USB device path
- [ ] Probe servo: run E2E `test_e2e_servo_center` and check SSH fallback log

1. Physically re-seat I2C and MCU cables. Test `i2cdetect -y 1` before and after.
2. Capture raw UART/I2C stream from STM32. Compare against `Rosmaster_Lib.py` packet
   structure to find the parsing gap in `Mcnamu_driver_patched.py`.
3. Fix the packet parsing. Confirm `ros2 topic echo /imu/data` returns real values.
4. Confirm `/battery_state` and `/odom` also populate once driver is correct.

### P0 — Fix the network priority (30 minutes)

5. On the Pi: set WiFi metric lower than ethernet via NetworkManager.
6. Confirm WiFi IP, assign a static DHCP lease on the router.
7. Update `YAHBOOM_IP` default throughout the codebase and docs.
8. Reconfigure `ROS2Bridge(host=WIFI_IP, fallback_host=ETHERNET_IP)`.

### P1 — Unblock the camera (half day)

9. Start the camera node inside the container manually. Verify topic publishes.
10. If Yahboom bringup doesn't include it, add it to the launch file.
11. Alternatively: implement a direct `cv2.VideoCapture` path in `VideoBridge` as fallback.

### P2 — Code cleanup (1 day)

12. Fix `monitor_connection` — calls `connect(timeout_sec=...)` but `connect()` signature
    uses `timeout` (no `_sec` suffix). This will raise a TypeError on reconnect.
13. Fix `CONNECTIVITY.md` title and IP references.
14. Archive the March 2026 Cascade assessments as `_ASSESSMENT_2026-03-04_CASCADE.md`
    to avoid confusion with this one.

### P3 — Future work (when sensors + camera work)

15. PTZ gimbal: implement proper servo commands via `yahboomcar_msgs/msg/ServoControl`.
16. Speech: map `/dev/snd` into Docker, start voice node.
17. Sonar/line sensor: confirm topic names on live hardware, verify callback data.
18. Gemma 4 E2B/E4B: install LiteRT-LM on Pi, prototype local ASR + tool calling
    (see `GEMMA4_EDGE_LLM.md`).

---

## Honest Readiness Score

| Area | Score | Basis |
|---|---|---|
| Wheels / motion control | 90% | Works on hardware |
| RGB lightstrip | 80% | Works on hardware; edge cases untested |
| MCP server / tools / agentic | 75% | Code solid; partially blocked by sensor blackout |
| Webapp frontend | 70% | Renders; sensor panels show null-state |
| Camera | 10% | Code correct; pipeline not running |
| Sensors (IMU/battery/odom) | 10% | Topics exist; data is null |
| Network stability | 30% | Eth/WiFi conflict unresolved |
| PTZ/gimbal | 5% | Topic wired; commands not verified |
| Sonar/line sensor | 20% | Callbacks written; hardware unverified |
| **Overall operational** | **~40%** | Honest assessment against stated goals |

The architecture deserves a B+. The operational state is a D until sensors and camera work.
These are fixable problems — none of them require significant code changes.

---

## Quick Reference: Key IPs and Ports

| Item | Value | Status |
|---|---|---|
| Ethernet IP (old default) | 192.168.0.250 | Should become fallback only |
| WiFi IP | TBD — check router | Should become primary |
| ROSBridge port | 9090 | Working |
| MCP backend | 10892 | Working |
| Webapp frontend | 10893 | Working |
| MCU I2C address | 0x2b | Visible but sensor data null |
| Docker container | yahboom_ros2 | Running |
| Camera device | /dev/video0 | Mapped, node not running |
