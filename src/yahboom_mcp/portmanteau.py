from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import Context
from pydantic import Field

from .state import _state

logger = logging.getLogger("yahboom-mcp.portmanteau")


async def yahboom_tool(
    ctx: Context | None = None,
    operation: Annotated[
        str,
        Field(description="Operation: health_check, forward, backward, turn_left, turn_right, strafe_left, strafe_right, stop, read_imu, read_battery, read_encoders, start_recording, stop_recording, list_trajectories, config_show."),
    ] = "health_check",
    param1: Annotated[
        str | float | None,
        Field(description="First parameter: duration, speed, or basename depending on operation."),
    ] = None,
    param2: Annotated[
        str | float | None,
        Field(description="Second parameter when required by operation."),
    ] = None,
    payload: Annotated[
        dict | None,
        Field(description="Optional key-value payload for future use."),
    ] = None,
) -> dict:
    """Unified control tool for Yahboom Raspbot v2 (ROS 2 Humble). Motion, sensors, diagnostics, trajectory.

    Returns:
        dict: success (bool); on failure error (str), correlation_id (str). On success may include message, trajectories, or operation-specific keys (e.g. result, battery, heading).
    """
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(
        f"Executing yahboom operation: {operation}",
        extra={"correlation_id": correlation_id},
    )

    op_lower = operation.lower().strip()

    try:
        if op_lower in [
            "forward",
            "backward",
            "turn_left",
            "turn_right",
            "stop",
            "strafe_left",
            "strafe_right",
        ]:
            from .operations import motion

            return await motion.execute(ctx, op_lower, param1, param2, payload)
        elif op_lower in ["read_imu", "read_encoders", "read_battery", "read_all", "read_lidar"]:
            from .operations import sensors

            return await sensors.execute(ctx, op_lower, param1, param2, payload)
        elif op_lower in ["say", "play"]:
            from .operations import voice

            return await voice.execute(ctx, op_lower, param1, param2, payload)
        elif op_lower in ["display", "clear_display"]:
            from .operations import display

            sub_op = "write" if op_lower == "display" else "clear"
            return await display.execute(ctx, sub_op, param1, param2, payload)
        elif op_lower in ["led", "led_off"]:
            from .operations import lightstrip

            sub_op = "set" if op_lower == "led" else "off"
            # LED expects 3 params (r, g, b) inside execute.
            # We handle the mapping from param1/2/3 here if needed, but lightstrip.execute can also handle it.
            return await lightstrip.execute(ctx, sub_op, param1, param2, payload.get("b") if payload else 0)
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
