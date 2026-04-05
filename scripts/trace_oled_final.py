import os
from yahboom_mcp.core.ssh_bridge import SSHBridge


def trace_oled_final():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Performing a deep search for OLED scripts...")
    # This command finds all .py files with 'oled' in the name
    out, err, code = ssh.execute("find /home/pi/ -name '*oled*.py'")
    if out:
        paths = out.strip().split("\n")
        print(f"[*] Found {len(paths)} scripts:")
        for p in paths[:10]:
            print(f"  - {p}")
            # Identify which one is the 'official' Yahboom one
            if "yahboom" in p.lower() or "sample" in p.lower():
                print(f"    -> LIKELY CANDIDATE: {p}")

    print("\n[*] Checking /dev/i2c-* availability again...")
    i2c_out, _, _ = ssh.execute("ls /dev/i2c-*")
    print(f"I2C_DEVS: {i2c_out}")


if __name__ == "__main__":
    trace_oled_final()
