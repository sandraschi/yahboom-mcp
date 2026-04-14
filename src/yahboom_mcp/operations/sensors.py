import logging
import time

from fastmcp import Context

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
        elif operation == "read_camera_status":
            # Check if camera topic is actually publishing
            v_bridge = _state.get("video_bridge")
            result = {
                "active": v_bridge.active if v_bridge else False,
                "topic": v_bridge.topic_name if v_bridge else None,
                "frame_count": v_bridge.frame_count if v_bridge else 0,
            }
        elif operation == "read_all":
            result = bridge.get_full_telemetry()
            v_bridge = _state.get("video_bridge")
            result["camera"] = {
                "active": v_bridge.active if v_bridge else False,
                "frame_count": v_bridge.frame_count if v_bridge else 0,
            }
        else:
            result = {
                "status": "unknown_sensor_operation",
                "valid_ops": [
                    "read_imu",
                    "read_battery",
                    "read_odom",
                    "read_lidar",
                    "read_camera_status",
                    "read_all",
                ],
            }
        status = "live_data"
    else:
        # ─────────────────────────────────────────────────────────────────────
        # SOTA v12.0 Integrity: No Silent Mocks.
        # ─────────────────────────────────────────────────────────────────────
        result = {
            "status": "robot_offline",
            "message": "Connection to ROS 2 bridge or SSH bridge is currently down.",
            "data": None,
        }
        status = "offline"
        logger.warning(
            f"Sensor '{operation}' failed: Robot is OFFLINE (No mock data fallback)"
        )

    return {
        "success": True,
        "operation": operation,
        "result": result,
        "status": status,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
    }
