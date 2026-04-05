import os
import time
import base64
from yahboom_mcp.core.ssh_bridge import SSHBridge
from yahboom_mcp.core.ros2_bridge import ROS2Bridge
import asyncio


async def final_reality_pulse():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    ros = ROS2Bridge(host=ip)

    print(f"[*] Starting FINAL REALITY PULSE on {ip}...")

    if not ssh.connect():
        print("[FAIL] SSH Connection failed")
        return

    if not await ros.connect():
        print("[FAIL] ROS 2 Connection failed")
        # return # Proceed anyway to test non-ROS hardware if needed

    # 1. TEST LIGHTSTRIP (ROS)
    print("[*] Pulsing Lightstrip (ROS)...")
    await ros.publish_velocity(0.0, 0.0)  # Ensure zero velocity
    # We use the raw topic pub for the pulse to be safe
    ssh.execute(
        "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic pub --once /RGBLight std_msgs/msg/Int32 {data: 1}'"
    )
    time.sleep(1)
    ssh.execute(
        "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic pub --once /RGBLight std_msgs/msg/Int32 {data: 2}'"
    )
    time.sleep(1)
    ssh.execute(
        "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic pub --once /RGBLight std_msgs/msg/Int32 {data: 3}'"
    )

    # 2. TEST OLED (Native)
    print("[*] Writing to OLED (Native)...")
    oled_text = "REALITY CHECK\nSYSTEMS: OK"
    encoded_text = base64.b64encode(oled_text.encode()).decode()
    ssh.execute(
        f"python3 /home/pi/software/oled_yahboom/yahboom_oled.py --base64 {encoded_text}"
    )

    # 3. TEST SPEECH (Serial)
    print("[*] Synthesizing Speech (Serial)...")
    # "$say,All systems operational. Reality check complete.#"
    # We use printf to avoid echoes/quoting issues
    speech_cmd = "printf '\\$say,All systems operational. Reality check complete.#' > /dev/ttyUSB0"
    ssh.execute(speech_cmd)

    # 4. TEST CAMERA (Docker)
    print("[*] Verifying Camera Node (Docker)...")
    # Launch the camera node
    ssh.execute(
        "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 launch usb_cam camera.launch.py' &"
    )

    print("[*] Waiting for camera topics to appear...")
    for _ in range(10):
        t_out, _, _ = ssh.execute(
            "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic list | grep -i image_raw'"
        )
        if t_out:
            print(f"[SUCCESS] Camera topics found:\n{t_out}")
            break
        await asyncio.sleep(2)
    else:
        print("[FAIL] Camera topics did not appear within 20 seconds.")

    print("\n[!] FINAL REALITY PULSE COMPLETE.")
    print(
        "[!] User: Please confirm you see the Lightstrip flash, text on OLED, and hear the speech."
    )


if __name__ == "__main__":
    asyncio.run(final_reality_pulse())
