import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def read_sample_driver():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Locating test_display.py...")
    out, err, code = ssh.execute("find /home/pi/ -name test_display.py")
    paths = out.strip().split('\n')
    if paths and paths[0]:
        target = paths[0]
        print(f"[*] Reading {target}...")
        c_out, c_err, c_code = ssh.execute(f"cat {target}")
        print("-" * 40)
        print(f"FILE_CONTENTS:\n{c_out}")
        print("-" * 40)
    else:
        print("[FAIL] test_display.py NOT FOUND.")

if __name__ == "__main__":
    read_sample_driver()
