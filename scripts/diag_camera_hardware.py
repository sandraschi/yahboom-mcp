import os

from yahboom_mcp.core.ssh_bridge import SSHBridge


def diag_camera():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] DIAGNOSTIC: Camera Subsystem on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Check Camera Node Info
    print("[*] Checking ROS 2 node info /usb_cam...")
    out, _, _ = ssh.execute(
        "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 node info /usb_cam'"
    )
    print("-" * 40)
    print(out)
    print("-" * 40)

    # 2. Check Topic List with Types
    print("[*] Checking topic list with types...")
    out, _, _ = ssh.execute(
        "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic list -t'"
    )
    print("-" * 40)
    print(out)
    print("-" * 40)

    # 3. Echo compressed topic data (just one message)
    print("[*] Echoing /image_raw/compressed (timeout 5s)...")
    out, _, _ = ssh.execute(
        "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && timeout 5 ros2 topic echo /image_raw/compressed --count 1'"
    )
    if out.strip():
        print(
            f"[SUCCESS] Received data from /image_raw/compressed (size: {len(out)} chars)"
        )
    else:
        print(
            "[FAIL] No data received from /image_raw/compressed. Node might be stalled."
        )

    # 4. Check for any /camera/ topics
    print("[*] Checking for /camera/* topics...")
    out, _, _ = ssh.execute(
        "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic list | grep camera'"
    )
    print(out)


if __name__ == "__main__":
    diag_camera()
