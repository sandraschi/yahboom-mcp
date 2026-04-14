import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from yahboom_mcp.core.ssh_bridge import SSHBridge


async def check_ollama():
    host = "192.168.1.11"
    password = "yahboom"
    ssh = SSHBridge(host, password=password)

    # Try connect
    if not await asyncio.to_thread(ssh.connect):
        print("SSH Connection failed")
        return

    # Check ollama models
    out, err, code = await ssh.execute("ollama list")
    print(f"Ollama Models:\n{out}")
    if code != 0:
        print(f"Error: {err}")

    ssh.close()

if __name__ == "__main__":
    asyncio.run(check_ollama())
