import asyncio
import base64
import logging
import threading
import time

import cv2
import numpy as np
import roslibpy

logger = logging.getLogger("yahboom-mcp.core.video_bridge")


class VideoBridge:
    """
    Bridge for receiving camera images and providing them via HTTP/MJPEG.

    Two capture modes (tried in order):
      1. ROS topic  — subscribes to /image_raw/compressed via rosbridge.
      2. Direct cv2 — opens the camera device directly over SSH-forwarded
                      video or a local /dev/video0 equivalent.
                      Activated automatically if ROS topic yields no frames
                      after FALLBACK_TIMEOUT_S seconds.

    Set YAHBOOM_CAMERA_DIRECT=1 to force direct mode and skip the ROS attempt.
    Set YAHBOOM_CAMERA_DEVICE to override the device index/URL (default: 0).
    """

    FALLBACK_TIMEOUT_S = 10  # seconds with no frames before switching to direct

    def __init__(
        self,
        ros_client: roslibpy.Ros,
        topic_name: str = "/image_raw/compressed",
        ssh_bridge=None,
    ):
        self.ros = ros_client
        self.topic_name = topic_name
        self.topic: roslibpy.Topic | None = None
        self.last_frame: np.ndarray | None = None
        self.frame_lock = threading.Lock()
        self.active = False
        self.frame_count = 0
        self.ssh = ssh_bridge

        # Direct capture state
        self._direct_cap: cv2.VideoCapture | None = None
        self._direct_thread: threading.Thread | None = None
        self._direct_active = False
        self._ros_start_time: float | None = None

        import os

        self._force_direct = os.environ.get("YAHBOOM_CAMERA_DIRECT", "0") == "1"
        self._device = int(os.environ.get("YAHBOOM_CAMERA_DEVICE", "0"))

        # SOTA 2026: Remote Stream Fallback Removed
        # The fallback logic using port 10895 belonged to dreame-mcp and was erroneously
        # failing because no robot webserver exists. We rely fully on ROS topic or direct /dev/video0.

    def start(self):
        """Start camera. Uses ROS topic unless forced to direct mode."""
        if self.active:
            return

        self.active = True

        if self._force_direct:
            logger.info("VideoBridge: forced direct capture mode (YAHBOOM_CAMERA_DIRECT=1)")
            self._start_direct()
        else:
            logger.info("VideoBridge: starting ROS topic subscription with direct fallback")
            self._start_ros_topic()
            # Start a watchdog that switches to direct if no ROS frames arrive
            threading.Thread(target=self._ros_fallback_watchdog, daemon=True).start()

    def _start_ros_topic(self):
        """Subscribe to the ROS compressed image topic."""
        import time

        self._ros_start_time = time.time()
        topic_type = "sensor_msgs/CompressedImage"
        try:
            self.ros.get_topics(lambda topics: None)
        except Exception:
            pass

        self.topic = roslibpy.Topic(self.ros, self.topic_name, topic_type)
        self.topic.subscribe(self._image_callback)
        logger.info(f"VideoBridge: subscribed to {self.topic_name}")

    def _remote_robot_ssh(self) -> bool:
        """True if SSH target looks like a robot (not this host) — skip local /dev/video0."""
        ssh = getattr(self, "ssh", None) or getattr(self, "ssh_bridge", None)
        if not ssh or not getattr(ssh, "connected", False):
            return False
        host = (getattr(ssh, "host", None) or "").strip().lower()
        if not host:
            return False
        return host not in ("127.0.0.1", "localhost", "::1")

    def _ros_fallback_watchdog(self):
        """After FALLBACK_TIMEOUT_S with no frames, try direct capture only on sensible hosts."""
        time.sleep(self.FALLBACK_TIMEOUT_S)
        if self.frame_count == 0 and self.active:
            if self._remote_robot_ssh() and not self._force_direct:
                logger.warning(
                    "VideoBridge: no frames from %s after %ss — direct /dev/video0 "
                    "is disabled while SSH targets a remote robot (would open the PC "
                    "webcam). Set YAHBOOM_CAMERA_DIRECT=1 to force local capture, or fix "
                    "ROS image topic / rosbridge.",
                    self.topic_name,
                    self.FALLBACK_TIMEOUT_S,
                )
                return
            logger.warning(
                f"VideoBridge: no frames from {self.topic_name} after "
                f"{self.FALLBACK_TIMEOUT_S}s — trying direct USB camera mode..."
            )
            self._start_direct()

    def _start_direct(self):
        """Open the camera device directly via cv2 in a background thread."""
        if self._direct_active:
            return
        self._direct_active = True
        self._direct_thread = threading.Thread(target=self._direct_capture_loop, daemon=True)
        self._direct_thread.start()
        logger.info(f"VideoBridge: direct capture started on device {self._device}")

    def _direct_capture_loop(self):
        """Background thread: continuously read frames from cv2.VideoCapture."""
        cap = cv2.VideoCapture(self._device)
        if not cap.isOpened():
            logger.error(
                f"VideoBridge: cannot open camera device {self._device}. Check /dev/video0 exists and is accessible."
            )
            self._direct_active = False
            return

        self._direct_cap = cap
        logger.info(f"VideoBridge: direct capture opened device {self._device}")

        while self._direct_active and self.active:
            ret, frame = cap.read()
            if ret and frame is not None:
                with self.frame_lock:
                    self.last_frame = frame
                    self.frame_count += 1
            else:
                import time

                time.sleep(0.05)

        cap.release()
        self._direct_cap = None
        logger.info("VideoBridge: direct capture stopped")

    def _image_callback(self, message):
        """Decode incoming ROS 2 sensor_msgs/CompressedImage or raw Image."""
        try:
            data = message.get("data")
            if not data:
                return

            if isinstance(data, str):
                image_bytes = base64.b64decode(data)
            else:
                image_bytes = bytes(data)

            # Attempt compressed decode (JPEG/PNG)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Fallback: raw image fields
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
                        frame = np.frombuffer(image_bytes, dtype=np.uint8).reshape((height, width, 2))
                        frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_YUYV)

            if frame is not None:
                with self.frame_lock:
                    self.last_frame = frame
                    self.frame_count += 1
            else:
                if self.frame_count == 0:
                    logger.warning(
                        f"VideoBridge: cannot decode ROS frame from {self.topic_name}. "
                        f"Encoding: {message.get('encoding')}"
                    )

        except Exception as e:
            logger.error(f"VideoBridge: error decoding image frame: {e}")

    def get_latest_frame_jpeg(self) -> bytes | None:
        """Return the latest frame encoded as JPEG bytes."""
        with self.frame_lock:
            if self.last_frame is None:
                return None
            ret, buffer = cv2.imencode(".jpg", self.last_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                return buffer.tobytes()
        return None

    def stop(self):
        """Stop all capture (ROS and direct)."""
        self.active = False
        self._direct_active = False

        if self.topic:
            try:
                self.topic.unsubscribe()
            except Exception:
                pass

        if self._direct_cap:
            try:
                self._direct_cap.release()
            except Exception:
                pass

        logger.info("VideoBridge stopped")

    async def mjpeg_generator(self):
        """Async generator for MJPEG streaming (~20 FPS)."""
        while self.active:
            frame = self.get_latest_frame_jpeg()
            if frame:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            else:
                await asyncio.sleep(0.05)
                continue
            await asyncio.sleep(0.05)
