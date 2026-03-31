import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def list_all_launch():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] LISTING ALL LAUNCH FILES on {ip}...")
    if not ssh.connect():
        print("[-] SSH CONNECTION FAILED")
        return

    # 1. Broadest possible search for ROS 2 launch files
    cmd = "docker exec yahboom_ros2 find / -name '*.launch.py' 2>/dev/null"
    out, _, _ = ssh.execute(cmd)
    
    print("-" * 40)
    print("ALL LAUNCH FILES FOUND IN CONTAINER:")
    # Filter for interesting ones
    lines = out.splitlines()
    for line in lines:
        if "yahboom" in line.lower() or "camera" in line.lower() or "usb_cam" in line.lower():
            print(line)
    print("-" * 40)

    # 2. Check for host ports
    print("[*] Checking host-side listening ports...")
    cmd = "netstat -tulnp"
    out, _, _ = ssh.execute(cmd)
    print(out)

if __name__ == "__main__":
    list_all_launch()
