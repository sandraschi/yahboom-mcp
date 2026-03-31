import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def discover_rosmaster():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Searching for 'Rosmaster.py' on the robot...")
    # Find the location of the Rosmaster library source
    out, err, code = ssh.execute("find /home/pi/ -name 'Rosmaster.py'")
    if out:
        path = out.strip().split('\n')[0]
        print(f"[*] Found Rosmaster at: {path}")
        print(f"[*] Searching for OLED methods in {path}...")
        m_out, _, _ = ssh.execute(f"grep -niE 'oled|display' {path}")
        print(f"METHODS:\n{m_out}")
    else:
        print("[FAIL] Rosmaster.py NOT FOUND.")

if __name__ == "__main__":
    discover_rosmaster()
