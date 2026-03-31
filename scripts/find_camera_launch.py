import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def find_camera_launch():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] SEARCHING FOR CAMERA LAUNCH on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search for all launch files in the container
    print("[*] Searching /opt/ros/humble/share for camera launch files...")
    cmd = "docker exec yahboom_ros2 find /opt/ros/humble/share -name '*camera*.launch.py'"
    out, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("CAM-RELATED LAUNCH FILES:")
    print(out)
    print("-" * 40)

    # 2. Check for port 8080 (often used for MJPEG streaming by Yahboom)
    print("[*] Checking for MJPEG streaming ports...")
    cmd = "netstat -tulnp | grep 8080"
    out, _, _ = ssh.execute(cmd)
    print(f"PORT 8080: {out}")

if __name__ == "__main__":
    find_camera_launch()
