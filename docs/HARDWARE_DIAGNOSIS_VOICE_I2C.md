# Boomy Hardware: Full Diagnosis & Fixes

**Date:** 2026-04-04
**Status:** Root causes identified, fixes documented
**Tags:** [yahboom-mcp, boomy, hardware, uart, i2c, oled, sensors, voice, critical]
**Supersedes:** `HARDWARE_DIAGNOSIS_VOICE_I2C.md` (partial — this is the complete picture)

---

## Critical Discovery: The Sensor Bus is UART, Not I2C

Reading `Mcnamu_driver_patched.py` reveals the actual hardware architecture:

```python
# Motion Controller — I2C (Raspbot class)
self.car = Raspbot()                        # Uses /dev/i2c-1, addr 0x2b

# Sensor Controller — UART SERIAL (Rosmaster class)
self.sensors = Rosmaster(com='/dev/ttyUSB0')  # ← SERIAL PORT
self.sensors.create_receive_threading()
```

**This rewrites the diagnosis completely:**

| Component | Bus | Port | Status |
|---|---|---|---|
| Motor control (wheels) | I2C | `/dev/i2c-1`, addr `0x2b` | ✅ Working |
| Lightstrip (RGB) | I2C | via `Raspbot.Ctrl_WQ2812_brightness_ALL()` | ✅ Working |
| Ultrasonic | I2C | `Raspbot.read_data_array(0x1b/0x1a)` | Working if I2C OK |
| Line follower | I2C | `Raspbot.read_data_array(0x0a)` | Working if I2C OK |
| **IMU / Battery / Gyro** | **UART** | **`/dev/ttyUSB0`** | ❌ Serial conflict |
| **Voice/audio hat** | **UART** | **`/dev/ttyUSB0`** | ❌ Same port! |
| OLED display | I2C | `/dev/i2c-1`, addr `0x3c` | ❌ Wrong library |

---

## Problem 1: IMU and Voice Hat are Fighting Over `/dev/ttyUSB0`

The `Rosmaster` sensor library opens `/dev/ttyUSB0` for IMU/battery/gyro data.
The Yahboom voice module also connects as a USB serial device — likely also `/dev/ttyUSB0`
or `/dev/ttyUSB1`.

If only one USB serial device is plugged in, both try to use it and the voice protocol
corrupts the sensor stream (or vice versa). If both are plugged in, which gets `ttyUSB0`
depends on USB enumeration order (not deterministic).

**The fix: assign stable device names via udev rules.**

### Udev rules for stable device names

Run this on the Pi host to identify the USB IDs of each device:

```bash
# Plug in ONLY the ROSMASTER expansion board USB, then:
udevadm info /dev/ttyUSB0 | grep -E "ID_VENDOR_ID|ID_MODEL_ID|ID_SERIAL"

# Unplug, plug in ONLY the voice hat USB, then:
udevadm info /dev/ttyUSB0 | grep -E "ID_VENDOR_ID|ID_MODEL_ID|ID_SERIAL"
```

Then create `/etc/udev/rules.d/99-boomy.rules`:

```udev
# Yahboom ROSMASTER serial (sensor data — IMU, battery, gyro)
# Replace XXXX:YYYY with actual VID:PID from udevadm above
SUBSYSTEM=="tty", ATTRS{idVendor}=="XXXX", ATTRS{idProduct}=="YYYY", \
    SYMLINK+="ttyROSMASTER", MODE="0666", GROUP="dialout"

# Yahboom AI Voice Module (TTS/STT serial)
# Replace AAAA:BBBB with actual VID:PID of voice hat
SUBSYSTEM=="tty", ATTRS{idVendor}=="AAAA", ATTRS{idProduct}=="BBBB", \
    SYMLINK+="ttyVOICE", MODE="0666", GROUP="dialout"
```

Apply:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
ls -la /dev/ttyROSMASTER /dev/ttyVOICE   # verify symlinks created
```

Then update `Mcnamu_driver_patched.py`:
```python
self.sensors = Rosmaster(com='/dev/ttyROSMASTER')
```

And `voice.py`:
```python
_VOICE_DEVICES = ["/dev/ttyVOICE", "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0"]
```

### Quick test without udev (if only one device plugged in)

If the voice hat is NOT currently plugged in:
```bash
# On Pi host
ls /dev/ttyUSB*    # should show only ttyUSB0
python3 -c "
from Rosmaster_Lib import Rosmaster
import time
bot = Rosmaster(com='/dev/ttyUSB0')
bot.create_receive_threading()
time.sleep(1.0)
print('Gyro:', bot.get_gyroscope_data())
print('Accel:', bot.get_accelerometer_data())
print('Battery:', bot.get_battery_voltage())
bot.cancel_receive_threading()
"
```

If this returns real data: sensor UART works. The issue is purely the device conflict.

---

## Problem 2: Docker Not Mapping Serial Devices

The Docker container may not have `/dev/ttyUSB0` mapped in. This would make
`Rosmaster(com='/dev/ttyUSB0')` fail silently inside the container.

**Check:**
```bash
docker exec yahboom_ros2 ls /dev/ttyUSB* 2>/dev/null || echo "MISSING"
```

**Fix — recreate the container with device mapping:**

If using `docker run` directly, add:
```bash
docker run \
  --device /dev/ttyUSB0:/dev/ttyUSB0 \
  --device /dev/ttyUSB1:/dev/ttyUSB1 \
  --device /dev/ttyACM0:/dev/ttyACM0 \
  --device /dev/i2c-1:/dev/i2c-1 \
  --device /dev/video0:/dev/video0 \
  --device /dev/snd:/dev/snd \
  --group-add dialout \
  --group-add audio \
  --group-add i2c \
  ... (other flags) ...
  yahboom_ros2:latest
```

**If using docker-compose**, add to the service:
```yaml
services:
  yahboom_ros2:
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
      - /dev/ttyUSB1:/dev/ttyUSB1
      - /dev/ttyACM0:/dev/ttyACM0
      - /dev/i2c-1:/dev/i2c-1
      - /dev/video0:/dev/video0
      - /dev/snd:/dev/snd
    group_add:
      - dialout
      - audio
      - i2c
```

**If the bringup runs directly on the Pi host** (outside Docker), this is moot —
but voice operations via `voice.py` (SSH path) already run on host, so they're fine.

---

## Problem 3: OLED — Wrong Library

The scripts in `scripts/` have been searching for `Adafruit_SSD1306`, which is a
Python 2 / deprecated library not typically present in the Yahboom Humble image.
The correct library is `luma.oled`.

The `display.py` operation was already rewritten to use luma.oled correctly. The
issue is whether luma is installed on the Pi host (for the SSH path) or inside Docker.

**Check and install:**
```bash
# On Pi host
python3 -c "from luma.oled.device import ssd1306; print('OK')" 2>&1

# If not installed:
pip3 install luma.oled luma.core pillow

# Check I2C bus for OLED address:
i2cdetect -y 1   # look for 3c or 3d
```

**Confirm the OLED I2C bus number.** The Raspbot V2 OLED connects to the Pi's
I2C-1 bus by default (GPIO pins 3/5), but some boards use I2C-3 or I2C-4 on Pi 5.
The Pi 5 has multiple I2C buses:

```bash
# Scan all possible buses
for bus in 0 1 2 3 4; do
    result=$(i2cdetect -y $bus 2>/dev/null | grep -o "3[cd]")
    [ -n "$result" ] && echo "OLED found on bus $bus at 0x$result"
done
```

**Once confirmed, test luma directly:**
```bash
python3 - << 'EOF'
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

serial = i2c(port=1, address=0x3c)   # change port if found on different bus
device = ssd1306(serial)

with canvas(device) as draw:
    font = ImageFont.load_default()
    draw.text((0, 0),  "Boomy v2",    fill="white", font=font)
    draw.text((0, 14), "Kaffeehaus",  fill="white", font=font)
    draw.text((0, 28), "Demo Bereit", fill="white", font=font)

print("OLED OK")
EOF
```

---

## Problem 4: Battery State and IMU — Dependency Chain

Once the UART conflict is resolved (Problem 1 + 2), battery and IMU should work
automatically because `Mcnamu_driver_patched.py` already has correct code:

```python
# Battery — already correct
volt = self.sensors.get_battery_voltage()
bat_msg.voltage = float(volt)
bat_msg.percentage = (bat_msg.voltage - 9.0) / (12.6 - 9.0)  # 9V=0%, 12.6V=100%

# IMU — already correct
acc  = self.sensors.get_accelerometer_data()   # [ax, ay, az]
gyro = self.sensors.get_gyroscope_data()       # [gx, gy, gz] in deg/s
```

The only bugs are the exception-swallowing `except: pass` clauses which hide errors.
**For debugging**, temporarily change these to `except Exception as e: print(e)`.

### Battery percentage formula check

The formula `(voltage - 9.0) / (12.6 - 9.0)` assumes:
- 3S LiPo: 3 × 4.2V = 12.6V full, 3 × 3.0V = 9.0V empty
- This is correct for the Raspbot V2's 11.1V nominal (3S) pack

If the battery shows 0% at full charge, the pack may be 2S (7.4V nominal):
```python
# 2S pack: full=8.4V, empty=6.0V
bat_msg.percentage = (bat_msg.voltage - 6.0) / (8.4 - 6.0)
```

Check actual voltage with a multimeter and adjust the formula.

---

## Ordered Fix Sequence

Do these in order. Each step unblocks the next.

### Step 1: Identify USB devices (5 minutes)

```bash
# On Pi — plug in ONLY the ROSMASTER board USB cable, run:
udevadm info -a -n /dev/ttyUSB0 | grep -E "ATTRS{idVendor}|ATTRS{idProduct}" | head -4
# Note the VID and PID

# Then plug in the voice hat too, run:
ls /dev/ttyUSB*   # if two devices: ttyUSB0 and ttyUSB1
# Identify which is which by unplugging one at a time
```

### Step 2: Create udev rules (10 minutes)

Use the VIDs/PIDs from Step 1 to create `/etc/udev/rules.d/99-boomy.rules` (see above).
Reload and verify `/dev/ttyROSMASTER` and `/dev/ttyVOICE` appear.

### Step 3: Update Mcnamu_driver_patched.py serial port (2 minutes)

Change `Rosmaster(com='/dev/ttyUSB0')` to `Rosmaster(com='/dev/ttyROSMASTER')`.
This file needs to be deployed into the Docker container at:
`/root/yahboomcar_ws/install/yahboomcar_bringup/lib/python3.10/site-packages/yahboomcar_bringup/Mcnamu_driver.py`

### Step 4: Map devices into Docker (5 minutes)

Find how the container is currently started:
```bash
docker inspect yahboom_ros2 | grep -A 20 '"HostConfig"' | grep -E "Devices|Binds"
```
Add the device flags and restart the container.

### Step 5: Add debug logging to driver (10 minutes)

Temporarily change `except: pass` to `except Exception as e: self.get_logger().error(str(e))`
in `pub_data()`. Restart, watch logs: `docker logs -f yahboom_ros2`.

### Step 6: Install luma.oled and test OLED (5 minutes)

Install on Pi host and test with the script above. If it works, `display.py` via SSH
will also work immediately — no Docker changes needed for OLED.

### Step 7: Verify with diagnose_sensors.sh

Run `scripts/diagnose_sensors.sh` after the above. All sections should pass.

---

## Battery Low Warning — Kaffeehaus Demo Protection

Once battery state is working, add a pre-demo check to `demo.py`:

```python
async def run_demo(bridge, ssh):
    # Safety check before starting
    tele = bridge.get_full_telemetry()
    battery = tele.get("battery")
    if battery is not None and battery < 25:
        await voice.execute(operation="say",
            param1=f"Akku nur bei {battery:.0f} Prozent. Demo abgebrochen. "
                   "Bitte laden Sie mich zuerst auf.")
        return {"success": False, "reason": "battery_low", "battery": battery}

    # ... rest of demo
```

And in the watchdog, a periodic low-battery announcement:
```python
# Every 5 minutes during autonomous operation
if battery < 20:
    await voice.execute(operation="say",
        param1="Warnung: Akku niedrig. Ich brauche bald Strom.")
    await lightstrip.execute(operation="set", param1=255, param2=50, param3=0)
```

---

## Summary: What Was Actually Wrong

| Problem | Real cause | Fix |
|---|---|---|
| IMU/battery null | Rosmaster uses UART `/dev/ttyUSB0`, possibly not mapped into Docker, or conflicting with voice hat | Udev stable names + Docker device mapping |
| Voice hat silent | `/dev/ttyUSB0` conflict with Rosmaster OR device not mapped in Docker | Udev stable names; voice.py SSH path bypasses Docker anyway |
| OLED not working | Code was using `Adafruit_SSD1306` (not installed); `display.py` was rewritten for luma but luma may not be installed | `pip3 install luma.oled` on Pi host |
| Sensors "topics exist but null" | Driver has `except: pass` everywhere, hiding the real error | Add logging, fix device path |
| I2C itself | Fine — wheels and lights prove it works | No action needed |
