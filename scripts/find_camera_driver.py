import os

from yahboom_mcp.core.ssh_bridge import SSHBridge


def find_driver():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] SEARCHING FOR CAMERA DRIVER on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search for all camera launch files in the container
    print("[*] Searching for *camera*.launch.py in /home/pi/software/...")
    cmd = "docker exec yahboom_ros2 find /home/pi/software/ -name '*camera*.launch.py'"
    out, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("FOUND LAUNCH FILES:")
    print(out)
    print("-" * 40)

    # 2. Check for libcamera-specific drivers (Pi 5)
    print("[*] Searching for libcamera or csi references...")
    cmd = "docker exec yahboom_ros2 find /home/pi/software/ -name '*libcamera*'"
    out, _, _ = ssh.execute(cmd)
    print(out)

    # 3. Check /dev/video* devices
    print("[*] Checking /dev/video* devices in container...")
    cmd = "docker exec yahboom_ros2 ls -l /dev/video*"
    out, _, _ = ssh.execute(cmd)
    print(out)


if __name__ == "__main__":
    find_driver()
