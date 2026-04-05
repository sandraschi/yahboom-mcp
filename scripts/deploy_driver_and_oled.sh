#!/usr/bin/env bash
# =============================================================================
# deploy_driver_and_oled.sh
# Deploy the patched Mcnamu driver and set up OLED on the Pi.
# Run from Goliath (Windows) via:
#   ssh pi@<ip> 'bash -s' < scripts/deploy_driver_and_oled.sh
#
# Or run the steps manually from the Pi.
# =============================================================================
set -euo pipefail

ROBOT_IP="${YAHBOOM_IP:-192.168.0.105}"
CONTAINER="yahboom_ros2"
DRIVER_DEST="/root/yahboomcar_ws/install/yahboomcar_bringup/lib/python3.10/site-packages/yahboomcar_bringup/Mcnamu_driver.py"

echo "=== Boomy Driver + OLED Deploy ==="
echo "Container: $CONTAINER"
echo ""

# ── Step 1: Install luma.oled on Pi host ────────────────────────────────────
echo "--- Installing luma.oled on Pi host ---"
pip3 install --quiet luma.oled luma.core pillow smbus2 2>&1 | tail -3
python3 -c "from luma.oled.device import ssd1306; print('luma.oled OK')" 2>&1 || \
    echo "WARNING: luma.oled import failed — check pip3 install output"

# ── Step 2: Probe I2C for OLED address ──────────────────────────────────────
echo ""
echo "--- Probing I2C for OLED (0x3c / 0x3d) ---"
OLED_BUS=""
OLED_ADDR=""
for bus in 1 0 2 3 4; do
    result=$(i2cdetect -y "$bus" 2>/dev/null | grep -oE "3[cd]" | head -1)
    if [ -n "$result" ]; then
        OLED_BUS="$bus"
        OLED_ADDR="0x$result"
        echo "OLED found on bus $bus at $OLED_ADDR"
        break
    fi
done
[ -z "$OLED_BUS" ] && echo "OLED not detected on any I2C bus — check wiring to SDA/SCL pins"

# ── Step 3: Test OLED if found ───────────────────────────────────────────────
if [ -n "$OLED_BUS" ]; then
    echo ""
    echo "--- Testing OLED display ---"
    python3 << PYEOF
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
try:
    serial = i2c(port=${OLED_BUS}, address=${OLED_ADDR})
    device = ssd1306(serial)
    with canvas(device) as draw:
        font = ImageFont.load_default()
        draw.text((0,  0), "Boomy v2",    fill="white", font=font)
        draw.text((0, 16), "OLED OK!",    fill="white", font=font)
        draw.text((0, 32), "Kaffeehaus",  fill="white", font=font)
    print("OLED test OK")
except Exception as e:
    print(f"OLED test FAILED: {e}")
    print("Check: pip3 install luma.oled  AND  i2cdetect -y 1")
PYEOF
fi

# ── Step 4: Write boomy_config.json with discovered OLED info ───────────────
echo ""
echo "--- Writing /home/pi/boomy_config.json ---"
cat > /home/pi/boomy_config.json << JSONEOF
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
  "door_check": {
    "enabled": false,
    "servo_pan": 90,
    "servo_tilt": 80,
    "interval_minutes": 30
  }
}
JSONEOF
echo "Config written to /home/pi/boomy_config.json"
cat /home/pi/boomy_config.json

# ── Step 5: Check if Docker container is running ─────────────────────────────
echo ""
echo "--- Docker container status ---"
if docker ps | grep -q "$CONTAINER"; then
    echo "Container $CONTAINER is running"

    # ── Step 6: Check current device mapping ────────────────────────────────
    echo ""
    echo "--- Device mapping in container ---"
    echo -n "  /dev/ttyUSB0 in container: "
    docker exec "$CONTAINER" ls /dev/ttyUSB0 2>/dev/null && echo "YES" || echo "NO — needs remapping"
    echo -n "  /dev/i2c-1 in container:   "
    docker exec "$CONTAINER" ls /dev/i2c-1 2>/dev/null && echo "YES" || echo "NO — needs remapping"
    echo -n "  /dev/video0 in container:  "
    docker exec "$CONTAINER" ls /dev/video0 2>/dev/null && echo "YES" || echo "NO"

    # ── Step 7: Quick Rosmaster serial test inside container ─────────────────
    echo ""
    echo "--- Rosmaster serial test inside container ---"
    docker exec "$CONTAINER" python3 -c "
import sys, time, os
sys.path.insert(0, '/root/yahboomcar_ws/install/yahboomcar_bringup/lib/python3.10/site-packages/yahboomcar_bringup')
try:
    from Rosmaster_Lib import Rosmaster
    port = '/dev/ttyUSB0'
    bot = Rosmaster(com=port)
    bot.create_receive_threading()
    time.sleep(1.0)
    gyro = bot.get_gyroscope_data()
    volt = bot.get_battery_voltage()
    bot.cancel_receive_threading()
    print(f'Gyro: {gyro}')
    print(f'Voltage: {volt}')
    if volt and float(volt) > 0.1:
        print('ROSMASTER_SERIAL_OK')
    else:
        print('ROSMASTER_SERIAL_NO_DATA — device may not be mapped')
except Exception as e:
    print(f'ROSMASTER_SERIAL_FAIL: {e}')
" 2>&1

    # ── Step 8: Deploy patched driver ────────────────────────────────────────
    echo ""
    echo "--- Deploying patched driver to container ---"
    # The patched driver is in the repo — copy from Pi filesystem
    # (This script assumes it has been scp'd to Pi alongside the repo)
    DRIVER_SRC="${HOME}/Mcnamu_driver_patched.py"

    if [ -f "$DRIVER_SRC" ]; then
        docker cp "$DRIVER_SRC" "$CONTAINER:$DRIVER_DEST"
        echo "Driver deployed to $DRIVER_DEST"
        echo "Restarting container..."
        docker restart "$CONTAINER"
        echo "Container restarted. Wait 10s for bringup..."
        sleep 10
        echo "Driver logs:"
        docker logs "$CONTAINER" --tail 30 2>&1 | grep -E "driver|serial|sensor|ERROR|WARN|OK" || true
    else
        echo "Driver source not found at $DRIVER_SRC"
        echo "Copy the file first: scp Mcnamu_driver_patched.py pi@${ROBOT_IP}:~/"
    fi

else
    echo "Container $CONTAINER not running — skipping Docker steps"
fi

echo ""
echo "=== Deploy complete ==="
echo ""
echo "Next: run scripts/diagnose_sensors.sh to verify"
