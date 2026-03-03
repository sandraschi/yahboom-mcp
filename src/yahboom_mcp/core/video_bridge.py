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
    """

    def __init__(self, ros_client: roslibpy.Ros, topic_name: str = "/camera/image_raw"):
        self.ros = ros_client
        self.topic_name = topic_name
        self.topic: Optional[roslibpy.Topic] = None
        self.last_frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()
        self.active = False

    def start(self):
        """Start subscribing to the image topic."""
        if self.active:
            return

        logger.info(f"Starting VideoBridge on topic: {self.topic_name}")
        self.topic = roslibpy.Topic(self.ros, self.topic_name, "sensor_msgs/Image")
        self.topic.subscribe(self._image_callback)
        self.active = True

    def _image_callback(self, message):
        """Decode incoming ROS 2 sensor_msgs/Image."""
        try:
            # ROS 2 sensor_msgs/Image structure:
            # height, width, encoding, is_bigendian, step, data (base64 or bytes)
            data = message.get("data")
            if not data:
                return

            # Decode from base64 if it's a string
            if isinstance(data, str):
                image_bytes = base64.b64decode(data)
            else:
                image_bytes = bytes(data)

            # Convert to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)

            # Note: ROS 2 images are often raw. For now, we assume it might be pre-encoded
            # or we need to reshape. Most rosbridge image topics send compressed or we use simple decoding.
            # If it's a raw image, we'd need to reshape based on width/height/encoding.
            # For simplicity in this SOTA bridge, we try to decode it as a standard format first.
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is not None:
                with self.frame_lock:
                    self.last_frame = frame
        except Exception as e:
            logger.error(f"Error decoding image frame: {e}")

    def get_latest_frame_jpeg(self) -> Optional[bytes]:
        """Return the latest frame encoded as JPEG."""
        with self.frame_lock:
            if self.last_frame is None:
                return None

            ret, buffer = cv2.imencode(
                ".jpg", self.last_frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
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
        """generator for MJPEG streaming."""
        while self.active:
            frame = self.get_latest_frame_jpeg()
            if frame:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            await asyncio.sleep(0.1)  # 10 FPS
