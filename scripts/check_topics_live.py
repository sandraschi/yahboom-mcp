import asyncio
import logging
import os

from yahboom_mcp.core.ros2_bridge import ROS2Bridge
from yahboom_mcp.core.ssh_bridge import SSHBridge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diag")

async def main():
    host = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    fallback = os.environ.get("YAHBOOM_FALLBACK_IP", "192.168.1.11")

    logger.info(f"Targeting Robot: {host} (Fallback: {fallback})")

    ssh = SSHBridge(host)
    bridge = ROS2Bridge(host=host, port=9090, fallback_host=fallback)
    bridge.ssh = ssh

    connected = await bridge.connect(timeout=10.0)
    if not connected:
        logger.error("Failed to connect to ROS 2 bridge.")
        return

    logger.info(f"Connected to {bridge.host}!")

    # Check nodes
    out, _, _ = ssh.execute("docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 node list'")
    logger.info(f"Active Nodes:\n{out}")

    # Check topics
    out, _, _ = ssh.execute("docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic list'")
    logger.info(f"Active Topics:\n{out}")

    await bridge.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
