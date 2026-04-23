"""
Yahboom AI Voice Module — correct implementation for CSK4002 / CI1302 chip.

Hardware reality
----------------
The Raspbot V2 voice module is a CSK4002 or CI1302 ASR+playback module.
It is NOT a TTS synthesiser — it cannot speak arbitrary text from a serial command.

What it CAN do over serial:
  - Trigger playback of a preset phrase by ID (1–85) using a 3-byte binary packet
  - Send recognition events (same 3-byte framing) when a wake word + command is heard

Binary packet format (both directions):
  [0xA5, byte_value, ~byte_value & 0xFF]
  Header 0xA5, payload byte, bitwise-NOT checksum of payload byte.

Baud rate: 115200 (not 9600 — that is the SYN6288 chip, which this is not).

Arbitrary TTS
-------------
For saying arbitrary text we use espeak-ng on the Pi host, piped to the ALSA
audio device.  espeak-ng is typically pre-installed on Pi OS; if not:
  sudo apt-get install espeak-ng

Device path
-----------
The voice module USB serial device should have a stable udev symlink /dev/ttyVOICE
(see docs/hardware/HARDWARE_DIAGNOSIS_VOICE_I2C.md).  Falls back to ttyUSB1,
ttyUSB0, ttyACM0 in that order if the symlink does not exist.

Override with env var YAHBOOM_VOICE_DEVICE on the MCP host.
"""

import logging
import os
import shlex
import time

from fastmcp import Context

logger = logging.getLogger("yahboom-mcp.operations.voice")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Baud rate for CSK4002/CI1302 — 115200, not 9600
_BAUD = int(os.environ.get("YAHBOOM_VOICE_BAUD", "115200"))

# USB VID:PID pairs for the CH340 and CP2102 USB-UART bridges used on Yahboom
# voice modules.  Used only for device-discovery scanning.
_VOICE_USB_IDS = {"1a86:7522", "1a86:7523", "10c4:ea60", "0403:6001"}

# Candidate device paths tried in order when YAHBOOM_VOICE_DEVICE is not set.
_CANDIDATE_DEVICES = [
    "/dev/ttyVOICE",  # udev symlink (preferred — see hardware doc)
    "/dev/ttyUSB1",  # second USB serial (Rosmaster is usually ttyUSB0)
    "/dev/ttyUSB0",
    "/dev/ttyACM0",
]

# Max preset phrase ID on the module firmware
_MAX_PHRASE_ID = 85


# ---------------------------------------------------------------------------
# Protocol helpers
# ---------------------------------------------------------------------------


def _make_packet(value: int) -> bytes:
    """
    Build a 3-byte Yahboom voice module command packet.
      [0xA5, value, ~value & 0xFF]
    """
    v = value & 0xFF
    return bytes([0xA5, v, (~v) & 0xFF])


# ---------------------------------------------------------------------------
# Device resolution
# ---------------------------------------------------------------------------


async def _resolve_device(ssh) -> tuple[str | None, str]:
    """
    Return (device_path, note).

    Priority:
      1. YAHBOOM_VOICE_DEVICE env var (path must exist on the Pi)
      2. /dev/ttyVOICE udev symlink
      3. Scan ttyUSB*/ttyACM* and match against known USB VID:PIDs via udevadm
    """
    forced = os.environ.get("YAHBOOM_VOICE_DEVICE", "").strip()
    if forced:
        out, _, _ = await ssh.execute(f"test -e {shlex.quote(forced)} && echo exists || echo missing")
        if "exists" in (out or ""):
            logger.info("Voice: using YAHBOOM_VOICE_DEVICE=%s", forced)
            return forced, "Using YAHBOOM_VOICE_DEVICE override."
        return None, f"YAHBOOM_VOICE_DEVICE={forced} not found on robot."

    for path in _CANDIDATE_DEVICES:
        out, _, _ = await ssh.execute(f"test -e {shlex.quote(path)} && echo exists || echo missing")
        if "exists" in (out or ""):
            if path == "/dev/ttyUSB0":
                ros_out, _, _ = await ssh.execute("test -e /dev/ttyROSMASTER && echo exists || echo missing")
                if "missing" in (ros_out or ""):
                    logger.warning(
                        "Voice: /dev/ttyROSMASTER udev symlink not set up — "
                        "ttyUSB0 may be the Rosmaster UART, not the voice module. "
                        "See docs/hardware/HARDWARE_DIAGNOSIS_VOICE_I2C.md."
                    )
            return path, ""

    ids_repr = repr(_VOICE_USB_IDS)
    scan_script = f"""
import glob, os, re, subprocess, sys
IDS = set({ids_repr})
for pat in ("/dev/ttyUSB*", "/dev/ttyACM*"):
    for tty in sorted(glob.glob(pat)):
        try:
            u = subprocess.check_output(
                ["udevadm", "info", "-q", "property", "-n", tty],
                text=True, timeout=5, stderr=subprocess.DEVNULL,
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
    out, _, _ = await ssh.execute(f"python3 -c {shlex.quote(scan_script)}")
    cand = (out or "").strip().splitlines()
    path = cand[-1].strip() if cand else ""
    if path.startswith("/dev/"):
        return path, "Found via udev VID:PID scan."

    return None, (
        "Voice module not found. Set up /dev/ttyVOICE udev symlink "
        "(see docs/hardware/HARDWARE_DIAGNOSIS_VOICE_I2C.md) or set "
        "YAHBOOM_VOICE_DEVICE=/dev/ttyUSBn on the MCP host."
    )


# ---------------------------------------------------------------------------
# SSH command builders
# ---------------------------------------------------------------------------


def _play_cmd(device: str, packet: bytes) -> str:
    """Open serial port on Pi and send a binary packet."""
    packet_list = list(packet)
    script = f"""
import serial, time, sys
try:
    with serial.Serial({device!r}, {_BAUD}, timeout=2) as ser:
        time.sleep(0.05)
        ser.write(bytes({packet_list!r}))
        ser.flush()
        time.sleep(0.1)
    print("OK")
except Exception as e:
    print(f"ERROR:{{e}}", file=sys.stderr)
    sys.exit(1)
"""
    return f"python3 -c {shlex.quote(script)}"


def _listen_cmd(device: str, timeout_s: float = 5.0) -> str:
    """
    Block and read one recognition-event packet from the voice module.
    Prints the decimal command ID on success, or TIMEOUT / ERROR:<msg>.
    """
    script = f"""
import serial, time, sys
deadline = time.time() + {timeout_s}
try:
    with serial.Serial({device!r}, {_BAUD}, timeout=0.2) as ser:
        buf = bytearray()
        while time.time() < deadline:
            chunk = ser.read(16)
            if chunk:
                buf.extend(chunk)
            while len(buf) >= 3:
                if buf[0] != 0xA5:
                    buf.pop(0)
                    continue
                if buf[2] == ((~buf[1]) & 0xFF):
                    print(buf[1])
                    sys.exit(0)
                buf.pop(0)
    print("TIMEOUT")
except Exception as e:
    print(f"ERROR:{{e}}", file=sys.stderr)
    sys.exit(1)
"""
    return f"python3 -c {shlex.quote(script)}"


def _say_cmd(text: str, voice: str, speed: int, pitch: int) -> str:
    """Speak arbitrary text via espeak-ng on the Pi host."""
    return f"espeak-ng -v {shlex.quote(voice)} -s {speed} -p {pitch} {shlex.quote(text)} 2>&1"


def _check_espeak_cmd() -> str:
    return "command -v espeak-ng && espeak-ng --version 2>&1 | head -1 || echo NOT_FOUND"


def _check_pyserial_cmd() -> str:
    return "python3 -c \"import serial; print('OK')\" 2>/dev/null || echo NOT_FOUND"


def _set_volume_cmd(level: int) -> str:
    return f"amixer -q sset Master {level}% 2>&1 || amixer -q sset PCM {level}% 2>&1"


# ---------------------------------------------------------------------------
# Main execute
# ---------------------------------------------------------------------------


async def execute(
    ctx: Context | None = None,
    operation: str = "",
    param1: str | float | None = None,
    param2: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    Yahboom AI Voice Module operations.

    Operations
    ----------
    get_status
        Probe voice module device, pyserial, and espeak-ng availability.

    play  (param1 = phrase ID 1-85)
        Trigger a preset phrase via 3-byte binary packet [0xA5, id, ~id].

    play_beep
        Play phrase ID 1.  Alias for play(1).

    listen  (param1 = timeout seconds, default 5)
        Wait for a voice recognition event from the module.
        Returns the recognised command ID (int).

    say  (param1 = text, payload = {voice, speed, pitch})
        Speak arbitrary text via espeak-ng on the Pi.
        NOTE: outputs to Pi ALSA audio, not the voice module speaker.
        Env overrides: YAHBOOM_ESPEAK_VOICE, YAHBOOM_ESPEAK_SPEED, YAHBOOM_ESPEAK_PITCH

    say_file  (param1 = local absolute path to .mp3/.wav)
        Upload to Pi /tmp/ and play via mpg123 (mp3) or aplay (wav).

    chat_and_say  (param1 = prompt text, param2 = ollama model, default gemma3:1b)
        Ask Ollama on the Pi, then speak the response via espeak-ng.

    volume  (param1 = 0-100)
        Set Pi ALSA master volume.  Does not affect the module's internal speaker.
    """
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info("Voice: %s", operation, extra={"correlation_id": correlation_id})

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

    espeak_voice = os.environ.get("YAHBOOM_ESPEAK_VOICE", "en")
    espeak_speed = int(os.environ.get("YAHBOOM_ESPEAK_SPEED", "150"))
    espeak_pitch = int(os.environ.get("YAHBOOM_ESPEAK_PITCH", "50"))

    result: dict = {}

    # ── get_status ──────────────────────────────────────────────────────────
    if operation == "get_status":
        device, resolve_note = await _resolve_device(ssh)
        ps_out, _, _ = await ssh.execute(_check_pyserial_cmd())
        pyserial_ok = "OK" in (ps_out or "")
        esp_out, _, _ = await ssh.execute(_check_espeak_cmd())
        espeak_ok = "NOT_FOUND" not in (esp_out or "")
        result = {
            "success": True,
            "device": device,
            "device_found": device is not None,
            "resolve_note": resolve_note or None,
            "pyserial_ok": pyserial_ok,
            "espeak_ok": espeak_ok,
            "espeak_version": (esp_out or "").strip() if espeak_ok else None,
            "baud": _BAUD,
            "protocol": "binary [0xA5, id, ~id] — CSK4002/CI1302",
            "note": _status_note(device, pyserial_ok, espeak_ok),
        }

    # ── play / play_beep ────────────────────────────────────────────────────
    elif operation in ("play", "play_beep"):
        phrase_id = 1 if operation == "play_beep" else max(1, min(_MAX_PHRASE_ID, int(param1 or 1)))
        device, resolve_note = await _resolve_device(ssh)
        if not device:
            result = {
                "success": False,
                "error": resolve_note or "Voice module not found",
                "hint": "Set up udev symlink /dev/ttyVOICE or set YAHBOOM_VOICE_DEVICE",
            }
        else:
            ps_out, _, _ = await ssh.execute(_check_pyserial_cmd())
            if "OK" not in (ps_out or ""):
                result = {
                    "success": False,
                    "error": "pyserial not installed on robot Pi",
                    "hint": "pip3 install pyserial",
                }
            else:
                packet = _make_packet(phrase_id)
                out, err, code = await ssh.execute(_play_cmd(device, packet))
                ok = code == 0 and "OK" in (out or "")
                result = {
                    "success": ok,
                    "device": device,
                    "phrase_id": phrase_id,
                    "packet_hex": packet.hex(),
                    "status": "played" if ok else "failed",
                    "log": (err or "").strip() if not ok else "",
                }
                if not ok:
                    if "No module named 'serial'" in (err or ""):
                        result["hint"] = "pip3 install pyserial on the robot Pi"
                    elif "Permission denied" in (err or ""):
                        result["hint"] = "sudo usermod -aG dialout pi (then re-login)"

    # ── listen ──────────────────────────────────────────────────────────────
    elif operation == "listen":
        try:
            timeout = float(param1) if param1 else 5.0
        except (TypeError, ValueError):
            timeout = 5.0
        device, resolve_note = await _resolve_device(ssh)
        if not device:
            result = {"success": False, "error": resolve_note or "Voice module not found"}
        else:
            out, err, code = await ssh.execute(_listen_cmd(device, timeout))
            out_s = (out or "").strip()
            if out_s == "TIMEOUT":
                result = {"success": True, "command_id": None, "status": "timeout"}
            elif out_s.startswith("ERROR"):
                result = {"success": False, "error": out_s, "log": (err or "").strip()}
            else:
                try:
                    result = {"success": True, "command_id": int(out_s), "status": "recognised"}
                except ValueError:
                    result = {"success": False, "error": f"Unexpected output: {out_s!r}"}

    # ── say ─────────────────────────────────────────────────────────────────
    elif operation == "say":
        text = str(param1).strip() if param1 else "Hello, I am Boomy."
        if not text:
            result = {"success": False, "error": "Empty text"}
        else:
            chk_out, _, _ = await ssh.execute(_check_espeak_cmd())
            if "NOT_FOUND" in (chk_out or ""):
                result = {
                    "success": False,
                    "error": "espeak-ng not installed on robot Pi",
                    "hint": "sudo apt-get install espeak-ng",
                }
            else:
                v = str((payload or {}).get("voice", espeak_voice))
                s = int((payload or {}).get("speed", espeak_speed))
                p = int((payload or {}).get("pitch", espeak_pitch))
                out, err, code = await ssh.execute(_say_cmd(text, v, s, p))
                ok = code == 0
                result = {
                    "success": ok,
                    "text": text,
                    "voice": v,
                    "status": "spoken" if ok else "failed",
                    "log": ((out or "") + (err or "")).strip() if not ok else "",
                }

    # ── say_file ─────────────────────────────────────────────────────────────
    elif operation == "say_file":
        import asyncio

        local_path = str(param1).strip() if param1 else ""
        if not local_path or not os.path.exists(local_path):
            result = {"success": False, "error": f"Local file not found: {local_path!r}"}
        else:
            remote_tmp = f"/tmp/{os.path.basename(local_path)}"
            try:
                await asyncio.to_thread(ssh.put_file, local_path, remote_tmp)
                ext = os.path.splitext(local_path)[1].lower()
                play_cmd = (
                    f"mpg123 -q {shlex.quote(remote_tmp)}" if ext == ".mp3" else f"aplay -q {shlex.quote(remote_tmp)}"
                )
                out, err, code = await ssh.execute(play_cmd)
                result = {
                    "success": code == 0,
                    "local_path": local_path,
                    "remote_path": remote_tmp,
                    "exit_code": code,
                    "log": (err or "").strip(),
                }
            except Exception as e:
                result = {"success": False, "error": f"File playback failed: {e}"}

    # ── chat_and_say ─────────────────────────────────────────────────────────
    elif operation == "chat_and_say":
        import json

        user_text = str(param1).strip() if param1 else "Tell me something."
        model = str(param2).strip() if param2 else "gemma3:1b"
        prompt = f"Give a short, friendly, robot-like response in one sentence to: {user_text}"
        payload_json = json.dumps({"model": model, "prompt": prompt, "stream": False})
        curl_cmd = f"curl -sf -X POST http://localhost:11434/api/generate -d {shlex.quote(payload_json)}"
        out, err, code = await ssh.execute(curl_cmd)
        if code != 0 or not (out or "").strip():
            result = {
                "success": False,
                "error": "Ollama request failed — is Ollama running on the Pi?",
                "hint": "ollama serve  (then: ollama pull gemma3:1b)",
                "raw_err": (err or "").strip(),
            }
        else:
            try:
                resp = json.loads(out)
                llm_text = resp.get("response", "").strip() or "I am thinking."
                speak_res = await execute(ctx, operation="say", param1=llm_text)
                result = {
                    "success": speak_res.get("success", False),
                    "input": user_text,
                    "response": llm_text,
                    "model": model,
                    "say_result": speak_res.get("result", {}),
                }
            except Exception as e:
                result = {"success": False, "error": f"Response parsing failed: {e}", "raw": out}

    # ── volume ───────────────────────────────────────────────────────────────
    elif operation == "volume":
        try:
            level = max(0, min(100, int(param1))) if param1 is not None else 80
        except (TypeError, ValueError):
            level = 80
        out, err, code = await ssh.execute(_set_volume_cmd(level))
        result = {
            "success": code == 0,
            "volume_pct": level,
            "note": "Controls Pi ALSA output (espeak-ng). Does not affect voice module speaker.",
            "log": (out or "").strip() if code != 0 else "",
        }

    else:
        result = {"success": False, "error": f"Unknown voice operation: {operation!r}"}

    return {
        "success": result.get("success", False),
        "operation": operation,
        "status": result.get("status", "ok" if result.get("success") else "error"),
        "log": result.get("log", ""),
        "result": result,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _status_note(device: str | None, pyserial_ok: bool, espeak_ok: bool) -> str:
    parts = []
    if device:
        parts.append(f"Voice module found at {device}.")
    else:
        parts.append(
            "Voice module not found — set up /dev/ttyVOICE udev symlink "
            "(see docs/hardware/HARDWARE_DIAGNOSIS_VOICE_I2C.md)."
        )
    if not pyserial_ok:
        parts.append("pyserial missing — pip3 install pyserial on Pi.")
    if not espeak_ok:
        parts.append("espeak-ng missing — sudo apt-get install espeak-ng on Pi.")
    if device and pyserial_ok and espeak_ok:
        parts.append("All voice subsystems ready.")
    return " ".join(parts)
