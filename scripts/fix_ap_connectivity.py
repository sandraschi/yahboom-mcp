#!/usr/bin/env python3
import os
import sys
import logging

# Add the src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

try:
    from yahboom_mcp.core.ssh_bridge import SSHBridge
except ImportError as e:
    print(f"ERROR: Could not import SSHBridge: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix-ap")


async def main():
    robot_ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    logger.info(f"Targeting Boomy at {robot_ip}...")

    ssh = SSHBridge(host=robot_ip, user="pi", password="yahboom")
    if not ssh.connect():
        logger.error("Failed to connect to Boomy via SSH.")
        return

    # 1. Hardening Raspbot for Windows 11 Compatibility
    # pmf=1 (Optional), proto=rsn (WPA2), group/pairwise=ccmp (AES)
    logger.info("🛡️ Hardening 'Raspbot' profile for Windows compatibility...")
    commands = [
        "nmcli connection modify Raspbot 802-11-wireless-security.pmf 1",
        "nmcli connection modify Raspbot 802-11-wireless-security.proto rsn",
        "nmcli connection modify Raspbot 802-11-wireless-security.group ccmp",
        "nmcli connection modify Raspbot 802-11-wireless-security.pairwise ccmp",
        "nmcli connection modify Raspbot 802-11-wireless-security.key-mgmt wpa-psk",
    ]

    for cmd in commands:
        logger.info(f"Executing: {cmd}")
        ssh.sudo_execute(cmd)

    # 2. Cycling the connection
    logger.info("🔄 Refreshing Raspbot connection...")
    ssh.sudo_execute("nmcli connection down Raspbot")
    ssh.sudo_execute("nmcli connection up Raspbot")

    logger.info("✅ Boomy AP is now in 'Windows-Compatible' mode.")
    logger.info(
        "👉 IMPORTANT: Please FORGET the 'raspbot' network on your Windows PC and reconnect."
    )

    ssh.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
