#!/usr/bin/env bash
# =============================================================================
# diagnose_sensors.sh
# Run this ON THE PI (or inside the Docker container) to diagnose the
# sensor blackout: IMU/battery/odom topics exist but publish null.
#
# Usage:
#   ssh pi@<robot-ip> 'bash -s' < scripts/diagnose_sensors.sh
# Or copy to Pi and run:
#   scp scripts/diagnose_sensors.sh pi@<robot-ip>:~/
#   ssh pi@<robot-ip> bash ~/diagnose_sensors.sh
# =============================================================================

set -euo pipefail
ROS_SETUP="/opt/ros/humble/setup.bash"
WS_SETUP="$HOME/yahboomcar_ws/install/setup.bash"

echo "============================================================"
echo " Yahboom Raspbot v2 — Sensor Diagnostic"
echo " $(date)"
echo "============================================================"

# --- 1. I2C bus health ---
echo ""
echo "--- I2C Bus (should show 0x2b for MCU) ---"
if command -v i2cdetect &>/dev/null; then
    i2cdetect -y 1 || echo "i2cdetect failed — check /dev/i2c-1 permissions"
else
    echo "i2cdetect not found; install i2c-tools: sudo apt install i2c-tools"
fi

echo "=== 2b. Docker I2C access (CRITICAL) ==="
docker exec yahboom_ros2 ls /dev/i2c* 2>/dev/null || echo "FAIL: /dev/i2c-1 NOT in container — add --device /dev/i2c-1 to docker run"

echo "=== 2c. Rosmaster_Lib direct sensor read ==="
docker exec yahboom_ros2 python3 -c "
import sys, time
sys.path.insert(0, '/root/yahboomcar_ws/install/yahboomcar_bringup/lib/python3.10/site-packages/yahboomcar_bringup')
try:
    from Rosmaster_Lib import Rosmaster
    bot = Rosmaster()
    bot.create_receive_threading()
    time.sleep(1.0)
    print('IMU:', bot.get_imu_data())
    print('Battery:', bot.get_battery_info())
    bot.cancel_receive_threading()
    print('ROSMASTER_LIB_OK')
except Exception as e:
    print(f'ROSMASTER_LIB_FAIL: {e}')
" 2>&1
echo ""
echo "--- ROS 2 Environment ---"
if [[ -f "$ROS_SETUP" ]]; then
    source "$ROS_SETUP"
    echo "ROS_DISTRO=$ROS_DISTRO"
else
    echo "ERROR: $ROS_SETUP not found. ROS 2 Humble not installed?"
    exit 1
fi

if [[ -f "$WS_SETUP" ]]; then
    source "$WS_SETUP"
    echo "Workspace: $WS_SETUP"
else
    echo "WARNING: $WS_SETUP not found. Yahboom workspace may not be built."
fi

# --- 3. Running nodes ---
echo ""
echo "--- Active ROS 2 Nodes ---"
ros2 node list 2>/dev/null || echo "No nodes running. Start bringup first."

# --- 4. Topic list ---
echo ""
echo "--- Active ROS 2 Topics ---"
ros2 topic list 2>/dev/null || echo "Cannot list topics."

# --- 5. Probe each sensor topic ---
echo ""
echo "--- Sensor Topic Probe (1 message each, 3s timeout) ---"

probe_topic() {
    local topic=$1
    local type=$2
    echo -n "  $topic ... "
    result=$(timeout 3 ros2 topic echo "$topic" --once 2>&1 | head -5) || true
    if [[ -z "$result" ]]; then
        echo "NO DATA (topic silent)"
    elif echo "$result" | grep -q "Could not determine"; then
        echo "TYPE ERROR: $result"
    else
        echo "OK"
        echo "$result" | sed 's/^/    /'
    fi
}

probe_topic /imu/data         "sensor_msgs/msg/Imu"
probe_topic /battery_state    "sensor_msgs/msg/BatteryState"
probe_topic /odom             "nav_msgs/msg/Odometry"
probe_topic /ultrasonic       "sensor_msgs/msg/Range"
probe_topic /line_sensor      "std_msgs/msg/Int32MultiArray"
probe_topic /image_raw/compressed "sensor_msgs/msg/CompressedImage"

# --- 6. Camera device ---
echo ""
echo "--- Camera Device ---"
if [[ -e /dev/video0 ]]; then
    echo "  /dev/video0 exists"
    ls -la /dev/video0
    # Check if a camera node is using it
    if fuser /dev/video0 &>/dev/null; then
        echo "  /dev/video0 is held by: $(fuser /dev/video0 2>/dev/null)"
    else
        echo "  /dev/video0 is NOT held by any process (camera node not running)"
    fi
else
    echo "  /dev/video0 NOT FOUND — camera not connected or not mapped into container"
fi

# --- 7. Publish rate check ---
echo ""
echo "--- Topic Publish Rates (3s window) ---"
check_hz() {
    local topic=$1
    echo -n "  $topic Hz: "
    timeout 4 ros2 topic hz "$topic" 2>&1 | grep -E "average rate|no new messages" | head -1 || echo "timeout/no data"
}
check_hz /imu/data
check_hz /battery_state
check_hz /odom

# --- 8. MCU driver check ---
echo ""
echo "--- Yahboom Driver Processes ---"
ps aux | grep -E "[Mm]cnamu|[Rr]osmaster|yahboom" | grep -v grep || echo "No Yahboom driver processes found"

# --- 9. dmesg I2C errors ---
echo ""
echo "--- Recent dmesg I2C/timeout errors ---"
dmesg --notime 2>/dev/null | grep -iE "i2c|timeout|error" | tail -10 || \
    journalctl -k --no-pager -n 20 2>/dev/null | grep -iE "i2c|timeout" || \
    echo "Cannot read dmesg (try sudo)"

echo ""
echo "============================================================"
echo " Diagnostic complete. Share this output when reporting issues."
echo "============================================================"
