from fastmcp import Context
import logging
import time

logger = logging.getLogger("yahboom-mcp.operations.voice")

# Known Yahboom AI Voice Module USB IDs
_VOICE_USB_IDS = ["1a86:7522", "1a86:7523", "10c4:ea60"]
_VOICE_DEVICES = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0"]


def _find_voice_device_cmd() -> str:
    """Shell snippet that returns the voice module device path or 'NOT_FOUND'."""
    ids_grep = "|".join(_VOICE_USB_IDS)
    return (
        f"python3 -c \""
        f"import subprocess, re; "
        f"lsusb = subprocess.check_output(['lsusb'], text=True); "
        f"found = any(id in lsusb for id in {_VOICE_USB_IDS!r}); "
        f"dev = None; "
        f"import glob; "
        f"[setattr(__import__('builtins'), '_d', d) for d in {_VOICE_DEVICES!r} if __import__('os').path.exists(d)]; "
        f"dev = getattr(__import__('builtins'), '_d', None); "
        f"print(dev if dev and found else 'NOT_FOUND')"
        f"\""
    )


def _serial_cmd(device: str, body: str) -> str:
    """Build a python3 one-liner that opens a serial port and runs body."""
    import shlex
    script = f"""
import serial, time, sys
try:
    with serial.Serial('{device}', 9600, timeout=2) as ser:
        time.sleep(0.15)
{body}
        print("OK")
except Exception as e:
    print(f"ERROR:{{e}}", file=sys.stderr)
    sys.exit(1)
"""
    return f"python3 -c {shlex.quote(script)}"


async def _resolve_device(ssh) -> str | None:
    """Return the voice module device path, or None if not found."""
    out, _, _ = await ssh.execute(_find_voice_device_cmd())
    dev = out.strip()
    if dev and dev != "NOT_FOUND" and dev.startswith("/dev/"):
        return dev
    # Brute-force: try each device path
    for d in _VOICE_DEVICES:
        exists_out, _, _ = await ssh.execute(f"test -e {d} && echo exists || echo missing")
        if "exists" in exists_out:
            logger.warning(f"Voice: USB ID not matched but {d} exists — trying it")
            return d
    return None


async def execute(
    ctx: Context | None = None,
    operation: str = "",
    param1: str | float | None = None,
    param2: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    AI Voice Module operations via SSH serial bridge.

    Operations:
      get_status  → Probe USB, return detected device path
      say         → TTS speak (param1=text)
      play        → Play built-in sound ID (param1=1-10)
      volume      → Set volume (param1=0-30)

    The module is detected by USB VID:PID (1a86:7522/7523 or 10c4:ea60).
    Falls back to probing /dev/ttyUSB0, /dev/ttyUSB1, /dev/ttyACM0.
    """
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(f"Voice: {operation}", extra={"correlation_id": correlation_id})

    from ..state import _state
    ssh = _state.get("ssh")

    if not ssh or not ssh.connected:
        return {
            "success": False,
            "operation": operation,
            "error": "SSH bridge not connected",
            "status": "offline",
            "correlation_id": correlation_id,
        }

    result: dict = {}

    # ── get_status ───────────────────────────────────────────────────────────
    if operation == "get_status":
        lsusb_out, _, _ = await ssh.execute("lsusb 2>/dev/null")
        matched_id = next((vid for vid in _VOICE_USB_IDS if vid in lsusb_out), None)

        device = await _resolve_device(ssh)
        result = {
            "success": True,
            "detected": device is not None,
            "device": device,
            "usb_id_matched": matched_id,
            "lsusb_snippet": lsusb_out[:300],
            "note": (
                f"Voice module found at {device}" if device
                else "Voice module NOT detected. Check USB connection and 'lsusb' output."
            ),
        }

    # ── say ──────────────────────────────────────────────────────────────────
    elif operation == "say":
        text = str(param1) if param1 else "Hello, I am Boomy."
        device = await _resolve_device(ssh)
        if not device:
            result = {
                "success": False,
                "status": "device_not_found",
                "error": "Voice module not detected. Check USB cable.",
            }
        else:
            # Protocol: $say,<text># at 9600 baud
            body = f"        ser.write('$say,{text}#'.encode('utf-8'))\n        time.sleep(0.1)"
            out, err, code = await ssh.execute(_serial_cmd(device, body))
            ok = "OK" in out
            result = {
                "success": ok,
                "device": device,
                "text": text,
                "status": "spoken" if ok else "failed",
                "log": err if not ok else "",
            }

    # ── play ─────────────────────────────────────────────────────────────────
    elif operation == "play":
        sound_id = max(1, min(10, int(param1))) if param1 is not None else 1
        device = await _resolve_device(ssh)
        if not device:
            result = {"success": False, "error": "Voice module not detected"}
        else:
            body = f"        ser.write(f'$play,{sound_id}#'.encode('utf-8'))\n        time.sleep(0.1)"
            out, err, code = await ssh.execute(_serial_cmd(device, body))
            ok = "OK" in out
            result = {"success": ok, "device": device, "sound_id": sound_id}

    # ── volume ───────────────────────────────────────────────────────────────
    elif operation == "volume":
        level = max(0, min(30, int(param1))) if param1 is not None else 20
        device = await _resolve_device(ssh)
        if not device:
            result = {"success": False, "error": "Voice module not detected"}
        else:
            body = f"        ser.write(f'$VOL,{level}#'.encode('utf-8'))\n        time.sleep(0.1)"
            out, err, code = await ssh.execute(_serial_cmd(device, body))
            ok = "OK" in out
            result = {"success": ok, "device": device, "volume": level}

    else:
        result = {"success": False, "error": f"Unknown voice operation: {operation}"}

    return {
        "success": result.get("success", False),
        "operation": operation,
        "status": result.get("status", "unknown"),
        "log": result.get("log", ""),
        "result": result,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
    }
