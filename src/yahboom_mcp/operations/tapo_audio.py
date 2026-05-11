"""Two-way audio for Tapo camera riding on Boomy.

Architecture:
- Listen: Tapo RTSP audio stream (G.711) → ffmpeg → WAV → faster-whisper → text
- Speak: edge-tts → play through Pi audio (aplay/pulseaudio) — simpler and better quality
  than the Tapo's tinny speaker.
- Tapo speaker is available via pytapo HTTP API but requires proprietary WebSocket
  protocol; use if sensor needs physical speaker.
"""
import asyncio, io, json, logging, os, tempfile, time
from typing import Any

_TP_USER = os.environ.get("TAPO_USER", "admin")
_TP_PASS = os.environ.get("TAPO_PASSWORD", "")
_TP_IP = os.environ.get("TAPO_IP", "192.168.1.100")
_TP_URL = f"http://{_TP_IP}"

logger = logging.getLogger("yahboom-mcp.operations.tapo_audio")


async def _pull_rtsp_audio(duration_sec: int, output_wav: str) -> bool:
    """Capture Tapo RTSP audio stream to WAV file using ffmpeg."""
    url = f"rtsp://{_TP_USER}:{_TP_PASS}@{_TP_IP}:554/stream2"
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-t", str(duration_sec), "-i", url,
        "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", output_wav,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        await asyncio.wait_for(proc.wait(), timeout=duration_sec + 15)
        return os.path.isfile(output_wav) and os.path.getsize(output_wav) > 1000
    except asyncio.TimeoutError:
        proc.kill()
        return False


async def listen(duration_sec: int = 5, language: str = "en") -> dict[str, Any]:
    """Capture audio from Tapo RTSP mic and transcribe with faster-whisper.

    ## Return Format
    {"success": bool, "text": str, "duration_sec": int}

    ## Examples
    await listen(duration_sec=5, language="en")
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return {"success": False, "error": "faster-whisper not installed"}

    wav = os.path.join(tempfile.gettempdir(), "tapo_stt.wav")
    ok = await _pull_rtsp_audio(duration_sec, wav)
    if not ok:
        return {"success": False, "error": "No audio captured from Tapo mic"}

    try:
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(wav, language=language)
        text = " ".join(s.text for s in segments)
        return {
            "success": bool(text.strip()),
            "text": text.strip(),
            "duration_sec": duration_sec,
        }
    except Exception as e:
        return {"success": False, "error": f"STT failed: {e}"}
    finally:
        try: os.unlink(wav)
        except: pass


async def speak(text: str, volume: int = 80) -> dict[str, Any]:
    """Convert text to speech and play through Pi audio output.

    Falls back to writing a WAV and using aplay when pulse not available.

    ## Return Format
    {"success": bool, "message": str}

    ## Examples
    await speak("Hello, I am Boomy")
    """
    try:
        from edge_tts import Communicate
    except ImportError:
        return {"success": False, "error": "edge-tts not installed"}

    lang = "auto"
    if any(ord(c) > 127 for c in text if c.isalpha()):
        lang = "de"  # has German chars
    voice = "de-DE-KatjaNeural" if lang == "de" else "en-US-AriaNeural"

    wav = os.path.join(tempfile.gettempdir(), "tapo_tts.wav")
    try:
        tts = Communicate(text, voice=voice)
        audio = b""
        async for chunk in tts.stream():
            if chunk["type"] == "audio":
                audio += chunk["data"]
        if not audio:
            return {"success": False, "error": "TTS produced no audio"}

        with open(wav, "wb") as f:
            f.write(audio)

        # Play through Pi's audio output via SSH
        ssh = getattr(logger, "_ssh_bridge", None)
        if ssh and ssh.connected:
            await ssh.sudo_execute(f"aplay {wav}")
        else:
            # Local playback (dev machine)
            proc = await asyncio.create_subprocess_exec(
                "aplay", wav, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            try: await asyncio.wait_for(proc.wait(), timeout=30)
            except: proc.kill()

        return {"success": True, "message": f"Spoke: {text[:60]}...", "voice": voice}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        try: os.unlink(wav)
        except: pass


async def status() -> dict[str, Any]:
    """Check Tapo camera connectivity."""
    import aiohttp
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as s:
            async with s.get(f"{_TP_URL}/") as r:
                return {
                    "success": True,
                    "connected": r.ok,
                    "ip": _TP_IP,
                    "mic": "rtsp://user@**masked**@ip:554/stream2",
                    "speaker": "Pi audio output",
                }
    except Exception as e:
        return {"success": False, "connected": False, "error": str(e)}
