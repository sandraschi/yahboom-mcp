import logging
import math
import asyncio
from typing import Any, Dict, Optional
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
    """

    def __init__(self, host: str = "localhost", port: int = 9090):
        self.host = host
        self.port = port
        self.ros: Optional[roslibpy.Ros] = None
        self.connected = False
        self.state: Dict[str, Any] = {
            "imu": {},
            "odom": {},
            "battery": {},
            "scan": {},
            "last_update": 0,
        }

        # Topics
        self.cmd_vel_topic: Optional[roslibpy.Topic] = None
        self.imu_listener: Optional[roslibpy.Topic] = None
        self.battery_listener: Optional[roslibpy.Topic] = None
        self.odom_listener: Optional[roslibpy.Topic] = None
        self.scan_listener: Optional[roslibpy.Topic] = None

    async def connect(self):
        """Establish connection to the ROSBridge server."""
        try:
            logger.info(f"Connecting to ROSBridge at {self.host}:{self.port}...")
            self.ros = roslibpy.Ros(host=self.host, port=self.port)
            self.ros.on_ready(lambda: logger.info("ROSBridge connection ready"))

            # Use run_in_executor to avoid blocking the event loop during initial connect
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.ros.run)

            self.connected = self.ros.is_connected
            if self.connected:
                self._setup_topics()
                logger.info(
                    "ROS 2 Bridge successfully connected and topics initialized"
                )
            return self.connected
        except Exception as e:
            logger.error(f"Failed to connect to ROSBridge: {e}")
            self.connected = False
            return False

    def _setup_topics(self):
        """Initialize publishers and subscribers."""
        if not self.ros:
            return

        # Velocity Publisher
        self.cmd_vel_topic = roslibpy.Topic(self.ros, "/cmd_vel", "geometry_msgs/Twist")

        # IMU Subscriber
        self.imu_listener = roslibpy.Topic(self.ros, "/imu/data", "sensor_msgs/Imu")
        self.imu_listener.subscribe(self._imu_callback)

        # Battery Subscriber
        self.battery_listener = roslibpy.Topic(
            self.ros, "/battery_state", "sensor_msgs/BatteryState"
        )
        self.battery_listener.subscribe(self._battery_callback)

        # Odometry Subscriber
        self.odom_listener = roslibpy.Topic(self.ros, "/odom", "nav_msgs/Odometry")
        self.odom_listener.subscribe(self._odom_callback)

        # LIDAR Scan Subscriber
        self.scan_listener = roslibpy.Topic(self.ros, "/scan", "sensor_msgs/LaserScan")
        self.scan_listener.subscribe(self._scan_callback)

        logger.info("Subscribed to: /imu/data, /battery_state, /odom, /scan")

    # ─── Callbacks ───────────────────────────────────────────────────────────

    def _imu_callback(self, message):
        """Cache full IMU state including derived euler angles."""
        orientation = message.get("orientation", {})
        angular_velocity = message.get("angular_velocity", {})
        linear_acceleration = message.get("linear_acceleration", {})

        euler = _quat_to_euler_deg(orientation) if orientation else {}

        self.state["imu"] = {
            # Raw quaternion
            "orientation": orientation,
            # Derived Euler in degrees
            "heading": euler.get("heading", 0.0),
            "yaw": euler.get("yaw", 0.0),
            "pitch": euler.get("pitch", 0.0),
            "roll": euler.get("roll", 0.0),
            # Gyroscope (rad/s)
            "angular_velocity": {
                "x": round(angular_velocity.get("x", 0.0), 4),
                "y": round(angular_velocity.get("y", 0.0), 4),
                "z": round(angular_velocity.get("z", 0.0), 4),
            },
            # Accelerometer (m/s²)
            "linear_acceleration": {
                "x": round(linear_acceleration.get("x", 0.0), 4),
                "y": round(linear_acceleration.get("y", 0.0), 4),
                "z": round(linear_acceleration.get("z", 0.0), 4),
            },
        }
        try:
            self.state["last_update"] = asyncio.get_event_loop().time()
        except RuntimeError:
            pass

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

    # ─── Connection management ───────────────────────────────────────────────

    async def disconnect(self):
        """Gracefully shut down the connection."""
        if self.ros:
            logger.info("Closing ROSBridge connection...")
            self.ros.terminate()
            self.connected = False

    # ─── Publish helpers ─────────────────────────────────────────────────────

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

    # ─── Data access ─────────────────────────────────────────────────────────

    async def get_sensor_data(self, key: str) -> Dict[str, Any]:
        """Retrieve cached sensor data by key: imu | battery | odom | scan."""
        return self.state.get(key, {})

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

        return {
            "battery": battery.get("percentage"),  # 0–100 %
            "voltage": battery.get("voltage"),  # volts
            "imu": {
                "heading": imu.get("heading"),
                "yaw": imu.get("yaw"),
                "pitch": imu.get("pitch"),
                "roll": imu.get("roll"),
                "angular_velocity": imu.get("angular_velocity"),
                "linear_acceleration": imu.get("linear_acceleration"),
            },
            "velocity": {
                "linear": vel.get("linear", 0.0),
                "angular": vel.get("angular", 0.0),
            },
            "position": odom.get("position"),  # x/y/z metres from start
            "scan": {
                "nearest_m": scan.get("nearest_m"),
                "obstacles": scan.get("obstacles"),  # per-sector nearest (m)
            },
        }
