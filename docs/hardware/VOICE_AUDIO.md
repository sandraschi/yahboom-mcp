# Boomy Voice & Audio Facility — Complete Reference

**Platform:** Yahboom Raspbot v2 (Boomy)  
**Date:** 2026-04-14  
**Tags:** `[yahboom-mcp, voice, audio, CSK4002, espeak-ng, vosk, chatrobot]`  
**Status:** Active — `operations/voice.py` v2 (binary protocol), `operations/chatbot.py` planned  
**Upgrade path:** [`VOICE_AUDIO_UPGRADE.md`](VOICE_AUDIO_UPGRADE.md) — ReSpeaker Lite + Piper TTS

> [!NOTE]
> The CSK4002 module bundled with Boomy has a fixed 85-phrase vocabulary and no AEC. For the full chatrobot, the planned upgrade is a **Seeed ReSpeaker Lite (XU316, ~€24)** for mic/output with hardware AEC, and **Piper TTS** replacing espeak-ng. See [`VOICE_AUDIO_UPGRADE.md`](VOICE_AUDIO_UPGRADE.md) for the full plan.

---

## 1. Hardware Inventory

Boomy has three distinct audio-related hardware components. They are independent and serve different functions.

### 1.1 Yahboom AI Voice Interaction Module (CSK4002)

| Property | Value |
|---|---|
| **Chip** | CSK4002 (AISoC by LISTENAI / iFLYTEK algorithm) |
| **Connection** | USB-CDC serial via CH340 or CP2102 USB-UART bridge |
| **udev path** | `/dev/ttyVOICE` (symlink) → physical `/dev/ttyUSB1` |
| **Baud rate** | 115200 |
| **Onboard microphones** | 2 (dual-mic array, beamforming, up to 5 m pickup) |
| **Onboard speaker** | Yes — small built-in speaker, PH2.0 connector |
| **Wake word** | "Hi, Yahboom" |
| **Preset phrases** | 85 (fixed in firmware, categories below) |
| **Wake timeout** | 20 seconds (no re-wake needed within window) |
| **USB VID:PIDs** | `1a86:7522`, `1a86:7523` (CH340), `10c4:ea60` (CP2102) |

**What the module CAN do:**
- Recognise spoken commands from the 85-item preset vocabulary
- Play preset phrases by ID on its own speaker
- Send recognition events to the Pi over serial (`[0xA5, id, ~id]`)
- Receive playback trigger commands from the Pi over serial (same packet format)

**What the module CANNOT do:**
- Synthesise arbitrary text (it is not a TTS chip)
- Play audio files
- Be reprogrammed at runtime

### 1.2 Pi 5 ALSA Audio Output

The Raspberry Pi 5 has a 3.5mm audio jack (requires `dtparam=audio=on` in `/boot/config.txt`) and supports USB audio adapters. `espeak-ng` and `aplay`/`mpg123` use this path. This is how Boomy speaks **arbitrary text** — it has nothing to do with the voice module's serial port.

| Property | Value |
|---|---|
| **Driver** | ALSA (Advanced Linux Sound Architecture) |
| **Default card** | Set in `/etc/asound.conf` |
| **TTS engine** | `espeak-ng` (install: `sudo apt-get install espeak-ng`) |
| **File playback** | `mpg123` (MP3), `aplay` (WAV) |
| **Relevant env vars** | `YAHBOOM_ESPEAK_VOICE`, `YAHBOOM_ESPEAK_SPEED`, `YAHBOOM_ESPEAK_PITCH` |

### 1.3 Pi 5 USB Microphone (for STT)

For the chatrobot loop, a USB microphone (or the voice module's built-in mics used as a USB audio capture device) provides audio input to the Pi for speech-to-text.

| Property | Value |
|---|---|
| **Input device** | USB mic, or voice module's Type-C as USB audio capture |
| **STT engine** | Vosk (recommended) or Whisper (higher quality, higher latency) |
| **Vosk model** | `vosk-model-small-en-us-0.15` (~50 MB) — real-time on Pi 5 |

---

## 2. Device Conflict: The ttyUSB0 Problem

> [!WARNING]
> This is the most common failure mode. Both the **Rosmaster UART** (IMU/battery/sensors) and the **voice module** enumerate as USB serial devices. Without udev rules, `ttyUSB0` assignment is non-deterministic on each boot.

**Diagnosis:**

```bash
# On Pi — plug in only Rosmaster board, check:
udevadm info -a -n /dev/ttyUSB0 | grep -E "ATTRS{idVendor}|ATTRS{idProduct}" | head -4

# Then plug in voice module too, check both:
ls /dev/ttyUSB*
```

**Fix — stable udev symlinks** (`/etc/udev/rules.d/99-boomy.rules`):

```udev
# Rosmaster expansion board (IMU / battery / gyro via Rosmaster_Lib)
SUBSYSTEM=="tty", ATTRS{idVendor}=="XXXX", ATTRS{idProduct}=="YYYY", \
    SYMLINK+="ttyROSMASTER", MODE="0666", GROUP="dialout"

# Yahboom AI Voice Module
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", \
    SYMLINK+="ttyVOICE", MODE="0666", GROUP="dialout"
```

Replace `XXXX:YYYY` with the Rosmaster board's actual VID:PID from `udevadm` above.

Apply:
```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
ls -la /dev/ttyROSMASTER /dev/ttyVOICE
```

After this: `voice.py` checks `/dev/ttyVOICE` first and warns if falling back to `ttyUSB0` without a `ttyROSMASTER` symlink present.

---

## 3. Serial Protocol

All communication with the CSK4002 module uses a 3-byte binary packet:

```
Byte 0: 0xA5          — header / sync byte (always)
Byte 1: value         — command ID or recognition ID (0x01–0x55)
Byte 2: ~value & 0xFF — bitwise-NOT checksum of byte 1
```

**Examples:**

| Purpose | Bytes (hex) | Notes |
|---|---|---|
| Trigger phrase 1 | `A5 01 FE` | Play preset phrase #1 |
| Trigger phrase 10 | `A5 0A F5` | Play preset phrase #10 |
| Trigger phrase 85 | `A5 55 AA` | Play preset phrase #85 (max) |
| Recognition event | Same format | Module sends this when it hears a command |

**Python packet builder:**

```python
def make_packet(value: int) -> bytes:
    v = value & 0xFF
    return bytes([0xA5, v, (~v) & 0xFF])

# Verify incoming packet:
def verify_packet(data: bytes) -> int | None:
    if len(data) < 3 or data[0] != 0xA5:
        return None
    if data[2] != ((~data[1]) & 0xFF):
        return None
    return data[1]
```

> [!IMPORTANT]
> The old implementation sent ASCII strings like `$say,text#` and `$play,N#`. These are the protocol for the **SYN6288** TTS chip — a completely different module. They do nothing on the CSK4002. All prior code was silently broken.

---

## 4. Preset Phrase Vocabulary

The CSK4002 firmware ships with **85 preset phrases** designed for robot car control. The full list is in Yahboom's download-only PDF. The categories, based on Yahboom's own ROS2 tutorial examples:

| Category | Examples |
|---|---|
| **Wake / acknowledgement** | Wake confirmation chime, "Ready", "OK" |
| **Motion** | Go forward, go backward, turn left, turn right, stop, speed up, slow down, strafe left, strafe right |
| **Modes** | Obstacle avoidance on/off, follow mode on/off, patrol on/off (red/yellow/green/blue lines), auto-drive on/off |
| **Lighting** | Lights on/off, red/green/blue/yellow, all off |
| **Camera** | Take photo, face recognition on/off, gesture control on/off |
| **System** | Battery level report, status OK, low battery warning, startup greeting, shutdown farewell |

**Discovering your firmware's exact mapping** — run this while speaking commands at the module:

```bash
# On Pi (or via MCP listen operation):
python3 -c "
import serial, time
with serial.Serial('/dev/ttyVOICE', 115200, timeout=0.2) as ser:
    print('Listening... say your wake word then commands. Ctrl+C to stop.')
    buf = bytearray()
    while True:
        chunk = ser.read(16)
        if chunk:
            buf.extend(chunk)
        while len(buf) >= 3:
            if buf[0] != 0xA5:
                buf.pop(0); continue
            if buf[2] == ((~buf[1]) & 0xFF):
                print(f'ID={buf[1]:3d}  hex=0x{buf[1]:02X}  time={time.time():.2f}')
                buf = buf[3:]
            else:
                buf.pop(0)
"
```

Or via the MCP server:

```
yahboom(operation="listen", param1=30)   # listen for 30 seconds
```

### 4.1 Customising the Firmware

The preset vocabulary **can be replaced** via firmware reflash. Yahboom's process:

1. Log into the customisation web UI (Chinese, use browser translate). Account: `15338857526` / `Yahboom123`
2. Define a new wake word and up to ~120 command words in English or Chinese
3. The site generates a `.bin` firmware file
4. Flash via Yahboom's burning tool — **Windows only**, connects via the module's Micro-USB "Program" port
5. After flashing, the `[0xA5, id, ~id]` protocol is unchanged; only the IDs and voices differ

This lets you give Boomy a custom name and vocabulary — "Hey Boomy", "Kaffeehaus mode", "Patrol the flat", etc.

---

## 5. MCP Voice Operations Reference

All operations go through `operations/voice.py`. Called via `yahboom(operation=...)` portmanteau or directly via `POST /api/v1/control/tool`.

### `get_status`
Probe the voice module device path, pyserial, and espeak-ng availability.

```python
yahboom(operation="get_status")
# Returns: device path, device_found bool, pyserial_ok, espeak_ok, baud, protocol note
```

### `play` (param1 = phrase ID 1–85)
Trigger playback of a preset phrase via 3-byte binary packet.

```python
yahboom(operation="play", param1=1)       # Phrase #1 (usually a greeting/beep)
yahboom(operation="play", param1=42)      # Phrase #42 (depends on firmware)
```

### `play_beep`
Alias for `play(1)`. Quick system-ready sound.

```python
yahboom(operation="play_beep")
```

### `listen` (param1 = timeout seconds, default 5)
Block and read one recognition event from the module. Useful for agentic workflows.

```python
result = yahboom(operation="listen", param1=10)
# Returns: {"command_id": 7, "status": "recognised"}
#      or: {"command_id": null, "status": "timeout"}
```

### `say` (param1 = text)
Speak arbitrary text via `espeak-ng` on the Pi. Uses ALSA audio output, **not** the voice module speaker.

```python
yahboom(operation="say", param1="Battery at forty percent. Please charge me soon.")
# payload overrides: {"voice": "en-us", "speed": 140, "pitch": 60}
```

Environment variable defaults:

| Variable | Default | Notes |
|---|---|---|
| `YAHBOOM_ESPEAK_VOICE` | `en` | Voice code: `en`, `en-us`, `de`, `ja`, etc. |
| `YAHBOOM_ESPEAK_SPEED` | `150` | Words per minute |
| `YAHBOOM_ESPEAK_PITCH` | `50` | 0–99 |

### `say_file` (param1 = local absolute path to .mp3/.wav)
Upload file to Pi `/tmp/` and play via `mpg123` or `aplay`.

```python
yahboom(operation="say_file", param1=r"E:\Multimedia Files\Music - Blues\Etta James.mp3")
```

### `chat_and_say` (param1 = text, param2 = model name)
Query Ollama on the Pi and speak the response.

```python
yahboom(operation="chat_and_say", param1="What can you do?", param2="gemma3:1b")
# Returns: {"input": ..., "response": ..., "say_result": ...}
```

### `volume` (param1 = 0–100)
Set Pi ALSA master volume. Affects `espeak-ng` output only — does not control the voice module's internal speaker.

```python
yahboom(operation="volume", param1=75)
```

---

## 6. Audio Setup on the Pi

### 6.1 Install espeak-ng

```bash
sudo apt-get update && sudo apt-get install -y espeak-ng
espeak-ng --version          # verify
espeak-ng "Hello, I am Boomy."   # test
```

### 6.2 Identify ALSA audio devices

```bash
aplay -l        # list playback devices
arecord -l      # list capture devices
```

Example output:
```
card 0: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
card 1: vc4hdmi0 [vc4-hdmi-0], device 0: MAI PCM i2s-hifi-0
card 2: Device [USB Audio Device], device 0: USB Audio [USB Audio]
```

### 6.3 Set default ALSA device

If using a USB audio dongle (recommended for best quality):

```bash
# /etc/asound.conf
defaults.pcm.card 2
defaults.ctl.card 2
```

### 6.4 Test the full chain

```bash
# TTS test:
espeak-ng "Systems online. Ready for deployment."

# Preset phrase test (requires pyserial):
python3 -c "
import serial
with serial.Serial('/dev/ttyVOICE', 115200, timeout=2) as s:
    s.write(bytes([0xA5, 0x01, 0xFE]))   # phrase #1
    print('Phrase 1 sent')
"
```

---

## 7. The Chatrobot — Architecture

The chatrobot loop is the primary "party trick" — Boomy listens, thinks, and speaks back. All processing is on-device (Pi 5), fully offline.

```
User speaks wake word
        │
Voice module hears "Hi, Yahboom"
        │
Module sends 0xA5 recognition packet to Pi over serial
        │
chatbot.py: wake event received
        │
Capture ~5s of audio from USB mic / voice module mic (ALSA)
        │
Vosk STT → transcript text
        │
Ollama API call (gemma3:1b on Pi) → response text
        │
espeak-ng → speech output through Pi speaker
        │
(optional) Parse response for motion intent → cmd_vel
        │
Loop back to listening
```

### 7.1 Latency budget on Pi 5

| Stage | Latency |
|---|---|
| Wake detection | ~0 ms (hardware, CSK4002) |
| Audio capture (5s window) | 5000 ms |
| Vosk STT (small model) | ~800 ms |
| Ollama gemma3:1b (~20 words) | ~2000 ms |
| espeak-ng TTS (~20 words) | ~500 ms |
| **Total end-to-end** | **~8 seconds** |

With Whisper tiny instead of Vosk: add ~1500 ms. With a bigger model: multiply Ollama time accordingly. For fluid demo use, gemma3:1b + Vosk is the practical ceiling.

### 7.2 Installing Vosk on the Pi

```bash
pip3 install vosk
# Download the small English model:
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d ~/vosk-models/
```

### 7.3 MCP operation (planned — `operations/chatbot.py`)

```python
yahboom(operation="chatbot_start")   # begins the wake-listen-think-speak loop
yahboom(operation="chatbot_stop")    # ends the loop
yahboom(operation="chatbot_status")  # returns current state and last exchange
```

The loop runs as a background asyncio task, persisting across MCP tool calls.

---

## 8. Troubleshooting

### "Voice module not found" / device missing

1. Check udev symlink: `ls -la /dev/ttyVOICE`
2. If missing: `ls /dev/ttyUSB*` — try `YAHBOOM_VOICE_DEVICE=/dev/ttyUSB1`
3. Set up udev rules (Section 2)
4. Check Docker device mapping if running bringup inside container (see `HARDWARE_DIAGNOSIS_VOICE_I2C.md`)

### "Permission denied" on serial port

```bash
sudo usermod -aG dialout pi
# Re-login required
```

### pyserial not installed

```bash
pip3 install pyserial
# Verify:
python3 -c "import serial; print(serial.__version__)"
```

### espeak-ng not installed

```bash
sudo apt-get install espeak-ng
```

### No audio output from espeak-ng

```bash
aplay -l          # confirm playback device exists
amixer            # check master volume not at 0
speaker-test -t wav -c 2   # basic audio test
# If USB audio dongle: set card in /etc/asound.conf (Section 6.3)
```

### Phrase triggered but nothing heard from module speaker

- Check PH2.0 cable between module and speaker is seated
- Check module power (USB must be 5V, ≥500mA)
- Try a different phrase ID — some IDs may be silent in certain firmware builds

### Ollama not responding in `chat_and_say`

```bash
# On Pi:
ollama serve &           # start if not running
ollama pull gemma3:1b    # pull model if not present
curl http://localhost:11434/api/version   # verify running
```

---

## 9. Environment Variable Reference

All variables set on the **MCP host** (Goliath), not on the Pi.

| Variable | Default | Description |
|---|---|---|
| `YAHBOOM_VOICE_DEVICE` | *(auto)* | Force device path, e.g. `/dev/ttyVOICE` or `/dev/ttyUSB1` |
| `YAHBOOM_VOICE_BAUD` | `115200` | Serial baud rate for CSK4002 |
| `YAHBOOM_ESPEAK_VOICE` | `en` | espeak-ng voice code |
| `YAHBOOM_ESPEAK_SPEED` | `150` | Words per minute (50–400) |
| `YAHBOOM_ESPEAK_PITCH` | `50` | Pitch 0–99 |

---

## 10. See Also

- [`VOICE_AUDIO_UPGRADE.md`](VOICE_AUDIO_UPGRADE.md) — **ReSpeaker Lite + Piper TTS upgrade plan** (recommended next step)
- [`HARDWARE_DIAGNOSIS_VOICE_I2C.md`](HARDWARE_DIAGNOSIS_VOICE_I2C.md) — udev conflict diagnosis, Docker device mapping
- [`SENSORS.md`](SENSORS.md) — IMU, battery, LIDAR, camera sensor reference
- [`../ops/installation.md`](../ops/installation.md) — server startup, environment setup
- [`../../src/yahboom_mcp/operations/voice.py`](../../src/yahboom_mcp/operations/voice.py) — implementation
- [`../../src/yahboom_mcp/operations/chatbot.py`](../../src/yahboom_mcp/operations/chatbot.py) — chatrobot loop (planned)
- [Yahboom Voice Module GitHub](https://github.com/YahboomTechnology/Voice-interaction-module)
- [CSK4002 product page](https://category.yahboom.net/products/voice-interaction)
