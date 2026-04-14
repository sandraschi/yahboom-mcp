import os

from yahboom_mcp.core.ssh_bridge import SSHBridge


def trace_oled_v2():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Searching for OLED-related scripts in /home/pi/...")
    # Find all .py files containing 'OLED' and read the initialization line
    cmd = "grep -rl 'OLED' /home/pi/ --include='*.py' 2>/dev/null | head -n 5"
    out, _err, _code = ssh.execute(cmd)

    if out:
        paths = out.strip().split("\n")
        print(f"[*] Found {len(paths)} OLED scripts:")
        for p in paths:
            print(f"[*] Analyzing {p}...")
            # We use grep on the robot to find only the initialization lines
            init_cmd = f"grep -Ei 'SSD1306|Adafruit|i2c_bus|sda|scl' {p}"
            i_out, _, _ = ssh.execute(init_cmd)
            print("-" * 40)
            print(f"INITIALIZATION_LOGIC in {p}:")
            # Encode output to avoid CP1252 crash
            print(i_out.encode("ascii", "ignore").decode())
            print("-" * 40)
            # Find the SSD1306 class call specifically
    else:
        print("[FAIL] No OLED initiation logic found.")
        out, _, _ = ssh.execute("ls /dev/i2c-*")
        print(f"I2C_DEVS: {out}")


if __name__ == "__main__":
    trace_oled_v2()
