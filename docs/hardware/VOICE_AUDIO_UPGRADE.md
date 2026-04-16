# Boomy Audio Upgrade: ReSpeaker Lite + Piper TTS

**Platform:** Yahboom Raspbot v2 (Boomy)  
**Date:** 2026-04-14  
**Tags:** `[yahboom-mcp, voice, audio, respeaker, piper-tts, vosk, chatrobot, upgrade]`  
**Status:** Planned — hardware not yet purchased  
**Parent doc:** [`VOICE_AUDIO.md`](VOICE_AUDIO.md)

---

## 1. Why Upgrade

The Yahboom CSK4002 voice module shipped with Boomy is useful but severely limited:

| Limitation | Impact |
|---|---|
| **No arbitrary TTS** — 85 fixed preset phrases only | Cannot speak LLM responses naturally |
| **Fixed Chinese-accented voice** — cannot be changed without reflashing | Sounds wrong for English use |
| **85-word ASR vocabulary** — hard ceiling on what it can recognise | Breaks the chatrobot concept entirely |
| **No AEC (Acoustic Echo Cancellation)** | Mic hears its own speaker output → feedback loops |
| **No beamforming or noise suppression on the capture path** | Motor noise, wheel noise corrupt STT input |
| **Serial-only control** — recognition events come as binary packets | Requires separate microphone for open-vocabulary STT |
| espeak-ng TTS (current fallback) | Robotic, 1980s GPS voice quality |

The CSK4002 is a freebie bundled with the robot. It is designed for fixed-vocabulary command control, not for a conversational AI. For the chatrobot to work properly, both the microphone capture and the TTS output need an upgrade.

### What we keep the CSK4002 for

One thing: **hardware wake detection**. When someone says "Hi, Yahboom", the module fires a `0xA5` recognition packet over serial in ~100 ms. This is fast, hardware-offloaded, and requires no Pi CPU. The chatrobot loop uses this as its wake trigger, then hands off to the ReSpeaker Lite for actual audio capture. The CSK4002 becomes a dedicated wake word detector — a reasonable use for it.

---

## 2. Upgrade Components

### 2.1 Seeed ReSpeaker Lite (XMOS XU316) — Microphone + Audio Output

**Price:** ~€24 from Seeed DE warehouse (~$25 USD). Also on AliExpress ~$20.  
**Buy:** https://www.seeedstudio.com/ReSpeaker-Lite-p-5928.html (select DE warehouse for EU)

| Property | Value |
|---|---|
| **Chip** | XMOS XU316 (industrial-grade audio DSP, same family used in commercial smart speakers) |
| **Microphones** | 2 × digital MEMS, -26 dBFS sensitivity, 120 dBL overload point, 64 dBA SNR |
| **Far-field pickup** | Up to 3 m with DSP active |
| **Connection to Pi** | USB-C → USB-A (one cable, no HAT, no GPIO) |
| **USB class** | UAC 2.0 — zero-driver on Pi OS, appears as standard ALSA device |
| **Audio output** | 3.5mm jack via onboard WM8960 codec — can drive a small passive speaker directly |
| **Onboard DSP algorithms** | AEC, beamforming, noise suppression, VNR, AGC — all run on the XU316, not the Pi |
| **Visual indicator** | WS2812 RGB LED (programmable, useful for wake/listening state feedback) |
| **Power** | USB 5V (bus-powered) |
| **Dimensions** | Compact — mounts on Boomy top plate with M3 hardware or double-sided tape |
| **Pi 5 compatibility** | Confirmed — no kernel patches required |

**Why the XU316 matters specifically:**

The XMOS XU316 runs a full acoustic front-end pipeline **before audio reaches the Pi over USB**. This means:

- When Piper TTS is playing through the speaker, the microphone does not hear it — AEC cancels it
- Motor noise from Boomy's mecanum wheels is suppressed before Vosk sees the audio
- Far-field speech at 2–3 m is beamformed toward the dominant speaker direction
- AGC normalises quiet speech and loud speech to the same level automatically

Without AEC specifically, any chatrobot loop is broken: the Pi starts recording, Piper begins speaking the previous response, the microphone hears Piper, Vosk transcribes "okay it is on" and sends it back to Ollama as a new prompt. The XU316 prevents this entirely in hardware.

**What it does NOT do:**

- It does not run wake word detection — that remains the CSK4002's job
- It does not do STT — Vosk runs on the Pi
- It has no speaker amplifier beyond the WM8960's low-power output — for loud environments, add a small USB-powered speaker (see Section 2.3)

### 2.2 Piper TTS — Neural Text-to-Speech

**Price:** Free, open source (Apache 2.0)  
**Project:** https://github.com/rhasspy/piper  
**Developed by:** rhasspy / Michael Hansen (Home Assistant audio lead)

Piper replaces espeak-ng. It is built on FastSpeech2 + HiFiGAN, quantised for CPU inference. On Pi 5, it generates speech in real-time or faster for most voice models.

| Property | espeak-ng | Piper (medium quality) |
|---|---|---|
| Voice quality | Robotic, monotone | Natural neural voice |
| Latency (20-word sentence) | ~50 ms | ~200 ms |
| Languages | 100+ | 50+ (growing) |
| Install size | ~5 MB | Model: 60–200 MB |
| CPU usage on Pi 5 | Negligible | ~60% for ~200 ms |
| Streaming support | No | Yes (sentence-by-sentence) |
| German support | Yes, poor quality | Yes, Thorsten voice — good quality |

**Voice model selection for Boomy:**

| Voice | Language | Quality | Model size | Notes |
|---|---|---|---|---|
| `en_US-lessac-medium` | English US | Excellent | 63 MB | Best general English, warm tone |
| `en_GB-alan-medium` | English GB | Very good | 61 MB | British, slightly formal |
| `de_DE-thorsten-medium` | German | Good | 89 MB | Best available German Piper voice |
| `en_US-ryan-medium` | English US | Good | 64 MB | Slightly deeper, more "robot" character |

For a bilingual Vienna deployment: install both `en_US-lessac-medium` and `de_DE-thorsten-medium`. Switch via env var or runtime parameter.

### 2.3 Speaker (optional but recommended)

The ReSpeaker Lite's WM8960 can drive a small 8Ω speaker up to ~1W — adequate for quiet indoor use. For a robot that may be competing with conversation noise, a louder option is better.

**Recommended: STEMMA 3W speaker** (~€5) or any USB-powered mini speaker.  
**Connection:** 3.5mm jack on ReSpeaker Lite → passive speaker, or use a USB-powered Bluetooth/wired speaker.

Total audio upgrade cost: **€24–32** depending on whether a new speaker is needed.

---

## 3. Physical Installation on Boomy

### 3.1 Mounting the ReSpeaker Lite

The ReSpeaker Lite is a bare PCB (~40 × 20 mm). Options:

- **Top plate mount** — M3 screw through existing holes in the Raspbot V2 top plate, or use M3 standoffs. Orient the board so the microphone array faces the direction Boomy faces (both mics forward for maximum beamforming benefit in conversation).
- **Double-sided foam tape** — adequate for testing. Not recommended permanently (vibration from motors degrades mic performance).
- **3D-printed bracket** — STL available from the Seeed community; attaches to the PTZ camera mount.

The USB-C cable routes through the chassis cable slot alongside the existing camera USB cable.

### 3.2 USB port allocation on Pi 5

Pi 5 has 2 × USB 3.0 + 2 × USB 2.0. Current usage:

| Port | Device |
|---|---|
| USB 3.0 | Camera (bandwidth-sensitive) |
| USB 2.0 | Rosmaster UART (`/dev/ttyROSMASTER`) |
| USB 2.0 | CSK4002 voice module (`/dev/ttyVOICE`) |
| USB 3.0 | **ReSpeaker Lite (new)** |

The ReSpeaker Lite on USB 3.0 is overkill for audio bandwidth but ensures no contention with the UART devices. Confirm with `lsusb` after connection.

### 3.3 udev rules update

Add to `/etc/udev/rules.d/99-boomy.rules` on the Pi:

```udev
# ReSpeaker Lite XU316 (XMOS USB audio)
SUBSYSTEM=="sound", ATTRS{idVendor}=="2b04", ATTRS{idProduct}=="fff6", \
    SYMLINK+="snd-respeaker", MODE="0666", GROUP="audio"
```

The VID `2b04` / PID `fff6` is the XMOS XU316 UAC identifier. Confirm with `lsusb -v` after connecting.

### 3.4 ALSA default device

Set the ReSpeaker Lite as the default ALSA device on the Pi:

```bash
# /etc/asound.conf
defaults.pcm.card 1       # adjust card number from 'aplay -l'
defaults.ctl.card 1
```

Find the correct card number:
```bash
aplay -l   # look for "ReSpeaker" or "XMOS" in the output
arecord -l # same
```

---

## 4. Software Setup

### 4.1 Install Piper TTS

```bash
# On the Pi (via SSH from Goliath or directly):
pip3 install piper-tts

# Create a voice models directory:
mkdir -p ~/piper-voices

# Download English voice (lessac medium — recommended):
cd ~/piper-voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Download German voice (optional):
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json
```

**Test Piper from command line:**
```bash
echo "Hello, I am Boomy. I am ready for deployment." \
  | piper --model ~/piper-voices/en_US-lessac-medium.onnx \
          --output_file /tmp/test.wav \
  && aplay /tmp/test.wav
```

**Test via Python:**
```python
from piper.voice import PiperVoice

voice = PiperVoice.load("/home/pi/piper-voices/en_US-lessac-medium.onnx")

# Direct synthesis to WAV bytes:
import wave, io
buf = io.BytesIO()
with wave.open(buf, "wb") as wf:
    voice.synthesize("Battery at forty percent. Please charge me soon.", wf)

# Or stream to ALSA directly:
import subprocess
proc = subprocess.Popen(
    ["aplay", "-r", "22050", "-f", "S16_LE", "-c", "1", "-"],
    stdin=subprocess.PIPE
)
for audio_bytes in voice.synthesize_stream_raw("Hello from Boomy."):
    proc.stdin.write(audio_bytes)
proc.stdin.close()
proc.wait()
```

### 4.2 Install Vosk STT with the ReSpeaker Lite

```bash
pip3 install vosk pyaudio

# Download the small English model (~50 MB):
cd ~
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 vosk-models/en-small

# Optionally the larger model for better accuracy (~1 GB, slower):
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
```

**Test Vosk with ReSpeaker Lite mic:**
```python
import pyaudio
import json
from vosk import Model, KaldiRecognizer

model = Model("/home/pi/vosk-models/en-small")
rec = KaldiRecognizer(model, 16000)

p = pyaudio.PyAudio()

# Find ReSpeaker device index:
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if "respeaker" in info["name"].lower() or "xmos" in info["name"].lower():
        print(f"ReSpeaker at index {i}: {info['name']}")

# Record and transcribe:
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    input_device_index=RESPEAKER_INDEX,  # from above
    frames_per_buffer=8000
)

print("Speak now...")
while True:
    data = stream.read(4000, exception_on_overflow=False)
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        if result.get("text"):
            print("Heard:", result["text"])
```

### 4.3 MCP environment variable updates

Add to the yahboom-mcp environment (in `start.bat` or `.env`):

```bash
# Piper TTS (replaces espeak-ng)
YAHBOOM_TTS_ENGINE=piper
YAHBOOM_PIPER_MODEL=/home/pi/piper-voices/en_US-lessac-medium.onnx
YAHBOOM_PIPER_VOICE=en_US-lessac-medium

# Optional German voice:
# YAHBOOM_PIPER_MODEL=/home/pi/piper-voices/de_DE-thorsten-medium.onnx

# ReSpeaker Lite device (for Vosk capture)
YAHBOOM_STT_DEVICE=respeaker   # matched by name in PyAudio device scan
YAHBOOM_VOSK_MODEL=/home/pi/vosk-models/en-small

# Keep existing voice module settings:
YAHBOOM_VOICE_DEVICE=/dev/ttyVOICE
YAHBOOM_VOICE_BAUD=115200
```

---

## 5. Updated voice.py: Piper Integration

The `say` operation in `operations/voice.py` needs to support Piper as the TTS engine when `YAHBOOM_TTS_ENGINE=piper`. The implementation strategy: build Piper synthesis on the Pi via SSH, same as the existing espeak-ng approach.

**SSH command builder for Piper:**

```python
def _say_piper_cmd(text: str, model_path: str) -> str:
    """
    Build SSH command: synthesise text with Piper and play via aplay.
    Streams directly — no temp file needed.
    """
    import shlex
    script = f"""
import subprocess, sys
text = {text!r}
model = {model_path!r}
piper_proc = subprocess.Popen(
    ["piper", "--model", model, "--output-raw"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
)
aplay_proc = subprocess.Popen(
    ["aplay", "-r", "22050", "-f", "S16_LE", "-c", "1", "-"],
    stdin=piper_proc.stdout,
    stderr=subprocess.DEVNULL,
)
piper_proc.stdin.write(text.encode())
piper_proc.stdin.close()
piper_proc.wait()
aplay_proc.wait()
print("OK")
"""
    return f"python3 -c {shlex.quote(script)}"
```

This will be integrated into `voice.py` when the hardware arrives and is tested. Until then, espeak-ng remains the fallback.

---

## 6. Updated Chatrobot Architecture

With the upgrade, the full chatrobot loop becomes:

```
User speaks: "Hi, Yahboom"
      │
CSK4002 module: hardware wake detection (~100 ms)
      │  fires 0xA5 packet over /dev/ttyVOICE
      │
chatbot.py: wake event received via listen()
      │  CSK4002 optionally plays preset greeting (phrase #1)
      │  RGB LED on ReSpeaker Lite → red (listening)
      │
ReSpeaker Lite XU316: begins capturing
      │  AEC active: cancels any residual speaker output
      │  Beamforming: focused on dominant speaker direction
      │  Noise suppression: motor noise removed
      │
Vosk on Pi 5: STT from clean ReSpeaker Lite audio
      │  ~500 ms for a short sentence
      │
Ollama gemma3:1b on Pi 5: generates response
      │  ~2000 ms for ~20 words
      │  RGB LED → amber (thinking)
      │
Piper TTS on Pi 5: synthesises response
      │  ~200 ms first audio
      │  RGB LED → green (speaking)
      │  Streams sentence-by-sentence → aplay → ReSpeaker 3.5mm → speaker
      │  AEC active during playback: XU316 cancels Piper output from mic
      │
(optional) Intent parser: extract motion commands from response text
      │  publish to /cmd_vel if motion detected
      │
RGB LED → off (idle)
Loop back to listening for next wake event
```

### 6.1 Revised latency budget

| Stage | Old stack | New stack |
|---|---|---|
| Wake detection | CSK4002 fixed vocab, ~100 ms | CSK4002 unchanged, ~100 ms |
| Audio capture (3s window) | Raw mic, noisy, 3000 ms | ReSpeaker AEC, 3000 ms |
| Vosk STT | ~800 ms (noisy input) | ~500 ms (clean input) |
| Ollama gemma3:1b | ~2000 ms | ~2000 ms (unchanged) |
| Piper TTS (first audio) | ~500 ms espeak | ~200 ms Piper |
| **Total to first spoken word** | **~6.4 s** | **~5.8 s** |
| **Voice quality** | Robotic | Natural neural |
| **Works without feedback** | No (no AEC) | Yes (XU316 AEC) |

The latency difference is modest — the real wins are **voice quality** and **AEC correctness**. Without AEC, the loop is fundamentally broken in a demo setting. With it, it works reliably.

### 6.2 Sentence-streaming optimisation

Piper supports streaming: it can begin playing the first sentence while generating the second. This can reduce perceived latency from ~5.8s to ~3.5s:

```
Ollama response: "Patrol initiated. Moving to perimeter. Obstacle detected at front."
                      ↓                    ↓                       ↓
Piper synthesises: sentence 1        sentence 2              sentence 3
aplay starts:       immediately    while 2 generating      while 3 generating
```

Implementation: stream Ollama tokens, detect sentence breaks (`.`, `!`, `?`), fire Piper per sentence. This is what the TrooperAI project implemented to get perceived latency under 4 seconds.

---

## 7. Comparison Table: Before vs After

| Aspect | Before (CSK4002 + espeak) | After (ReSpeaker Lite + Piper) |
|---|---|---|
| Mic quality | Single MEMS, no DSP | Dual MEMS + XMOS XU316 DSP |
| Echo cancellation | None | Hardware AEC on XU316 |
| Noise suppression | None | Hardware NS on XU316 |
| Far-field range | ~1 m reliable | ~3 m reliable |
| TTS voice quality | Robotic (espeak-ng) | Natural neural (Piper) |
| Arbitrary TTS | Yes (espeak) | Yes (Piper, much better) |
| TTS latency | ~500 ms | ~200 ms |
| Wake word detection | CSK4002 hardware | CSK4002 hardware (unchanged) |
| Preset phrase playback | CSK4002 serial | CSK4002 serial (unchanged) |
| STT engine | Vosk on raw mic | Vosk on AEC-cleaned mic |
| STT accuracy in noisy room | Moderate | High |
| Chatrobot loop stability | Broken without AEC | Stable |
| Total cost | Included in robot | +€24–32 |
| Driver installation | None needed | None needed (UAC 2.0) |

---

## 8. Shopping Checklist

- [ ] **Seeed ReSpeaker Lite** (XMOS XU316) — ~€24 — Seeed DE warehouse or AliExpress
  - Product page: https://www.seeedstudio.com/ReSpeaker-Lite-p-5928.html
  - AliExpress: search "ReSpeaker Lite XU316"
- [ ] **Small speaker** (if none available) — ~€5–8 — any 8Ω 1W+ passive speaker, or USB-powered mini speaker with 3.5mm input
- [ ] **USB-C to USB-A cable** (short, ~15cm) — Boomy already has several; check stock

**Optional:**
- [ ] M3 standoffs + screws for top-plate mounting (may already have in workshop)

---

## 9. Installation Sequence

Do these in order after hardware arrives.

1. **Connect ReSpeaker Lite** to Pi via USB-C. Do not configure anything yet.
2. **Verify ALSA sees it:** `aplay -l` — should show "ReSpeaker" or XMOS device
3. **Test capture:** `arecord -D hw:CARD=ReSpeaker,DEV=0 -f S16_LE -r 16000 -c 1 /tmp/test.wav` (5 seconds), then `aplay /tmp/test.wav`
4. **Test playback:** `aplay -D hw:CARD=ReSpeaker,DEV=0 /tmp/test.wav` through the 3.5mm
5. **Set ALSA defaults** in `/etc/asound.conf`
6. **Install Piper** and download voice model (Section 4.1)
7. **Test Piper** end-to-end with aplay
8. **Install Vosk** (if not already), test with ReSpeaker mic (Section 4.2)
9. **Update environment variables** in yahboom-mcp start script (Section 4.3)
10. **Update udev rules** (Section 3.3)
11. **Test get_status** MCP operation — should now report ReSpeaker device
12. **Test say operation** — should use Piper
13. **Test chatbot loop** when `chatbot.py` is implemented

---

## 10. See Also

- [`VOICE_AUDIO.md`](VOICE_AUDIO.md) — base voice facility reference (CSK4002 protocol, current operations)
- [`HARDWARE_DIAGNOSIS_VOICE_I2C.md`](HARDWARE_DIAGNOSIS_VOICE_I2C.md) — udev conflict diagnosis
- [ReSpeaker Lite wiki](https://wiki.seeedstudio.com/reSpeaker_usb_v3/) — official Seeed documentation
- [Piper TTS GitHub](https://github.com/rhasspy/piper) — voice model downloads, Python API
- [TrooperAI reference implementation](https://github.com/m15-ai/TrooperAI) — Pi 5 + Vosk + Piper + Ollama working chatbot (same architecture)
- [Vosk models](https://alphacephei.com/vosk/models) — all available STT models
