# Boomy Racing: Living Room Cup (Vision & Roadmap)

This document formalizes the future vision for competitive, multi-robot racing within the Boomy ecosystem.

## 🏎️ Fleet Architecture: The Dual-Racer Grid

- **Boomy #1 (High-Performance)**: Raspberry Pi 5 + 3.5" Dashboard. Serves as the primary racer and AI reference node.
- **Boomy #2 (Lightweight)**: Raspberry Pi 3 B+. Optimized for lightweight ROS 2 Humble control, proving that even legacy hardware belongs on the track.

## 🎮 Controller-Based Steering

Integration of physical gamepads (Xbox, PS5, or generic USB/Bluetooth controllers) to provide low-latency, analog steering.
- **Substrate**: Use of `pygame.joystick` or `linux-evdev` within the MCP server.
- **Mapping**: Left Analog (Linear X), Right Analog (Angular Z), Bumpers (Strafe).

## 🏆 Competitive Modes

1.  **Human vs. Human**: Real-time teleoperation battle with FPV headsets.
2.  **Human vs. AI**: A human racer competes against a Boomy running an autonomous "Tangent-Pivot" racing algorithm.
3.  **AI vs. AI**: Pure autonomous competition; Boomy agents must navigate a track while avoiding each other (and Benny).

## 💥 The "Shazbat!" Protocol

Reactive interaction logic for on-track collisions.
- **Detection**: Triangulation between Ultrasound (proximity) and IMU Accelerometer (impact G-force).
- **Reaction**: If `impact > threshold`, stop motors and broadcast: `"Shazbat! Watch the paint, fellow robot!"`
- **LED Pulse**: Immediate flash of collision-white across the lightstrip.

## 🕶️ FPV (First Person View)

Low-latency MJPEG/WebRTC streaming from the robot's camera directly to a headset.
- **Integration**: `VideoBridge` expansion to support VR-friendly aspect ratios and HUD overlays (Battery, Lap Time, Obstacle Radar).

---

> [!TIP]
> **Benny as Safety Marshal**: Benny acts as the biological safety officer. The "Benny-Safe" avoidance logic will be tuned to ensure racers divert around the dog even during a heated lap!
