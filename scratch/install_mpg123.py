import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from yahboom_mcp.core.ssh_bridge import SSHBridge

async def install_mpg123():
    host = "192.168.1.11"
    password = "yahboom"
    ssh = SSHBridge(host, password=password)
    
    # Try connect
    if not await asyncio.to_thread(ssh.connect):
        print("SSH Connection failed")
        return

    # Install mpg123
    print("Updating packages and installing mpg123...")
    out, err, code = await ssh.execute("sudo apt-get update && sudo apt-get install -y mpg123")
    print(f"Result Code: {code}")
    if out: print(f"Output: {out}")
    if err: print(f"Error: {err}")
    
    ssh.close()

if __name__ == "__main__":
    asyncio.run(install_mpg123())
