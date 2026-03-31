#!/usr/bin/env bash
# Enable ROSBridge to start automatically at boot on the Raspbot v2 (Raspberry Pi).
# The Raspbot image already has ROS 2 and rosbridge_suite; this script only adds a systemd unit.
# Run ONCE on the robot with: sudo bash install-rosbridge-at-boot.sh

set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo: sudo bash install-rosbridge-at-boot.sh"
  exit 1
fi

# Detect ROS distro (Raspbot v2 typically ships with Humble)
if [ -f /opt/ros/humble/setup.bash ]; then
  ROS_DISTRO=humble
elif [ -f /opt/ros/foxy/setup.bash ]; then
  ROS_DISTRO=foxy
else
  echo "ROS 2 not found under /opt/ros. The Raspbot image should include it; check the SD image."
  exit 1
fi

echo "Using ROS 2 $ROS_DISTRO (Raspbot pre-installed)"

# Wrapper script so systemd can run rosbridge with a sourced environment
WRAPPER=/usr/local/bin/rosbridge-launch.sh
cat > "$WRAPPER" << 'WRAPPER_EOF'
#!/usr/bin/env bash
source /opt/ros/ROSDISTRO_PLACEHOLDER/setup.bash
exec ros2 launch rosbridge_server rosbridge_websocket_launch.xml
WRAPPER_EOF
sed -i "s/ROSDISTRO_PLACEHOLDER/$ROS_DISTRO/" "$WRAPPER"
chmod +x "$WRAPPER"

# systemd unit (runs at boot, restarts on failure)
UNIT=/etc/systemd/system/rosbridge.service
cat > "$UNIT" << UNIT_EOF
[Unit]
Description=ROS 2 ROSBridge WebSocket (yahboom-mcp)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/rosbridge-launch.sh
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT_EOF

systemctl daemon-reload
systemctl enable rosbridge.service
systemctl start rosbridge.service

echo "rosbridge.service installed and started. It will start automatically at boot."
echo "Check: systemctl status rosbridge.service"
