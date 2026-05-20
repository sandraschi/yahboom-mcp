"""Skill: yahboom-diagnostic-triage — layered stack health triage."""


def yahboom_diagnostic_triage() -> str:
    """Systematic diagnostic triage: bottom-up from TCP to ROS graph."""
    return """Diagnose the Yahboom Raspbot v2 connection stack bottom-up.

## Layer 1: TCP reachability
Check GET /api/v1/health → robot_connection.ip and stack.goliath_to_robot.
If TCP fails: verify YAHBOOM_IP, Pi power, Wi-Fi/Ethernet link.

## Layer 2: SSH session
Check GET /api/v1/health → robot_connection.ssh.
If disconnected: check YAHBOOM_PASSWORD, Pi SSH daemon (port 22).

## Layer 3: Docker engine on Pi
Check GET /api/v1/health → stack.docker_engine → systemd_active.
If inactive: `sudo systemctl start docker` on Pi (requires SSH).

## Layer 4: ROS container
Check GET /api/v1/health → stack.ros_container → lifecycle.phase.
- "running" → container is up.
- "restart_loop" → check docker logs; OOM or missing USB device.
- "ran_then_stopped" → `docker start yahboom_ros2_final`.
- "not_found" → wrong YAHBOOM_ROS2_CONTAINER name.
Follow remediation_steps from the response.

## Layer 5: ROS graph inside container
Check GET /api/v1/health → stack.ros_graph_in_container → status.
Use ros_topic_list() to see active topics and ros_node_info(node_name) for details.

## Layer 6: rosbridge WebSocket
Check GET /api/v1/health → robot_connection.ros.
If disconnected: ros_resync() first, then ros_restart_bringup() if needed.

## Layer 7: cmd_vel topic
Check GET /api/v1/health → robot_connection.cmd_vel_ready.
If false: wait 5 seconds and re-check. Use resync if still missing.

## Reporting
After triage, report:
- Which layer failed (1-7).
- Recommended fix (from remediation_steps if available).
- Whether motion/sensors/voice/video are expected to work with current state."""
