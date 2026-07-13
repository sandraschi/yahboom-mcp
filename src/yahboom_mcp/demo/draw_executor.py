"""Execute floor-draw segments on Boomy (mecanum open-loop)."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from .. import fail_response
from ..state import _state
from .draw_patterns import list_patterns, pattern_layers

logger = logging.getLogger("yahboom-mcp.demo.draw")


def _fast_demo() -> bool:
    return os.getenv("YAHBOOM_DEMO_FAST", "0") == "1"


class DrawExecutor:
    def __init__(self) -> None:
        self.status = "idle"
        self.logs: list[str] = []
        self._task: asyncio.Task | None = None

    def _log(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        self.logs.append(line)
        if len(self.logs) > 80:
            self.logs.pop(0)
        logger.info(line)

    def describe(self) -> dict[str, Any]:
        base = list_patterns()
        return {
            **base,
            "operations": ["describe", "run", "status", "stop"],
            "env": {
                "YAHBOOM_DRAW_SPEED": os.getenv("YAHBOOM_DRAW_SPEED", "0.06"),
                "YAHBOOM_PEN_SERVO": os.getenv("YAHBOOM_PEN_SERVO", "0"),
            },
            "message": "Chalk/marker floor art via mecanum waypoints (open-loop).",
        }

    def get_status(self) -> dict[str, Any]:
        return {
            "success": True,
            "status": self.status,
            "logs": list(self.logs),
            "running": self._task is not None and not self._task.done(),
        }

    async def stop(self) -> dict[str, Any]:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        bridge = _state.get("bridge")
        if bridge and bridge.connected:
            await bridge.publish_velocity(0.0, 0.0)
        self.status = "stopped"
        return {"success": True, "message": "Draw demo stopped"}

    async def run(
        self,
        *,
        pattern: str = "smiley",
        speed: float | None = None,
        skip_color_swap_pause: bool = False,
    ) -> dict[str, Any]:
        if self._task and not self._task.done():
            return fail_response("Draw demo already running")
        draw_speed = speed or float(os.getenv("YAHBOOM_DRAW_SPEED", "0.06"))
        self.logs = []
        self._task = asyncio.create_task(
            self._run_draw(pattern=pattern, speed=draw_speed, skip_color_swap_pause=skip_color_swap_pause)
        )
        return {"success": True, "pattern": pattern, "message": "Draw demo started", "speed": draw_speed}

    async def _run_draw(
        self,
        *,
        pattern: str,
        speed: float,
        skip_color_swap_pause: bool,
    ) -> dict[str, Any]:
        bridge = _state.get("bridge")
        ssh = _state.get("ssh")
        self.status = "running"
        steps: list[dict[str, Any]] = []
        try:
            from ..operations import lightstrip, voice

            await lightstrip.execute(None, "pattern", 10)
            await asyncio.sleep(0.8)
            await lightstrip.execute(None, "set", 180, 120, 255)

            layers = pattern_layers(pattern, speed=speed)
            for layer_idx, layer in enumerate(layers):
                if layer_idx > 0:
                    await self._pen_up(ssh)
                    steps.append({"step": "pen_up", "color": layer["color"]})
                    if not skip_color_swap_pause:
                        self._log(f"Swap to color {layer['color']} — waiting 8s")
                        await voice.execute(None, "play_beep")
                        await asyncio.sleep(8.0)
                    await self._pen_down(ssh)
                    steps.append({"step": "pen_down", "color": layer["color"]})

                self._log(f"Drawing layer {layer['label']} (color {layer['color']})")
                for seg in layer["segments"]:
                    await self._exec_segment(bridge, seg)
                    steps.append({"layer": layer["label"], "segment": seg})

            await self._pen_up(ssh)
            if bridge and bridge.connected:
                await bridge.publish_velocity(0.0, 0.0)
            await lightstrip.execute(None, "set", 0, 255, 120)
            await voice.execute(
                None,
                "say",
                "I drew that on the floor. Boomy artist mode complete.",
            )
            self.status = "completed"
            return {
                "success": True,
                "pattern": pattern,
                "layers": len(layers),
                "steps_count": len(steps),
                "message": "Floor draw complete.",
            }
        except asyncio.CancelledError:
            self.status = "cancelled"
            if bridge and bridge.connected:
                await bridge.publish_velocity(0.0, 0.0)
            raise
        except Exception as exc:
            self.status = "error"
            self._log(f"Error: {exc}")
            if bridge and bridge.connected:
                await bridge.publish_velocity(0.0, 0.0)
            return fail_response(str(exc))

    async def _exec_segment(self, bridge, seg: dict[str, Any]) -> None:
        kind = seg.get("kind")
        if kind == "drive":
            dist = float(seg["distance_m"])
            spd = max(0.03, float(seg.get("speed", 0.06)))
            duration = dist / spd
            duration = min(duration, 0.01) if _fast_demo() else duration
            if bridge and bridge.connected:
                await bridge.publish_velocity(linear_x=spd, angular_z=0.0)
                await asyncio.sleep(duration)
                await bridge.publish_velocity(0.0, 0.0)
            else:
                await asyncio.sleep(duration)
            await asyncio.sleep(min(0.15, 0.01) if _fast_demo() else 0.15)
            return
        if kind == "turn":
            angle = float(seg["angle_rad"])
            rate = max(0.2, float(seg.get("rate", 0.45)))
            duration = abs(angle) / rate
            duration = min(duration, 0.01) if _fast_demo() else duration
            az = rate if angle > 0 else -rate
            if bridge and bridge.connected:
                await bridge.publish_velocity(linear_x=0.0, angular_z=az)
                await asyncio.sleep(duration)
                await bridge.publish_velocity(0.0, 0.0)
            else:
                await asyncio.sleep(duration)
            await asyncio.sleep(min(0.15, 0.01) if _fast_demo() else 0.15)
            return
        if kind == "strafe":
            dist = float(seg["distance_m"])
            spd = max(0.03, float(seg.get("speed", 0.06)))
            duration = dist / spd
            if bridge and bridge.connected:
                await bridge.publish_velocity(linear_x=0.0, angular_z=0.0, linear_y=spd)
                await asyncio.sleep(duration)
                await bridge.publish_velocity(0.0, 0.0)
            else:
                await asyncio.sleep(min(duration, 0.05))
            await asyncio.sleep(0.15)

    async def _pen_up(self, ssh) -> None:
        if os.getenv("YAHBOOM_PEN_SERVO", "0") == "1" and ssh:
            self._log("pen_up (servo — wire YAHBOOM_PEN_SERVO GPIO in hardware)")
        else:
            self._log("pen_up (virtual — fixed mount: lift robot slightly or use servo when wired)")

    async def _pen_down(self, ssh) -> None:
        if os.getenv("YAHBOOM_PEN_SERVO", "0") == "1" and ssh:
            self._log("pen_down (servo)")
        else:
            self._log("pen_down (virtual — chalk engaged)")


_draw_executor: DrawExecutor | None = None


def get_draw_executor() -> DrawExecutor:
    global _draw_executor
    if _draw_executor is None:
        _draw_executor = DrawExecutor()
    return _draw_executor
