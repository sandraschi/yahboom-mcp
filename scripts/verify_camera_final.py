import os
import time
from yahboom_mcp.core.ssh_bridge import SSHBridge

def verify_camera_final():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)
    
    print(f"[*] Final Camera Verification on {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    # Trigger launch just in case (non-blocking)
    print("[*] Launching camera node (docker exec)...")
    ssh.execute("docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 launch usb_cam camera.launch.py' &")
    
    time.sleep(5)
    
    print("[*] Checking for /image_raw topic inside Docker...")
    # This command uses grep to confirm topic existence
    cmd = "docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic list | grep -i image_raw'"
    out, err, code = ssh.execute(cmd)
    
    if out:
        print(f"[SUCCESS] Camera topic detected:\n{out}")
    else:
        print(f"[FAIL] Camera topic NOT detected correctly. ERR: {err}")

if __name__ == "__main__":
    verify_camera_final()
