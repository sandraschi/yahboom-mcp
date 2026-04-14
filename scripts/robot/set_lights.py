import sys

import paramiko


def set_lights(r, g, b):
    host = "192.168.0.250"
    user = "pi"
    password = "yahboom"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)

    # Use single quotes for the bash command and properly escaped double quotes for the JSON
    cmd = f"docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && ros2 topic pub --once /rgblight std_msgs/msg/Int32MultiArray \"{{data: [{r}, {g}, {b}]}}\"'"

    print(f"Executing: {cmd}")
    _stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    ssh.close()


if __name__ == "__main__":
    if len(sys.argv) == 4:
        set_lights(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        set_lights(0, 255, 0)  # Default green
