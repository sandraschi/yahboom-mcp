import paramiko
import logging
import threading
from typing import Tuple

logger = logging.getLogger("yahboom-mcp.ssh-bridge")

class SSHBridge:
    def __init__(self, host: str = "192.168.0.250", user: str = "pi", password: str = "yahboom"):
        self.host = host
        self.user = user
        self.password = password
        self.client = None
        self.connected = False
        self.lock = threading.Lock()

    def connect(self) -> bool:
        """Establish SSH connection with timeout."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # Ensure password is used if provided
            self.client.connect(
                self.host, 
                username=self.user, 
                password=self.password, 
                look_for_keys=True,
                allow_agent=False,
                timeout=5
            )
            self.connected = True
            logger.info(f"SSH connected to {self.host} as {self.user}")
            return True
        except Exception as e:
            logger.error(f"SSH connection failed to {self.host}: {e}")
            return False

    def execute(self, command: str) -> Tuple[str, str, int]:
        """Execute a standard command and return (stdout, stderr, exit_code)."""
        with self.lock:
            if not self.client:
                if not self.connect():
                    return "", "SSH Not Connected", -1
            
            try:
                stdin, stdout, stderr = self.client.exec_command(command)
                out = stdout.read().decode().strip()
                err = stderr.read().decode().strip()
                code = stdout.channel.recv_exit_status()
                return out, err, code
            except Exception as e:
                logger.error(f"SSH execution failed: {e}")
                return "", str(e), -1

    def sudo_execute(self, command: str) -> Tuple[str, str, int]:
        """Execute a command with sudo, providing the password via stdin."""
        with self.lock:
            if not self.client:
                if not self.connect():
                    return "", "SSH Not Connected", -1
    
            try:
                # Use -S to read password from stdin
                sudo_cmd = f"sudo -S {command}"
                stdin, stdout, stderr = self.client.exec_command(sudo_cmd)
                
                # Write password to stdin
                stdin.write(f"{self.password}\n")
                stdin.flush()
                
                out = stdout.read().decode().strip()
                err = stderr.read().decode().strip()
                code = stdout.channel.recv_exit_status()
                
                # Simple cleanup of sudo prefix in stderr if it appears as a prompt
                if "password for" in err.lower() and "\n" in err:
                    err = err.split("\n", 1)[1].strip()
    
                return out, err, code
            except Exception as e:
                logger.error(f"SSH sudo execution failed: {e}")
                return "", str(e), -1

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            self.connected = False
