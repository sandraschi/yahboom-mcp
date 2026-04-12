import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from yahboom_mcp.operations import voice
from yahboom_mcp.core.ssh_bridge import SSHBridge
from yahboom_mcp.state import _state

async def run_integration_test():
    host = "192.168.1.11"
    password = "yahboom"
    ssh = SSHBridge(host, password=password)
    
    if not await asyncio.to_thread(ssh.connect):
        print("SSH Connection failed")
        return
    
    _state["ssh"] = ssh

    print("\n--- TEST 1: Beep (Loudness Check) ---")
    res = await voice.execute(operation="play_beep")
    print(f"Beep Result: {res}")

    print("\n--- TEST 2: LLM Pipe (Gemma 3) ---")
    res = await voice.execute(operation="chat_and_say", param1="Say hello to the industrial robot fleet.")
    print(f"Chat Result: {res}")

    print("\n--- TEST 3: Media Playback (Etta James) ---")
    # This might take a while due to upload
    path = "E:\\Multimedia Files\\Music - Blues\\James, Etta\\Her Best (1997)\\James, Etta - Her Best (1997) - 16 - I'd Rather Go Blind.mp3"
    res = await voice.execute(operation="play_file", param1=path)
    print(f"Media Result: {res}")

    ssh.close()

if __name__ == "__main__":
    # Ensure environment vars
    os.environ["YAHBOOM_VOICE_DEVICE"] = "/dev/ttyUSB0"
    # Force UTF-8 for windows terminal
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    asyncio.run(run_integration_test())
