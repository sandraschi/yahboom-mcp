import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def audit_container():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Searching for camera launch files INSIDE yahboom_ros2 container...")
    # Find camera launch files inside the workspace in the container
    cmd = "docker exec yahboom_ros2 find /root/yahboomcar_ws/ -name '*camera*launch*.py'"
    out, err, code = ssh.execute(cmd)
    
    if out:
        paths = out.strip().split('\n')
        print(f"[*] Found {len(paths)} launch files in container:")
        for p in paths:
             print(f"  - {p}")
             # Check the first one
             print(f"\n[*] Reading {p} contents...")
             c_out, _, _ = ssh.execute(f"docker exec yahboom_ros2 cat {p}")
             print("-" * 40)
             print(c_out)
             print("-" * 40)
             break
    else:
        print("[FAIL] No camera launch files found in container.")

if __name__ == "__main__":
    audit_container()
