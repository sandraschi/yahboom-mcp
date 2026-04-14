import os

from yahboom_mcp.core.ssh_bridge import SSHBridge


def final_camera_probe():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] FINAL HARDWARE-VERIFIED PROBE on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Identify USB devices (privileged)
    print("[*] Identifying USB devices...")
    cmd = "lsusb"
    out, _, _ = ssh.execute(cmd)
    print("-" * 50)
    print(f"LSUSB:\n{out}")

    # 2. Identify Video Devices
    print("[*] Identifying V4L2 video devices...")
    cmd = "ls -l /dev/video*"
    out, _, _ = ssh.execute(cmd)
    print("-" * 50)
    print(f"VIDEO_DEVICES:\n{out}")

    # 3. Check official ROS 2 camera node status
    print("[*] Checking ROS 2 camera node status...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 node list | grep cam'"
    out, _, _ = ssh.execute(cmd)
    print("-" * 50)
    print(f"CAM_NODES:\n{out}")

    # 4. Check for publishers on image topics
    print("[*] Checking for publishers on /image_raw/compressed...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic info /image_raw/compressed'"
    out, _, _ = ssh.execute(cmd)
    print("-" * 50)
    print(f"TOPIC_INFO:\n{out}")


if __name__ == "__main__":
    final_camera_probe()
