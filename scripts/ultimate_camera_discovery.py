import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def discover_camera():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] SEARCHING FOR CAMERA DRIVER on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search for camera nodes inside ROS 2
    # We'll use a more robust way to list all active nodes and their topics
    print("[*] Performing ROS 2 Node/Topic Audit...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 node list && ros2 topic list'"
    out, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("ROS 2 AUDIT:")
    print(out)
    print("-" * 40)

    # 2. Check for host ports (Yahboom often uses 8080/MJPEG)
    print("[*] Checking host-side network ports...")
    cmd = "netstat -tulnp"
    out, _, _ = ssh.execute(cmd)
    print("PORTS:")
    print(out)

    # 3. Check for specific Yahboom camera processes on host
    print("[*] Checking host-side processes for 'camera'...")
    cmd = "ps aux | grep -i camera | grep -v grep"
    out, _, _ = ssh.execute(cmd)
    print("HOST PROCESSES:")
    print(out)

if __name__ == "__main__":
    discover_camera()
