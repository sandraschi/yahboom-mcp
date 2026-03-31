import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def discover_cam():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] ULTIMATE CAMERA DISCOVERY on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search for EVERYTHING in the container related to camera
    print("[*] Searching entire container for camera/image files...")
    cmd = "docker exec yahboom_ros2 find / -name '*camera*' 2>/dev/null | grep -v 'usr/share' | head -n 50"
    out, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("FILES FOUND IN CONTAINER:")
    print(out)
    print("-" * 40)

    # 2. Check for port 8080 or 8081 (common MJPEG ports)
    print("[*] Checking for MJPEG streaming ports...")
    cmd = "netstat -tulnp | grep -E '8080|8081|5000'"
    out, _, _ = ssh.execute(cmd)
    print(f"ACTIVE STREAMS: {out}")

    # 3. Check for specific Yahboom visual nodes
    print("[*] Auditing ROS 2 topics with types again...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic list -t'"
    out, _, _ = ssh.execute(cmd)
    print("TOPIC LIST:")
    print(out)

if __name__ == "__main__":
    discover_cam()
