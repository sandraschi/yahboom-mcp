#!/usr/bin/env bash
# setup-autostart.sh - Automate Yahboom Raspbot v2 ROS 2 services via Docker.
# Run ONCE on the robot: sudo bash setup-autostart.sh

set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo: sudo bash setup-autostart.sh"
  exit 1
fi

# 1. Ensure the Docker container starts automatically
echo "Configuring Docker container to restart always..."
docker update --restart always yahboom_ros2 || true

# 2. Create the launch wrapper on the host
WRAPPER=/usr/local/bin/yahboom-launch.sh
echo "Creating launch wrapper at $WRAPPER..."
cat > "$WRAPPER" << 'WRAPPER_EOF'
#!/usr/bin/env bash
# Wait for Docker to be ready
until docker ps > /dev/null 2>&1; do sleep 1; done

# Wait for container to be running
until [ "$(docker inspect -f '{{.State.Running}}' yahboom_ros2 2>/dev/null)" == "true" ]; do sleep 1; done

echo "Starting ROSBridge and Yahboom Driver inside container..."
docker exec yahboom_ros2 bash -c '
    source /opt/ros/humble/setup.bash
    source /root/yahboomcar_ws/install/setup.bash
    
    # Start ROSBridge in background
    ros2 launch rosbridge_server rosbridge_websocket_launch.xml &
    
    # Start Yahboom Driver
    ros2 launch yahboomcar_bringup yahboomcar_bringup.launch.py
'
WRAPPER_EOF

chmod +x "$WRAPPER"

# 3. Create the systemd service
UNIT=/etc/systemd/system/yahboom-robot.service
echo "Creating systemd unit at $UNIT..."
cat > "$UNIT" << UNIT_EOF
[Unit]
Description=Yahboom Raspbot v2 ROS 2 Services (Docker)
After=docker.service network-online.target
Wants=docker.service network-online.target

[Service]
Type=simple
ExecStart=$WRAPPER
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT_EOF

# 4. Enable and start
systemctl daemon-reload
systemctl enable yahboom-robot.service
systemctl restart yahboom-robot.service

echo "Setup complete. yahboom-robot.service is active."
echo "Check logs: journalctl -u yahboom-robot.service -f"
