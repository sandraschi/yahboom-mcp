#!/usr/bin/env python3
import logging
import os
import sys

# Add the src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

try:
    from yahboom_mcp.core.ssh_bridge import SSHBridge
except ImportError as e:
    print(f"ERROR: Could not import SSHBridge: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audit-ap-v2")


async def main():
    robot_ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    logger.info(f"Targeting Boomy at {robot_ip}...")

    ssh = SSHBridge(host=robot_ip, user="pi", password="yahboom")
    if not ssh.connect():
        logger.error("Failed to connect to Boomy via SSH.")
        return

    # 1. Check NetworkManager Connections
    logger.info("🔍 Probing NetworkManager for 'raspbot' identity...")
    out, _err, _code = ssh.execute("nmcli connection show")
    if "raspbot" in out:
        logger.info("✅ Found 'raspbot' profile in NetworkManager.")

        # Audit the specific profile
        out_prof, _err_prof, _code_prof = ssh.sudo_execute(
            "nmcli connection show raspbot"
        )
        print("\n--- NetworkManager 'raspbot' Profile ---")
        # Filter for sensitive/relevant fields for the model to see
        relevant_keywords = [
            "802-11-wireless.ssid",
            "802-11-wireless-security",
            "wifi-sec.key-mgmt",
            "wifi-sec.pairwise",
            "wifi-sec.pmf",
            "ipv4.method",
            "802-11-wireless.channel",
        ]
        for line in out_prof.split("\n"):
            if any(kw in line for kw in relevant_keywords):
                print(line)
        print("------------------------------------------\n")
    else:
        logger.warn(
            "⚠️ No 'raspbot' profile found in nmcli. Checking for generic hotspot..."
        )
        # Check all wifi devices
        out_dev, _err_dev, _code_dev = ssh.execute("nmcli device show wlan0")
        print(out_dev)

    # 2. Check Systemd services for non-standard AP wrappers
    logger.info("🔍 Probing system services for custom wrappers...")
    out_serv, _err_serv, _code_serv = ssh.execute(
        "systemctl list-units --type=service | grep -E 'ap|wifi|hostapd|create_ap'"
    )
    print(out_serv)

    # 3. Check for regional/driver frequency rejection
    logger.info("🔍 Checking WiFi regulatory domain...")
    out_reg, _err_reg, _code_reg = ssh.execute("iw reg get")
    print(out_reg)

    ssh.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
