"""
In-memory stand-in for ROS2Bridge: no roslibpy, no network.

Use in tests and optional local runs via YAHBOOM_USE_MOCK_BRIDGE=1 (see server lifespan).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("yahboom_mcp.testing.mock_bridge")


class MockROS2Bridge:
    """Mirrors the public surface of ROS2Bridge used by tools and FastAPI routes."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9090):
        self.host = host
        self.port = port
        self.ros = None  # skip VideoBridge (requires real roslibpy.Ros)
        self.connected = False
        self.cmd_vel_topic: object | None = None
        self.cmd_vel_history: list[dict[str, Any]] = []
        self.servo_history:   list[dict[str, Any]] = []

        # Fake lightstrip topic — records published messages
        class _FakeTopic:
            def __init__(self): self.published = []
            def publish(self, msg): self.published.append(msg)

        self.rgblight_topic = _FakeTopic()

        self.state: dict[str, Any] = {
            "imu": {
                "heading": 90.0,
                "yaw": 90.0,
                "pitch": 0.0,
                "roll": 0.0,
                "angular_velocity": {"x": 0.0, "y": 0.0, "z": 0.0},
                "linear_acceleration": {"x": 0.0, "y": 0.0, "z": 9.81},
            },
            "battery": {
                "voltage": 12.2,
                "percentage": 88.0,
                "power_supply_status": 1,
            },
            "odom": {
                "position": {"x": 0.1, "y": 0.0, "z": 0.0},
                "heading": 90.0,
                "velocity": {"linear": 0.0, "angular": 0.0},
            },
            "scan": {
                "nearest_m": 2.5,
                "obstacles": {
                    "front": 2.5,
                    "front_right": None,
                    "right": None,
                    "back_right": None,
                    "back": None,
                    "back_left": None,
                    "left": None,
                    "front_left": None,
                },
                "range_max_m": 12.0,
                "num_points": 360,
            },
            "last_update": 0.0,
        }

    async def connect(self, timeout: float = 10.0) -> bool:
        self.connected = True
        self.cmd_vel_topic = object()
        # Mock pre-flight node check success
        logger.info("MockROS2Bridge: connected (no network) with pre-flight success")
        return True

    async def get_all_topics(self) -> list[list[str]]:
        """Mock return for the 74+ topics discovered on the real robot."""
        if not self.connected:
            return []

        # Sample of the 74 topics for testing
        return [
            ["/cmd_vel", "geometry_msgs/msg/Twist"],
            ["/scan", "sensor_msgs/msg/LaserScan"],
            ["/imu/data", "sensor_msgs/msg/Imu"],
            ["/odom", "nav_msgs/msg/Odometry"],
            ["/battery_state", "sensor_msgs/msg/BatteryState"],
            ["/joint_states", "sensor_msgs/msg/JointState"],
            ["/tf", "tf2_msgs/msg/TFMessage"],
            ["/tf_static", "tf2_msgs/msg/TFMessage"],
            ["/camera/image_raw", "sensor_msgs/msg/Image"],
        ] + [[f"/mock_topic_{i}", "std_msgs/msg/Header"] for i in range(65)]

    async def publish_servo(self, servo_id: int, angle: int) -> bool:
        if not self.connected:
            return False
        angle = max(0, min(180, angle))
        self.servo_history.append({"id": servo_id, "angle": angle})
        return True

    async def move(self, linear: float = 0.0, angular: float = 0.0, linear_y: float = 0.0) -> bool:
        return await self.publish_velocity(linear_x=linear, angular_z=angular, linear_y=linear_y)

    async def disconnect(self):
        """Mock graceful shutdown."""
        self.connected = False
        self.cmd_vel_topic = None
        logger.info("MockROS2Bridge: disconnected")

    async def publish_velocity(
        self, linear_x: float, angular_z: float, linear_y: float = 0.0
    ) -> bool:
        if not self.connected:
            logger.warning("MockROS2Bridge: publish_velocity while disconnected")
            return False
        twist = {
            "linear": {"x": linear_x, "y": linear_y, "z": 0.0},
            "angular": {"x": 0.0, "y": 0.0, "z": angular_z},
        }
        self.cmd_vel_history.append(twist)
        return True

    async def resync_metadata(self) -> bool:
        """Mock re-sync."""
        logger.info("MockROS2Bridge: resync_metadata")
        return True

    async def get_sensor_data(self, key: str) -> dict[str, Any]:
        return self.state.get(key, {})

    def get_full_telemetry(self) -> dict[str, Any]:
        imu = self.state.get("imu", {})
        battery = self.state.get("battery", {})
        odom = self.state.get("odom", {})
        scan = self.state.get("scan", {})
        vel = odom.get("velocity", {})

        return {
            "battery": battery.get("percentage"),
            "voltage": battery.get("voltage"),
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
            "position": odom.get("position"),
            "scan": {
                "nearest_m": scan.get("nearest_m"),
                "obstacles": scan.get("obstacles"),
            },
        }
