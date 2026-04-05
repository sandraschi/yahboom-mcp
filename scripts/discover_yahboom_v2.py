import os
from yahboom_mcp.core.ssh_bridge import SSHBridge


def discover_yahboom():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Searching for 'Rosmaster' in python packages...")
    out, err, code = ssh.execute(
        "python3 -c 'import Rosmaster; print(Rosmaster.__file__)'"
    )
    print(f"ROSMASTER_PATH: {out}")
    if err:
        print(f"ERROR: {err}")

    print("[*] Searching for 'Yahboom' related folders in /home/pi/...")
    out, err, code = ssh.execute("ls -d /home/pi/*/ | grep -i yahboom")
    print(f"YAHBOOM_FOLDERS: {out}")

    print("[*] Searching for SSD1306 imports in /home/pi/...")
    out, err, code = ssh.execute("grep -r 'SSD1306' /home/pi/ 2>/dev/null | head -n 5")
    print(f"SSD1306_GREP: {out}")


if __name__ == "__main__":
    discover_yahboom()
