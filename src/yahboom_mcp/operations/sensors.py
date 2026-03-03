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
    """Execute sensor operations: read_imu, read_encoders, read_battery."""
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(f"Sensors: {operation}", extra={"correlation_id": correlation_id})

    # Use bridge from global state
    from ..state import _state

    bridge = _state.get("bridge")

    if bridge and bridge.connected:
        if operation == "read_imu":
            result = await bridge.get_sensor_data("imu")
        elif operation == "read_battery":
            result = await bridge.get_sensor_data("battery")
        elif operation == "read_encoders":
            result = await bridge.get_sensor_data(
                "odom"
            )  # Odom often contains encoder-derived data
        else:
            result = {"status": "unknown_sensor"}
        status = "live_data"
    else:
        # Fallback to mock data
        mock_data = {
            "read_imu": {
                "accel": {"x": 0.01, "y": 0.0, "z": 9.81},
                "gyro": {"x": 0.0, "y": 0.0, "z": 0.0},
            },
            "read_encoders": {"left": 1024, "right": 1028, "drift": 0.003},
            "read_battery": {"voltage": 12.4, "percentage": 85.0},
        }
        result = mock_data.get(operation, {"status": "unknown_sensor"})
        status = "mock_data"
        logger.warning("Operating in mock mode (Bridge not connected)")

    return {
        "success": True,
        "operation": operation,
        "result": result,
        "status": status,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
    }
