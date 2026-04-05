import os
from yahboom_mcp.core.ssh_bridge import SSHBridge


def discover_camera_v3():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] ULTIMATE CAMERA DISCOVERY v3 on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search for everything in the root workspace
    print("[*] Searching /root/yahboomcar_ws/ for camera launch files...")
    cmd = (
        "docker exec yahboom_ros2 find /root/yahboomcar_ws/ -name '*camera*.launch.py'"
    )
    out, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("CAM-RELATED LAUNCH FILES:")
    print(out)
    print("-" * 40)

    # 2. Check for yahboomcar_visual package
    print("[*] Checking for yahboomcar_visual package...")
    cmd = (
        "docker exec yahboom_ros2 ls /root/yahboomcar_ws/src/yahboomcar_visual/launch/"
    )
    out, _, _ = ssh.execute(cmd)
    print("VISUAL LAUNCH FILES:")
    print(out)

    # 3. Check for specific Pi 5 camera driver
    print("[*] Checking for libcamera-vid or v4l2_camera...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 pkg list | grep camera'"
    out, _, _ = ssh.execute(cmd)
    print("CAMERA PACKAGES:")
    print(out)


if __name__ == "__main__":
    discover_camera_v3()
