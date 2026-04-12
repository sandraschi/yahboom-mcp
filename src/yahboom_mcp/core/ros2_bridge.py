import logging
import math
import asyncio
import os
import time
from typing import Any, Dict, List, Optional, Tuple
import roslibpy

logger = logging.getLogger("yahboom-mcp.core.ros2_bridge")


# ─────────────────────────────────────────────────────────────────────────────
# Quaternion → Euler (radians → degrees)
# ─────────────────────────────────────────────────────────────────────────────


def _quat_to_euler_deg(q: dict) -> dict:
    """Convert a ROS quaternion dict to roll/pitch/yaw in degrees."""
    x = q.get("x", 0.0)
    y = q.get("y", 0.0)
    z = q.get("z", 0.0)
    w = q.get("w", 1.0)

    # Roll (x-axis rotation)
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = math.degrees(math.atan2(sinr_cosp, cosr_cosp))

    # Pitch (y-axis rotation)
    sinp = 2.0 * (w * y - z * x)
    pitch = math.degrees(
        math.copysign(math.pi / 2, sinp) if abs(sinp) >= 1 else math.asin(sinp)
    )

    # Yaw (z-axis rotation) → normalised to 0–360
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.degrees(math.atan2(siny_cosp, cosy_cosp))
    heading = yaw % 360.0

    return {
        "roll": round(roll, 2),
        "pitch": round(pitch, 2),
        "yaw": round(yaw, 2),
        "heading": round(heading, 2),
    }


def _quat_valid(q: dict) -> bool:
    """False if missing or all-zero quaternion (driver marks orientation unusable)."""
    if not q:
        return False
    x = float(q.get("x", 0.0))
    y = float(q.get("y", 0.0))
    z = float(q.get("z", 0.0))
    w = float(q.get("w", 0.0))
    n = math.sqrt(x * x + y * y + z * z + w * w)
    return n > 1e-4


def _accel_tilt_deg(accel: dict) -> Tuple[float, float]:
    """Pitch/roll from gravity vector when orientation quaternion is invalid."""
    ax = float(accel.get("x", 0.0))
    ay = float(accel.get("y", 0.0))
    az = float(accel.get("z", 0.0))
    denom = math.sqrt(ay * ay + az * az)
    pitch = math.degrees(math.atan2(-ax, denom)) if denom > 1e-6 else 0.0
    roll = math.degrees(math.atan2(ay, az)) if abs(az) > 1e-6 else 0.0
    return round(pitch, 2), round(roll, 2)


# ─────────────────────────────────────────────────────────────────────────────
# LIDAR scan → obstacle summary (nearest per 8 sectors)
# ─────────────────────────────────────────────────────────────────────────────

_SECTOR_NAMES = [
    "front",
    "front_right",
    "right",
    "back_right",
    "back",
    "back_left",
    "left",
    "front_left",
]

# Order matches webapp Sensors.tsx IR_LABELS: FL, F, FR, R, BR, B, BL, L
_UI_PROXIMITY_KEYS = [
    "front_left",
    "front",
    "front_right",
    "right",
    "back_right",
    "back",
    "back_left",
    "left",
]


def _scan_to_obstacle_summary(
    ranges: list, angle_min: float, angle_increment: float
) -> dict:
    """
    Collapse a full LaserScan ranges[] array into nearest obstacle per sector.
    Returns a dict of {sector_name: distance_metres} for 8 sectors.
    Infinite / NaN readings are treated as 'clear' (set to None).
    """
    sectors: Dict[str, Optional[float]] = {n: None for n in _SECTOR_NAMES}
    if not ranges:
        return sectors

    sector_size = (2 * math.pi) / 8

    for i, r in enumerate(ranges):
        if r is None or math.isnan(r) or math.isinf(r) or r <= 0:
            continue
        angle = angle_min + i * angle_increment
        # Normalise to [0, 2π)
        angle = angle % (2 * math.pi)
        sector_idx = int(angle / sector_size) % 8
        name = _SECTOR_NAMES[sector_idx]
        if sectors[name] is None or r < sectors[name]:
            sectors[name] = round(r, 3)

    return sectors


class ROS2Bridge:
    """
    Functional Bridge for communicating with ROS 2 topics via rosbridge_suite.
    Uses roslibpy for high-level asynchronous interaction.

    Subscriptions
    ─────────────
    /imu/data          sensor_msgs/Imu          → state["imu"]
    /battery_state     sensor_msgs/BatteryState  → state["battery"]
    /odom              nav_msgs/Odometry         → state["odom"]
    /scan              sensor_msgs/LaserScan     → state["scan"]
    /sonar             sensor_msgs/Range         → state["ir_proximity"]
    /line_sensor       std_msgs/msg/Int32MultiArray → state["line_sensors"] (env overrides)
    /image_raw/compressed sensor_msgs/CompressedImage → last_image
    """

    def __init__(self, host: str = "localhost", port: int = 9090, fallback_host: Optional[str] = None):
        self.host = host
        self.port = port
        self.fallback_host = fallback_host
        self.ros: Optional[roslibpy.Ros] = None
        self.connected = False
        self.state: Dict[str, Any] = {
            "imu": {},
            "odom": {},
            "battery": {},
            "scan": {},
            "ir_proximity": None,  # Optional: list of distances (m) when topic configured
            "line_sensors": None,  # Optional: list of line-follower readings when topic configured
            "last_image": None,  # Base64 or bytes of the latest frame
            "last_update": 0,
        }
        self.on_reconnect_callback = None

        _imu = (os.environ.get("YAHBOOM_IMU_TOPIC") or "/imu/data").strip()
        self.imu_topic = _imu if _imu else "/imu/data"
        _ult = (os.environ.get("YAHBOOM_ULTRASONIC_TOPIC") or "/ultrasonic").strip()
        self.ultrasonic_topic = _ult if _ult else "/ultrasonic"
        _lt = (os.environ.get("YAHBOOM_LINE_TOPIC") or "/line_sensor").strip()
        self.line_topic = _lt if _lt else "/line_sensor"
        _lmt = (
            os.environ.get("YAHBOOM_LINE_MSG_TYPE") or "std_msgs/msg/Int32MultiArray"
        ).strip()
        self.line_msg_type = _lmt if _lmt else "std_msgs/msg/Int32MultiArray"

        # Topics
        self.cmd_vel_topic: Optional[roslibpy.Topic] = None
        self.imu_listener: Optional[roslibpy.Topic] = None
        self.battery_listener: Optional[roslibpy.Topic] = None
        self.odom_listener: Optional[roslibpy.Topic] = None
        self.scan_listener: Optional[roslibpy.Topic] = None
        self.sonar_listener: Optional[roslibpy.Topic] = None
        self.line_status_listener: Optional[roslibpy.Topic] = None
        self.button_listener: Optional[roslibpy.Topic] = None
        self.image_listener: Optional[roslibpy.Topic] = None

    async def _tcp_reachable(self, host: str, port: int, timeout: float = 0.8) -> bool:
        """True if something accepts TCP on host:port (quick rosbridge preflight)."""
        try:
            _reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout,
            )
        except (asyncio.TimeoutError, OSError, ConnectionError):
            return False
        except Exception:
            return False
        else:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return True

    async def _pick_rosbridge_host(self, hosts: List[str]) -> str:
        """
        Prefer the first host that accepts TCP on self.port.
        roslibpy uses a process-global Twisted reactor; only one Ros.run() is safe,
        so we must pick a single target before connecting (no retry loop that calls run() twice).
        """
        for h in hosts:
            if await self._tcp_reachable(h, self.port):
                logger.info("Selected ROSBridge host %s:%s (TCP reachable)", h, self.port)
                return h
        logger.warning(
            "No host accepted TCP on port %s for %s; using primary %s (handshake may still fail)",
            self.port,
            hosts,
            hosts[0],
        )
        return hosts[0]

    async def connect(self, timeout: float = 15.0) -> bool:
        """Establish connection to the ROSBridge server (non-blocking).
        Picks primary or fallback using a TCP probe, then a single roslibpy Ros.run()
        (Twisted reactor is not restartable in-process).
        """
        if self.ros and self.ros.is_connected:
            return True

        hosts_to_try = [self.host]
        if self.fallback_host and self.fallback_host != self.host:
            hosts_to_try.append(self.fallback_host)

        original_host = self.host
        current_host = await self._pick_rosbridge_host(hosts_to_try)
        self.host = current_host

        try:
            logger.info("Attempting ROSBridge handshake at %s:%s...", current_host, self.port)
            logger.info("Triggering hardware drive bringup on %s...", current_host)
            await self._ensure_ros_running()

            logger.info("Initializing ROSBridge client at %s:%s...", current_host, self.port)
            self.ros = roslibpy.Ros(host=current_host, port=self.port)

            # roslibpy emits "ready" with the protocol as the first argument
            self.ros.on(
                "ready",
                lambda *_args: logger.info("ROSBridge handshake success on %s", current_host),
            )
            self.ros.on(
                "error",
                lambda *args: logger.error(
                    "ROSBridge Handshake Error: %s", args[0] if args else "unknown"
                ),
            )

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.ros.run)

            handshake_timeout = 5.0
            handshake_start = time.time()
            while not self.ros.is_connected and (
                time.time() - handshake_start < handshake_timeout
            ):
                await asyncio.sleep(0.5)

            if self.ros.is_connected:
                logger.info("CONNECTED: ROS 2 Bridge is now active on %s", current_host)
                self.host = current_host
                self.connected = True

                try:
                    await self._setup_topics()
                    logger.info("Telemetry topics successfully registered.")
                except Exception as e:
                    logger.error("Partial telemetry failure: %s", e)

                if self.on_reconnect_callback:
                    self.on_reconnect_callback()
                return True

            logger.warning(
                "Bridge handshake failed at %s:%s. Is rosbridge_websocket running?",
                current_host,
                self.port,
            )
            if self.ros:
                self.ros.terminate()
            self.connected = False
            self.host = original_host
            return False
        except Exception as e:
            logger.error(
                "Critical failure during bridge initialization at %s: %s", current_host, e
            )
            if self.ros:
                try:
                    self.ros.terminate()
                except Exception:
                    pass
            self.host = original_host
            self.connected = False
            return False

    async def _ensure_ros_running(self):
        """Verify ROS 2 nodes via SSH and trigger bringup if missing."""
        if (
            not hasattr(self, "ssh_bridge")
            or not self.ssh_bridge
            or not self.ssh_bridge.connected
        ):
            # Fallback check for 'ssh' attribute if named differently
            ssh = getattr(self, "ssh", None)
            if not ssh or not ssh.connected:
                logger.warning("SSH not connected - skipping ROS 2 health check.")
                return
            target_ssh = ssh
        else:
            target_ssh = self.ssh_bridge

        # Phase 1: Check for core hardware driver (Mcnamu_driver)
        out, _, _ = await target_ssh.execute(
            "docker exec yahboom_ros2_final bash -c 'source /opt/ros/humble/setup.bash; source /root/yahboomcar_ws/install/setup.bash; ros2 node list'"
        )

        if not out or "Mcnamu_driver" not in out:
            logger.info("CRITICAL: Hardware driver (Mcnamu_driver) offline. Attempting SOTA V15 Recovery Bringup...")
            # Use setsid to ensure the process survives SSH disconnect
            launch_cmd = (
                "docker exec yahboom_ros2_final bash -c '"
                "source /opt/ros/humble/setup.bash; "
                "source /root/yahboomcar_ws/install/setup.bash; "
                "setsid ros2 launch yahboomcar_bringup yahboomcar_bringup.launch.py > /tmp/sota_launch.log 2>&1 &'"
            )
            await target_ssh.execute(launch_cmd)
            await asyncio.sleep(8) 
            logger.info("V14 Recovery Bringup triggered. Waiting for hardware stability...")
        else:
            logger.info("Hardware driver (driver_node) confirmed active.")

        # Phase 2: Check for Rosbridge (Webapp link)
        if "rosbridge_websocket" not in out:
            logger.warning("TELEMETRY BLACKOUT: rosbridge_websocket is missing from the node list. Webapp will remain disconnected.")
            # We don't block here, as the MCP can still use SSH-fallback if we implement it, 
            # but we warn the user via logs.

    async def get_all_topics(self) -> list[dict[str, str]]:
        """
        Fetch full list of active topics and types from the bridge.
        Returns a list of {"name": "/topic", "type": "type_name"}.
        """
        if not self.ros or not self.ros.is_connected:
            return []

        try:
            # SOTA ROS 2 Introspection via rosapi Service
            service = roslibpy.Service(
                self.ros, "/rosapi/topics_and_types", "rosapi/TopicsAndTypes"
            )
            request = roslibpy.ServiceRequest()

            future = asyncio.Future()
            service.call(
                request,
                lambda response: future.set_result(response),
                lambda err: future.set_exception(Exception(err)),
            )

            result = await asyncio.wait_for(future, timeout=5.0)

            # Map result (topics, types) to list of dicts
            enriched = []
            if "topics" in result and "types" in result:
                for name, t_type in zip(result["topics"], result["types"]):
                    enriched.append({"name": name, "type": t_type})

            return enriched
        except Exception as e:
            logger.error(f"Failed to fetch detailed topic list: {e}")
            # Fallback to simple topics if service fails
            try:
                future_names = asyncio.Future()
                self.ros.get_topics(lambda names: future_names.set_result(names))
                names = await asyncio.wait_for(future_names, timeout=2.0)
                return [{"name": n, "type": "unknown"} for n in names]
            except Exception:
                return []

    async def _setup_topics(self):
        """Initialize publishers and subscribers with Verified Humble Registry."""
        if not self.ros or not self.ros.is_connected:
            return

        # 1. Map Topics (Hardcoded for Pi 5 Humble Registry - Resolved Sensory Blindness)
        # Velocity
        self.cmd_vel_topic = roslibpy.Topic(self.ros, "/cmd_vel", "geometry_msgs/Twist")

        # IMU (override with YAHBOOM_IMU_TOPIC if your stack remaps e.g. /imu → /imu/data)
        self.imu_listener = roslibpy.Topic(
            self.ros, self.imu_topic, "sensor_msgs/Imu"
        )
        self.imu_listener.subscribe(self._imu_callback)

        # Battery
        bat_topic = "/battery_state"
        self.battery_listener = roslibpy.Topic(
            self.ros, bat_topic, "sensor_msgs/BatteryState"
        )
        self.battery_listener.subscribe(self._battery_callback)

        # Odometry
        self.odom_listener = roslibpy.Topic(self.ros, "/odom", "nav_msgs/Odometry")
        self.odom_listener.subscribe(self._odom_callback)

        # LIDAR Scan
        self.scan_listener = roslibpy.Topic(self.ros, "/scan", "sensor_msgs/LaserScan")
        self.scan_listener.subscribe(self._scan_callback)

        # Ultrasonic ranger (std_msgs/msg/Float32) — Observed in Mcnamu_driver bridge
        self.sonar_listener = roslibpy.Topic(
            self.ros, self.ultrasonic_topic, "std_msgs/msg/Float32"
        )
        self.sonar_listener.subscribe(self._sonar_callback)

        # Line follower (Int32MultiArray: typically 3–5 binary channels, 0/1)
        self.line_status_listener = roslibpy.Topic(
            self.ros, self.line_topic, self.line_msg_type
        )
        self.line_status_listener.subscribe(self._line_callback)

        # RGB Lightstrip
        rgblight_topic = "/rgblight"
        self.rgblight_topic = roslibpy.Topic(
            self.ros, rgblight_topic, "std_msgs/Int32MultiArray"
        )

        # Camera (Compressed)
        image_topic = "/image_raw/compressed"
        self.image_topic = roslibpy.Topic(
            self.ros, image_topic, "sensor_msgs/CompressedImage"
        )
        self.image_topic.subscribe(self._image_callback)

        # KEY Button
        self.button_listener = roslibpy.Topic(self.ros, "/button", "std_msgs/Bool")
        self.button_listener.subscribe(self._button_callback)

        # Servo Control (Verified yahboomcar_msgs for Humble)
        self.servo_topic = roslibpy.Topic(
            self.ros, "/servo", "yahboomcar_msgs/msg/ServoControl"
        )

        logger.info(
            "Subscribed using Verified Humble Registry: IMU=%s, Bat=%s, Vision=%s, Line=%s, Ultrasonic=%s",
            self.imu_topic,
            bat_topic,
            image_topic,
            self.line_topic,
            self.ultrasonic_topic,
        )

    async def resync_metadata(self):
        """Force a re-discovery of topics and re-subscribe to telemetry."""
        logger.info("Triggering Total Synchronization: Metadata re-discovery...")
        # Unsubscribe if listeners exist
        if hasattr(self, "imu_listener") and self.imu_listener:
            self.imu_listener.unsubscribe()
        if hasattr(self, "battery_listener") and self.battery_listener:
            self.battery_listener.unsubscribe()
        if hasattr(self, "odom_listener") and self.odom_listener:
            self.odom_listener.unsubscribe()
        if hasattr(self, "scan_listener") and self.scan_listener:
            self.scan_listener.unsubscribe()
        if hasattr(self, "sonar_listener") and self.sonar_listener:
            self.sonar_listener.unsubscribe()
        if hasattr(self, "line_status_listener") and self.line_status_listener:
            self.line_status_listener.unsubscribe()
        if hasattr(self, "button_listener") and self.button_listener:
            self.button_listener.unsubscribe()
        if hasattr(self, "image_topic") and self.image_topic:
            self.image_topic.unsubscribe()

        await self._setup_topics()
        return True

    # ─── Callbacks ───────────────────────────────────────────────────────────

    def _imu_callback(self, message):
        """Cache full IMU state including derived euler angles."""
        orientation = message.get("orientation") or {}
        angular_velocity = message.get("angular_velocity") or {}
        linear_acceleration = message.get("linear_acceleration") or {}

        ori_ok = _quat_valid(orientation)
        euler: Dict[str, float] = {}
        if ori_ok:
            euler = _quat_to_euler_deg(orientation)
        elif linear_acceleration:
            # Many stacks publish invalid quat (-1 covariance); use accel tilt for pitch/roll
            pr = _accel_tilt_deg(linear_acceleration)
            euler = {"pitch": pr[0], "roll": pr[1], "yaw": 0.0, "heading": 0.0}

        self.state["imu"] = {
            "orientation": orientation,
            "_orientation_valid": ori_ok,
            "_accel_tilt": not ori_ok and bool(linear_acceleration),
            "heading": euler.get("heading", 0.0),
            "yaw": euler.get("yaw", 0.0),
            "pitch": euler.get("pitch", 0.0),
            "roll": euler.get("roll", 0.0),
            "angular_velocity": {
                "x": round(angular_velocity.get("x", 0.0), 4),
                "y": round(angular_velocity.get("y", 0.0), 4),
                "z": round(angular_velocity.get("z", 0.0), 4),
            },
            "linear_acceleration": {
                "x": round(linear_acceleration.get("x", 0.0), 4),
                "y": round(linear_acceleration.get("y", 0.0), 4),
                "z": round(linear_acceleration.get("z", 0.0), 4),
            },
        }

        self.state["last_update"] = time.time()

    def _battery_callback(self, message):
        """Cache battery state."""
        pct = message.get("percentage", None)
        volt = message.get("voltage", None)
        self.state["battery"] = {
            "voltage": round(volt, 2) if volt is not None else None,
            "percentage": round(pct * 100, 1)
            if pct is not None
            else None,  # ROS sends 0–1
            "power_supply_status": message.get("power_supply_status"),
        }

    def _odom_callback(self, message):
        """Cache odometry: position + velocity from wheel encoders."""
        twist = message.get("twist", {}).get("twist", {})
        pose = message.get("pose", {}).get("pose", {})
        pos = pose.get("position", {})
        orient = pose.get("orientation", {})

        euler = _quat_to_euler_deg(orient) if orient else {}

        self.state["odom"] = {
            "position": {
                "x": round(pos.get("x", 0.0), 4),
                "y": round(pos.get("y", 0.0), 4),
                "z": round(pos.get("z", 0.0), 4),
            },
            "heading": euler.get("heading", 0.0),
            "velocity": {
                "linear": round(twist.get("linear", {}).get("x", 0.0), 4),
                "angular": round(twist.get("angular", {}).get("z", 0.0), 4),
            },
        }

    def _scan_callback(self, message):
        """Cache LIDAR scan as full ranges + obstacle summary."""
        ranges = message.get("ranges", [])
        angle_min = message.get("angle_min", -math.pi)
        angle_increment = message.get("angle_increment", 0.0)
        range_max = message.get("range_max", 10.0)

        obstacles = _scan_to_obstacle_summary(ranges, angle_min, angle_increment)
        nearest = min((v for v in obstacles.values() if v is not None), default=None)

        self.state["scan"] = {
            "obstacles": obstacles,  # nearest per sector (metres)
            "nearest_m": nearest,  # single closest reading
            "range_max_m": range_max,
            "num_points": len(ranges),
        }

    def _sonar_callback(self, message):
        """Cache Ultrasound sonar range (m) from std_msgs/msg/Float32."""
        try:
            # Float32 message has a 'data' field
            rng = float(message.get("data", float("nan")))
        except (TypeError, ValueError):
            return
        if math.isnan(rng) or math.isinf(rng):
            return
        # Values are usually in cm or m depending on driver version; 
        # Mcnamu_driver usually sends metres.
        self.state["ir_proximity"] = round(rng, 3)

    def _line_callback(self, message):
        """Cache line-follower channels from std_msgs/Int32MultiArray (typically 0/1 per IR)."""
        raw = message.get("data")
        if raw is None and isinstance(message.get("msg"), dict):
            raw = message["msg"].get("data")
        if raw is None:
            return
        try:
            parsed = [int(x) for x in raw]
        except (TypeError, ValueError):
            logger.warning("line_sensor: data is not a numeric list: %r", raw)
            return
        self.state["line_sensors"] = parsed

    def _button_callback(self, message):
        """Cache physical button state (True=Pressed)."""
        # Logic: If pressed, we might trigger a 'Silence Alarm' event immediately
        is_pressed = message.get("data", False)
        self.state["button_pressed"] = is_pressed
        if is_pressed:
            logger.info("Boomy: Physical button pressed!")

    def _image_callback(self, message):
        """Cache latest raw frame for the vision bridge."""
        # data is Base64 encoded string from rosbridge
        self.state["last_image"] = message.get("data")

    # ─── Connection management ───────────────────────────────────────────────

    async def disconnect(self):
        """Gracefully shut down the connection."""
        self.connected = False
        if self.ros:
            logger.info("Closing ROSBridge connection...")
            try:
                self.ros.terminate()
            except Exception:
                pass
            self.ros = None

    async def monitor_connection(self, interval: float = 10.0, on_reconnect=None):
        """Background task to ensure the ROSBridge connection stays alive."""
        logger.info(f"Starting connection watchdog (interval={interval}s)")
        self.on_reconnect_callback = on_reconnect

        while True:
            try:
                # Check real status from roslibpy instance
                current_status = self.ros.is_connected if self.ros else False

                if not current_status:
                    if self.connected:
                        logger.warning(
                            "ROSBridge connection lost. Attempting reconnection..."
                        )
                        self.connected = False

                    # Try to reconnect
                    if await self.connect(timeout=3.0):
                        # Trigger reconnection callback if provided
                        if self.on_reconnect_callback:
                            if asyncio.iscoroutinefunction(self.on_reconnect_callback):
                                await self.on_reconnect_callback()
                            else:
                                self.on_reconnect_callback()
                else:
                    # Sync internal flag
                    if not self.connected:
                        logger.info(
                            "ROSBridge connection restored manually/autonomously."
                        )
                    self.connected = True
            except Exception as e:
                logger.debug(f"Watchdog iteration error: {e}")

            await asyncio.sleep(interval)

    # ─── Publish helpers ─────────────────────────────────────────────────────

    async def move(
        self, linear: float = 0.0, angular: float = 0.0, linear_y: float = 0.0
    ):
        """SOTA Proxy method for publish_velocity, providing a standard 'move' interface."""
        return await self.publish_velocity(
            linear_x=linear, angular_z=angular, linear_y=linear_y
        )

    async def publish_velocity(
        self, linear_x: float, angular_z: float, linear_y: float = 0.0
    ):
        """Send velocity command to the robot (including strafing for Mecanum wheels)."""
        if not self.connected or not self.cmd_vel_topic:
            logger.warning("Cannot publish velocity: Not connected")
            return False

        twist = {
            "linear": {"x": linear_x, "y": linear_y, "z": 0.0},
            "angular": {"x": 0.0, "y": 0.0, "z": angular_z},
        }
        self.cmd_vel_topic.publish(roslibpy.Message(twist))
        logger.info(f"Published cmd_vel: x={linear_x}, y={linear_y}, z={angular_z}")
        return True

    async def publish_servo(self, servo_id: int, angle: int):
        """Send angle command to a specific servo channel."""
        if not self.connected or not self.servo_topic:
            logger.warning("Cannot publish servo: Not connected")
            return False

        msg = {"id": servo_id, "angle": int(angle)}
        self.servo_topic.publish(roslibpy.Message(msg))
        logger.info(f"Published servo: id={servo_id}, angle={angle}")
        return True

    # ─── Data access ─────────────────────────────────────────────────────────

    async def get_sensor_data(self, key: str) -> Dict[str, Any]:
        """Retrieve cached sensor data by key: imu | battery | odom | scan."""
        return self.state.get(key, {})

    def _ir_proximity_ring_for_api(self) -> Optional[List[Optional[float]]]:
        """
        Eight distances (m) for the Sensors page (FL,F,FR,…): LIDAR ring + front ultrasonic.
        The webapp expects ir_proximity as an array; raw state stores a single float from Range.
        """
        obs = (self.state.get("scan") or {}).get("obstacles") or {}
        ring: List[Optional[float]] = [obs.get(k) for k in _UI_PROXIMITY_KEYS]

        raw = self.state.get("ir_proximity")
        if isinstance(raw, list) and raw:
            if len(raw) >= 8:
                return [float(x) if x is not None else None for x in raw[:8]]
            merged = list(ring)
            for i, v in enumerate(raw[:8]):
                if v is not None:
                    merged[i] = float(v)
            return merged if any(x is not None for x in merged) else None

        if isinstance(raw, (int, float)):
            ring[1] = float(raw)

        if any(v is not None for v in ring):
            return ring
        return None

    def _line_sensors_for_api(self) -> Optional[List[int]]:
        raw = self.state.get("line_sensors")
        if raw is None:
            return None
        if isinstance(raw, list):
            try:
                return [int(x) for x in raw]
            except (TypeError, ValueError):
                return None
        return None

    def get_full_telemetry(self) -> Dict[str, Any]:
        """
        Return a structured telemetry snapshot from all cached sensor data.
        Falls back gracefully with None fields if sensors haven't published yet.
        """
        imu = self.state.get("imu", {})
        battery = self.state.get("battery", {})
        odom = self.state.get("odom", {})
        scan = self.state.get("scan", {})

        # Velocity: prefer odometry (encoder-based), fall back to zero
        vel = odom.get("velocity", {})

        # Planar heading/yaw: use IMU quaternion only when valid; else wheel odometry
        ori_ok = imu.get("_orientation_valid")
        heading = imu.get("heading")
        yaw = imu.get("yaw")
        od_h = odom.get("heading") if odom else None
        if od_h is not None and ori_ok is not True:
            heading = od_h
            yaw = (od_h + 180.0) % 360.0 - 180.0

        imu_api = {
            "heading": heading,
            "yaw": yaw,
            "pitch": imu.get("pitch"),
            "roll": imu.get("roll"),
            "angular_velocity": imu.get("angular_velocity"),
            "linear_acceleration": imu.get("linear_acceleration"),
        }
        if ori_ok is not None:
            imu_api["orientation_valid"] = bool(ori_ok)

        return {
            "battery": battery.get("percentage"),  # 0–100 %
            "voltage": battery.get("voltage"),  # volts
            "imu": imu_api,
            "velocity": {
                "linear": vel.get("linear", 0.0),
                "angular": vel.get("angular", 0.0),
            },
            "position": odom.get("position"),  # x/y/z metres from start
            "scan": {
                "nearest_m": scan.get("nearest_m"),
                "obstacles": scan.get("obstacles"),  # per-sector nearest (m)
            },
            "ir_proximity": self._ir_proximity_ring_for_api(),
            "sonar_m": self.state.get("ir_proximity")
            if isinstance(self.state.get("ir_proximity"), (int, float))
            else None,
            "line_sensors": self._line_sensors_for_api(),
            "button_pressed": self.state.get("button_pressed", False),
        }
