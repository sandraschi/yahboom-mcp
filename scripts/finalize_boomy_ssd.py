import sys
import time

from yahboom_mcp.core.ssh_bridge import SSHBridge

ROBOT_IP = "192.168.0.250"
RETRIES = 30
DELAY = 10

print(f"--- BOOMY FINALIZATION: WAITING FOR HEARTBEAT ({ROBOT_IP}) ---")

bridge = SSHBridge(ROBOT_IP, "pi", "yahboom")

connected = False
for i in range(RETRIES):
    try:
        bridge.connect()
        connected = True
        print(f"\n[SUCCESS] Boomy SSH Link Established (Attempt {i + 1}).")
        break
    except Exception:
        print(".", end="", flush=True)
        time.sleep(DELAY)

if not connected:
    print("\n[ERROR] Boomy heartbeat failed to return. Task stalled.")
    sys.exit(1)

try:
    print("\n--- SUBSTRATE AUDIT ---")
    out, _, _ = bridge.execute("lsblk")
    print(f"Current Layout:\n{out}")

    if "sda" in out:
        print("\n--- FORMATTING SSD #2 TO EXT4 (HIGH-PERFORMANCE) ---")
        # We format the whole disk /dev/sda for simplicity and performance
        bridge.sudo_execute("umount /dev/sda*")
        bridge.sudo_execute("mkfs.ext4 -F /dev/sda")

        print("MOUNTING TO /mnt/ssd...")
        bridge.sudo_execute("mkdir -p /mnt/ssd")
        bridge.sudo_execute("mount /dev/sda /mnt/ssd")

        # Add to fstab for persistency
        print("HARDENING MOUNT PERSISTENCE (/etc/fstab)...")
        bridge.sudo_execute(
            'grep -v "/mnt/ssd" /etc/fstab | sudo tee /etc/fstab > /dev/null'
        )
        bridge.sudo_execute(
            'echo "/dev/sda /mnt/ssd ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab'
        )

        out, _, _ = bridge.execute("df -h /mnt/ssd")
        print(f"New Substrate State:\n{out}")
        print("\nBOOMY SSD #2 INTEGRATION: 100% COMPLETE.")
    else:
        print("[ERROR] SSD #2 (/dev/sda) missing after power cycle.")

    bridge.close()

except Exception as e:
    print(f"Integration Error: {e!s}")
    bridge.close()
    sys.exit(1)
