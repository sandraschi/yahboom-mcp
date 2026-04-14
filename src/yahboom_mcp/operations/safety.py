import logging
from typing import Any

from fastmcp import Context

logger = logging.getLogger("yahboom-mcp.operations.safety")


async def execute(
    ctx: Context | None = None,
    operation: str = "stop_all",
    param1: Any = None,
    param2: Any = None,
    payload: dict | None = None,
) -> dict:
    """
    Execute global safety operations.
    Operation: stop_all -> Stops motion, missions, sequencers, and recordings.
    """
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(f"Safety: {operation}", extra={"correlation_id": correlation_id})

    from ..state import _state

    bridge = _state.get("bridge")
    sequencer = _state.get("sequencer")
    trajectory_manager = _state.get("trajectory_manager")

    results = []

    if operation == "stop_all":
        # 1. Stop Motion immediately
        if bridge and bridge.connected:
            await bridge.publish_velocity(0.0, 0.0, 0.0)
            results.append("motion_stopped")

        # 2. Stop Missions
        from .missions import MissionManager

        try:
            mgr = MissionManager.get_instance()
            if mgr.active_mission:
                await mgr.stop_mission()
                results.append("mission_aborted")
        except Exception as e:
            logger.debug(f"MissionManager stop failed (likely not initialized): {e}")

        # 3. Stop Peripherals Sequencer
        if sequencer and sequencer.active:
            await sequencer.stop()
            results.append("sequencer_stopped")

        # 4. Stop Trajectory Recording
        if trajectory_manager and trajectory_manager.is_recording:
            trajectory_manager.stop_recording("emergency_halt")
            results.append("recording_finalized")

        return {
            "success": True,
            "operation": operation,
            "status": "system_halted",
            "actions": results,
            "correlation_id": correlation_id,
        }

    return {
        "success": False,
        "operation": operation,
        "error": f"Unknown safety operation: {operation}",
        "correlation_id": correlation_id,
    }
