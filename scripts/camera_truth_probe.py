import os

from yahboom_mcp.core.ssh_bridge import SSHBridge


def probe_camera_truth():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] STARTING HARDWARE-VERIFIED CAMERA PROBE on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search for launch files in the container (System-wide)
    print("[*] Finding all camera-related launch files...")
    cmd = "docker exec yahboom_ros2 find / -name '*camera*.launch.py' 2>/dev/null"
    out_launch, _, _ = ssh.execute(cmd)
    print("-" * 50)
    print(f"LAUNCH_FILES:\n{out_launch}")

    # 2. Check current ROS 2 nodes for image publishers
    print("[*] Identifying current image publishers...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic info /image_raw/compressed -v'"
    out_topic, _, _ = ssh.execute(cmd)
    print("-" * 50)
    print(f"TOPIC_INFO:\n{out_topic}")

    # 3. Check for the official Yahboom video process on host
    print("[*] Checking host-side processes for camera/streaming...")
    cmd = "ps aux | grep -E 'camera|mjpg|stream|picamera' | grep -v grep"
    out_proc, _, _ = ssh.execute(cmd)
    print("-" * 50)
    print(f"HOST_PROCESSES:\n{out_proc}")


if __name__ == "__main__":
    probe_camera_truth()
