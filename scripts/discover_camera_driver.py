import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def discover_camera_driver():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] DISCOVERING CAMERA DRIVER on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search for all .launch.py files in the root workspace
    print("[*] Searching /root/yahboomcar_ws/ for camera drivers...")
    cmd = "docker exec yahboom_ros2 find /root/yahboomcar_ws/ -name '*.launch.py' | grep -E 'camera|usb|image|cam'"
    out, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("CAM-RELATED LAUNCH FILES:")
    print(out)
    print("-" * 40)

    # 2. Check for yahboomcar package source
    print("[*] Checking for yahboomcar packages in src...")
    cmd = "docker exec yahboom_ros2 ls /root/yahboomcar_ws/src/"
    out, _, _ = ssh.execute(cmd)
    print("SRC PACKAGES:")
    print(out)

    # 3. Check for any running camera nodes
    print("[*] Checking for active camera nodes in ROS 2...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 node list'"
    out, _, _ = ssh.execute(cmd)
    print("ACTIVE NODES:")
    print(out)

if __name__ == "__main__":
    discover_camera_driver()
