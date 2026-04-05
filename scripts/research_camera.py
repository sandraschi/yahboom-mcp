import asyncio
import os
import sys
import logging

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from yahboom_mcp.core.ssh_bridge import SSHBridge

async def research():
    host = "192.168.1.11"
    print(f"Researching camera on {host}...")
    
    ssh = SSHBridge(host)
    ssh.connect()
    
    # Check for core bringup node (yahboomcar_bringup) inside container
    print("\n--- Active Nodes ---")
    out, _, _ = ssh.execute("docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 node list'")
    print(f"Nodes:\n{out}")

    # Check topics
    print("\n--- Active Topics ---")
    out, _, _ = ssh.execute("docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic list'")
    print(f"Topics:\n{out}")

    # Try starting the node manually to see errors (no timeout param this time)
    print("\n--- Manual Start Attempt ---")
    cmd = ("source /opt/ros/humble/setup.bash && "
           "ros2 run usb_cam usb_cam_node_exe "
           "--ros-args "
           "-p video_device:=/dev/video0 "
           "-p image_width:=640 -p image_height:=480")
    
    # We'll run it and read output normally, then we'll have to kill it or wait
    out, err, code = ssh.execute(f"docker exec yahboom_ros2 bash -c '{cmd}'")
    print(f"Exit Code: {code}")
    print(f"STDOUT:\n{out}")
    print(f"STDERR:\n{err}")

if __name__ == "__main__":
    asyncio.run(research())
