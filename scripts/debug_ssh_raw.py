import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def debug_ssh():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Testing 'uname -a'...")
    out, err, code = ssh.execute("uname -a")
    print(f"OUT: '{out}'")
    print(f"ERR: '{err}'")
    print(f"CODE: {code}")

    print("\n[*] Testing 'python3 --version'...")
    out, err, code = ssh.execute("python3 --version")
    print(f"OUT: '{out}'")
    print(f"ERR: '{err}'")
    print(f"CODE: {code}")

if __name__ == "__main__":
    debug_ssh()
