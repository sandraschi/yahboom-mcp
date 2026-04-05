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
logger = logging.getLogger("audit-ap")


async def main():
    robot_ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    logger.info(f"Targeting Boomy at {robot_ip}...")

    ssh = SSHBridge(host=robot_ip, user="pi", password="yahboom")
    if not ssh.connect():
        logger.error("Failed to connect to Boomy via SSH.")
        return

    # 1. Audit hostapd.conf
    logger.info("🔍 Auditing /etc/hostapd/hostapd.conf...")
    out, err, code = ssh.execute("cat /etc/hostapd/hostapd.conf")
    if code == 0:
        print("\n--- hostapd.conf content ---")
        print(out)
        print("----------------------------\n")
    else:
        logger.error(f"❌ Failed to read hostapd.conf: {err}")

    # 2. Check PMF and IEEE standards
    logger.info("🔍 Checking IEEE 802.11w (PMF) and channel settings...")
    # Search for specific compatibility hurdles
    keywords = [
        "ieee80211w",
        "channel",
        "hw_mode",
        "wpa_pairwise",
        "rsn_pairwise",
        "country_code",
    ]
    for kw in keywords:
        if kw in out:
            matches = [ln for ln in out.split("\n") if kw in ln]
            if matches:
                logger.info(f"Setting found: {matches[0]}")

    # 3. Check logs for association failures
    logger.info("🔍 Examining hostapd logs for recent deauthentications...")
    out, err, code = ssh.sudo_execute("journalctl -u hostapd --no-pager -n 20")
    if code == 0:
        print("\n--- hostapd logs ---")
        print(out)
        print("--------------------\n")
    else:
        logger.error(f"❌ Failed to read hostapd logs: {err}")

    ssh.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
