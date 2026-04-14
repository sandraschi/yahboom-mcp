import os
import time

from yahboom_mcp.core.ssh_bridge import SSHBridge


def debug_camera_logs():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] STARTING CAM DEBUG on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Kill any existing nodes
    print("[*] Killing existing camera nodes...")
    ssh.execute("docker exec yahboom_ros2 pkill -f usb_cam || true")
    time.sleep(2)

    # 2. Run the command and capture logs (Synchronous)
    print("[*] Launching camera node with 720p parameters...")
    launch_cmd = (
        "ros2 run usb_cam usb_cam_node_exe "
        "--ros-args "
        "-p video_device:=/dev/video0 "
        "-p image_width:=1280 "
        "-p image_height:=720 "
        "-p pixel_format:=yuyv "
        "-p io_method:=mmap "
        "-p camera_name:=raspbot_cam"
    )
    # We use a timeout to capture first few seconds of logs
    docker_cmd = f"docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && timeout 5s {launch_cmd}'"

    out, err, _ = ssh.execute(docker_cmd)
    print("-" * 50)
    print(f"OUTPUT:\n{out}")
    print(f"ERRORS:\n{err}")


if __name__ == "__main__":
    debug_camera_logs()
