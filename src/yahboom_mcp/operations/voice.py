from fastmcp import Context
import logging
import time

logger = logging.getLogger("yahboom-mcp.operations.voice")

async def execute(
    ctx: Context | None = None,
    operation: str = "",
    param1: str | float | None = None,
    param2: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    Execute AI Voice Module operations via SSH Serial Bridge.
    Supported Ops:
      say           → Speak text (param1)
      play          → Play a built-in sound ID (param1)
      cmd           → Send raw serial string (param1)
      get_status    → Returns active/detected status
    """
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(f"Voice: {operation}", extra={"correlation_id": correlation_id})

    from ..state import _state
    ssh = _state.get("ssh_bridge")

    if not ssh or not ssh.connected:
        return {
            "success": False,
            "operation": operation,
            "error": "SSH bridge not connected",
            "status": "offline"
        }

    # Auto-discovery of the Speech Module port (CH340: 1a86:7522)
    # We scan /dev/ttyUSB* for the correct signature or just try the first one if only one exists.
    # For now, we'll use a robust python-serial snippet.

    if operation == "say":
        text = str(param1) if param1 else "Hello"
        if text == "PARDON":
            text = "Pardon me! Boomy patrol in progress."
        
        # SOTA v12.0 Robust Script Execution (Single-line Base64)
        # Locked to verified serial port: /dev/ttyUSB0
        import base64
        script = f"""
import sys, os, subprocess, serial
try:
    # Use the hardware-verified serial port for the speech module
    port = '/dev/ttyUSB0'
    text = "{text}"
    with serial.Serial(port, 115200, timeout=1) as ser:
        # Yahboom Speech Protocol: $say,text#
        ser.write(f"$say,{{text}}#".encode())
        print("VERIFIED")
except Exception as e:
    print(f"ERROR:{{e}}")
"""
        encoded_script = base64.b64encode(script.encode()).decode()
        shell_cmd = f"python3 -c \"import base64; exec(base64.b64decode('{encoded_script}').decode())\""
        
        out, err, code = ssh.execute(shell_cmd)
        verified = "VERIFIED" in out
        result = {
            "success": verified,
            "status": "applied" if verified else "failed",
            "log": out if verified else f"Out: {out}\nErr: {err}"
        }
    
    elif operation == "play":
        sound_id = int(param1) if param1 else 1
        py_cmd = f"""
import serial
ports = ['/dev/ttyUSB0', '/dev/ttyUSB1']
for p in ports:
    try:
        with serial.Serial(p, 115200, timeout=1) as ser:
            cmd = f"$play,{sound_id}#".encode('utf-8')
            ser.write(cmd)
            break
    except: continue
"""
        ssh.execute(f"python3 -c \"{py_cmd}\"")
        result = {"played_id": sound_id}

    elif operation == "get_status":
        # Check if the USB device is present
        usb_out, _, _ = ssh.execute("lsusb")
        active = "1a86:7522" in usb_out or "1a86:7523" in usb_out
        result = {"active": active, "hw_id": "1a86:7522"}

    else:
        result = {"error": f"Unknown voice operation: {operation}"}

    return {
        "success": result.get("success", False) if "error" not in result else False,
        "operation": operation,
        "status": result.get("status", "unknown"),
        "log": result.get("log", ""),
        "result": result,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
    }
