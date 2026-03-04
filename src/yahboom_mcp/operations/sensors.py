from fastmcp import Context
import logging
import time

logger = logging.getLogger("yahboom-mcp.operations.sensors")


async def execute(
    ctx: Context | None = None,
    operation: str = "",
    param1: str | float | None = None,
    param2: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    Execute sensor read operations: read_imu, read_lidar, read_battery, read_odom.

    Live data is sourced from the ROS 2 bridge'scached topic subscriptions:
      read_imu      → /imu/data   (heading/pitch/roll/accel/gyro)
      read_battery  → /battery_state
      read_odom     → /odom       (position + encoder velocity)
      read_lidar    → /scan       (nearest obstacle per sector)
      read_all      → full telemetry snapshot from all sensors
    """
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(f"Sensors: {operation}", extra={"correlation_id": correlation_id})

    from ..state import _state

    bridge = _state.get("bridge")

    if bridge and bridge.connected:
        if operation == "read_imu":
            result = await bridge.get_sensor_data("imu")
        elif operation == "read_battery":
            result = await bridge.get_sensor_data("battery")
        elif operation in ("read_encoders", "read_odom"):
            result = await bridge.get_sensor_data("odom")
        elif operation == "read_lidar":
            result = await bridge.get_sensor_data("scan")
        elif operation == "read_all":
            result = bridge.get_full_telemetry()
        else:
            result = {
                "status": "unknown_sensor_operation",
                "valid_ops": [
                    "read_imu",
                    "read_battery",
                    "read_odom",
                    "read_lidar",
                    "read_all",
                ],
            }
        status = "live_data"
    else:
        # Clearly-marked mock fallback when bridge is not connected
        mock_data: dict = {
            "read_imu": {
                "heading": 0.0,
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0,
                "angular_velocity": {"x": 0.0, "y": 0.0, "z": 0.0},
                "linear_acceleration": {"x": 0.0, "y": 0.0, "z": 9.81},
            },
            "read_battery": {
                "voltage": 11.8,
                "percentage": 85.0,
                "power_supply_status": None,
            },
            "read_odom": {
                "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "heading": 0.0,
                "velocity": {"linear": 0.0, "angular": 0.0},
            },
            "read_lidar": {
                "nearest_m": None,
                "obstacles": {
                    "front": None,
                    "front_right": None,
                    "right": None,
                    "back_right": None,
                    "back": None,
                    "back_left": None,
                    "left": None,
                    "front_left": None,
                },
                "num_points": 0,
            },
            "read_all": {
                "battery": 85.0,
                "voltage": 11.8,
                "imu": {"heading": 0.0, "pitch": 0.0, "roll": 0.0},
                "velocity": {"linear": 0.0, "angular": 0.0},
                "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "scan": {"nearest_m": None},
            },
        }
        # Also handle legacy alias
        if operation == "read_encoders":
            operation = "read_odom"
        result = mock_data.get(operation, {"status": "unknown_sensor_operation"})
        status = "mock_data"
        logger.warning(
            f"Sensor '{operation}' returning mock data (bridge not connected)"
        )

    return {
        "success": True,
        "operation": operation,
        "result": result,
        "status": status,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
    }
