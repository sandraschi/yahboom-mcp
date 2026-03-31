import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def trace_oled_hw():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Searching for SSD1306 initialization in Python source files...")
    # Find all .py files containing 'Adafruit_SSD1306' and read the initialization line
    # We use grep with --include to target only source files
    cmd = "grep -r 'Adafruit_SSD1306.SSD1306_128_64' /home/pi/ --include='*.py' 2>/dev/null | head -n 5"
    out, err, code = ssh.execute(cmd)
    
    if out:
        print(f"[*] Found initialization logic:\n{out}")
        # Extract path from the first result
        path = out.split(':')[0]
        print(f"[*] Reading full script: {path}...")
        c_out, _, _ = ssh.execute(f"cat {path}")
        print("-" * 40)
        print(c_out)
        print("-" * 40)
    else:
        print("[FAIL] No SSD1306 source code found. Checking for 'i2c_bus' configuration...")
        out, _, _ = ssh.execute("grep -r 'i2c_bus' /home/pi/ --include='*.py' 2>/dev/null | head -n 5")
        print(f"I2C_CONFIG_GREP: {out}")

if __name__ == "__main__":
    trace_oled_hw()
