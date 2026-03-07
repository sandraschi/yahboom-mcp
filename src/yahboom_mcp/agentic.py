"""
Agentic workflow and sampling tools for Yahboom MCP (FastMCP 3.1 / SEP-1577).

Exposes a single high-level tool that uses ctx.sample() so the LLM can plan and
execute sequences of robot operations via sub-tools.
"""

from __future__ import annotations

import logging
from fastmcp import Context

from .state import _state
from .portmanteau import yahboom_tool

logger = logging.getLogger("yahboom-mcp.agentic")


async def _get_robot_health() -> str:
    """Get robot connection and battery status. Call before planning motion."""
    out = await yahboom_tool(ctx=None, operation="health_check")
    if isinstance(out, dict):
        return str(out.get("result", out))
    return str(out)


async def _move_robot(direction: str, duration_seconds: float = 1.0) -> str:
    """
    Send a motion command. direction: forward, backward, turn_left, turn_right, strafe_left, strafe_right, stop.
    duration_seconds: how long to apply (approximate). Use stop to halt.
    """
    speed = 0.3
    if direction == "stop":
        out = await yahboom_tool(ctx=None, operation="stop", param1=0)
    elif direction == "forward":
        out = await yahboom_tool(ctx=None, operation="forward", param1=speed)
    elif direction == "backward":
        out = await yahboom_tool(ctx=None, operation="backward", param1=speed)
    elif direction == "turn_left":
        out = await yahboom_tool(ctx=None, operation="turn_left", param1=0.4)
    elif direction == "turn_right":
        out = await yahboom_tool(ctx=None, operation="turn_right", param1=0.4)
    elif direction == "strafe_left":
        out = await yahboom_tool(ctx=None, operation="strafe_left", param1=0.2)
    elif direction == "strafe_right":
        out = await yahboom_tool(ctx=None, operation="strafe_right", param1=0.2)
    else:
        return f"Unknown direction: {direction}. Use one of: forward, backward, turn_left, turn_right, strafe_left, strafe_right, stop."
    return str(out)


async def _read_sensors(sensor_type: str = "all") -> str:
    """
    Read robot sensors. sensor_type: imu, battery, all.
    Returns heading (degrees), battery %, or full telemetry.
    """
    if sensor_type == "imu":
        out = await yahboom_tool(ctx=None, operation="read_imu")
    elif sensor_type == "battery":
        out = await yahboom_tool(ctx=None, operation="read_battery")
    else:
        out = await yahboom_tool(ctx=None, operation="health_check")
    return str(out)


async def yahboom_agentic_workflow(goal: str, ctx: Context) -> str:
    """
    Achieve a high-level robot goal by planning and executing a sequence of operations (SEP-1577).

    Use this for goals like: "patrol in a square", "check battery and report", "move forward 2 seconds then stop".
    The LLM will use the available sub-tools (get_robot_health, move_robot, read_sensors) to plan and run steps.
    """
    import json

    async def get_robot_health() -> str:
        return await _get_robot_health()

    async def move_robot(direction: str, duration_seconds: float = 1.0) -> str:
        return await _move_robot(direction, duration_seconds)

    async def read_sensors(sensor_type: str = "all") -> str:
        return await _read_sensors(sensor_type)

    system_prompt = (
        "You are a Yahboom G1 robot operator. You have tools: get_robot_health (no args), "
        "move_robot(direction, duration_seconds) with direction one of forward, backward, turn_left, turn_right, strafe_left, strafe_right, stop, "
        "and read_sensors(sensor_type) with sensor_type one of imu, battery, all. "
        "Plan a short sequence of steps to achieve the user's goal. Execute the steps and then summarize what was done and the outcome."
    )
    try:
        result = await ctx.sample(
            messages=goal,
            system_prompt=system_prompt,
            tools=[get_robot_health, move_robot, read_sensors],
            temperature=0.2,
            max_tokens=1024,
        )
        return result.text or "No response from planner."
    except Exception as e:
        logger.exception("Agentic workflow failed")
        return f"Workflow failed: {e}"
