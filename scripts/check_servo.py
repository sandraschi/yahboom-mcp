import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from yahboom_mcp.core.ssh_bridge import SSHBridge


async def check_servo():
    host = "192.168.1.11"
    print(f"Checking servo on {host}...")

    ssh = SSHBridge(host)
    ssh.connect()

    # 1. Check topic info
    print("\n--- Topic Info ---")
    out, _, _ = ssh.execute("docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic info /servo'")
    print(out)

    # 2. Check interface definition
    print("\n--- Interface Definition ---")
    out, _, _ = ssh.execute("docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 interface show yahboomcar_msgs/msg/ServoControl'")
    print(out)

if __name__ == "__main__":
    asyncio.run(check_servo())
