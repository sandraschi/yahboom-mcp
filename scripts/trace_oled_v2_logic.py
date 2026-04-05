import os
from yahboom_mcp.core.ssh_bridge import SSHBridge


def trace_oled_v2_logic():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Searching for OLED-related source code in /home/pi/...")
    # This command finds all .py files containing 'SSD1306' or 'Adafruit_SSD1306'
    cmd = "grep -rlE 'SSD1306|Adafruit_SSD1306' /home/pi/ --include='*.py' 2>/dev/null"
    out, err, code = ssh.execute(cmd)

    if out:
        paths = out.strip().split("\n")
        print(f"[*] Found {len(paths)} OLED source files:")
        for p in paths[:5]:  # Check the first 5
            print(f"  - Analyzing {p}...")
            # We look for the initialization line specifically
            init_grep = f"grep -Ei 'SSD1306|Adafruit|i2c_bus|sda|scl|rst' {p}"
            i_out, _, _ = ssh.execute(init_grep)
            print("-" * 40)
            print(f"INIT CODE in {p}:")
            print(i_out)
            print("-" * 40)
    else:
        print("[FAIL] No OLED initiation logic found.")


if __name__ == "__main__":
    trace_oled_v2_logic()
