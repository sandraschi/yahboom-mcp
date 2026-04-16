import paramiko
import os
import sys

def check_robot():
    host = "192.168.1.11"
    user = "yahboom"
    password = "yahboom"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {host}...")
        client.connect(host, username=user, password=password, timeout=10)
        
        # Check docker container
        print("Checking docker containers...")
        _, stdout, _ = client.exec_command("docker ps --format '{{.Names}}'")
        containers = stdout.read().decode().strip().split('\n')
        print(f"Containers found: {containers}")
        
        target = "yahboom_ros2_final"
        if target not in containers:
            print(f"ERROR: {target} container is NOT running!")
            return

        # Check ROS 2 nodes
        print(f"Checking ROS 2 nodes in {target}...")
        cmd_nodes = f"docker exec {target} bash -c 'source /opt/ros/humble/setup.bash; source /root/yahboomcar_ws/install/setup.bash; ros2 node list'"
        _, stdout, stderr = client.exec_command(cmd_nodes)
        nodes = stdout.read().decode().strip()
        print("Nodes:")
        print(nodes if nodes else "[None]")
        
        # Check ROS 2 topics
        print(f"Checking ROS 2 topics in {target}...")
        cmd_topics = f"docker exec {target} bash -c 'source /opt/ros/humble/setup.bash; source /root/yahboomcar_ws/install/setup.bash; ros2 topic list'"
        _, stdout, stderr = client.exec_command(cmd_topics)
        topics = stdout.read().decode().strip()
        print("Topics:")
        print(topics if topics else "[None]")
        
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        client.close()

if __name__ == '__main__':
    check_robot()
