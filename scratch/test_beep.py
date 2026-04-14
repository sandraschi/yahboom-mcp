import asyncio
import os
import shlex
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from yahboom_mcp.core.ssh_bridge import SSHBridge


async def test_beep():
    host = "192.168.1.11"
    password = "yahboom"
    ssh = SSHBridge(host, password=password)

    # Try connect
    if not await asyncio.to_thread(ssh.connect):
        print("SSH Connection failed")
        return

    # Find device (typical is /dev/ttyUSB0)
    device = "/dev/ttyUSB0"
    baud = 9600

    # Python script to write to serial
    body = f"""
import serial, time, sys
try:
    with serial.Serial({device!r}, {baud}, timeout=2) as ser:
        time.sleep(0.1)
        ser.write(b"$VOL,25#")
        time.sleep(0.1)
        ser.write(b"$play,1#")
        time.sleep(0.1)
        ser.flush()
    print("OK")
except Exception as exc:
    print(f"ERROR: {{exc}}", file=sys.stderr)
"""
    cmd = f"python3 -c {shlex.quote(body)}"
    out, err, _code = await ssh.execute(cmd)
    print(f"Result: {out}")
    if err:
        print(f"Error: {err}")

    ssh.close()

if __name__ == "__main__":
    asyncio.run(test_beep())
