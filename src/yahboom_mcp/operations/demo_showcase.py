"""Unified Boomy show-floor demo dispatcher."""

from __future__ import annotations

from typing import Any

from .. import fail_response
from ..demo.draw_executor import get_draw_executor
from ..demo.interactions import get_cafe_demo, get_dog_demo
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
                "found_dog": get_dog_demo().describe(),
                "cafe_host": get_cafe_demo().describe(),
            },
            "usage": (
                "yahboom_demo(operation='draw', pattern='smiley') or yahboom_demo(operation='talkbot', max_turns=3)"
                " or yahboom_demo(operation='found_dog') or yahboom_demo(operation='cafe_host')"
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

    if op in ("found_dog", "dog"):
        return await get_dog_demo().run(use_speech_mcp=use_speech_mcp)
    if op in ("found_dog_status", "dog_status"):
        return get_dog_demo().get_status()
    if op in ("found_dog_stop", "dog_stop"):
        return await get_dog_demo().stop()

    if op in ("cafe_host", "cafe"):
        return await get_cafe_demo().run(
            use_speech_mcp=use_speech_mcp,
            max_facts=max_turns,
            scripted_customer=scripted_user_lines[0] if scripted_user_lines else None,
        )
    if op in ("cafe_host_status", "cafe_status"):
        return get_cafe_demo().get_status()
    if op in ("cafe_host_stop", "cafe_stop"):
        return await get_cafe_demo().stop()

    if op == "status":
        return {
            "success": True,
            "draw": get_draw_executor().get_status(),
            "talkbot": get_talkbot_demo().get_status(),
            "found_dog": get_dog_demo().get_status(),
            "cafe_host": get_cafe_demo().get_status(),
        }
    if op == "stop":
        d = await get_draw_executor().stop()
        t = await get_talkbot_demo().stop()
        g = await get_dog_demo().stop()
        c = await get_cafe_demo().stop()
        return {"success": True, "draw": d, "talkbot": t, "found_dog": g, "cafe_host": c}

    return fail_response(
        f"Unknown demo operation: {operation}",
        recovery_options=[
            "describe",
            "draw",
            "draw_status",
            "draw_stop",
            "talkbot",
            "talkbot_status",
            "talkbot_stop",
            "found_dog",
            "found_dog_status",
            "found_dog_stop",
            "cafe_host",
            "cafe_host_status",
            "cafe_host_stop",
            "status",
            "stop",
        ],
    )
