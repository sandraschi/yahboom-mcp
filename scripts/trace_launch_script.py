import os
from yahboom_mcp.core.ssh_bridge import SSHBridge


def trace_launch_script():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    print("[*] Reading /usr/local/bin/yahboom-launch.sh...")
    out, err, code = ssh.execute("cat /usr/local/bin/yahboom-launch.sh")
    if out:
        print("-" * 40)
        print(out)
        print("-" * 40)
    else:
        print(f"[FAIL] Could not read launch script. ERR: {err}")


if __name__ == "__main__":
    trace_launch_script()
