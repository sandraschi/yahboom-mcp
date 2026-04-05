# Yahboom Raspbot v2: Telemetry Restoration Handoff (v1.0.0)
**Timestamp**: 2026-04-01  
**Status**: DEGRADED (Kinematics Active / Telemetry Null)  
**Platform**: Windows 11 Pro ↔ Raspberry Pi 5 (ROS 2 Humble / Docker)

---

## I. Current Capabilities (What Works)
- **Kinematics (Wheels)**: `cmd_vel` is fully functional. The robot responds to motion commands via the dashboard/API.
- **Connectivity**: SSH bridge and Docker exec bridge are stable. Backend (10892) and Frontend (10893) are operational.
- **Container Registry**: The `yahboom_ros2` container is running the March 2026 Humble image.
- **I2C Heartbeat**: `i2cdetect -y 1` confirms the MCU is active at address **0x2b**.
- **Camera Device**: `/dev/video0` exists inside the container and is successfully mapped.

## II. Known Problems (The Sensory Blackout)
- **Topic Existence vs. Data Flow**: `ros2 topic list` shows `/imu/data` and `/battery_state` are active. However, `ros2 topic echo` often returns empty or null values.
- **Protocol Desync**: The underlying `Rosmaster_Lib.py` uses a complex checksum/UART-over-I2C protocol. My patched driver (`Mcnamu_driver.py`) attempts to use the library's `create_receive_threading()`, but the internal parser is not satisfying the ROS 2 message objects.
- **Bridge Mapping (UI Issues)**: The WebApp (10893) seems disconnected from the backend (10892) for everything except the wheels. This is because the backend bridge is currently returning `null` for all sensory data, causing the UI to enter a "null-state."
- **Camera, PTZ, Lightstrip, Speech**: These all show a "Hardware Unreachable" or "Null-state."
    - **Camera**: No `/image_raw/compressed` stream despite device mapping.
    - **PTZ/Lightstrip**: These are MCU-controlled. The current driver lacks the packet structure to talk to these registers (0x0c, 0x09).
    - **Speech**: Missing sound device (`/dev/snd`) mapping in Docker and no active `speech_node`.
- **I2C Reliability**: `dmesg` says I2C is "registered in interrupt mode," but if the cabling is oxidized or loose, the packet loss will be 100% despite the device address being visible.

## III. Remaining Tasks (What Has to be Done ASAP)
1. **Sensory Protocol Patch**: Finalize the bitwise packet parsing in `Mcnamu_driver.py` using the `Rosmaster_Lib` logic as the source of truth.
2. **Vision Restoration**: Manually initialize the `usb_cam` node inside the container (or equivalent Humble camera node) and verify the `/image_raw/compressed` topic.
3. **Hardware Shield Re-mapping**: 
    - **Lightstrip**: Restore the legacy register calls (worked yesterday because a different driver was likely active).
    - **Speech**: Map `/dev/snd` into the `yahboom_ros2` container and start the voice node.
4. **Physical Cable Check**: Re-seat the I2C and PTZ servo cables at the MCU junction to rule out connection failure.
5. **UI-Backend Hardening**: Update `Dashboard.tsx` to handle `null` telemetry gracefully and alert if the `rosbridge` connection is flapping.

---

## IV. Technical Reference
- **Robot IP**: `192.168.0.250`
- **Driver Path**: `/root/yahboomcar_ws/install/yahboomcar_bringup/lib/python3.10/site-packages/yahboomcar_bringup/Mcnamu_driver.py`
- **MCU Registry**: `0x2b` (Device Address)
- **Backend Port**: `10892`
- **Frontend Port**: `10893`
