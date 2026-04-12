#!/bin/bash
# deactivate_demo.sh — Surgical deactivation of Yahboom Factory Bypass
# Part of yahboom-mcp SOTA v15.0 Hardware Handshake

set -e

echo "--- DEACTIVATING YAHBOOM BYPASS ---"

# 1. Stop the Docker services if they are in a crash loop
echo "[1/3] Stopping yahboom-robot.service..."
sudo systemctl stop yahboom-robot.service || true

# 2. Kill host-level Python demo processes
echo "[2/3] Terminating host-level python demo (raspbot.pyc)..."
sudo pkill -f raspbot.pyc || echo "raspbot.pyc was not running."
sudo pkill -f yb-discover.py || echo "yb-discover.py was not running."

# 3. Verify Serial Port Release
echo "[3/3] Verifying release of /dev/ttyUSB0..."
if fuser /dev/ttyUSB0; then
    echo "⚠️ ERROR: /dev/ttyUSB0 is still locked! Check process list."
    exit 1
else
    echo "✅ SUCCESS: /dev/ttyUSB0 is clear for ROS 2 / Docker passthrough."
fi

echo "--- DEACTIVATION COMPLETE ---"
