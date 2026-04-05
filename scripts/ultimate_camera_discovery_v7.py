import os
from yahboom_mcp.core.ssh_bridge import SSHBridge


def discover_camera_v7():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] ULTIMATE CAMERA DISCOVERY v7 on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search for everything in the container related to camera
    print("[*] Searching entire container for camera launch files...")
    cmd = "docker exec yahboom_ros2 find / -name '*camera*.launch.py' 2>/dev/null | head -n 50"
    out_cam, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("CAM-RELATED LAUNCH FILES:")
    print(out_cam)
    print("-" * 40)

    # 2. Check yahboomcar_visual for specific Pi 5 camera nodes
    print("[*] Checking yahboomcar_visual packages...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 pkg list | grep -i yahboomcar'"
    out_pkg, _, _ = ssh.execute(cmd)
    print(f"YAHBOOM PACKAGES: {out_pkg}")

    # 3. Check for specific Pi 5 camera driver (v4l2_camera or libcamera)
    print("[*] Checking for libcamera or v4l2_camera...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 pkg list | grep -E \"camera|v4l2\"'"
    out_drv, _, _ = ssh.execute(cmd)
    print(f"CAMERA DRIVERS FOUND: {out_drv}")

    # 4. Check for port 8080 or 8081 (Yahboom often uses mjpg-streamer on these ports)
    print("[*] Checking host-side network ports...")
    cmd = "netstat -tulnp"
    out_net, _, _ = ssh.execute(cmd)
    print("ACTIVE HOST PORTS:")
    print(out_net)


if __name__ == "__main__":
    discover_camera_v7()
