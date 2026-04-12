import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from yahboom_mcp.core.ssh_bridge import SSHBridge

async def check_tools():
    host = "192.168.1.11"
    password = "yahboom"
    ssh = SSHBridge(host, password=password)
    
    # Try connect
    if not await asyncio.to_thread(ssh.connect):
        print("SSH Connection failed")
        return

    # Check tools
    out, err, code = await ssh.execute("which mpg123 || which ffplay || which cvlc || which aplay")
    print(f"Tool Path: {out}")
    
    ssh.close()

if __name__ == "__main__":
    asyncio.run(check_tools())
