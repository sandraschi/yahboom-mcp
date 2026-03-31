import logging
import base64
import asyncio
import threading
from typing import Optional
import cv2
import numpy as np
import roslibpy

logger = logging.getLogger("yahboom-mcp.core.video_bridge")

class VideoBridge:
    """
    Bridge for receiving ROS 2 camera images and providing them via HTTP/MJPEG.
    Supports both compressed and raw image formats.
    """

    def __init__(self, ros_client: roslibpy.Ros, topic_name: str = "/image_raw/compressed", ssh_bridge=None):
        self.ros = ros_client
        self.topic_name = topic_name
        self.topic: Optional[roslibpy.Topic] = None
        self.last_frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()
        self.active = False
        self.frame_count = 0
        self.ssh = ssh_bridge

    def start(self):
        """Start subscribing and auto-launch the camera node inside Docker if needed."""
        if self.active:
            return

        logger.info("Starting VideoBridge with Auto-Activation...")
        
        # 1. Trigger camera node launch inside yahboom_ros2 Docker container
        if self.ssh:
            # Direct ros2 run for Microdia USB Webcam at 720p (1280x720)
            # Optimization: Use 'mjpeg' pixel format for native 30Hz support
            launch_cmd = (
                "ros2 run usb_cam usb_cam_node_exe "
                "--ros-args "
                "-p video_device:=/dev/video0 "
                "-p image_width:=1280 "
                "-p image_height:=720 "
                "-p pixel_format:=mjpeg "
                "-p io_method:=mmap "
                "-p framerate:=30.0 "
                "-p camera_name:=raspbot_cam"
            )
            docker_cmd = f"docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && {launch_cmd}' &"
            
            # Kill any existing camera node first to prevent device busy errors
            self.ssh.execute("docker exec yahboom_ros2 pkill -f usb_cam_node_exe || true")
            
            self.ssh.execute(docker_cmd)
            logger.info("Executed 720p hardware-verified camera node activation.")

        # 2. Subscribe to the standard Yahboom compressed topic
        self.topic_name = "/image_raw/compressed" 
        topic_type = "sensor_msgs/CompressedImage"

        self.topic = roslibpy.Topic(self.ros, self.topic_name, topic_type)
        self.topic.subscribe(self._image_callback)
        self.active = True
        
        logger.info(f"Subscribed to {self.topic_name}. Stream active.")

    def _image_callback(self, message):
        """Decode incoming ROS 2 sensor_msgs/Image (or CompressedImage)."""
        try:
            # Detect data field
            data = message.get("data")
            if not data:
                return

            # Decode from base64 if it's a string (common in roslibpy/rosbridge)
            if isinstance(data, str):
                image_bytes = base64.b64decode(data)
            else:
                image_bytes = bytes(data)

            # 1. Attempt Compressed Decoding (JPEG/PNG)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # 2. Fallback: Raw Image Handing (sensor_msgs/Image)
            if frame is None:
                width = message.get("width")
                height = message.get("height")
                encoding = message.get("encoding", "rgb8").lower()
                
                if width and height:
                    if encoding in ("rgb8", "bgr8"):
                        frame = np.frombuffer(image_bytes, dtype=np.uint8).reshape((height, width, 3))
                        if encoding == "rgb8":
                            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    elif encoding == "mono8":
                        frame = np.frombuffer(image_bytes, dtype=np.uint8).reshape((height, width))
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    elif encoding == "yuv422":
                        # Common on some Yahboom/Raspberry Pi cameras
                        frame = np.frombuffer(image_bytes, dtype=np.uint8).reshape((height, width, 2))
                        frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_YUYV)

            if frame is not None:
                with self.frame_lock:
                    self.last_frame = frame
                    self.frame_count += 1
            else:
                if self.frame_count == 0:
                    logger.warning(f"Could not decode frame from {self.topic_name}. Encoding: {message.get('encoding')}")

        except Exception as e:
            logger.error(f"Error decoding image frame: {e}")

    def get_latest_frame_jpeg(self) -> Optional[bytes]:
        """Return the latest frame encoded as JPEG."""
        with self.frame_lock:
            if self.last_frame is None:
                return None

            ret, buffer = cv2.imencode(
                ".jpg", self.last_frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
            )
            if ret:
                return buffer.tobytes()
        return None

    def stop(self):
        """Stop subscription."""
        if self.topic:
            self.topic.unsubscribe()
        self.active = False
        logger.info("VideoBridge stopped")

    async def mjpeg_generator(self):
        """Generator for MJPEG streaming."""
        while self.active:
            frame = self.get_latest_frame_jpeg()
            if frame:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            else:
                # If no frame yet, wait a bit
                await asyncio.sleep(0.5)
                continue
            await asyncio.sleep(0.1)  # Target ~10 FPS
