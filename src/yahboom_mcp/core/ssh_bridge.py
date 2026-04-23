import logging
import os
import threading
import time

import paramiko

logger = logging.getLogger("yahboom-mcp.ssh-bridge")

_EXEC_ERROR_LOG_INTERVAL_S = 5.0


class SSHBridge:
    def __init__(self, host: str, user: str = "pi", password: str | None = None):
        self.host = host
        self.user = user
        self.password = password or os.getenv("YAHBOOM_PASSWORD")
        self.client = None
        self.connected = False
        self.lock = threading.Lock()
        self._last_exec_error_log: float | None = None
        self._exec_error_suppressed = 0

    def _log_exec_failure(self, prefix: str, exc: Exception) -> None:
        """Log SSH exec failures; cap ERROR lines to once per interval."""
        msg = str(exc)
        now = time.monotonic()
        prev = self._last_exec_error_log
        if prev is None or now - prev >= _EXEC_ERROR_LOG_INTERVAL_S:
            suffix = ""
            if self._exec_error_suppressed:
                suffix = f" ({self._exec_error_suppressed} more in the last {_EXEC_ERROR_LOG_INTERVAL_S:.0f}s)"
                self._exec_error_suppressed = 0
            self._last_exec_error_log = now
            logger.error(f"{prefix}: {msg}{suffix}")
        else:
            self._exec_error_suppressed += 1
            logger.debug(f"{prefix}: {msg}")

    def connect(self) -> bool:
        """Establish SSH connection with timeout and robust error trapping."""
        logger.info(f"Attempting SSH connection to {self.host}...")
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Use password if provided, else rely on keys
            self.client.connect(
                self.host,
                username=self.user,
                password=self.password,
                look_for_keys=True,
                allow_agent=False,
                timeout=15,
            )
            self.connected = True
            logger.info(f"SSH successfully connected to {self.host}")
            return True
        except paramiko.AuthenticationException:
            logger.error(f"SSH Authentication failed for {self.user}@{self.host}. Check YAHBOOM_PASSWORD.")
            return False
        except TimeoutError:
            logger.error(f"SSH Connection timed out to {self.host}. Is the robot powered on?")
            return False
        except Exception as e:
            logger.error(f"SSH Critical failure connecting to {self.host}: {e}")
            return False

    async def execute(self, command: str) -> tuple[str, str, int]:
        """Execute a standard command asynchronously and return (stdout, stderr, exit_code)."""
        import asyncio

        return await asyncio.to_thread(self._execute_sync, command)

    def _execute_sync(self, command: str) -> tuple[str, str, int]:
        """Synchronous implementation."""
        with self.lock:
            if not self.client or not self.connected:
                if self.client:
                    try:
                        self.client.close()
                    except Exception:
                        pass
                    self.client = None
                if not self.connect():
                    return "", "SSH Not Connected", -1

            try:
                _stdin, stdout, stderr = self.client.exec_command(command)
                out = stdout.read().decode().strip()
                err = stderr.read().decode().strip()
                code = stdout.channel.recv_exit_status()
                return out, err, code
            except Exception as e:
                self._log_exec_failure("SSH execution failed", e)
                return "", str(e), -1

    async def sudo_execute(self, command: str) -> tuple[str, str, int]:
        """Execute a command with sudo asynchronously, providing the password via stdin."""
        import asyncio

        return await asyncio.to_thread(self._sudo_execute_sync, command)

    def _sudo_execute_sync(self, command: str) -> tuple[str, str, int]:
        """Synchronous implementation."""
        with self.lock:
            if not self.client or not self.connected:
                if self.client:
                    try:
                        self.client.close()
                    except Exception:
                        pass
                    self.client = None
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
                self._log_exec_failure("SSH sudo execution failed", e)
                return "", str(e), -1

    def put_file(self, local_path: str, remote_path: str):
        """Upload a local file to the remote robot host via SFTP."""
        with self.lock:
            if not self.client or not self.connected:
                if not self.connect():
                    raise ConnectionError("SSH Not Connected")

            sftp = self.client.open_sftp()
            try:
                logger.info(f"SFTP: Uploading {local_path} to {remote_path}...")
                sftp.put(local_path, remote_path)
            finally:
                sftp.close()

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            self.connected = False
