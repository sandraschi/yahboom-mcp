#!/usr/bin/env bash
# =============================================================================
# boomy_full_setup.sh  —  Complete Pi-side setup for Boomy
#
# Runs all fixes in the correct order:
#   1. udev device rules (stable /dev/ttyROSMASTER, /dev/ttyVOICE)
#   2. luma.oled + smbus2 install
#   3. OLED probe + test
#   4. Rosmaster serial test (outside Docker)
#   5. Docker device mapping check + report
#   6. Patched driver deployment
#   7. luma.oled install inside Docker too
#   8. boomy_config.json
#   9. Final diagnose_sensors summary
#
# Run from Goliath:
#   scp scripts/boomy_full_setup.sh pi@192.168.0.105:~/
#   scp Mcnamu_driver_patched.py    pi@192.168.0.105:~/
#   ssh pi@192.168.0.105 bash boomy_full_setup.sh
#
# Or pipe directly:
#   ssh pi@192.168.0.105 'bash -s' < scripts/boomy_full_setup.sh
# (Note: driver file must be scp'd separately when piping)
# =============================================================================
set -euo pipefail

CONTAINER="yahboom_ros2"
DRIVER_DEST="/root/yahboomcar_ws/install/yahboomcar_bringup/lib/python3.10/site-packages/yahboomcar_bringup/Mcnamu_driver.py"
DRIVER_SRC="${HOME}/Mcnamu_driver_patched.py"
CONFIG_FILE="/home/pi/boomy_config.json"

ok()   { echo "  ✓ $*"; }
fail() { echo "  ✗ $*"; }
info() { echo ""; echo "=== $* ==="; }

# ── 1. udev rules ────────────────────────────────────────────────────────────
info "1. USB Device Rules"

cat > /etc/udev/rules.d/99-boomy.rules << 'RULES'
# Yahboom ROSMASTER serial — CH340 variants (sensor data: IMU, battery, gyro)
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", \
    SYMLINK+="ttyROSMASTER", MODE="0666", GROUP="dialout"
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7522", \
    SYMLINK+="ttyROSMASTER", MODE="0666", GROUP="dialout"

# Yahboom AI Voice Module — CP2102
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", \
    SYMLINK+="ttyVOICE", MODE="0666", GROUP="dialout"

# I2C + audio permissions
SUBSYSTEM=="i2c-dev", MODE="0666", GROUP="i2c"
SUBSYSTEM=="sound",   MODE="0666", GROUP="audio"
RULES

udevadm control --reload-rules
udevadm trigger --subsystem-match=tty
sleep 1

[ -L /dev/ttyROSMASTER ] && ok "ttyROSMASTER → $(readlink /dev/ttyROSMASTER)" \
    || fail "ttyROSMASTER not created — check VID:PID with: udevadm info -a -n /dev/ttyUSB0 | grep idVendor"
[ -L /dev/ttyVOICE ] && ok "ttyVOICE → $(readlink /dev/ttyVOICE)" \
    || fail "ttyVOICE not created — voice hat may not be plugged in or uses different VID:PID"

# List current USB serial devices for reference
echo "  USB serial devices found:"
for d in /dev/ttyUSB* /dev/ttyACM*; do
    [ -e "$d" ] && echo "    $d" || true
done

# ── 2. Python packages on host ────────────────────────────────────────────────
info "2. Installing Python packages on Pi host"

pip3 install --quiet --break-system-packages \
    luma.oled luma.core pillow smbus2 2>&1 | tail -2

python3 -c "from luma.oled.device import ssd1306; print('luma.oled OK')" 2>&1 \
    && ok "luma.oled installed" || fail "luma.oled install failed"

python3 -c "import smbus2; print('smbus2 OK')" 2>&1 \
    && ok "smbus2 installed" || fail "smbus2 install failed"

# ── 3. OLED probe ─────────────────────────────────────────────────────────────
info "3. OLED I2C Probe"

OLED_BUS=""
OLED_ADDR=""
for bus in 1 0 2 3 4; do
    result=$(i2cdetect -y "$bus" 2>/dev/null | grep -oE "3[cd]" | head -1 || true)
    if [ -n "$result" ]; then
        OLED_BUS="$bus"
        OLED_ADDR="0x$result"
        ok "OLED found: bus $bus, addr $OLED_ADDR"
        break
    fi
done
[ -z "$OLED_BUS" ] && fail "OLED not found on any I2C bus — check wiring to pins 3(SDA)/5(SCL)"

# Test OLED if found
if [ -n "$OLED_BUS" ]; then
    python3 << PYEOF 2>&1 && ok "OLED display test passed" || fail "OLED display test failed"
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
serial = i2c(port=${OLED_BUS}, address=${OLED_ADDR})
device = ssd1306(serial)
with canvas(device) as draw:
    font = ImageFont.load_default()
    draw.text((0,  0), "Boomy Setup",  fill="white", font=font)
    draw.text((0, 14), "OK!",          fill="white", font=font)
print("OLED_DRAW_OK")
PYEOF
fi

# ── 4. Rosmaster serial test (host, not Docker) ───────────────────────────────
info "4. Rosmaster Serial Test (Pi host)"

SENSOR_PORT="/dev/ttyROSMASTER"
[ -e "$SENSOR_PORT" ] || SENSOR_PORT="/dev/ttyUSB0"
echo "  Using port: $SENSOR_PORT"

python3 << PYEOF 2>&1
import sys, time, os
sys.path.insert(0, '/root/yahboomcar_ws/install/yahboomcar_bringup/lib/python3.10/site-packages/yahboomcar_bringup')
try:
    from Rosmaster_Lib import Rosmaster
    bot = Rosmaster(com='${SENSOR_PORT}')
    bot.create_receive_threading()
    time.sleep(1.5)
    gyro = bot.get_gyroscope_data()
    volt = bot.get_battery_voltage()
    bot.cancel_receive_threading()
    print(f'Gyro: {gyro}')
    print(f'Voltage: {volt}V')
    if volt and float(volt) > 0.5:
        print('ROSMASTER_OK')
    else:
        print('ROSMASTER_NO_DATA')
except Exception as e:
    print(f'ROSMASTER_FAIL: {e}')
PYEOF

# ── 5. Docker device mapping check ───────────────────────────────────────────
info "5. Docker Device Mapping"

if ! docker ps | grep -q "$CONTAINER"; then
    fail "Container $CONTAINER not running — skipping Docker checks"
else
    echo "  Container: $CONTAINER"

    check_dev() {
        local dev="$1"
        local label="$2"
        if docker exec "$CONTAINER" ls "$dev" >/dev/null 2>&1; then
            ok "$label ($dev) mapped"
        else
            fail "$label ($dev) NOT mapped — add --device $dev:$dev to docker run"
        fi
    }

    check_dev /dev/ttyUSB0   "Sensor serial"
    check_dev /dev/i2c-1     "I2C bus"
    check_dev /dev/video0    "Camera"

    # Check ttyROSMASTER symlink inside container
    if docker exec "$CONTAINER" ls /dev/ttyROSMASTER >/dev/null 2>&1; then
        ok "ttyROSMASTER symlink visible in container"
    else
        fail "ttyROSMASTER not in container (udev symlinks don't propagate) — use --device /dev/ttyUSB0"
    fi

    # ── 6. Deploy patched driver ──────────────────────────────────────────────
    info "6. Deploy Patched Driver"

    if [ -f "$DRIVER_SRC" ]; then
        docker cp "$DRIVER_SRC" "$CONTAINER:$DRIVER_DEST"
        ok "Driver deployed to $DRIVER_DEST"

        # ── 7. Install luma inside Docker ─────────────────────────────────────
        info "7. Install luma.oled inside Docker"
        docker exec "$CONTAINER" pip3 install --quiet luma.oled luma.core pillow 2>&1 | tail -2 \
            && ok "luma.oled installed in container" || fail "luma.oled install in container failed"

        # Restart container
        echo "  Restarting $CONTAINER..."
        docker restart "$CONTAINER"
        echo "  Waiting 12s for bringup..."
        sleep 12

        # Check driver started
        echo "  Driver startup logs:"
        docker logs "$CONTAINER" --tail 20 2>&1 \
            | grep -E "serial|sensor|IMU|battery|ERROR|WARNING|OK|driver" \
            | head -15 || true

    else
        fail "Patched driver not found at $DRIVER_SRC"
        fail "Run: scp Mcnamu_driver_patched.py pi@<ip>:~/"
    fi

    # ── 8. Post-restart sensor test inside Docker ─────────────────────────────
    info "8. Sensor Test inside Docker (post-restart)"
    sleep 3

    docker exec "$CONTAINER" python3 << PYEOF 2>&1
import sys, time
sys.path.insert(0, '/root/yahboomcar_ws/install/yahboomcar_bringup/lib/python3.10/site-packages/yahboomcar_bringup')
try:
    from Rosmaster_Lib import Rosmaster
    import os
    port = '/dev/ttyROSMASTER' if os.path.exists('/dev/ttyROSMASTER') else '/dev/ttyUSB0'
    bot = Rosmaster(com=port)
    bot.create_receive_threading()
    time.sleep(1.5)
    gyro = bot.get_gyroscope_data()
    volt = bot.get_battery_voltage()
    bot.cancel_receive_threading()
    print(f'CONTAINER GYRO: {gyro}')
    print(f'CONTAINER VOLT: {volt}')
    print('CONTAINER_SENSOR_OK' if volt and float(volt) > 0.5 else 'CONTAINER_SENSOR_FAIL')
except Exception as e:
    print(f'CONTAINER_SENSOR_FAIL: {e}')
PYEOF

fi  # end Docker section

# ── 9. Write boomy_config.json ────────────────────────────────────────────────
info "9. Writing boomy_config.json"

cat > "$CONFIG_FILE" << JSONEOF
{
  "oled": {
    "enabled": $([ -n "$OLED_BUS" ] && echo true || echo false),
    "bus": ${OLED_BUS:-1},
    "address": "${OLED_ADDR:-0x3c}",
    "driver": "ssd1306",
    "width": 128,
    "height": 64
  },
  "sensor_serial": {
    "port_symlink": "/dev/ttyROSMASTER",
    "port_fallback": "/dev/ttyUSB0",
    "baud": 115200
  },
  "voice_serial": {
    "port_symlink": "/dev/ttyVOICE",
    "port_fallback": "/dev/ttyUSB1",
    "baud": 9600
  },
  "battery": {
    "cell_count": 3,
    "cell_full_v": 4.20,
    "cell_empty_v": 3.00,
    "low_warning_pct": 20,
    "critical_pct": 15
  },
  "demo": {
    "forward_speed": 0.20,
    "turn_speed": 0.50,
    "language": "de"
  },
  "door_check": {
    "enabled": false,
    "servo_pan": 90,
    "servo_tilt": 80,
    "interval_minutes": 30
  }
}
JSONEOF
ok "Config written to $CONFIG_FILE"

# ── Final summary ─────────────────────────────────────────────────────────────
info "Setup Complete — Summary"
echo ""
echo "  ttyROSMASTER: $([ -L /dev/ttyROSMASTER ] && readlink /dev/ttyROSMASTER || echo NOT_CREATED)"
echo "  ttyVOICE:     $([ -L /dev/ttyVOICE ]     && readlink /dev/ttyVOICE     || echo NOT_CREATED)"
echo "  OLED:         ${OLED_ADDR:-NOT_FOUND} on bus ${OLED_BUS:-?}"
echo "  luma.oled:    $(python3 -c 'from luma.oled.device import ssd1306; print("OK")' 2>/dev/null || echo NOT_INSTALLED)"
echo ""
echo "Next: run scripts/diagnose_sensors.sh for full sensor check"
echo "Then: YAHBOOM_E2E=1 YAHBOOM_IP=<ip> pytest tests/e2e/ -v -s"
