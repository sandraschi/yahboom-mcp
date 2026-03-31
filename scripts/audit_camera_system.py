import os
from yahboom_mcp.core.ssh_bridge import SSHBridge

def audit_camera_system():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Auditing System ROS 2 Packages...")
    p_out, _, _ = ssh.execute("bash -c 'source /opt/ros/humble/setup.bash && ros2 pkg list | grep -Ei \"camera|v4l|usb\"'")
    print(f"SYSTEM_PACKAGES:\n{p_out}")

    print("[*] Auditing Running ROS 2 Nodes...")
    n_out, _, _ = ssh.execute("bash -c 'source /opt/ros/humble/setup.bash && ros2 node list'")
    print(f"ACTIVE_NODES:\n{n_out}")

    print("[*] Checking for Yahboom-related systemd services...")
    s_out, _, _ = ssh.execute("systemctl list-units --type=service | grep -i yahboom")
    print(f"SERVICES:\n{s_out}")

    print("[*] Checking for any running python camera scripts...")
    ps_out, _, _ = ssh.execute("ps aux | grep -Ei \"python|camera|video\" | grep -v grep")
    print(f"RUNNING_PROCESSES:\n{ps_out}")

if __name__ == "__main__":
    audit_camera_system()
