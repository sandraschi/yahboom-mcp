import paramiko


def deploy():
    host = "192.168.0.250"
    user = "pi"
    password = "yahboom"
    local_script = r"D:\Dev\repos\yahboom-mcp\scripts\robot\setup-autostart.sh"
    remote_path = "/tmp/setup-autostart.sh"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"Connecting to {host}...")
    ssh.connect(host, username=user, password=password)

    # Upload script
    sftp = ssh.open_sftp()
    print(f"Uploading {local_script} to {remote_path}...")
    sftp.put(local_script, remote_path)
    sftp.close()

    # Run script
    print("Running setup-autostart.sh on the robot...")
    _stdin, stdout, stderr = ssh.exec_command(
        f"chmod +x {remote_path} && sudo bash {remote_path}"
    )

    for line in stdout:
        print(f"STDOUT: {line.strip()}")
    for line in stderr:
        print(f"STDERR: {line.strip()}")

    ssh.close()
    print("Deployment complete.")


if __name__ == "__main__":
    deploy()
