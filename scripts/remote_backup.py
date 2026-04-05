from yahboom_mcp.core.ssh_bridge import SSHBridge
import os
import sys

# Substrate Configuration
ROBOT_IP = "192.168.0.250"
TARGET_PATH = "D:\\backups\\boomy_sd_backup.img"
CHUNK_SIZE = 1024 * 1024  # 1MB Buffer for Gigabit

# Ensure backup directory exists
os.makedirs(os.path.dirname(TARGET_PATH), exist_ok=True)

print("--- BOOMY REMOTE BACKUP: INITIATING ---")
print(f"Source: {ROBOT_IP} (/dev/mmcblk0)")
print(f"Target: {TARGET_PATH}")

try:
    bridge = SSHBridge(ROBOT_IP, "pi", "yahboom")
    bridge.connect()

    # Use dd to stream the full card
    print("Streaming data (this may take 15-20 minutes)...")

    # We use a lower-level Paramiko call to get the raw binary stream
    ssh = bridge.client
    stdin, stdout, stderr = ssh.exec_command(
        "sudo dd if=/dev/mmcblk0 bs=1M status=none"
    )

    with open(TARGET_PATH, "wb") as f:
        bytes_copied = 0
        while True:
            data = stdout.read(CHUNK_SIZE)
            if not data:
                break
            f.write(data)
            bytes_copied += len(data)

            # Progress reporting (every 100MB)
            if bytes_copied % (100 * 1024 * 1024) == 0:
                print(f"Transferred: {bytes_copied // (1024 * 1024)} MB", end="\r")

    print(f"\n--- BACKUP COMPLETE: {bytes_copied // (1024 * 1024)} MB ---")
    bridge.close()

except Exception as e:
    print(f"Backup Error: {str(e)}")
    sys.exit(1)
