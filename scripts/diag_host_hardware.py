import os
from yahboom_mcp.core.ssh_bridge import SSHBridge


def diag_host():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] HOST DIAGNOSTIC: Hardware Discovery on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Check for running camera processes on host
    print("[*] Checking for camera processes (libcamera, mjpg, python)...")
    cmd = "ps aux | grep -v grep | grep -E 'camera|mjpg|video|usb_cam|ros2'"
    out, _, _ = ssh.execute(cmd)
    print("-" * 40)
    print("HOST PROCESSES:")
    print(out)
    print("-" * 40)

    # 2. Check host-side video devices
    print("[*] Checking host-side /dev/video* devices...")
    cmd = "ls -l /dev/video*"
    out, _, _ = ssh.execute(cmd)
    print(out)

    # 3. Check for Yahboom car scripts on host
    print("[*] Searching host for yahboomcar scripts...")
    cmd = "find /home/pi/ -name '*camera*' | grep -v 'venv' | head -n 10"
    out, _, _ = ssh.execute(cmd)
    print("HOST CAMERA SCRIPTS:")
    print(out)


if __name__ == "__main__":
    diag_host()
