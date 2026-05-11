"""Two-way audio for Tapo camera via proprietary streaming protocol.

Architecture:
- Listen: Tapo RTSP audio (G.711) → ffmpeg → WAV → faster-whisper → text
- Speak: edge-tts → WAV → μ-law encode → TCP streaming to Tapo port 8800

Tapo streaming protocol (reverse-engineered from pytapo media_stream):
- TCP connection to camera:8800
- HTTP POST /stream with digest auth + multipart boundaries
- Audio is G.711 μ-law (8kHz, 8-bit) sent in 160-byte frames (20ms)
"""
import asyncio, hashlib, io, json, logging, os, struct, tempfile, time
from typing import Any

_TP_USER = os.environ.get("TAPO_USER", "admin")
_TP_PASS = os.environ.get("TAPO_PASSWORD", "")
_TP_IP = os.environ.get("TAPO_IP", "192.168.1.100")
_TP_URL = f"http://{_TP_IP}"

logger = logging.getLogger("yahboom-mcp.operations.tapo_audio")
_tapo = None


async def _get_tapo():
    global _tapo
    if _tapo is None:
        try:
            from pytapo import Tapo
            _tapo = Tapo(_TP_URL, _TP_USER, _TP_PASS)
        except Exception as e:
            logger.error("Tapo auth failed: %s", e)
            raise
    return _tapo


async def _stream_audio_to_tapo(mulaw_bytes: bytes):
    """Stream μ-law audio to Tapo speaker via TCP port 8800."""
    tapo = await _get_tapo()
    session = tapo.getMediaSession()
    try:
        reader, writer = await asyncio.open_connection(_TP_IP, 8800)
        boundary = b"--client-stream-boundary--"

        def _nonce():
            return "%016x" % random.getrandbits(64)

        # Digest auth handshake
        realm = "IP Camera"
        nonce = _nonce()
        ha1 = hashlib.md5(f"{_TP_USER}:{realm}:{_TP_PASS}".encode()).hexdigest()
        ha2 = hashlib.md5(b"POST:/stream").hexdigest()
        resp = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()

        auth = f'Digest username="{_TP_USER}",realm="{realm}",nonce="{nonce}",uri="/stream",response="{resp}",algorithm=MD5'
        headers = (
            f"POST /stream HTTP/1.1\r\n"
            f"Host: {_TP_IP}:8800\r\n"
            f"Authorization: {auth}\r\n"
            f"Content-Type: multipart/x-mixed-replace; boundary={boundary.decode()}\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"Connection: keep-alive\r\n\r\n"
        ).encode()
        writer.write(headers)
        await writer.drain()

        # Read HTTP response
        resp_line = await reader.readline()
        if b"200" not in resp_line:
            logger.error("Tapo stream auth failed: %s", resp_line)
            writer.close()
            return False

        # Consume remaining response headers
        while (await reader.readline()).strip():
            pass

        # Send audio chunks in multipart format
        chunk_size = 160  # 20ms at 8kHz
        for i in range(0, len(mulaw_bytes), chunk_size):
            chunk = mulaw_bytes[i:i+chunk_size]
            part = b"--" + boundary + b"\r\n"
            part += b"Content-Type: audio/basic\r\n"
            part += f"Content-Length: {len(chunk)}\r\n\r\n".encode()
            part += chunk + b"\r\n"
            writer.write(f"{len(part):x}\r\n".encode() + part + b"\r\n")
            await writer.drain()
            await asyncio.sleep(0.02)

        writer.close()
        return True
    except Exception as e:
        logger.error("Tapo audio stream failed: %s", e)
        return False


async def speak(text: str, volume: int = 80) -> dict[str, Any]:
    """Text-to-speech via edge-tts, played through Tapo speaker.

    ## Return Format
    {"success": bool, "message": str}

    ## Examples
    await speak("Hello, I am Boomy")
    """
    try:
        from edge_tts import Communicate
    except ImportError:
        return {"success": False, "error": "edge-tts not installed"}

    voice = "de-DE-KatjaNeural" if any(ord(c) > 127 for c in text if c.isalpha()) else "en-US-AriaNeural"
    wav = os.path.join(tempfile.gettempdir(), "tapo_tts.wav")
    mulaw_path = os.path.join(tempfile.gettempdir(), "tapo_tts.ulaw")

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

        # Convert WAV to 8kHz μ-law
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-i", wav, "-ar", "8000", "-ac", "1",
            "-f", "mulaw", mulaw_path
        ], capture_output=True, timeout=30)

        if not os.path.isfile(mulaw_path):
            return {"success": False, "error": "Audio conversion failed"}

        with open(mulaw_path, "rb") as f:
            mulaw = f.read()

        ok = await _stream_audio_to_tapo(mulaw)
        return {
            "success": ok,
            "message": f"Spoke through Tapo: {text[:60]}...",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        for p in [wav, mulaw_path]:
            try: os.unlink(p)
            except: pass


async def listen(duration_sec: int = 5, language: str = "en") -> dict[str, Any]:
    """Capture audio from Tapo RTSP mic → faster-whisper → text."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return {"success": False, "error": "faster-whisper not installed"}

    wav = os.path.join(tempfile.gettempdir(), "tapo_stt.wav")
    url = f"rtsp://{_TP_USER}:{_TP_PASS}@{_TP_IP}:554/stream2"

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-t", str(duration_sec), "-i", url,
        "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        await asyncio.wait_for(proc.wait(), timeout=duration_sec + 15)
    except asyncio.TimeoutError:
        proc.kill()

    if not os.path.isfile(wav) or os.path.getsize(wav) < 1000:
        return {"success": False, "error": "No audio captured"}

    try:
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(wav, language=language)
        text = " ".join(s.text for s in segments)
        return {"success": bool(text.strip()), "text": text.strip(), "duration_sec": duration_sec}
    except Exception as e:
        return {"success": False, "error": f"STT failed: {e}"}
    finally:
        try: os.unlink(wav)
        except: pass


async def status() -> dict[str, Any]:
    """Check Tapo connectivity and audio abilities."""
    import aiohttp
    try:
        tapo = await _get_tapo()
        info = tapo.getDeviceInfo()
        return {
            "success": True,
            "connected": True,
            "model": info.get("device_alias", info.get("model", "unknown")),
            "ip": _TP_IP,
            "speaker": "Tapo built-in (μ-law 8kHz)",
            "mic": "RTSP stream2 (listen-only)",
            "mic_rtsp": f"rtsp://{_TP_USER}@**masked**@{_TP_IP}:554/stream2",
        }
    except Exception as e:
        return {"success": False, "connected": False, "error": str(e)}
