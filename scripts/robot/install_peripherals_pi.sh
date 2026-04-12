#!/usr/bin/env bash
# Install Python packages on the Raspberry Pi host for MCP voice (pyserial) and OLED (luma).
# Run on the Pi, or from Windows:
#   ssh pi@<YAHBOOM_IP> 'bash -s' < scripts/robot/install_peripherals_pi.sh
set -euo pipefail

echo "=== Yahboom MCP: Pi peripherals (voice + OLED) ==="

if ! command -v pip3 >/dev/null 2>&1; then
  echo "Installing python3-pip..."
  sudo apt-get update -qq
  sudo apt-get install -y python3-pip python3-serial
fi

echo "--- pip3 install (user) ---"
pip3 install --user --upgrade \
  pyserial \
  luma.oled \
  luma.core \
  pillow \
  smbus2

echo "--- Verify imports ---"
python3 -c "import serial; print('pyserial OK')"
python3 -c "from luma.oled.device import ssd1306; print('luma.oled OK')"

echo ""
echo "If serial open fails with permission denied, add user to dialout:"
echo "  sudo usermod -aG dialout \"\$USER\""
echo "Then log out and back in."
echo "Done."
