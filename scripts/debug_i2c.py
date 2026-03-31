import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def check_i2c():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Checking All I2C Buses...")
    for bus in [0, 1, 2, 3, 4, 11]:
        out, err, code = ssh.execute(f"i2cdetect -y {bus}")
        if "3c" in out:
            print(f"[OK] OLED Address 0x3c DETECTED on BUS {bus}!")
            return
        else:
            print(f"  - Bus {bus}: Empty")
    
    print("[FAIL] OLED Address 0x3c NOT FOUND on any common bus.")

if __name__ == "__main__":
    check_i2c()
