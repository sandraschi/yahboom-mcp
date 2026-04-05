import os
from yahboom_mcp.core.ssh_bridge import SSHBridge


def discover_camera_v4():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] ULTIMATE CAMERA DISCOVERY v4 on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Search for everything in the root workspace
    print("[*] Searching /root/yahboomcar_ws/ for camera launch files...")
    cmd = (
        "docker exec yahboom_ros2 find /root/yahboomcar_ws/ -name '*camera*.launch.py'"
    )
    out, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("CAM-RELATED LAUNCH FILES:")
    print(out)
    print("-" * 40)

    # 2. Check for port 8080 or 8081 (common MJPEG ports)
    print("[*] Checking host-side network ports...")
    cmd = "netstat -tulnp"
    out, _, _ = ssh.execute(cmd)
    print("ACTIVE PORTS:")
    print(out)

    # 3. Check for picamera2 on host
    print("[*] Checking host-side picamera2 installation...")
    cmd = "python3 -c 'import picamera2; print(\"picamera2 found\")' 2>/dev/null || echo 'picamera2 missing'"
    out, _, _ = ssh.execute(cmd)
    print(f"HOST PICAMERA: {out.strip()}")


if __name__ == "__main__":
    discover_camera_v4()
