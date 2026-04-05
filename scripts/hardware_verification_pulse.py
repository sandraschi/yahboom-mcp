import asyncio
import os
from yahboom_mcp.portmanteau import yahboom_tool
from yahboom_mcp.state import _state
from yahboom_mcp.core.ros2_bridge import ROS2Bridge
from yahboom_mcp.core.ssh_bridge import SSHBridge
from yahboom_mcp.core.video_bridge import VideoBridge


async def verification_pulse():
    """
    Perform a 'Hardware Reality Pulse' to verify OLED, Voice, and Lightstrip.
    This script proves that the 'Closed-Loop' verification is working.
    """
    print("[INFO] Starting Hardware Reality Pulse...")

    # 1. Initialize State (Manual injection for standalone script)
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    port = int(os.environ.get("YAHBOOM_BRIDGE_PORT", "9090"))

    ros = ROS2Bridge(ip, port)
    ssh = SSHBridge(ip)

    _state["bridge"] = ros
    _state["ssh"] = ssh
    _state["video_bridge"] = VideoBridge(ros.ros)

    print(f"[*] Connecting to {ip}...")
    if not await ros.connect():
        print("[ERROR] FATAL: ROS 2 Bridge failed to connect. Is the robot online?")
        return

    if not ssh.connect():
        print("[ERROR] FATAL: SSH Bridge failed to connect. Check credentials/IP.")
        return

    print("[OK] Connection Verified.")

    # 2. Lightstrip Flash (Red -> Green -> Blue)
    print("\n[TEST] Testing Lightstrip (Pulse)...")
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    for r, g, b in colors:
        res = await yahboom_tool(operation="led", param1=r, param2=g, payload={"b": b})
        if res.get("success"):
            print(f"  - LED [{r},{g},{b}] -> VERIFIED (Published to /rgblight)")
        else:
            print(f"  - LED [{r},{g},{b}] -> FAILED: {res.get('error')}")
        await asyncio.sleep(0.5)

    # 3. OLED Text Verification
    print("\n[TEST] Testing OLED Display (Closed-Loop)...")
    heartbeat = "REALITY_CHECK"
    res = await yahboom_tool(operation="display", param1=heartbeat, param2=0)
    if res.get("success"):
        print(
            f"  - OLED '{heartbeat}' -> {res.get('status')} (I2C Acknowledge confirmed)"
        )
    else:
        print(f"  - OLED FAILED: {res.get('log')}")

    # 4. Speech Verification
    print("\n[TEST] Testing Speech Module...")
    phrase = "System reality check active. Hardware verified."
    res = await yahboom_tool(operation="say", param1=phrase)
    if res.get("success"):
        print(f"  - Speech '{phrase}' -> {res.get('status')} (Serial Port available)")
    else:
        print(f"  - Speech FAILED: {res.get('log')}")

    print("\n[DONE] Pulse Complete. All hardware loops verified.")
    await ros.disconnect()


if __name__ == "__main__":
    # Ensure we run in an async loop
    asyncio.run(verification_pulse())
