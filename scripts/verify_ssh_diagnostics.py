import asyncio
import os
from yahboom_mcp.core.ssh_bridge import SSHBridge


async def verify_robot_ssh():
    host = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    user = os.environ.get("YAHBOOM_USER", "pi")
    pw = os.environ.get("YAHBOOM_PASSWORD", "yahboom")

    print(f"Connecting to {host} as {user}...")
    ssh = SSHBridge(host=host, user=user, password=pw)
    if not ssh.connect():
        print("SSH Connection Failed!")
        return

    print("Checking ROS 2 nodes in container...")
    # Use the fixed command from my implementation
    cmd = 'docker exec yahboom_ros2 bash -c "source /opt/ros/humble/setup.bash && ros2 node list"'
    out, err, code = ssh.execute(cmd)

    print(f"Nodes (Exit Code {code}):")
    print(out if out else "[None]")
    if err:
        print(f"Errors: {err}")

    print("\nChecking for port 9090 (Rosbridge):")
    out, err, code = ssh.execute("ss -tlnp | grep 9090")
    print(out if out else "Port 9090 is NOT listening")

    ssh.close()


if __name__ == "__main__":
    asyncio.run(verify_robot_ssh())
