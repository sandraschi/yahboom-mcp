import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def trace_root_camera():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Searching for camera launch files in /root/yahboomcar_ws/...")
    # This command finds all .py files in the root workspace with camera/launch in path
    cmd = "sudo find /root/yahboomcar_ws/ -name '*camera*.launch.py'"
    out, err, code = ssh.execute(cmd)
    
    if out:
        paths = out.strip().split('\n')
        print(f"[*] Found {len(paths)} launch files:")
        for p in paths:
             print(f"  - {p}")
             # Let's inspect the first one
             print(f"\n[*] Reading {p}...")
             c_out, _, _ = ssh.execute(f"sudo cat {p}")
             print("-" * 40)
             print(c_out)
             print("-" * 40)
             break
    else:
        print("[FAIL] No camera launch files found in /root/yahboomcar_ws/.")

if __name__ == "__main__":
    trace_root_camera()
