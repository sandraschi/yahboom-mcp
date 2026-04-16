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
        Field(
            description="Operation: health_check, forward/backward, turn_left/right, strafe_left/right, stop/stop_all, read_imu/battery/encoders/lidar, say/play, display/clear_display, led/off/light_effect/patrol_car, camera_up/down/left/right, camera_reset, stack_inspect, execute_command."

        ),
    ] = "health_check",
    param1: Annotated[
        str | float | None,
        Field(
            description="First parameter: duration, speed, or basename depending on operation."
        ),
    ] = None,
    param2: Annotated[
        str | float | None,
        Field(description="Second parameter when required by operation."),
    ] = None,
    param3: Annotated[
        str | float | None,
        Field(
            description="Third parameter when required by operation (e.g. RGB Blue)."
        ),
    ] = None,
    payload: Annotated[
        dict | None,
        Field(description="Optional key-value payload for future use."),
    ] = None,
) -> dict:
    """
    Unified control for Yahboom Raspbot v2 (ROS 2 Humble).
    Routes motion, sensors, diagnostics, and peripheral commands to hardware drivers.
    Returns success (bool) and operation-specific telemetry or status dictionaries.
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
        elif op_lower in [
            "read_imu",
            "read_encoders",
            "read_battery",
            "read_all",
            "read_lidar",
        ]:
            from .operations import sensors

            return await sensors.execute(ctx, op_lower, param1, param2, payload)
        elif op_lower in ["say", "play", "play_beep", "play_file", "chat_and_say"]:
            from .operations import voice

            return await voice.execute(ctx, op_lower, param1, param2, payload)
        elif op_lower in ["display", "clear_display"]:
            from .operations import display

            sub_op = "write" if op_lower == "display" else "clear"
            return await display.execute(ctx, sub_op, param1, param2, payload)
        elif op_lower in ["led", "led_off", "light_effect", "patrol_car"]:
            from .operations import lightstrip

            if op_lower == "patrol_car":
                return await lightstrip.execute(ctx, "pattern", 10)

            sub_op = (
                "set"
                if op_lower == "led"
                else ("off" if op_lower == "led_off" else "pattern")
            )
            # LED expects 3 params (r, g, b) inside execute.
            p3 = param3 if param3 is not None else (payload.get("b") if payload else 0)
            return await lightstrip.execute(ctx, sub_op, param1, param2, p3)
        elif op_lower in ["camera_up", "camera_down", "camera_left", "camera_right", "camera_reset"]:
            from .operations import camera_ptz

            bridge = _state.get("bridge")
            ssh = _state.get("ssh")

            if op_lower == "camera_reset":
                return await camera_ptz.camera_reset(bridge, ssh_bridge=ssh)

            direction = op_lower.replace("camera_", "")
            step = int(param1) if param1 else 15
            return await camera_ptz.camera_move(bridge, direction, step=step, ssh_bridge=ssh)

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
        elif op_lower in [
            "health_check",
            "config_show",
            "inspect_stack",
            "execute_command",
        ]:
            from .operations import diagnostics

            return await diagnostics.execute(ctx, op_lower, param1, param2, payload)
        elif op_lower == "stop_all":
            from .operations import safety

            return await safety.execute(ctx, "stop_all", param1, param2, payload)
    except Exception as e:
        logger.error(f"Operation {operation} failed: {e}", exc_info=True)
        return {
            "success": False,
            "operation": operation,
            "error": str(e),
            "correlation_id": correlation_id,
        }
