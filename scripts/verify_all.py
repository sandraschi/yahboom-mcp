import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from yahboom_mcp.core.ssh_bridge import SSHBridge


async def verify_system():
    host = "192.168.1.11"
    print(f"Verifying system on {host}...")

    ssh = SSHBridge(host)
    ssh.connect()

    # 1. Check Camera Frequency
    print("\n--- Camera Frequency (/image_raw/compressed) ---")
    # Timeout after 3s to not hang if topic is dead
    out, _, _ = ssh.execute("docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && timeout 3s ros2 topic hz /image_raw/compressed'")
    print(out)

    # 2. Check Servo Publisher
    print("\n--- Servo Topic Info ---")
    out, _, _ = ssh.execute("docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic info /servo'")
    print(out)

if __name__ == "__main__":
    asyncio.run(verify_system())
