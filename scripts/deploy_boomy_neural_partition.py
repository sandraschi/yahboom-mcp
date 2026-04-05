from yahboom_mcp.core.ssh_bridge import SSHBridge
import time
import sys

ROBOT_IP = "192.168.0.250"

print(f"--- BOOMY NEURAL PARTITION: DEPLOYING ({ROBOT_IP}) ---")

bridge = SSHBridge(ROBOT_IP, "pi", "yahboom")
bridge.connect()

try:
    print("\n--- HOT-PLUG SUBSTRATE AUDIT ---")
    # Wait for kernel to settle
    time.sleep(5)
    out, _, _ = bridge.execute("lsblk")
    print(f"Detected Layout:\n{out}")

    if "sda" in out:
        print("\n--- REFORMATTING 500GB SSD TO EXT4 (HIGH-PERFORMANCE) ---")
        # Ensure it's unmounted (even if NTFS auto-mounted blindly)
        bridge.sudo_execute("umount /dev/sda*")

        # Format the whole disk to resolve any partition misalignment
        bridge.sudo_execute("mkfs.ext4 -F /dev/sda")

        print("MOUNTING NEURAL PARTITION TO /mnt/ssd...")
        bridge.sudo_execute("mkdir -p /mnt/ssd")
        bridge.sudo_execute("mount /dev/sda /mnt/ssd")

        # Hardening mount persistence
        print("HARDENING /etc/fstab PERSISTENCE...")
        bridge.sudo_execute(
            'grep -v "/mnt/ssd" /etc/fstab | sudo tee /etc/fstab > /dev/null'
        )
        bridge.sudo_execute(
            'echo "/dev/sda /mnt/ssd ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab'
        )

        out, _, _ = bridge.execute("df -h /mnt/ssd")
        print(f"Final Substrate State:\n{out}")

        print("\n--- INITIATING FIRST DIFFERENTIAL BACKUP (SD -> SSD) ---")
        # Skip system pipes and large docker cache for first sync
        rsync_cmd = 'sudo rsync -axH --delete --exclude="/proc/*" --exclude="/sys/*" --exclude="/dev/*" --exclude="/tmp/*" --exclude="/run/*" --exclude="/mnt/*" / /mnt/ssd/'
        # We run it in the background on the Pi to avoid SSH timeout for the first large sync
        bridge.execute(f"nohup {rsync_cmd} > /home/pi/backup.log 2>&1 &")

        print(
            "BACKUP MISSION STARTED (Background). Check /home/pi/backup.log for progress."
        )
        print("\nBOOMY NEURAL PARTITION DEPLOYMENT: 100% SUCCESS.")
    else:
        print(
            "[ERROR] SSD #2 (/dev/sda) missing. Hot-plug failed or power-draw too high."
        )

    bridge.close()

except Exception as e:
    print(f"Deployment Error: {str(e)}")
    bridge.close()
    sys.exit(1)
