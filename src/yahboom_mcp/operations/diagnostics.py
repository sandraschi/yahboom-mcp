from fastmcp import Context
import logging

logger = logging.getLogger("yahboom-mcp.operations.diagnostics")


async def execute(
    ctx: Context | None = None,
    operation: str = "",
    param1: str | float | None = None,
    param2: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """Execute diagnostic operations: health_check, config_show."""
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(f"Diagnostics: {operation}", extra={"correlation_id": correlation_id})

    # Use bridge from global state
    from ..state import _state

    bridge = _state.get("bridge")
    bridge_connected = bridge.connected if bridge else False

    if operation == "health_check":
        battery_data = (
            await bridge.get_sensor_data("battery") if bridge_connected else {}
        )

        return {
            "success": True,
            "operation": operation,
            "result": {
                "system": "OK",
                "ros_bridge": "CONNECTED" if bridge_connected else "DISCONNECTED",
                "stm32_link": "STABLE" if bridge_connected else "UNKNOWN",
                "battery_health": "GOOD"
                if battery_data.get("percentage", 0) > 20
                else "LOW",
                "live_mode": bridge_connected,
            },
            "correlation_id": correlation_id,
        }
    elif operation == "config_show":
        return {
            "success": True,
            "operation": operation,
            "result": {"max_speed": 0.5, "pid_p": 1.2, "pid_i": 0.1, "pid_d": 0.05},
            "correlation_id": correlation_id,
        }

    return {
        "success": False,
        "operation": operation,
        "error": f"Unknown diagnostic operation: {operation}",
        "correlation_id": correlation_id,
    }
