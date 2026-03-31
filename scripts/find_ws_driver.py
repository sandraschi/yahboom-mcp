import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def find_ws_driver():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] DEEP SEARCH FOR CAMERA DRIVER on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search everything in pi's home
    print("[*] Searching /home/pi/ for camera-related files...")
    cmd = "docker exec yahboom_ros2 find /home/pi/ -name '*camera*' | grep -v 'venv' | head -n 20"
    out, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("MATCHING FILES:")
    print(out)
    print("-" * 40)

    # 2. List ROS 2 packages
    print("[*] Listing installed ROS 2 packages...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 pkg list | grep cam'"
    out, _, _ = ssh.execute(cmd)
    print("INSTALLED CAMERA PACKAGES:")
    print(out)
    
    # 3. Check for specific Yahboom bringup
    print("[*] Checking for yahboomcar_bringup...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 pkg list | grep bringup'"
    out, _, _ = ssh.execute(cmd)
    print("BRINGUP PACKAGES:")
    print(out)

if __name__ == "__main__":
    find_ws_driver()
