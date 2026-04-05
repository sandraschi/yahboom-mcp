#!/usr/bin/env bash
# =============================================================================
# start_camera.sh
# Start the ROS 2 camera node on the Pi (or inside Docker).
# Run this if /image_raw/compressed has no data.
#
# Usage (on Pi directly):
#   bash scripts/start_camera.sh
#
# Usage (via MCP SSH bridge or terminal):
#   ssh pi@<robot-ip> 'bash -s' < scripts/start_camera.sh
#
# Usage (inside Docker container):
#   docker exec yahboom_ros2 bash -c "$(cat scripts/start_camera.sh)"
# =============================================================================

set -euo pipefail
ROS_SETUP="/opt/ros/humble/setup.bash"
WS_SETUP="$HOME/yahboomcar_ws/install/setup.bash"

source "$ROS_SETUP"
[[ -f "$WS_SETUP" ]] && source "$WS_SETUP"

DEVICE="${CAMERA_DEVICE:-/dev/video0}"
TOPIC="${CAMERA_TOPIC:-/image_raw}"

echo "Starting camera node on device $DEVICE → topic $TOPIC"

# Check device exists
if [[ ! -e "$DEVICE" ]]; then
    echo "ERROR: $DEVICE not found."
    echo "  If running in Docker, ensure the device is mapped:"
    echo "  docker run --device=$DEVICE ..."
    echo "  or: docker exec with device access"
    exit 1
fi

# Try usb_cam first (standard Humble package)
if ros2 pkg list 2>/dev/null | grep -q "usb_cam"; then
    echo "Using usb_cam package"
    ros2 run usb_cam usb_cam_node_exe \
        --ros-args \
        -p video_device:="$DEVICE" \
        -p image_width:=640 \
        -p image_height:=480 \
        -p framerate:=30.0 \
        -p pixel_format:=mjpeg2rgb \
        -r /image_raw:="$TOPIC" \
        &
    CAM_PID=$!
    echo "usb_cam started (PID $CAM_PID)"

# Fallback: v4l2_camera
elif ros2 pkg list 2>/dev/null | grep -q "v4l2_camera"; then
    echo "Using v4l2_camera package"
    ros2 run v4l2_camera v4l2_camera_node \
        --ros-args \
        -p video_device:="$DEVICE" \
        &
    CAM_PID=$!
    echo "v4l2_camera started (PID $CAM_PID)"

else
    echo "ERROR: Neither usb_cam nor v4l2_camera found."
    echo "Install one:"
    echo "  sudo apt install ros-humble-usb-cam"
    echo "  # or"
    echo "  sudo apt install ros-humble-v4l2-camera"
    exit 1
fi

sleep 2

# Verify topic is publishing
echo "Checking /image_raw/compressed ..."
timeout 5 ros2 topic echo /image_raw/compressed --once &>/dev/null && \
    echo "Camera topic publishing OK" || \
    echo "WARNING: /image_raw/compressed not publishing yet. Check node logs."

echo "Camera node running. PID $CAM_PID"
echo "Topic: /image_raw/compressed (compressed by image_transport)"
echo "To stop: kill $CAM_PID"
