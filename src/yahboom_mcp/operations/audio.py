"""
Yahboom Audio Player — upload, store, play audio files through USB speaker.

Routes all playback through the C-Media USB Audio device (plughw:2,0).
Audio files can be stored permanently on the Pi at ~/boomy_audio/.

Built-in sound effects: fart, clap, boo, ding, buzzer, reveille, deguello,
circus, elevator, siren, applause, tada, sad_trombone, take_five, coin, zap.
"""

import logging
import os
import shlex

from .. import fail_response

logger = logging.getLogger("yahboom-mcp.operations.audio")

_AUDIO_DEV = "plughw:2,0"
_AUDIO_DIR = "/home/pi/boomy_audio"

# ── Built-in sound effects ──────────────────────────────────────────────────

_SOUND_GENERATOR = r"""
import struct, math, wave, sys, random
name = sys.argv[1] if len(sys.argv) > 1 else "ding"
rate = 44100
def tone(freq, dur, vol=0.6):
    n = int(rate * dur)
    return [int(vol * 32767 * math.sin(2 * math.pi * freq * i / rate)) for i in range(n)]
def noise(dur, vol=0.6):
    n = int(rate * dur)
    return [int(vol * 32767 * (random.random() * 2 - 1)) for i in range(n)]
def mix(*tracks):
    return [max(-32767, min(32767, sum(t))) for t in zip(*tracks)]

samples = []
if name == "fart":
    samples = [int(0.5 * 32767 * (random.random() * 2 - 1)) for _ in range(int(rate * 0.4))]
elif name == "clap":
    samples = noise(0.12, 0.8)[:int(rate*0.08)] + [0] * int(rate*0.02)
elif name == "boo":
    for i in range(int(rate * 0.6)):
        f = 400 - 250 * i / (rate * 0.6)
        samples.append(int(0.6 * 32767 * math.sin(2 * math.pi * f * i / rate)))
elif name == "ding":
    s1 = tone(880, 0.15, 0.5) + tone(0, 0.02, 0)
    s2 = tone(1175, 0.25, 0.5)
    samples = s1 + [0]*int(rate*0.02) + s2
elif name == "buzzer":
    s = tone(120, 0.5, 0.7)
    s2 = [int(0.3 * s[i] * (1 if (i // 200) % 2 == 0 else 0.5)) for i in range(len(s))]
    samples = s2
elif name == "reveille":
    notes = [(523,0.2),(659,0.2),(784,0.4),(523,0.2),(659,0.2),(784,0.4),
             (523,0.2),(659,0.2),(784,0.2),(1047,0.3),(784,0.2),(659,0.2),(523,0.4),
             (784,0.2),(1047,0.2),(784,0.2),(1047,0.4)]
    for f, d in notes:
        samples.extend(tone(f, d, 0.5))
elif name == "deguello":
    notes = [(440,0.3),(494,0.3),(554,0.6),(440,0.3),(494,0.3),(554,0.6),
             (440,0.3),(494,0.3),(554,0.3),(659,0.3),(554,0.3),(494,0.3),(440,0.6)]
    for f, d in notes:
        samples.extend(tone(f, d, 0.5))
elif name == "circus":
    mel = [(392,0.15),(523,0.15),(659,0.15),(784,0.15),(659,0.15),(784,0.3),
           (784,0.15),(988,0.15),(784,0.15),(659,0.15),(523,0.15),(659,0.3)]
    for f, d in mel:
        samples.extend(tone(f, d, 0.4))
elif name == "elevator":
    mel = [(262,0.25),(330,0.25),(392,0.25),(523,0.35),(392,0.25),(523,0.5),
           (330,0.25),(392,0.25),(262,0.25),(330,0.25),(392,0.5)]
    for f, d in mel:
        samples.extend(tone(f, d, 0.35))
elif name == "siren":
    for i in range(int(rate * 1.5)):
        f = 400 + 600 * abs(math.sin(2 * math.pi * 0.5 * i / rate))
        samples.append(int(0.6 * 32767 * math.sin(2 * math.pi * f * i / rate)))
elif name == "applause":
    for _ in range(8):
        samples.extend(noise(0.15, 0.5))
        samples.extend([0] * int(rate * 0.08))
elif name == "tada":
    mel = [(523,0.15),(659,0.15),(784,0.15),(1047,0.5)]
    for f, d in mel:
        samples.extend(tone(f, d, 0.6))
elif name == "sad_trombone":
    for i in range(int(rate * 0.8)):
        f = 350 - 280 * i / (rate * 0.8)
        samples.append(int(0.6 * 32767 * math.sin(2 * math.pi * f * i / rate)))
elif name == "take_five":
    mel = [(294,0.2),(330,0.2),(349,0.3),(294,0.2),(330,0.2),(349,0.3),
           (294,0.2),(330,0.2),(349,0.2),(392,0.3),(349,0.2),(330,0.3)]
    for f, d in mel:
        samples.extend(tone(f, d, 0.4))
elif name == "coin":
    for i in range(int(rate * 0.15)):
        f = 2000 + 1000 * (i / (rate * 0.15))
        samples.append(int(0.4 * 32767 * math.sin(2 * math.pi * f * i / rate)))
    for i in range(int(rate * 0.05)):
        f = 3000 - 500 * (i / (rate * 0.05))
        samples.append(int(0.2 * 32767 * math.sin(2 * math.pi * f * i / rate)))
elif name == "zap":
    for i in range(int(rate * 0.2)):
        f = 200 + 3000 * (i / (rate * 0.2)) ** 2
        samples.append(int(0.6 * 32767 * math.sin(2 * math.pi * f * i / rate)))
elif name == "beep":
    samples = tone(880, 0.5, 0.6)
else:
    print(f"UNKNOWN:{name}")
    sys.exit(0)

out = "/tmp/boomy_sound.wav"
f = wave.open(out, "w")
f.setnchannels(1)
f.setsampwidth(2)
f.setframerate(rate)
for s in samples:
    f.writeframes(struct.pack("<h", max(-32767, min(32767, int(s)))))
f.close()
print(f"GENERATED:{len(samples)}")
"""

_SOUNDS = {
    "fart",
    "clap",
    "boo",
    "ding",
    "buzzer",
    "reveille",
    "deguello",
    "circus",
    "elevator",
    "siren",
    "applause",
    "tada",
    "sad_trombone",
    "take_five",
    "coin",
    "zap",
    "beep",
}


def _get_ssh():
    from .state import _state

    ssh = _state.get("ssh")
    if ssh and ssh.connected:
        return ssh, None
    return None, "SSH bridge not connected"


def _direct_ssh():
    import paramiko

    host = "192.168.1.11"
    pwd = os.environ.get("YAHBOOM_PASSWORD", "yahboom")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username="pi", password=pwd, timeout=10)
    return client


def _run_ssh(client, cmd, timeout_s=30):
    """Run a command via SSH client (paramiko) and return out, err, code."""
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout_s)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    try:
        code = stdout.channel.recv_exit_status()
    except Exception:
        code = -1
    return out, err, code


async def execute(
    operation: str = "play",
    file_path: str = "",
    file_name: str = "",
) -> dict:
    """
    Audio playback via USB voice module speaker.

    Operations
    ----------
    play  (file_path = absolute local path)
        Upload a .mp3/.wav to Pi, play it immediately, then delete.

    sound  (file_name = sound name, e.g. fart, ding, tada, reveille...)
        Generate and play a built-in sound effect through the speaker.

    store  (file_path = absolute local path, file_name = desired name on Pi)
        Upload to ~/boomy_audio/ for permanent storage.

    play_stored  (file_name = filename in depot)
        Play a previously stored file.

    list_stored
        List files in the Pi audio depot.

    delete_stored  (file_name)
        Remove a file from the depot.

    stop
        Kill all running mpg123/aplay processes.
    """
    ext = os.path.splitext(file_path)[1].lower() if file_path else ""
    is_audio = ext in (".mp3", ".wav")

    # --- STOP ---
    if operation == "stop":
        try:
            c = _direct_ssh()
            _run_ssh(c, "pkill -f 'mpg123|aplay' 2>/dev/null; echo OK")
            c.close()
        except Exception as e:
            return fail_response(str(e), operation=operation)
        return {"success": True, "operation": "stop", "status": "stopped"}

    # --- LIST STORED ---
    if operation == "list_stored":
        try:
            c = _direct_ssh()
            out, _, _ = _run_ssh(c, f"ls -lah {_AUDIO_DIR}/ 2>/dev/null || echo EMPTY")
            c.close()
            files = [line for line in out.split("\n") if line and "EMPTY" not in line and "total" not in line]
            return {"success": True, "operation": "list_stored", "files": files, "count": len(files)}
        except Exception as e:
            return fail_response(str(e), operation=operation)

    # --- SOUND (built-in effects) ---
    if operation == "sound":
        if not file_name or file_name not in _SOUNDS:
            return fail_response(
                f"Unknown sound: {file_name!r}",
                operation="sound",
                available=sorted(_SOUNDS),
            )
        try:
            c = _direct_ssh()
            # Write generator script, run it, play output
            sftp = c.open_sftp()
            with sftp.file("/tmp/boomy_gen_sound.py", "w") as f:
                f.write(_SOUND_GENERATOR)
            sftp.close()
            out, err, _code = _run_ssh(c, f"python3 /tmp/boomy_gen_sound.py {shlex.quote(file_name)} 2>&1")
            if "GENERATED" not in out:
                c.close()
                return fail_response(f"Generation failed: {out} {err}", operation="sound")

            play_out, _, _ = _run_ssh(c, f"aplay -q -D {_AUDIO_DEV} /tmp/boomy_sound.wav 2>&1; echo OK")
            c.close()
            return {
                "success": "OK" in play_out,
                "operation": "sound",
                "sound": file_name,
                "status": "played" if "OK" in play_out else "failed",
                "samples": out.split(":")[-1] if ":" in out else "",
            }
        except Exception as e:
            return fail_response(str(e), operation="sound")

    # --- PLAY ---
    if operation == "play":
        if not file_path or not os.path.exists(file_path):
            return fail_response(f"File not found: {file_path!r}", operation="play")
        if not is_audio:
            return fail_response(f"Unsupported: {ext} (use .mp3 or .wav)", operation="play")

        remote = f"/tmp/audio_play_{os.path.basename(file_path)}"
        try:
            c = _direct_ssh()
            sftp = c.open_sftp()
            sftp.put(file_path, remote)
            sftp.close()

            if ext == ".mp3":
                cmd = f"nohup mpg123 -q -a {_AUDIO_DEV} {shlex.quote(remote)} >/dev/null 2>&1 & echo OK"
            else:
                cmd = f"nohup aplay -q -D {_AUDIO_DEV} {shlex.quote(remote)} >/dev/null 2>&1 & echo OK"
            out, err, _code = _run_ssh(c, cmd)
            c.close()
            return {
                "success": "OK" in out,
                "operation": "play",
                "file": file_path,
                "status": "playing" if "OK" in out else "failed",
                "log": err or "",
            }
        except Exception as e:
            return fail_response(str(e), operation="play")

    # --- STORE ---
    if operation == "store":
        if not file_path or not os.path.exists(file_path):
            return fail_response(f"File not found: {file_path!r}", operation="store")
        if not is_audio:
            return fail_response(f"Unsupported: {ext}", operation="store")

        name = file_name or os.path.basename(file_path)
        remote = f"{_AUDIO_DIR}/{name}"
        try:
            c = _direct_ssh()
            _run_ssh(c, f"mkdir -p {_AUDIO_DIR}")
            sftp = c.open_sftp()
            sftp.put(file_path, remote)
            sftp.close()
            c.close()
            return {"success": True, "operation": "store", "file": file_path, "stored_as": remote}
        except Exception as e:
            return fail_response(str(e), operation="store")

    # --- PLAY STORED ---
    if operation == "play_stored":
        if not file_name:
            return fail_response("file_name required", operation="play_stored")
        remote = f"{_AUDIO_DIR}/{file_name}"
        try:
            c = _direct_ssh()
            out, _, _ = _run_ssh(c, f"test -f {shlex.quote(remote)} && echo EXISTS || echo MISSING")
            if "MISSING" in out:
                c.close()
                return fail_response(f"Not found: {file_name!r}", operation="play_stored")

            if file_name.endswith(".mp3"):
                cmd = f"nohup mpg123 -q -a {_AUDIO_DEV} {shlex.quote(remote)} >/dev/null 2>&1 & echo OK"
            else:
                cmd = f"nohup aplay -q -D {_AUDIO_DEV} {shlex.quote(remote)} >/dev/null 2>&1 & echo OK"
            out, _, _ = _run_ssh(c, cmd)
            c.close()
            return {
                "success": "OK" in out,
                "operation": "play_stored",
                "file_name": file_name,
                "status": "playing" if "OK" in out else "failed",
            }
        except Exception as e:
            return fail_response(str(e), operation="play_stored")

    # --- DELETE STORED ---
    if operation == "delete_stored":
        if not file_name:
            return fail_response("file_name required", operation="delete_stored")
        remote = f"{_AUDIO_DIR}/{file_name}"
        try:
            c = _direct_ssh()
            out, _, _ = _run_ssh(c, f"rm -f {shlex.quote(remote)} && echo OK || echo FAIL")
            c.close()
            if "OK" in out:
                return {"success": True, "operation": "delete_stored", "file_name": file_name}
            return fail_response("Delete failed", operation="delete_stored")
        except Exception as e:
            return fail_response(str(e), operation="delete_stored")

    return fail_response(f"Unknown: {operation!r}", operation=operation)
