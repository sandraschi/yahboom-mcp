# Yahboom Robots Expert Skill

Use this skill when you need **domain expertise** on Yahboom Raspbot v2 hardware, ROS 2 setup, mecanum kinematics, or integration architecture—beyond routine operator procedures (see **yahboom-operator.md** for day-to-day tool use).

---

## Hardware

- **Platform**: Yahboom Raspbot v2. Main compute: **Raspberry Pi 5** (ARM64). OS: Ubuntu 24.04 + **ROS 2 Humble**.
- **Drive**: Four **mecanum wheels** (32.5 mm radius). Layout: front_left, front_right, back_left, back_right; axles parallel to robot X (forward). Enables holonomic motion: forward/back, strafe left/right, rotate in place.
- **Sensors**: 2D LIDAR (laser_link), camera (camera_link); IMU and wheel encoders for odometry.
- **Power**: Onboard battery; monitor via `read_battery` / telemetry. Low battery (< 20%) limits recommended motion duration.

---

## Frames and URDF

- **base_footprint**: Ground plane (z = 0).
- **base_link**: Body frame; z offset = +wheel_radius (0.0325 m) above ground. Wheel joints at z = -wheel_radius relative to base_link.
- **Wheel positions** (joint xyz from URDF, in metres): x = ±0.08, y = ±0.0745 (half track), z = -0.0325. Left/right sign and spin direction matter for mecanum (front_left and back_left spin one way; front_right and back_right opposite for straight drive).
- **LIDAR**: Offset (0, 0, 0.0825) from base_link; mesh rpy often -π/2 0 0 for horizontal scan plane.
- **Camera**: Offset (0.105, 0, 0.05); pitch ~-0.5 rad typical.

---

## ROS 2 and Bridge

- **ROS 2**: Humble on Ubuntu 24.04. Topics/services follow ROS 2 naming (e.g. cmd_vel, odom, scan, image).
- **MCP ↔ Robot**: yahboom-mcp server talks to a **REST bridge** (or direct ROS 2 node) on the robot network. Robot IP and bridge port configurable (env or settings). Health check confirms bridge and battery before motion.
- **Dual mode**: Server can run `--mode stdio` (MCP only) or `--mode dual --port 10792` (REST API + MCP). Dashboard (Vite) uses REST on 10792; frontend dev server on 10793.

---

## Mecanum and Motion

- **Operations**: forward, backward, turn_left, turn_right, strafe_left, strafe_right, stop. Speed/duration via param1 (and param2 where defined).
- **Kinematics**: Mecanum rollers at 45°; combined wheel velocities yield body linear and angular velocity. Odometry from encoders + IMU; heading from IMU.
- **Trajectory recording**: start_recording → run motions → stop_recording(basename). List with list_trajectories. Useful for replay or tuning.

---

## Integration and Fleet

- **Federated fleet**: Yahboom-MCP is one node; others include Dreame-MCP (mapping/sweeping), Virtual-Robotics-MCP (simulation), central hub (orchestration). Cross-MCP workflows possible via same client (e.g. Cursor) or hub.
- **3D viz**: Dashboard loads real STL meshes from URDF (base_link, wheels, LIDAR, camera). Wheels vertical (disc in YZ), axle along X; spin around axle for correct motion cue.

---

## When to Use This Skill vs Operator Skill

| Use **yahboom-robots-expert** when | Use **yahboom-operator** when |
|------------------------------------|------------------------------|
| Explaining hardware, frames, or kinematics | Running tools and following workflows |
| Debugging connection, URDF, or frame issues | Choosing which tool/prompt to call |
| Designing integrations or fleet behaviour | Doing health_check → motion → recording |
| Answering “how does the robot work?” | Answering “how do I make it patrol?” |

---

## Quick References

- **Tools**: yahboom, yahboom_help, yahboom_agentic_workflow (see operator skill for full list).
- **Prompts**: yahboom_quick_start(robot_ip), yahboom_patrol(duration_seconds), yahboom_diagnostics().
- **Scripts**: `scripts/check_health.py` (REST health/telemetry), `scripts/run_patrol_square.ps1` (run server + dashboard hint).
- **Docs**: `docs/CONNECTIVITY.md`, `docs/architecture.md`, `docs/fleet_overview.md`, `docs/PI_LESS_SETUP.md`.
