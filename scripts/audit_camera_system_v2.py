import os
from yahboom_mcp.core.ssh_bridge import SSHBridge


def audit_camera_system_v2():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Auditing ROS 2 Packages (from root workspace)...")
    p_out, _, _ = ssh.execute(
        "sudo bash -c 'source /root/yahboomcar_ws/install/setup.bash && ros2 pkg list | grep -Ei \"camera|v4l|usb\"'"
    )
    print(f"ROOT_PACKAGES:\n{p_out}")

    print("[*] Auditing Running ROS 2 Nodes...")
    n_out, _, _ = ssh.execute(
        "sudo bash -c 'source /root/yahboomcar_ws/install/setup.bash && ros2 node list'"
    )
    print(f"ACTIVE_NODES:\n{n_out}")

    print("[*] Inspecting yahboom-robot.service unit file...")
    s_out, _, _ = ssh.execute("systemctl cat yahboom-robot.service")
    print(f"SERVICE_DEFINITION:\n{s_out}")

    print("[*] Checking for camera topics again (from root)...")
    t_out, _, _ = ssh.execute(
        "sudo bash -c 'source /root/yahboomcar_ws/install/setup.bash && ros2 topic list | grep -i image'"
    )
    print(f"CAMERA_TOPICS:\n{t_out}")


if __name__ == "__main__":
    audit_camera_system_v2()
