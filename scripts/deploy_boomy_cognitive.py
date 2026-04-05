#!/usr/bin/env python3
import os
import sys

# Ensure src is in PYTHONPATH
sys.path.insert(0, os.path.join(os.getcwd(), "src"))

from yahboom_mcp.core.ssh_bridge import SSHBridge

# Target: Boomy (Pi 5 16GB)
BOOMY_IP = "192.168.1.11"
BOOMY_USER = "pi"
BOOMY_PASS = "yahboom"


def deploy():
    print(f"Connecting to Boomy at {BOOMY_IP}...")
    bridge = SSHBridge(BOOMY_IP, BOOMY_USER, BOOMY_PASS)
    bridge.connect()

    print("\n--- STEP 1: EMERGENCY STORAGE AUDIT ---")
    print("Identifying largest directories on root...")
    out, err, code = bridge.sudo_execute(
        "du -xh / --max-depth=2 | sort -rh | head -n 40"
    )
    print(f"Top 40 Space Hogs:\n{out}")

    print("\n--- STEP 2: LOG & CACHE PURGE ---")
    bridge.sudo_execute("apt-get clean")
    bridge.sudo_execute("journalctl --vacuum-time=1s")
    bridge.sudo_execute("rm -rf /var/log/*.gz /var/log/*.1")
    bridge.sudo_execute("rm -rf /home/pi/.cache/*")

    out, err, code = bridge.execute("df -h /")
    print(f"Current Disk Usage:\n{out}")

    bridge.close()
    print("BOOMY EMERGENCY AUDIT: Finalized.")


if __name__ == "__main__":
    deploy()
