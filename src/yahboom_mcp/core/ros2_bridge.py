import logging
import asyncio
from typing import Any, Dict, Optional
import roslibpy

logger = logging.getLogger("yahboom-mcp.core.ros2_bridge")


class ROS2Bridge:
    """
    Functional Bridge for communicating with ROS 2 topics via rosbridge_suite.
    Uses roslibpy for high-level asynchronous interaction.
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
            "last_update": 0,
        }

        # Topics
        self.cmd_vel_topic: Optional[roslibpy.Topic] = None
        self.imu_listener: Optional[roslibpy.Topic] = None
        self.battery_listener: Optional[roslibpy.Topic] = None

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

    def _imu_callback(self, message):
        """Update internal IMU state."""
        self.state["imu"] = {
            "orientation": message.get("orientation"),
            "angular_velocity": message.get("angular_velocity"),
            "linear_acceleration": message.get("linear_acceleration"),
        }
        self.state["last_update"] = asyncio.get_event_loop().time()

    def _battery_callback(self, message):
        """Update internal Battery state."""
        self.state["battery"] = {
            "voltage": message.get("voltage"),
            "percentage": message.get("percentage"),
            "power_supply_status": message.get("power_supply_status"),
        }

    async def disconnect(self):
        """Gracefully shut down the connection."""
        if self.ros:
            logger.info("Closing ROSBridge connection...")
            self.ros.terminate()
            self.connected = False

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

    async def get_sensor_data(self, key: str) -> Dict[str, Any]:
        """Retrieve cached sensor data."""
        return self.state.get(key, {})
