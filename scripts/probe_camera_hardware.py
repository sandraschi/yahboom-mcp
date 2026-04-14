import os
import time

from yahboom_mcp.core.ssh_bridge import SSHBridge


def probe_camera():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] REALITY PROBE: Camera Discovery on {ip}...")
    if not ssh.connect():
        print("[-] SSH FAILED")
        return

    # 1. Check if node is already running
    print("[*] Checking for existing usb_cam node...")
    out, _, _ = ssh.execute(
        "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 node list | grep -v \"/\"'"
    )
    print(f"[DEBUG] Node list: {out.strip()}")

    # 2. Trigger launch manually to see logs
    print("[*] Triggering camera launch (blocking for 5 seconds to catch errors)...")
    # We use a timeout to let it start then check topics
    ssh.execute(
        "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && timeout 10 ros2 launch usb_cam camera.launch.py' &"
    )

    time.sleep(12)

    print("[*] Performing Topic Discovery...")
    topics, _, _ = ssh.execute(
        "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic list'"
    )
    print("-" * 40)
    print("ALL TOPICS FOUND:")
    print(topics)
    print("-" * 40)

    # 3. Check for image topicsSpecifically
    img_topics = [t for t in topics.splitlines() if "image" in t.lower()]
    if img_topics:
        print(f"[SUCCESS] Found {len(img_topics)} image topics: {img_topics}")
    else:
        print("[FAIL] No image topics found. Camera launch might be failing.")


if __name__ == "__main__":
    probe_camera()
