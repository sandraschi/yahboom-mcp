import paramiko
import sys

def test_ssh(host, user, password, command="hostname"):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=10)
        stdin, stdout, stderr = ssh.exec_command(command)
        print(f"STDOUT: {stdout.read().decode().strip()}")
        print(f"STDERR: {stderr.read().decode().strip()}")
        ssh.close()
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    host = "192.168.0.250"
    user = "pi"
    password = "yahboom"
    cmd = "source /opt/ros/humble/setup.bash && ros2 node list"
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    test_ssh(host, user, password, cmd)
