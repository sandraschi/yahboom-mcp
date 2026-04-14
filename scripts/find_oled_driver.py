import os

from yahboom_mcp.core.ssh_bridge import SSHBridge


def find_working_sample():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Searching for 'SSD1306' in /home/pi/...")
    # This command finds files containing 'SSD1306' and prints their paths
    out, _err, _code = ssh.execute("grep -rl 'Adafruit_SSD1306' /home/pi/ 2>/dev/null")
    if out:
        paths = out.strip().split("\n")
        print(f"[*] Found {len(paths)} scripts:")
        for p in paths[:5]:
            print(f"  - {p}")
            # Read the first one
            print(f"\n[*] Reading {p}...")
            c_out, _, _ = ssh.execute(f"cat {p}")
            print("-" * 40)
            print(c_out)
            print("-" * 40)
            break
    else:
        print("[FAIL] No SSD1306 scripts found.")


if __name__ == "__main__":
    find_working_sample()
