import os

from yahboom_mcp.core.ssh_bridge import SSHBridge


def discover_camera_v6():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] ULTIMATE CAMERA DISCOVERY v6 on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search for EVERYTHING in the container related to camera
    print("[*] Searching entire container for camera launch files...")
    cmd = "docker exec yahboom_ros2 find / -name '*camera*.launch.py' 2>/dev/null | head -n 50"
    out, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("FILES FOUND IN CONTAINER:")
    print(out)
    print("-" * 40)

    # 2. Check for port 8080 (Yahboom often uses mjpg-streamer on 8080 or 8081)
    print("[*] Checking host-side network ports...")
    cmd = "netstat -tulnp"
    out, _, _ = ssh.execute(cmd)
    print("ACTIVE PORTS:")
    print(out)

    # 3. Check official yahboom workspace location
    print("[*] Checking for yahboomcar packages in container...")
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 pkg list | grep yahboomcar'"
    out, _, _ = ssh.execute(cmd)
    print(f"YAHBOOM PACKAGES: {out}")


if __name__ == "__main__":
    discover_camera_v6()
