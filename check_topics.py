import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect('192.168.1.11', username='yahboom', password='yahboom', timeout=5.0)
    stdin, stdout, stderr = client.exec_command("docker exec yahboom_ros2_final bash -c 'source /opt/ros/humble/setup.bash && ros2 topic list'")
    print('STDOUT:')
    print(stdout.read().decode())
    print('STDERR:')
    print(stderr.read().decode())
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
