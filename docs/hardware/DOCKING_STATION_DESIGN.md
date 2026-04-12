# Boomy Docking Station: Design & Implementation Plan

**Date:** 2026-04-04
**Status:** Future project — design document
**Tags:** [yahboom-mcp, boomy, docking, charging, hardware, design, medium]

---

## Overview

A docking station lets Boomy charge autonomously without human intervention. This closes
the loop on fully autonomous operation: Boomy can patrol for hours, detect low battery,
dock itself, charge, undock, and resume — all without Sandra touching it.

The design below covers three progressively capable approaches, from simple to full SLAM.

---

## Approach A — Passive Charging Dock (Simplest)

**No vision, no sensors, just a physical guide.**

### Hardware

```
┌─────────────────────────────────────────────────────┐
│  DOCK STATION                                        │
│                                                      │
│  ┌──────────┐   Two V-shaped guide rails (metal or  │
│  │ CHARGING │    3D-printed plastic) funnel Boomy   │
│  │  PADS    │   into alignment from ±10cm offset.   │
│  └──────────┘                                        │
│   ↑        ↑                                         │
│  Spring-loaded brass charging contacts (5V/3A)       │
│  Match contacts on Boomy's underside/front.          │
└─────────────────────────────────────────────────────┘
```

**Components:**
- 2× V-shaped guide rails (aluminum extrusion or 3D printed) ~30cm long
- 2× spring-loaded pogo pin connectors (~€3 each, common on Amazon)
- 5V 3A DC power supply (or 12V if charging the main LiPo directly)
- LED indicator: charging=red, full=green (simple voltage comparator circuit)

**Cost estimate: €15-30 in parts + 3D printing**

### Navigation to dock (no SLAM needed)

Boomy knows where the dock is — it's a fixed location in the apartment.
Navigation is dead-reckoning from a known starting position:

```python
# boomy_config.json — dock location relative to home position
"dock": {
    "approach_sequence": [
        {"action": "turn_to_heading", "heading_deg": 270},
        {"action": "forward", "distance_m": 2.5},
        {"action": "turn_to_heading", "heading_deg": 180},
        {"action": "forward_slow", "distance_m": 0.8}  # final approach
    ],
    "final_approach_speed": 0.05   # very slow — 5cm/s
}
```

**Limitation:** Dead-reckoning drifts. Works reliably for ~1-2 metres but not across
a large apartment. Good enough for a fixed "home base" within one room.

---

## Approach B — Visual Docking (Recommended First Implementation)

**Camera + ArUco marker = reliable ±2cm precision without SLAM.**

### Hardware additions

- 1× ArUco marker (print on A4, laminate, stick to dock) — **€0**
- 1× IR LED strip around the dock (optional, improves detection at night) — **€8**

ArUco marker: print marker ID 0 from the standard 6×6 ArUco dictionary at 15cm size.
Stick it vertically on the front face of the dock, centred.

### How visual docking works

```
DOCKING SEQUENCE:

1. COARSE APPROACH (dead-reckoning to within ~1m of dock)
   → Boomy drives to known dock area using pre-recorded sequence
   → Speed: 0.15 m/s

2. MARKER SEARCH (rotate to find ArUco)
   → Slow 360° rotation
   → Camera scans for ArUco marker ID 0
   → Timeout 30s: if not found, announce and request human help

3. ALIGNMENT
   → Camera sees marker: compute pan offset and distance
   → PD controller corrects heading: if marker left of centre → turn left
   → Approach until marker fills ~40% of frame width (≈30cm away)

4. FINAL DOCKING (slow + straight)
   → Lock heading, drive forward at 0.05 m/s
   → Stop when current draw detected on charging pins OR after distance timeout
   → LED: charging pattern

5. VERIFY CHARGING
   → Read battery voltage via sensors — is it rising? (30s check)
   → If yes: "Ich lade auf. Bis gleich, Sandra!"
   → If no: back up, retry approach (max 3 attempts)
```

### ArUco detection with OpenCV

```python
# scripts/dock_approach.py — runs on Pi via boomy_agent or yahboom-mcp tool

import cv2
import cv2.aruco as aruco
import numpy as np

ARUCO_DICT  = aruco.DICT_6X6_250
TARGET_ID   = 0
CAMERA_FOV  = 60.0   # degrees horizontal (estimate for Raspbot v2 USB cam)

def find_dock_marker(frame):
    """
    Returns (found, center_x_norm, distance_estimate_m)
    center_x_norm: -1.0 (left) to +1.0 (right), 0.0 = centred
    distance_estimate_m: rough estimate from marker apparent size
    """
    gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    adict   = aruco.getPredefinedDictionary(ARUCO_DICT)
    params  = aruco.DetectorParameters()
    detector = aruco.ArucoDetector(adict, params)
    corners, ids, _ = detector.detectMarkers(gray)

    if ids is None:
        return False, 0.0, None

    for i, marker_id in enumerate(ids.flatten()):
        if marker_id != TARGET_ID:
            continue
        c = corners[i][0]
        cx = float(np.mean(c[:, 0]))               # pixel x centre
        w  = float(np.max(c[:, 0]) - np.min(c[:, 0]))  # apparent width in pixels

        frame_w = frame.shape[1]
        cx_norm = (cx / frame_w - 0.5) * 2.0       # -1 to +1

        # Rough distance: real marker = 0.15m wide
        # distance = (real_width * focal_length) / apparent_pixel_width
        # Focal length approx from FOV: f ≈ frame_w / (2 * tan(FOV/2))
        focal = frame_w / (2.0 * np.tan(np.deg2rad(CAMERA_FOV / 2)))
        dist  = (0.15 * focal) / w if w > 0 else None

        return True, cx_norm, dist

    return False, 0.0, None


async def dock(bridge, max_attempts=3):
    cap = cv2.VideoCapture(0)

    for attempt in range(1, max_attempts + 1):
        print(f"Docking attempt {attempt}/{max_attempts}")

        # Step 1: Rotate to find marker
        found = False
        for deg in range(0, 361, 15):
            ret, frame = cap.read()
            if not ret: continue
            found, cx_norm, dist = find_dock_marker(frame)
            if found: break
            await bridge.publish_velocity(linear_x=0, angular_z=0.3)
            await asyncio.sleep(0.3)

        await bridge.publish_velocity(0, 0)

        if not found:
            print("Marker not found")
            continue

        # Step 2: Align and approach
        while dist is None or dist > 0.05:
            ret, frame = cap.read()
            if not ret: break
            found, cx_norm, dist_now = find_dock_marker(frame)
            if not found: break
            if dist_now is not None:
                dist = dist_now

            # PD heading correction
            angular = -cx_norm * 0.8   # proportional
            linear  = 0.05 if dist and dist > 0.10 else 0.03

            await bridge.publish_velocity(linear_x=linear, angular_z=angular)
            await asyncio.sleep(0.1)

        await bridge.publish_velocity(0, 0)
        print(f"Docked (attempt {attempt})")
        cap.release()
        return True

    cap.release()
    return False
```

---

## Approach C — SLAM-Based Docking (Future, Requires LIDAR)

With a LIDAR add-on (YDLIDAR X2, ~€45), Boomy can:
- Build a map of the apartment (Nav2 + SLAM Toolbox)
- Label the dock as a named waypoint
- Navigate there autonomously from anywhere in the apartment
- Use the ArUco marker for final precision alignment

This is the full autonomous solution but requires:
- LIDAR hardware
- ROS 2 Nav2 configured and running
- Several hours of initial mapping
- Dock waypoint saved in the map

**This is the Phase E goal in the autonomy roadmap.**

---

## Charging Circuit Design

### Option 1: 5V USB charging (Li-ion cells via BMS — safe, simple)

```
Wall outlet → 5V 3A USB charger → dock pogo pins → Boomy charging port
                                                    (if Boomy has Li-ion cells)
```

For the Raspbot v2's LiPo pack (11.1V, 3S), a 5V input won't charge the main pack.
This option works only if a separate small Li-ion bank (for Pi 5) is used.

### Option 2: Direct LiPo charging (correct for Raspbot v2's 12.6V 3S pack)

```
Wall outlet → LiPo charger module (TP5100 or similar)
           → dock contacts → Boomy's battery JST connector (or XT60)
```

**TP5100 charger module** (~€5):
- Input: 12-24V DC
- Output: CV/CC for 1S-2S or with modified resistors for 3S (12.6V)
- Built-in balance charging support optional

**Safety:**
- Always use a charger with overcharge protection
- LiPo charging MUST be supervised initially — do not leave unattended until tested
- Consider a LiPo bag for the dock area

### Option 3: Wireless charging pad (QI — most elegant but lossy)

Qi wireless charging at 15W (11.1V @ 1.3A) is feasible at very short range.
- Transmitter coil embedded in dock floor
- Receiver coil on Boomy's underside
- Alignment needs to be ±5mm — requires very precise docking
- Not practical without SLAM-level docking precision

**Recommendation: start with Option 2 (TP5100 + pogo pins + V-rails). Cheap, works,
safe enough with a basic charger module. Upgrade to wireless later.**

---

## Dock Detection via Battery Voltage Rise

Once charging contacts are made, verify docking success by monitoring voltage:

```python
async def verify_charging(bridge, timeout=60):
    """Check if battery voltage is rising — confirms dock contact made."""
    tele = bridge.get_full_telemetry()
    v_start = tele.get("voltage")
    if v_start is None:
        return None   # no voltage data — can't verify

    await asyncio.sleep(30)
    tele = bridge.get_full_telemetry()
    v_now = tele.get("voltage")

    if v_now and v_now > v_start + 0.1:   # voltage rising = charging
        return True
    return False
```

---

## Implementation Timeline

| Phase | What | When |
|---|---|---|
| A | Buy pogo pins + print V-rails, wire TP5100 charger | 1 weekend |
| A | Dead-reckoning dock approach (fixed sequence) | 2-3 hours coding |
| B | Print ArUco marker, implement visual servo loop | 1 day |
| B | Integrate into watchdog low-battery path | 2-3 hours |
| B | Test and tune alignment PD controller | 1 afternoon |
| C | Buy LIDAR, configure Nav2 + SLAM | 2-3 days |
| C | Map apartment, save dock waypoint | 1 afternoon |

---

## Bill of Materials (Approach A + B)

| Item | Price (est.) |
|---|---|
| Spring pogo pin connectors (2×) | €6 |
| TP5100 LiPo charger module | €5 |
| V-rail guide (aluminium extrusion, 30cm × 2) | €8 |
| 12V DC power supply 3A | €12 |
| ArUco marker (print at home) | €0 |
| Wiring, JST connectors, heat shrink | €5 |
| **Total** | **~€36** |

For SLAM (Approach C), add:
| YDLIDAR X2 | €45 |
| Mounting bracket (3D print) | €2 |
| **Additional** | **~€47** |

---

## Integration with yahboom-mcp

The dock operation becomes a standard yahboom-mcp operation:

```python
# src/yahboom_mcp/operations/dock.py
async def execute(operation="dock", ...):
    if operation == "dock":
        return await dock_approach(bridge, ssh)
    elif operation == "undock":
        return await undock(bridge)
    elif operation == "check_charging":
        return await verify_charging(bridge)
```

MCP tool callable from Claude/Cursor:
```
yahboom(operation="dock")     → drives to dock, aligns, charges
yahboom(operation="undock")   → backs out, resumes previous mode
```

REST endpoint for webapp:
```
POST /api/v1/dock/start
POST /api/v1/dock/abort
GET  /api/v1/dock/status
```

---

## References

- ArUco marker generation: https://chev.me/arucogen/ (free, print as PDF)
- TP5100 datasheet: standard LiPo charger chip, widely available
- ROS 2 Nav2: https://docs.nav2.org/
- SLAM Toolbox: https://github.com/SteveMacenski/slam_toolbox
- Yahboom MS200 LIDAR: https://www.yahboom.net/study/MS200
