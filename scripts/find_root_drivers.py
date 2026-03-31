import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def find_root_drivers():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] DEEP ROOT SEARCH on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search the root workspace in the container
    print("[*] Searching /root/yahboomcar_ws/ for camera launch files...")
    cmd = "docker exec yahboom_ros2 find /root/yahboomcar_ws/ -name '*camera*.launch.py'"
    out, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("MATCHING LAUNCH FILES:")
    print(out)
    print("-" * 40)

    # 2. Check for yahboom_camera package
    print("[*] Checking for yahboom_camera package...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 pkg list | grep camera'"
    out, _, _ = ssh.execute(cmd)
    print("CAMERA PACKAGES:")
    print(out)

if __name__ == "__main__":
    find_root_drivers()
