import os

import paramiko

hostname = "192.168.0.250"
username = "pi"
password = "yahboom"
key_path = os.path.expanduser("~/.ssh/id_rsa.pub")

with open(key_path) as f:
    key = f.read().strip()

print(f"Deploying key to {username}@{hostname}...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, username=username, password=password)

# Append key to authorized_keys
client.exec_command("mkdir -p ~/.ssh && chmod 700 ~/.ssh")
client.exec_command(f"echo '{key}' >> ~/.ssh/authorized_keys")
client.exec_command("chmod 600 ~/.ssh/authorized_keys")

print("Key deployed successfully.")
client.close()
