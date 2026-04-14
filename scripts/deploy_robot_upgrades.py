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
logger = logging.getLogger("deploy-upgrades")


async def main():
    robot_ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")  # Fallback to common pi IP
    logger.info(f"Targeting Boomy at {robot_ip}...")

    ssh = SSHBridge(host=robot_ip, user="pi", password="yahboom")
    if not ssh.connect():
        logger.error("Failed to connect to Boomy via SSH.")
        return

    # 1. Install Stockfish & Python-Chess
    logger.info("📦 Installing Stockfish & Chess substrate...")
    ssh.sudo_execute("apt-get update && apt-get install -y stockfish")
    ssh.sudo_execute("pip3 install python-chess")
    logger.info("✅ Stockfish & Chess substrate deployed.")

    # 2. Deploy updated Peripheral Bridge
    logger.info("⚡ Deploying high-precision Peripheral Bridge (Touch enabled)...")
    local_bridge_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "robot", "peripheral_bridge.py")
    )
    with open(local_bridge_path) as f:
        bridge_content = f.read()

    # Upload via base64 to avoid escaping issues
    import base64

    encoded = base64.b64encode(bridge_content.encode()).decode()
    remote_cmd = f"echo '{encoded}' | base64 -d > ~/yahboom-mcp/scripts/robot/peripheral_bridge.py"
    ssh.execute(remote_cmd)
    ssh.execute("chmod +x ~/yahboom-mcp/scripts/robot/peripheral_bridge.py")
    logger.info("✅ Bridge script deployed.")

    # 3. Reload Service
    logger.info("🔄 Restarting Boomy Sensory Hub service...")
    ssh.sudo_execute("systemctl daemon-reload")
    ssh.sudo_execute("systemctl restart yahboom-peripheral-bridge.service")
    logger.info("✅ Boomy senses are now 100% active.")

    ssh.close()
    logger.info("🚀 100% Operational Upgrade sequence COMPLETE.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
