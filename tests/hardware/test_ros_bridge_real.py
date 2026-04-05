import pytest
import os
from yahboom_mcp.core.ros2_bridge import ROS2Bridge
from yahboom_mcp.core.ssh_bridge import SSHBridge


@pytest.mark.needs_robot
@pytest.mark.asyncio
async def test_real_ros_bridge_connection():
    """Live hardware test: verifies the bridge can handshake with the Pi 5."""
    target_ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    bridge = ROS2Bridge(host=target_ip, port=9090)

    # Attempt live connect
    connected = await bridge.connect(timeout=10.0)
    if not connected:
        pytest.skip(f"Robot @ {target_ip} not reachable. Skipping hardware test.")

    try:
        topics = await bridge.get_all_topics()
        assert len(topics) > 0
        # Check for mission-critical topics
        topic_names = [t[0] for t in topics]
        assert "/cmd_vel" in topic_names
        assert "/scan" in topic_names
    finally:
        await bridge.disconnect()


@pytest.mark.needs_robot
def test_real_ssh_recovery_command():
    """Live hardware test: verifies the SSH recovery command formatting on the Pi 5."""
    target_ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(target_ip)

    if not ssh.connect():
        pytest.skip(f"SSH @ {target_ip} not reachable. Skipping hardware test.")

    try:
        # Check that the critical setup files exist
        out, err, code = ssh.execute("ls /home/pi/yahboomcar_ws/install/setup.bash")
        assert code == 0, f"ROS workspace not found on Pi: {err}"

        # Verify ROS nodes can be listed (even if none are running)
        out, err, code = ssh.execute(
            "source /opt/ros/foxy/setup.bash && ros2 node list"
        )
        assert code == 0, f"ROS 2 environment issue on Pi: {err}"
    finally:
        ssh.disconnect()
