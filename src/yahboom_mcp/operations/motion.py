from fastmcp import Context
import logging

logger = logging.getLogger("yahboom-mcp.operations.motion")


async def execute(
    ctx: Context | None = None,
    operation: str = "",
    param1: str | float | None = None,
    param2: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """Execute motion operations: forward, backward, turn_left, turn_right, stop."""
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(
        f"Motion: {operation} (param1={param1}, param2={param2})",
        extra={"correlation_id": correlation_id},
    )

    # Use bridge from global state
    from ..state import _state

    bridge = _state.get("bridge")

    linear_x = param1 if operation in ["forward", "backward"] else 0.0
    linear_y = param1 if operation in ["strafe_left", "strafe_right"] else 0.0
    angular_z = param1 if "turn" in operation else 0.0

    # Adjust signs for direction
    if operation == "backward":
        linear_x = -linear_x
    if operation == "strafe_right":
        linear_y = -linear_y

    if bridge and bridge.connected:
        success = await bridge.publish_velocity(
            linear_x=linear_x,
            linear_y=linear_y,
            angular_z=angular_z,
        )
        status = "command_sent" if success else "command_failed"
    else:
        status = "mock_command_sent"
        logger.warning("Operating in mock mode (Bridge not connected)")

    return {
        "success": True,
        "operation": operation,
        "result": {
            "status": status,
            "parameters": {
                "linear_x": linear_x,
                "linear_y": linear_y,
                "angular_z": angular_z,
            },
        },
        "correlation_id": correlation_id,
        "requires_sampling": True,
        "sampling_intent": f"Requested {operation} with {param1}. Verify trajectory via odometry.",
    }
