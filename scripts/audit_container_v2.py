import os

from yahboom_mcp.core.ssh_bridge import SSHBridge


def audit_container_v2():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Auditing ROS 2 Packages inside yahboom_ros2 container...")
    # Source setup.bash inside container and list packages
    p_out, _, _ = ssh.execute(
        "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 pkg list | grep -Ei \"camera|v4l|usb\"'"
    )
    print(f"CONTAINER_PACKAGES:\n{p_out}")

    print("[*] Searching for ANY launch files in container...")
    # Deep search in /
    l_out, _, _ = ssh.execute(
        "docker exec yahboom_ros2 find / -name '*.launch.py' 2>/dev/null | grep -i camera"
    )
    if l_out:
        print(f"[*] Found launch files in container:\n{l_out}")
    else:
        print("[FAIL] No camera launch files found in the entire container.")

    print("[*] Checking for /dev/video0 inside the container...")
    v_out, _, _ = ssh.execute("docker exec yahboom_ros2 ls /dev/video0")
    print(f"CONTAINER_VIDEO_DEVS: {v_out}")


if __name__ == "__main__":
    audit_container_v2()
