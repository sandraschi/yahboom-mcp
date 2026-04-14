import os

from yahboom_mcp.core.ssh_bridge import SSHBridge


def trace_ros2_ws():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Searching for 'setup.bash' in /home/pi/ to find ROS 2 workspaces...")
    out, _err, _code = ssh.execute("find /home/pi/ -name 'setup.bash' -maxdepth 4")
    if out:
        paths = out.strip().split("\n")
        print(f"[*] Found {len(paths)} workspaces:")
        for p in paths:
            print(f"  - {p}")
            # Try to find camera info in these workspaces
            base = os.path.dirname(os.path.dirname(p))
            print(f"    - Checking {base}/src for camera packages...")
            pkg_out, _, _ = ssh.execute(f"ls {base}/src | grep -i camera")
            if pkg_out:
                print(f"      -> FOUND: {pkg_out.strip()}")
                # List launch files
                l_out, _, _ = ssh.execute(
                    f"find {base}/src -name '*launch*.py' | grep -i camera"
                )
                print(f"      -> LAUNCH FILES: {l_out}")
    else:
        print("[FAIL] No ROS 2 workspaces found.")


if __name__ == "__main__":
    trace_ros2_ws()
