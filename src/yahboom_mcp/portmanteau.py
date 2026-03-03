from fastmcp import Context
import logging
from .state import _state

logger = logging.getLogger("yahboom-mcp.portmanteau")


async def yahboom_tool(
    ctx: Context | None = None,
    operation: str = "health_check",
    param1: str | float | None = None,
    param2: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    Unified control tool for Yahboom ROS 2.
    Consolidates motion, sensor, and hardware operations.
    """
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(
        f"Executing yahboom operation: {operation}",
        extra={"correlation_id": correlation_id},
    )

    op_lower = operation.lower().strip()

    try:
        if op_lower in ["forward", "backward", "turn_left", "turn_right", "stop"]:
            from .operations import motion

            return await motion.execute(ctx, op_lower, param1, param2, payload)
        elif op_lower in ["read_imu", "read_encoders", "read_battery"]:
            from .operations import sensors

            return await sensors.execute(ctx, op_lower, param1, param2, payload)
        elif op_lower in ["start_recording", "stop_recording", "list_trajectories"]:
            # Trajectory operations from global state
            manager = _state.get("trajectory_manager")
            if not manager:
                return {"success": False, "error": "Trajectory manager not available"}

            if op_lower == "start_recording":
                manager.start_recording()
                return {"success": True, "message": "Started recording"}
            elif op_lower == "stop_recording":
                path = manager.stop_recording(str(param1) if param1 else "trajectory")
                return {"success": True, "message": f"Saved to {path}"}
            elif op_lower == "list_trajectories":
                return {"success": True, "trajectories": manager.list_trajectories()}
        elif op_lower in ["health_check", "config_show"]:
            from .operations import diagnostics

            return await diagnostics.execute(ctx, op_lower, param1, param2, payload)
        else:
            return {
                "success": False,
                "operation": operation,
                "error": f"Unknown operation: {operation}",
                "correlation_id": correlation_id,
            }
    except Exception as e:
        logger.error(f"Operation {operation} failed: {e}", exc_info=True)
        return {
            "success": False,
            "operation": operation,
            "error": str(e),
            "correlation_id": correlation_id,
        }
