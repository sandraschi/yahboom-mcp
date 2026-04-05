from yahboom_mcp.core.ssh_bridge import SSHBridge
import os


def check_robot_topics():
    host = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    user = os.environ.get("YAHBOOM_USER", "pi")
    pw = os.environ.get("YAHBOOM_PASSWORD", "yahboom")

    ssh = SSHBridge(host=host, user=user, password=pw)
    if not ssh.connect():
        print("SSH Connection Failed!")
        return

    cmd = 'docker exec yahboom_ros2 bash -c "source /opt/ros/humble/setup.bash && ros2 topic list"'
    out, err, code = ssh.execute(cmd)

    print("\n--- ROS 2 Topics ---")
    print(out if out else "[None]")
    if err:
        print(f"Error: {err}")

    print("\n--- Camera Check ---")
    if "/camera/image_raw" in out:
        print("Found /camera/image_raw (Matches bridge!)")
    elif "/image_raw" in out:
        print("Found /image_raw (Bridge must be updated to use this)")
    elif "/usb_cam/image_raw" in out:
        print("Found /usb_cam/image_raw (Bridge must be updated to use this)")
    else:
        print("No camera topic found. Driver is likely NOT running.")

    ssh.close()


if __name__ == "__main__":
    check_robot_topics()
