import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from yahboom_mcp.core.ssh_bridge import SSHBridge

async def check_camera_logs():
    host = "192.168.1.11"
    print(f"Checking camera logs on {host}...")
    
    ssh = SSHBridge(host)
    ssh.connect()
    
    # Run the camera node for 10 seconds and capture output
    print("\n--- Starting Camera Node (10s capture) ---")
    # Using timeout to capture output before it terminates
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && timeout 10s ros2 run usb_cam usb_cam_node_exe --ros-args -p video_device:=/dev/video0 -p pixel_format:=mjpeg'"
    out, err, _ = ssh.execute(cmd)
    
    print("STDOUT:")
    print(out)
    print("\nSTDERR:")
    print(err)

if __name__ == "__main__":
    asyncio.run(check_camera_logs())
