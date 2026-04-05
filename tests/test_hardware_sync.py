import os
import asyncio
import logging
import sys

# Add src to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from yahboom_mcp.core.ssh_bridge import SSHBridge
from yahboom_mcp.core.ros2_bridge import ROS2Bridge
from yahboom_mcp.state import _state
from yahboom_mcp.operations import lightstrip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hardware-test")


async def test_sync():
    robot_ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    logger.info(f"--- STARTING HARDWARE SYNC TEST (IP: {robot_ip}) ---")

    # 1. SSH Test
    ssh = SSHBridge(robot_ip)
    if ssh.connect():
        logger.info("[SUCCESS] SSH Connected.")
        out, err, code = ssh.execute("ros2 topic list")
        if code == 0:
            logger.info(f"[SUCCESS] Robot Perspective Topics:\n{out}")
        else:
            logger.error(f"[FAILURE] Could not list topics via SSH: {err}")
    else:
        logger.error("[FAILURE] SSH Connection failed.")
        return

    # 2. Bridge sync
    bridge = ROS2Bridge(host=robot_ip)
    _state["bridge"] = bridge
    _state["ssh"] = ssh

    logger.info("Connecting Bridge (Wait 15s)...")
    if await bridge.connect(timeout_sec=15.0):
        logger.info("[SUCCESS] ROS 2 Bridge connected.")
        # Discovery should have happened. Let's check what it mapped.
        logger.info(
            f"Mapped Topics: IMU={getattr(bridge, 'imu_listener', None).name if getattr(bridge, 'imu_listener', None) else 'None'}"
        )
        logger.info(
            f"Mapped Topics: RGB={getattr(bridge, 'rgblight_topic', None).name if getattr(bridge, 'rgblight_topic', None) else 'None'}"
        )

        # 3. Lightstrip Test
        logger.info("Running Lightstrip Test (RED)...")
        res = await lightstrip.execute(operation="set", param1=255, param2=0, param3=0)
        logger.info(f"Lightstrip Result: {res}")

        await asyncio.sleep(2)

        logger.info("Running Lightstrip Test (OFF)...")
        res = await lightstrip.execute(operation="off")
        logger.info(f"Lightstrip Result: {res}")
    else:
        logger.error("[FAILURE] ROS 2 Bridge failed to connect.")

    ssh.close()
    logger.info("--- TEST COMPLETE ---")


if __name__ == "__main__":
    asyncio.run(test_sync())
