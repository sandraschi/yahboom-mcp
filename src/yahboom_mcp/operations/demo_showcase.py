"""Unified Boomy show-floor demo dispatcher."""

from __future__ import annotations

from typing import Any

from .. import fail_response
from ..demo.draw_executor import get_draw_executor
from ..demo.talkbot import get_talkbot_demo


async def execute(
    operation: str,
    *,
    pattern: str = "smiley",
    speed: float | None = None,
    skip_color_swap_pause: bool = False,
    approach: bool | None = None,
    max_turns: int | None = None,
    use_speech_mcp: bool = True,
    scripted_user_lines: list[str] | None = None,
) -> dict[str, Any]:
    op = operation.strip().lower()

    if op in ("describe", "help"):
        return {
            "success": True,
            "demos": {
                "draw": get_draw_executor().describe(),
                "talkbot": get_talkbot_demo().describe(),
            },
            "usage": (
                "yahboom_demo(operation='draw', pattern='smiley') or "
                "yahboom_demo(operation='talkbot', max_turns=3)"
            ),
        }

    if op == "draw":
        return await get_draw_executor().run(
            pattern=pattern,
            speed=speed,
            skip_color_swap_pause=skip_color_swap_pause,
        )
    if op == "draw_status":
        return get_draw_executor().get_status()
    if op == "draw_stop":
        return await get_draw_executor().stop()

    if op == "talkbot":
        return await get_talkbot_demo().run(
            approach=approach,
            max_turns=max_turns,
            use_speech_mcp=use_speech_mcp,
            scripted_user_lines=scripted_user_lines,
        )
    if op == "talkbot_status":
        return get_talkbot_demo().get_status()
    if op == "talkbot_stop":
        return await get_talkbot_demo().stop()

    if op == "status":
        return {
            "success": True,
            "draw": get_draw_executor().get_status(),
            "talkbot": get_talkbot_demo().get_status(),
        }
    if op == "stop":
        d = await get_draw_executor().stop()
        t = await get_talkbot_demo().stop()
        return {"success": True, "draw": d, "talkbot": t}

    return fail_response(f"Unknown demo operation: {operation}", recovery_options=[
        "describe", "draw", "draw_status", "draw_stop", "talkbot", "talkbot_status", "talkbot_stop", "status", "stop",
    ])
