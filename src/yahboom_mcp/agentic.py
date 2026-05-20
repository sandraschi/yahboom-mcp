"""
Agentic workflow and sampling tools for Yahboom MCP (FastMCP 3.1 / SEP-1577).

Exposes a single high-level tool that uses ctx.sample() so the LLM can plan and
execute sequences of robot operations via sub-tools.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import Context
from pydantic import Field

from .portmanteau import yahboom_tool

logger = logging.getLogger("yahboom-mcp.agentic")


async def _get_robot_health(ctx: Context | None = None) -> str:
    """Get robot connection and battery status. Call before planning motion."""
    out = await yahboom_tool(ctx=ctx, operation="health_check")
    if isinstance(out, dict):
        return str(out.get("result", out))
    return str(out)


async def _move_robot(direction: str, duration_seconds: float = 1.0, ctx: Context | None = None) -> str:
    """
    Send a motion command. direction: forward, backward, turn_left, turn_right, strafe_left, strafe_right, stop.
    duration_seconds: how long to apply (approximate). Use stop to halt.
    """
    speed = 0.3
    if direction == "stop":
        out = await yahboom_tool(ctx=ctx, operation="stop", param1=0)
    elif direction == "forward":
        out = await yahboom_tool(ctx=ctx, operation="forward", param1=speed)
    elif direction == "backward":
        out = await yahboom_tool(ctx=ctx, operation="backward", param1=speed)
    elif direction == "turn_left":
        out = await yahboom_tool(ctx=ctx, operation="turn_left", param1=0.4)
    elif direction == "turn_right":
        out = await yahboom_tool(ctx=ctx, operation="turn_right", param1=0.4)
    elif direction == "strafe_left":
        out = await yahboom_tool(ctx=ctx, operation="strafe_left", param1=0.2)
    elif direction == "strafe_right":
        out = await yahboom_tool(ctx=ctx, operation="strafe_right", param1=0.2)
    else:
        return f"Unknown direction: {direction}. Use one of: forward, backward, turn_left, turn_right, strafe_left, strafe_right, stop."
    return str(out)


async def _read_sensors(sensor_type: str = "all", ctx: Context | None = None) -> str:
    """
    Read robot sensors. sensor_type: imu, battery, all.
    Returns heading (degrees), battery %, or full telemetry.
    """
    if sensor_type == "imu":
        out = await yahboom_tool(ctx=ctx, operation="read_imu")
    elif sensor_type == "battery":
        out = await yahboom_tool(ctx=ctx, operation="read_battery")
    else:
        out = await yahboom_tool(ctx=ctx, operation="health_check")
    return str(out)


async def yahboom_agentic_workflow(
    goal: Annotated[
        str,
        Field(
            description="High-level goal in natural language, e.g. 'patrol in a square', 'check battery and report'."
        ),
    ],
    ctx: Context,
) -> str:
    """
    Achieve a high-level robot goal by planning and executing a sequence of operations (SEP-1577).
    Uses ctx.sample() so the LLM can call get_robot_health, move_robot, and read_sensors as sub-tools.

    ## Return Format
    str: Summary of steps executed and the outcome, or error message if the workflow failed.

    ## Examples
    yahboom_agentic_workflow(goal="patrol in a square and report battery")
    yahboom_agentic_workflow(goal="check health, then move forward 2 seconds")
    """

    async def get_robot_health() -> str:
        return await _get_robot_health(ctx)

    async def move_robot(direction: str, duration_seconds: float = 1.0) -> str:
        return await _move_robot(direction, duration_seconds, ctx=ctx)

    async def read_sensors(sensor_type: str = "all") -> str:
        return await _read_sensors(sensor_type, ctx=ctx)

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
