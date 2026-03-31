# Boomy "Benny-Safe" Avoidance Strategy

Boomy's intelligence substrate incorporates a reactive state machine for safe, autonomous navigation in dynamic environments (e.g., apartments with canine companions like Benny).

## 🧠 Avoidance State Machine

The `MissionManager` (in `missions.py`) polls sensory data at 10Hz during all autonomous movement phases.

### 🛡️ 1. Cliff Guard Dominance (Priority 0)
- **Sensor**: Line Follower (Infrared Array)
- **Logic**: If all sensors detect `[0, 0, 0]` (Void/White), Boomy is at a table edge or cliff.
- **Action**: Immediate motor halt (`cmd_vel: 0, 0`). Mission is aborted with `Emergency Halt` status.

### 🛡️ 2. Benny-Safe Reactive Avoidance (Priority 1)
- **Sensor**: Ultrasound (Sonar)
- **Threshold**: Obstacle detected within **20cm**.
- **Action**: **Tangent-Pivot Maneuver**
    1.  **Stop**: All motors cease.
    2.  **Alert**: Pulse Red LEDs and play "Pardon me!" voice prompt.
    3.  **Pivot**: 45° rotation away from the obstacle's likely center.
    4.  **Bypass**: Forward movement for 1.5s to clear the tangent.
    5.  **Resume**: Pivot -45° to original heading and continue patrol leg.

### 🛡️ 3. Physical Override (Priority 2)
- **Sensor**: KEY Button (RPi 5 GPIO 18)
- **Action**: Pressing the button immediately silences all active alarms (Morning Briefing/Snooze) and aborts the mission.

## 🚀 Mission Integration

The avoidance loop is currently integrated into the **Patrol Car** mission:

```python
while movement_time < 2.0:
    await self._check_critical_safety() # Cliff/Button
    if await self._sense_obstacle():   # Sonar < 20cm
        await self._avoid_obstacle()   # Tangent Maneuver
        self._add_log("Resuming patrol...")
```

> [!IMPORTANT]
> **Benny Alert**: This system is designed for "biological safe-distance." It provides a 20cm buffer, ensuring Boomy provides a polite and non-threatening response to pets.
