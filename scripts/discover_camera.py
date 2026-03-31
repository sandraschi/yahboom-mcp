import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def discover_camera():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Checking for /dev/video* devices...")
    v_out, _, _ = ssh.execute("ls /dev/video*")
    print(f"VIDEO_DEVS: {v_out}")

    print("[*] Checking for ROS 2 camera topics...")
    # Source ROS 2 and list topics
    t_out, _, _ = ssh.execute("bash -c 'source /opt/ros/humble/setup.bash && ros2 topic list'")
    if t_out:
        topics = [t for t in t_out.strip().split('\n') if 'image' in t.lower() or 'camera' in t.lower()]
        print(f"[*] Found {len(topics)} potential camera topics:")
        for t in topics:
            print(f"  - {t}")
    else:
        print("[FAIL] No image topics found. Is the camera node running?")

if __name__ == "__main__":
    discover_camera()
