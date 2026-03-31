import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def discover_drivers():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Searching for Yahboom Python packages...")
    out, err, code = ssh.execute("pip list | grep -i yahboom")
    print(f"PIP_YAHBOOM: {out}")
    
    print("[*] Searching for Rosmaster packages...")
    out, err, code = ssh.execute("pip list | grep -i rosmaster")
    print(f"PIP_ROSMASTER: {out}")

    print("[*] Checking /home/pi/ (Yahboom usually keeps sample scripts there)")
    out, err, code = ssh.execute("ls -R /home/pi/ | grep -i display")
    print(f"FS_DISPLAY: {out}")

if __name__ == "__main__":
    discover_drivers()
