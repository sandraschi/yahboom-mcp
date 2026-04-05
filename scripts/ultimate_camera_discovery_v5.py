import os
from yahboom_mcp.core.ssh_bridge import SSHBridge


def discover_camera_v5():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] ULTIMATE CAMERA DISCOVERY v5 on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search for all .launch.py files in the root workspace
    print("[*] Searching /root/yahboomcar_ws/ for camera launch files...")
    cmd = "docker exec yahboom_ros2 find /root/yahboomcar_ws/ -name '*.launch.py' | grep -i camera"
    out_cam, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("CAM-RELATED LAUNCH FILES:")
    print(out_cam)
    print("-" * 40)

    # 2. Check for port 8080 (Yahboom often uses mjpg-streamer on 8080 or 8081)
    print("[*] Checking host-side network ports...")
    cmd = "netstat -tulnp"
    out_net, _, _ = ssh.execute(cmd)
    print("ACTIVE PORTS:")
    print(out_net)

    # 3. Check for specific Pi 5 camera packages
    print("[*] Checking for libcamera or v4l2_camera packages...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 pkg list | grep -E \"camera|v4l2\"'"
    out_pkg, _, _ = ssh.execute(cmd)
    print("CAMERA PACKAGES:")
    print(out_pkg)

    # 4. Check for yahboomcar_visual contents
    print("[*] Inspecting yahboomcar_visual launch directory...")
    cmd = "docker exec yahboom_ros2 ls /root/yahboomcar_ws/src/yahboomcar_visual/launch/ 2>/dev/null"
    out_vis, _, _ = ssh.execute(cmd)
    print("VISUAL LAUNCHES:")
    print(out_vis)


if __name__ == "__main__":
    discover_camera_v5()
