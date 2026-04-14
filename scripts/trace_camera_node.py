import os

from yahboom_mcp.core.ssh_bridge import SSHBridge


def trace_camera_node():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Searching for 'usb_cam' or 'camera' packages...")
    # List ROS 2 packages and grep for camera
    p_out, _, _ = ssh.execute(
        "bash -c 'source /opt/ros/humble/setup.bash && ros2 pkg list | grep -i camera'"
    )
    print(f"PACKAGES:\n{p_out}")

    print("[*] Searching for camera launch files in /home/pi/...")
    # Broad search for launch files
    l_out, _, _ = ssh.execute("find /home/pi/ -name '*camera*.launch.py' 2>/dev/null")
    if l_out:
        print(f"[*] Found launch files:\n{l_out}")
    else:
        print("[FAIL] No camera launch files found in /home/pi/.")


if __name__ == "__main__":
    trace_camera_node()
