from fastmcp import Context
import logging
import os
import time
import asyncio

logger = logging.getLogger("yahboom_mcp.operations.voice")

# Known Yahboom / common USB-UART chips for the AI voice hat (lsusb & udev ID_VENDOR_ID:ID_MODEL_ID)
_DEFAULT_VOICE_USB_IDS = ["1a86:7522", "1a86:7523", "10c4:ea60"]


def _voice_usb_ids() -> list[str]:
    ids = list(_DEFAULT_VOICE_USB_IDS)
    extra = os.environ.get("YAHBOOM_VOICE_USB_IDS", "").strip()
    if not extra:
        return ids
    for part in extra.split(","):
        p = part.strip().lower().replace(" ", "")
        if p and p not in ids and ":" in p:
            ids.append(p)
    return ids


def _find_voice_device_remote_cmd() -> str:
    """Single Python script on the Pi: scan all tty devices, match udev VID:PID to voice list."""
    import shlex

    ids = _voice_usb_ids()
    ids_repr = repr(ids)
    inner = f"""import glob, os, re, subprocess, sys
IDS = set({ids_repr})
paths = []
v = "/dev/ttyVOICE"
if os.path.exists(v):
    paths.append(v)
for pat in ("/dev/ttyUSB*", "/dev/ttyACM*"):
    paths.extend(sorted(glob.glob(pat)))
seen = set()
for tty in paths:
    if tty in seen or not os.path.exists(tty):
        continue
    seen.add(tty)
    try:
        u = subprocess.check_output(
            ["udevadm", "info", "-q", "property", "-n", tty],
            text=True,
            timeout=5,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        continue
    vm = re.search(r"ID_VENDOR_ID=(\\w+)", u)
    pm = re.search(r"ID_MODEL_ID=(\\w+)", u)
    if not vm or not pm:
        continue
    key = f"{{vm.group(1).lower()}}:{{pm.group(1).lower()}}"
    if key in IDS:
        print(tty)
        sys.exit(0)
print("NOT_FOUND")
"""
    return f"python3 -c {shlex.quote(inner)}"


def _serial_cmd(device: str, body: str, baud: int) -> str:
    """Build a python3 one-liner that opens a serial port and runs body."""
    import shlex

    script = f"""
import serial, time, sys
try:
    with serial.Serial({device!r}, {baud}, timeout=2) as ser:
        time.sleep(0.15)
{body}
        print("OK")
except Exception as e:
    print(f"ERROR:{{e}}", file=sys.stderr)
    sys.exit(1)
"""
    return f"python3 -c {shlex.quote(script)}"


def _pyserial_probe_cmd() -> str:
    import shlex

    inner = "import serial; print('PY_SERIAL_OK')"
    return f"python3 -c {shlex.quote(inner)}"


async def _resolve_device(ssh) -> tuple[str | None, str]:
    """
    Return (device_path or None, diagnostic_note).
    YAHBOOM_VOICE_DEVICE on the MCP host forces a path if that device exists on the Pi.
    """
    forced = os.environ.get("YAHBOOM_VOICE_DEVICE", "").strip()
    if forced:
        out, _, _ = await ssh.execute(
            f"test -e {__import__('shlex').quote(forced)} && echo exists || echo missing"
        )
        if "exists" in out:
            logger.info("Voice: using YAHBOOM_VOICE_DEVICE=%s", forced)
            return forced, "Using YAHBOOM_VOICE_DEVICE override."
        return None, f"YAHBOOM_VOICE_DEVICE={forced} not found on robot."

    out, err, _ = await ssh.execute(_find_voice_device_remote_cmd())
    line = (out or "").strip().splitlines()
    cand = line[-1].strip() if line else ""
    if cand.startswith("/dev/"):
        return cand, ""

    note = (
        "No tty matched voice USB IDs in udev. "
        "Set YAHBOOM_VOICE_DEVICE=/dev/ttyUSBn on the MCP host if needed, "
        "or YAHBOOM_VOICE_USB_IDS=vid:pid for nonstandard chips."
    )
    if (err or "").strip():
        note += f" Remote stderr: {(err or '')[:200]}"
    return None, note


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

    Env (MCP host): YAHBOOM_VOICE_DEVICE, YAHBOOM_VOICE_USB_IDS (comma-separated vid:pid),
    YAHBOOM_VOICE_BAUD (default 9600).
    """
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info("Voice: %s", operation, extra={"correlation_id": correlation_id})

    from ..state import _state

    ssh = _state.get("ssh")
    baud = int(os.environ.get("YAHBOOM_VOICE_BAUD", "9600"))

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
        ids = _voice_usb_ids()
        matched_id = next((vid for vid in ids if vid in lsusb_out), None)

        py_ok = "PY_SERIAL_OK" in (await ssh.execute(_pyserial_probe_cmd()))[0]

        device, resolve_note = await _resolve_device(ssh)
        result = {
            "success": True,
            "detected": device is not None,
            "device": device,
            "usb_id_matched": matched_id,
            "lsusb_snippet": lsusb_out[:300],
            "pyserial_ok": py_ok,
            "resolve_note": resolve_note or None,
            "note": (
                f"Voice module found at {device}"
                if device
                else (
                    "Voice module not detected. "
                    + (resolve_note or "")
                    + (" Install pyserial on the Pi: pip3 install pyserial" if not py_ok else "")
                )
            ),
        }

    # ── say ──────────────────────────────────────────────────────────────────
    elif operation == "say":
        text = str(param1) if param1 else "Hello, I am Boomy."
        device, resolve_note = await _resolve_device(ssh)
        if not device:
            result = {
                "success": False,
                "status": "device_not_found",
                "error": resolve_note or "Voice module not detected.",
                "log": resolve_note or "",
            }
        else:
            import base64
            import shlex

            b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
            inner = f"""
import base64, serial, time, sys
try:
    plain = base64.b64decode({b64!r}).decode("utf-8")
    with serial.Serial({device!r}, {baud}, timeout=2) as ser:
        time.sleep(0.15)
        payload = ("$say," + plain + "#").encode("utf-8", errors="replace")
        ser.write(payload)
        ser.flush()
        time.sleep(0.1)
    print("OK")
except Exception as e:
    print(f"ERROR:{{e}}", file=sys.stderr)
    sys.exit(1)
"""
            cmd = f"python3 -c {shlex.quote(inner)}"
            out, err, code = await ssh.execute(cmd)
            ok = "OK" in out
            err_s = (err or "").strip()
            out_s = (out or "").strip()
            hint = ""
            if not ok:
                if "No module named 'serial'" in err_s or "serial" in err_s.lower():
                    hint = " On the Pi: pip3 install pyserial && sudo usermod -aG dialout pi"
                elif "Permission denied" in err_s or "permission" in err_s.lower():
                    hint = " Add user to dialout: sudo usermod -aG dialout pi (then re-login)."
            result = {
                "success": ok,
                "device": device,
                "text": text,
                "status": "spoken" if ok else "failed",
                "log": err_s if not ok else "",
                "stdout": out_s if not ok else "",
                "hint": hint,
            }

    # ── play ─────────────────────────────────────────────────────────────────
    elif operation == "play":
        sound_id = max(1, min(10, int(param1))) if param1 is not None else 1
        device, resolve_note = await _resolve_device(ssh)
        if not device:
            result = {
                "success": False,
                "error": resolve_note or "Voice module not detected",
                "log": resolve_note or "",
            }
        else:
            body = f"        ser.write(f'$play,{sound_id}#'.encode('utf-8'))\n        time.sleep(0.1)\n        ser.flush()"
            out, err, code = await ssh.execute(_serial_cmd(device, body, baud))
            ok = "OK" in out
            result = {
                "success": ok,
                "device": device,
                "sound_id": sound_id,
                "log": (err or "").strip() if not ok else "",
            }

    # ── play_beep ────────────────────────────────────────────────────────────
    elif operation == "play_beep":
        device, resolve_note = await _resolve_device(ssh)
        if not device:
            result = {"success": False, "error": resolve_note or "Voice module not detected"}
        else:
            # Set volume to 25 then play sound 1
            body = (
                "        ser.write(b'$VOL,25#')\n"
                "        time.sleep(0.1)\n"
                "        ser.write(b'$play,1#')\n"
                "        time.sleep(0.1)\n"
                "        ser.flush()"
            )
            out, err, code = await ssh.execute(_serial_cmd(device, body, baud))
            result = {"success": "OK" in out, "device": device, "log": err}

    # ── play_file ────────────────────────────────────────────────────────────
    elif operation == "play_file":
        local_path = str(param1) if param1 else ""
        if not local_path or not os.path.exists(local_path):
            result = {"success": False, "error": f"Local file not found: {local_path}"}
        else:
            remote_tmp = f"/tmp/{os.path.basename(local_path)}"
            # 1. Upload
            try:
                await asyncio.to_thread(ssh.put_file, local_path, remote_tmp)
                # 2. Play via Card 2 (USB Audio)
                # We use mpg123 -D hw:2,0 (Card 2, Device 0)
                # -q for quiet, -m for mono fallback
                import shlex
                q_tmp = shlex.quote(remote_tmp)
                cmd = f"mpg123 -q -D hw:2,0 {q_tmp}"
                out, err, code = await ssh.execute(cmd)
                result = {
                    "success": code == 0,
                    "local_path": local_path,
                    "remote_path": remote_tmp,
                    "exit_code": code,
                    "log": (err or "").strip()
                }
            except Exception as e:
                result = {"success": False, "error": f"Media playback failed: {e}"}

    # ── chat_and_say ─────────────────────────────────────────────────────────
    elif operation == "chat_and_say":
        user_text = str(param1) if param1 else "Tell me something."
        # Call local Ollama on the Pi via SSH
        import json
        import shlex
        
        prompt = f"Give a short, friendly, robot-like response to: {user_text}. Max 20 words."
        payload_data = {"model": "gemma3:1b", "prompt": prompt, "stream": False}
        payload_json = json.dumps(payload_data)
        
        cmd = f"curl -s -X POST http://localhost:11434/api/generate -d {shlex.quote(payload_json)}"
        out, err, _ = await ssh.execute(cmd)
        
        try:
            resp = json.loads(out)
            llm_text = resp.get("response", "I am thinking.")
            # Now speak it
            speak_res = await execute(ctx, operation="say", param1=llm_text)
            result = {
                "success": speak_res["success"],
                "input": user_text,
                "response": llm_text,
                "say_result": speak_res
            }
        except Exception as e:
            result = {"success": False, "error": f"LLM parsing failed: {e}", "raw": out}

    # ── volume ───────────────────────────────────────────────────────────────
    elif operation == "volume":
        level = max(0, min(30, int(param1))) if param1 is not None else 20
        device, resolve_note = await _resolve_device(ssh)
        if not device:
            result = {
                "success": False,
                "error": resolve_note or "Voice module not detected",
                "log": resolve_note or "",
            }
        else:
            body = f"        ser.write(f'$VOL,{level}#'.encode('utf-8'))\n        time.sleep(0.1)\n        ser.flush()"
            out, err, code = await ssh.execute(_serial_cmd(device, body, baud))
            ok = "OK" in out
            result = {
                "success": ok,
                "device": device,
                "volume": level,
                "log": (err or "").strip() if not ok else "",
            }

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
