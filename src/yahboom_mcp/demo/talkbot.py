"""Boomy talkbot: approach, PTZ wiggle, conversation via voice + speech-mcp."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from typing import Any

from ..state import _state
from .speech_client import SpeechMcpClient

logger = logging.getLogger("yahboom-mcp.demo.talkbot")

OPENING = "Hi, I am Boomy. Who are you?"

_NAME_PATTERNS = (
    re.compile(r"\b(?:i am|i'm|my name is|call me)\s+([A-Za-z][A-Za-z\-']{1,24})", re.I),
    re.compile(r"\b(?:ich heiße|ich bin)\s+([A-Za-zäöüÄÖÜß][A-Za-zäöüÄÖÜß\-']{1,24})", re.I),
)


def _extract_name(text: str) -> str | None:
    for pat in _NAME_PATTERNS:
        m = pat.search(text.strip())
        if m:
            return m.group(1).strip().title()
    words = text.strip().split()
    if 1 <= len(words) <= 3 and words[0].istitle():
        return words[0]
    return None


def _reply_for_turn(turn: int, user_text: str, name: str | None) -> str:
    t = user_text.strip().lower()
    if turn == 0:
        if name:
            return f"Nice to meet you, {name}. I can draw on the floor or just chat. What would you like?"
        return "I did not catch a name, but hello anyway. Ask me about drawing or what I can do."
    if any(w in t for w in ("draw", "picture", "chalk", "art", "malen", "zeichnen")):
        return "Say demo draw and I will sketch a smiley with chalk. Two colors look best."
    if any(w in t for w in ("who", "what are you", "boomy", "robot")):
        return "I am Boomy, a Yahboom Raspbot with mecanum wheels, a PTZ camera, and a curious personality."
    if name:
        return f"Thanks {name}. I am still learning — but I love meeting people at demos."
    return "Tell me your name, or ask me to draw something on the floor."


class TalkbotDemo:
    def __init__(self) -> None:
        self.status = "idle"
        self.logs: list[str] = []
        self.transcript: list[dict[str, str]] = []
        self._task: asyncio.Task | None = None

    def _log(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        self.logs.append(line)
        if len(self.logs) > 80:
            self.logs.pop(0)
        logger.info(line)

    def describe(self) -> dict[str, Any]:
        return {
            "success": True,
            "demo": "boomy_talkbot",
            "beats": [
                "optional approach (ultrasonic stop)",
                "PTZ tilt up + pan wiggle",
                "opening TTS: Hi, I am Boomy. Who are you?",
                "listen turns (voice module or speech-mcp FunASR)",
                "template replies + optional speech-mcp TTS",
            ],
            "env": {
                "YAHBOOM_SPEECH_MCP_URL": os.getenv("YAHBOOM_SPEECH_MCP_URL", "http://127.0.0.1:10909"),
                "YAHBOOM_TALKBOT_APPROACH": os.getenv("YAHBOOM_TALKBOT_APPROACH", "1"),
                "YAHBOOM_TALKBOT_TURNS": os.getenv("YAHBOOM_TALKBOT_TURNS", "3"),
            },
            "message": "Social approach demo — Boomy, not Noomy.",
        }

    def get_status(self) -> dict[str, Any]:
        return {
            "success": True,
            "status": self.status,
            "logs": list(self.logs),
            "transcript": list(self.transcript),
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
        return {"success": True, "message": "Talkbot demo stopped"}

    async def run(
        self,
        *,
        approach: bool | None = None,
        max_turns: int | None = None,
        use_speech_mcp: bool = True,
        scripted_user_lines: list[str] | None = None,
    ) -> dict[str, Any]:
        if self._task and not self._task.done():
            return {"success": False, "error": "Talkbot demo already running"}
        do_approach = approach if approach is not None else os.getenv("YAHBOOM_TALKBOT_APPROACH", "1") == "1"
        turns = max_turns or int(os.getenv("YAHBOOM_TALKBOT_TURNS", "3"))
        self.logs = []
        self.transcript = []
        self._task = asyncio.create_task(
            self._run_talkbot(
                approach=do_approach,
                max_turns=turns,
                use_speech_mcp=use_speech_mcp,
                scripted_user_lines=scripted_user_lines,
            )
        )
        return {"success": True, "message": "Talkbot demo started", "max_turns": turns}

    async def _speak(self, text: str, *, use_speech_mcp: bool) -> dict[str, Any]:
        from ..operations import voice

        if use_speech_mcp:
            client = SpeechMcpClient()
            health = await client.health()
            if health.get("reachable"):
                out = await client.speak(text)
                if out.get("success"):
                    self._log(f"TTS (speech-mcp): {text[:60]}...")
                    await asyncio.sleep(max(1.5, len(text) / 45))
                    return out
        await voice.execute(None, "say", text)
        self._log(f"TTS (espeak): {text[:60]}...")
        await asyncio.sleep(max(1.5, len(text) / 45))
        return {"success": True, "provider": "espeak"}

    async def _listen_once(self, timeout_s: float, *, scripted: str | None) -> str:
        if scripted is not None:
            self._log(f"Scripted user: {scripted}")
            await asyncio.sleep(0.5)
            return scripted

        from ..operations import voice

        out = await voice.execute(None, "listen", timeout_s)
        if out.get("success") and out.get("result", {}).get("command_id") is not None:
            cid = out["result"]["command_id"]
            self._log(f"Voice module command id: {cid}")
            return f"voice command {cid}"

        return ""

    async def _ptz_wiggle(self) -> None:
        from ..operations import camera_ptz

        bridge = _state.get("bridge")
        ssh = _state.get("ssh")
        if not bridge:
            self._log("PTZ wiggle skipped (no bridge)")
            return
        await camera_ptz.camera_set_pos(bridge, 90, 60, ssh_bridge=ssh)
        await asyncio.sleep(0.4)
        for pan in (70, 110, 90, 75, 105, 90):
            await camera_ptz.camera_set_pos(bridge, pan, 60, ssh_bridge=ssh)
            await asyncio.sleep(0.25)
        self._log("PTZ wiggle complete")

    async def _approach(self, bridge) -> None:
        if not bridge or not bridge.connected:
            self._log("Approach skipped (mock/offline)")
            return
        self._log("Approaching (slow forward, ultrasonic stop ~0.55m)")
        for _ in range(40):
            sonar = bridge.state.get("ir_proximity")
            if isinstance(sonar, (int, float)) and sonar < 0.55:
                self._log(f"Stopped at {sonar:.2f} m")
                break
            await bridge.publish_velocity(linear_x=0.12, angular_z=0.0)
            await asyncio.sleep(0.2)
        await bridge.publish_velocity(0.0, 0.0)
        await asyncio.sleep(0.3)

    async def _run_talkbot(
        self,
        *,
        approach: bool,
        max_turns: int,
        use_speech_mcp: bool,
        scripted_user_lines: list[str] | None,
    ) -> dict[str, Any]:
        bridge = _state.get("bridge")
        self.status = "running"
        name: str | None = None
        try:
            from ..operations import lightstrip

            await lightstrip.execute(None, "set", 200, 180, 255)
            if approach:
                await self._approach(bridge)
            await self._ptz_wiggle()
            await self._speak(OPENING, use_speech_mcp=use_speech_mcp)
            self.transcript.append({"role": "boomy", "text": OPENING})

            for turn in range(max_turns):
                scripted = None
                if scripted_user_lines and turn < len(scripted_user_lines):
                    scripted = scripted_user_lines[turn]
                user_text = await self._listen_once(5.0, scripted=scripted)
                if not user_text and turn == 0 and scripted_user_lines is None:
                    user_text = "My name is guest"
                    self._log("No input — using demo fallback line")
                if not user_text:
                    break
                self.transcript.append({"role": "user", "text": user_text})
                if name is None:
                    name = _extract_name(user_text)
                reply = _reply_for_turn(turn, user_text, name)
                await self._speak(reply, use_speech_mcp=use_speech_mcp)
                self.transcript.append({"role": "boomy", "text": reply})

            farewell = f"Nice meeting you{', ' + name if name else ''}. Boomy signing off."
            await self._speak(farewell, use_speech_mcp=use_speech_mcp)
            self.transcript.append({"role": "boomy", "text": farewell})
            await lightstrip.execute(None, "off")
            self.status = "completed"
            return {
                "success": True,
                "name_detected": name,
                "turns": len([t for t in self.transcript if t["role"] == "user"]),
                "transcript": list(self.transcript),
                "message": "Talkbot demo complete.",
            }
        except asyncio.CancelledError:
            self.status = "cancelled"
            if bridge and bridge.connected:
                await bridge.publish_velocity(0.0, 0.0)
            raise
        except Exception as exc:
            self.status = "error"
            self._log(str(exc))
            return {"success": False, "error": str(exc)}


_talkbot: TalkbotDemo | None = None


def get_talkbot_demo() -> TalkbotDemo:
    global _talkbot
    if _talkbot is None:
        _talkbot = TalkbotDemo()
    return _talkbot
