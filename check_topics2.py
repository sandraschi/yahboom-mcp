import subprocess
res = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "yahboom@192.168.1.11", 
    "docker exec yahboom_ros2_final bash -c 'source /opt/ros/humble/setup.bash && ros2 topic list'"], 
    capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
