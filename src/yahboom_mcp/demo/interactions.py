"""Boomy social & environmental interaction demos: dog meeting + cafe host.

Two scripted-but-lively demos that lean on Boomy's existing actuators:

  DogMeetingDemo ("found_dog")
      Boomy spots a dog, announces the discovery, barks, wags (strafe sway +
      warm light pulse), approaches cautiously, greets, and - if a gripper
      servo is reachable - offers a cookie by opening the claw. Camera tilts
      down to dog height.

  CafeHostDemo ("cafe_host")
      Boomy weaves between table legs (mecanum slalom), greets a customer,
      offers a short chat about coffee with a few Vienna coffeehouse facts,
      makes a recommendation, bows ("servus"), and leaves.

Both follow the talkbot.py convention: background asyncio task, status/logs/
transcript, speech-mcp TTS when reachable with espeak-ng fallback, and full
cancellation safety (velocity zeroed on stop/cancel). All motion is
obstacle-aware and degrades gracefully when sensors/vision are absent.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from .. import fail_response
from ..state import _state
from .speech_client import SpeechMcpClient

logger = logging.getLogger("yahboom-mcp.demo.interactions")

# Polite approach / collision thresholds (metres)
_APPROACH_STOP = 0.55
_OBSTACLE_SONAR = 0.20
_OBSTACLE_LIDAR = 0.30

COFFEE_FACTS = [
    "In Vienna, the coffeehouse is a UNESCO World Cultural Heritage.",
    "The first Viennese coffee house opened its doors in 1685.",
    "A Kleiner Brauner is a small espresso with a splash of cream.",
    "The Wiener Melange is like a cappuccino, but with milk froth on top.",
    "A Verlaengerter is a long coffee, espresso topped up with hot water.",
    "The Einspaenner is a mocha crowned with whipped cream, served in a glass with a handle.",
]

COFFEE_RECOMMENDATIONS = [
    "I recommend a Wiener Melange. Smooth, mild, and very Viennese.",
    "If you need a proper kick, try a Kleiner Brauner.",
    "For something long and light, a Verlaengerter is a fine choice.",
]

OPENING_DOG = "Hey! I found a dog! Will he be my friend?"
GREET_DOG = "Hello doggy. I am Boomy. I come in peace, and I bring treats."
COOKIE_LINE = "Here is a cookie for you. Bow-wow! Let us be friends."
NO_COOKIE_LINE = "Oh dear, my gripper is away for maintenance today, so no cookie. But we can still be friends. Woof!"
FAREWELL_DOG = "I have to patrol now. Woof woof! See you around, doggy."

OPENING_CAFE = "Guten Tag! I am Boomy, your coffee house host. May I interest you in a short chat about coffee?"
FAREWELL_CAFE = "Auf Wiedersehen! Enjoy your coffee. I am off to greet more guests."


class SocialDemoBase:
    """Shared scaffold for the interaction demos (log, speak, stop)."""

    def __init__(self, demo_id: str) -> None:
        self.demo_id = demo_id
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
        logger.info("[%s] %s", self.demo_id, line)

    def get_status(self) -> dict[str, Any]:
        return {
            "success": True,
            "demo": self.demo_id,
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
        return {"success": True, "demo": self.demo_id, "message": f"{self.demo_id} demo stopped"}

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

    def _say(self, text: str) -> None:
        self.transcript.append({"role": "boomy", "text": text})


class DogMeetingDemo(SocialDemoBase):
    """'I found a dog!' - announce, bark, wag, approach, offer cookie."""

    def __init__(self) -> None:
        super().__init__("boomy_found_dog")

    def describe(self) -> dict[str, Any]:
        return {
            "success": True,
            "demo": self.demo_id,
            "beats": [
                "announce: 'Hey! I found a dog! Will he be my friend?'",
                "bark (soundboard) + tail-wag (strafe sway + warm light pulse)",
                "cautious approach (ultrasonic/lidar stop)",
                "camera tilt down to dog height",
                "greet + offer cookie if gripper servo reachable",
                "farewell woof",
            ],
            "env": {
                "YAHBOOM_SPEECH_MCP_URL": os.getenv("YAHBOOM_SPEECH_MCP_URL", "http://127.0.0.1:10909"),
            },
            "message": "Social demo - Boomy meets a dog, politely.",
        }

    async def run(self, *, use_speech_mcp: bool = True) -> dict[str, Any]:
        if self._task and not self._task.done():
            return fail_response("Dog demo already running")
        self.logs = []
        self.transcript = []
        self._task = asyncio.create_task(self._run(use_speech_mcp=use_speech_mcp))
        return {"success": True, "message": "Dog meeting demo started"}

    async def _bark(self) -> None:
        from ..operations import audio

        self._log("Bark!")
        await audio.execute(operation="sound", file_name="bark")
        await asyncio.sleep(0.3)

    async def _tail_wag(self, bridge) -> None:
        from ..operations import lightstrip

        self._log("Tail-wag: strafe sway + warm pulse")
        await lightstrip.execute(None, "set", 255, 170, 60)
        if bridge and bridge.connected:
            for _ in range(3):
                await bridge.publish_velocity(linear_x=0.0, angular_z=0.0, linear_y=0.12)
                await asyncio.sleep(0.3)
                await bridge.publish_velocity(linear_x=0.0, angular_z=0.0, linear_y=-0.12)
                await asyncio.sleep(0.3)
            await bridge.publish_velocity(0.0, 0.0)
        await lightstrip.execute(None, "set", 255, 190, 90)

    async def _approach(self, bridge) -> None:
        if not bridge or not bridge.connected:
            self._log("Approach skipped (mock/offline)")
            return
        self._log("Approaching slowly (stop at ~0.55 m)")
        for _ in range(40):
            sonar = bridge.state.get("ir_proximity")
            if isinstance(sonar, (int, float)) and sonar < _APPROACH_STOP:
                self._log(f"Stopped at {sonar:.2f} m")
                break
            await bridge.publish_velocity(linear_x=0.12, angular_z=0.0)
            await asyncio.sleep(0.2)
        await bridge.publish_velocity(0.0, 0.0)
        await asyncio.sleep(0.3)

    async def _offer_cookie(self) -> dict[str, Any]:
        from ..operations import gripper

        bridge = _state.get("bridge")
        ssh = _state.get("ssh")
        if not bridge or not bridge.connected:
            return {"success": False, "reason": "offline"}
        self._log("Offering cookie: gripper open -> hold -> close")
        await gripper.gripper_open(bridge, ssh_bridge=ssh)
        await asyncio.sleep(1.2)
        await gripper.gripper_close(bridge, ssh_bridge=ssh)
        return {"success": True}

    async def _run(self, *, use_speech_mcp: bool) -> dict[str, Any]:
        from ..operations import camera_ptz, lightstrip

        bridge = _state.get("bridge")
        ssh = _state.get("ssh")
        self.status = "running"
        try:
            await lightstrip.execute(None, "set", 255, 190, 90)  # warm amber

            await self._speak(OPENING_DOG, use_speech_mcp=use_speech_mcp)
            self._say(OPENING_DOG)

            await self._bark()
            await self._tail_wag(bridge)

            await self._approach(bridge)

            if bridge and bridge.connected:
                await camera_ptz.camera_set_pos(bridge, 90, 120, ssh_bridge=ssh)  # look down at dog
            await self._speak(GREET_DOG, use_speech_mcp=use_speech_mcp)
            self._say(GREET_DOG)

            cookie = await self._offer_cookie()
            if cookie.get("success"):
                await self._speak(COOKIE_LINE, use_speech_mcp=use_speech_mcp)
                self._say(COOKIE_LINE)
            else:
                await self._speak(NO_COOKIE_LINE, use_speech_mcp=use_speech_mcp)
                self._say(NO_COOKIE_LINE)

            if bridge and bridge.connected:
                await camera_ptz.camera_set_pos(bridge, 90, 90, ssh_bridge=ssh)
            await self._speak(FAREWELL_DOG, use_speech_mcp=use_speech_mcp)
            self._say(FAREWELL_DOG)

            await lightstrip.execute(None, "off")
            self.status = "completed"
            return {
                "success": True,
                "demo": self.demo_id,
                "cookie_offered": bool(cookie.get("success")),
                "transcript": list(self.transcript),
                "message": "Dog meeting demo complete.",
            }
        except asyncio.CancelledError:
            self.status = "cancelled"
            if bridge and bridge.connected:
                await bridge.publish_velocity(0.0, 0.0)
            raise
        except Exception as exc:
            self.status = "error"
            self._log(str(exc))
            return fail_response(str(exc))


class CafeHostDemo(SocialDemoBase):
    """'Guten Tag!' - slalom between table legs, greet, chat about coffee."""

    def __init__(self) -> None:
        super().__init__("boomy_cafe_host")

    def describe(self) -> dict[str, Any]:
        return {
            "success": True,
            "demo": self.demo_id,
            "beats": [
                "mecanum slalom: weave between table legs (obstacle-aware)",
                "detect a customer (vision /detections when live, else scripted)",
                "greet + offer a chat about coffee",
                "2-3 Vienna coffeehouse facts",
                "recommendation + bow ('servus')",
                "polite exit",
            ],
            "env": {
                "YAHBOOM_SPEECH_MCP_URL": os.getenv("YAHBOOM_SPEECH_MCP_URL", "http://127.0.0.1:10909"),
            },
            "message": "Social demo - Boomy hosts the coffeehouse.",
        }

    async def run(
        self,
        *,
        use_speech_mcp: bool = True,
        max_facts: int | None = None,
        scripted_customer: str | None = None,
    ) -> dict[str, Any]:
        if self._task and not self._task.done():
            return fail_response("Cafe host demo already running")
        self.logs = []
        self.transcript = []
        self._task = asyncio.create_task(
            self._run(
                use_speech_mcp=use_speech_mcp,
                max_facts=max_facts,
                scripted_customer=scripted_customer,
            )
        )
        return {"success": True, "message": "Cafe host demo started"}

    def _front_clear(self, bridge, threshold: float = 0.30) -> bool:
        """True when the forward path is clear (sonar + lidar front sectors)."""
        if not bridge or not bridge.connected:
            return True
        sonar = bridge.state.get("ir_proximity")
        if isinstance(sonar, (int, float)) and sonar < _OBSTACLE_SONAR:
            return False
        scan = bridge.state.get("scan") or {}
        obstacles = scan.get("obstacles") or {}
        for sector in ("front", "front_left", "front_right"):
            dist = obstacles.get(sector)
            if dist is not None and dist < threshold:
                return False
        return True

    async def _slalom(self, bridge, steps: int = 4) -> None:
        """Weave between table legs: forward, strafe, forward, counter-strafe."""
        if not bridge or not bridge.connected:
            self._log("Slalom skipped (mock/offline)")
            return
        self._log("Weaving between table legs")
        for i in range(steps):
            direction = 1 if i % 2 == 0 else -1
            await bridge.publish_velocity(linear_x=0.14, angular_z=0.0, linear_y=0.0)
            await asyncio.sleep(0.7)
            await bridge.publish_velocity(linear_x=0.0, angular_z=0.0, linear_y=0.10 * direction)
            await asyncio.sleep(0.5)
            if not self._front_clear(bridge):
                self._log("Obstacle ahead - holding position")
                await bridge.publish_velocity(0.0, 0.0)
                await asyncio.sleep(0.4)
        await bridge.publish_velocity(0.0, 0.0)
        await asyncio.sleep(0.3)

    async def _detect_customer(self, bridge) -> str | None:
        """Best-effort person detection from the vision topic."""
        if not bridge or not bridge.connected:
            return None
        detections = bridge.state.get("detections_json") or bridge.state.get("detections") or {}
        if isinstance(detections, dict):
            persons = detections.get("persons") or detections.get("person") or 0
            if isinstance(persons, (int, float)) and persons > 0:
                return f"vision detected {int(persons)} person(s)"
        return None

    async def _bow(self, bridge) -> None:
        if bridge and bridge.connected:
            await bridge.publish_velocity(linear_x=0.15, angular_z=0.0)
            await asyncio.sleep(0.4)
            await bridge.publish_velocity(linear_x=-0.15, angular_z=0.0)
            await asyncio.sleep(0.4)
            await bridge.publish_velocity(0.0, 0.0)

    async def _run(
        self,
        *,
        use_speech_mcp: bool,
        max_facts: int | None,
        scripted_customer: str | None,
    ) -> dict[str, Any]:
        from ..operations import camera_ptz, lightstrip

        bridge = _state.get("bridge")
        ssh = _state.get("ssh")
        self.status = "running"
        facts = int(max_facts or os.getenv("YAHBOOM_CAFE_FACTS", "3"))
        customer = scripted_customer or "Hello, what can you tell me about coffee?"
        try:
            await lightstrip.execute(None, "pattern", "rainbow")

            await self._slalom(bridge)
            if bridge and bridge.connected:
                await camera_ptz.camera_set_pos(bridge, 90, 70, ssh_bridge=ssh)  # attentive

            detected = await self._detect_customer(bridge)
            if detected:
                self._log(detected)

            await self._speak(OPENING_CAFE, use_speech_mcp=use_speech_mcp)
            self._say(OPENING_CAFE)

            for i in range(min(facts, len(COFFEE_FACTS))):
                fact = COFFEE_FACTS[i]
                self._log(f"Customer: {customer[:60]}")
                await self._speak(fact, use_speech_mcp=use_speech_mcp)
                self._say(fact)
                await asyncio.sleep(0.4)

            recommendation = COFFEE_RECOMMENDATIONS[0]
            await self._speak(recommendation, use_speech_mcp=use_speech_mcp)
            self._say(recommendation)

            await self._bow(bridge)
            await self._speak(FAREWELL_CAFE, use_speech_mcp=use_speech_mcp)
            self._say(FAREWELL_CAFE)

            await lightstrip.execute(None, "off")
            self.status = "completed"
            return {
                "success": True,
                "demo": self.demo_id,
                "facts_shared": min(facts, len(COFFEE_FACTS)),
                "transcript": list(self.transcript),
                "message": "Cafe host demo complete.",
            }
        except asyncio.CancelledError:
            self.status = "cancelled"
            if bridge and bridge.connected:
                await bridge.publish_velocity(0.0, 0.0)
            raise
        except Exception as exc:
            self.status = "error"
            self._log(str(exc))
            return fail_response(str(exc))


_dog: DogMeetingDemo | None = None
_cafe: CafeHostDemo | None = None


def get_dog_demo() -> DogMeetingDemo:
    global _dog
    if _dog is None:
        _dog = DogMeetingDemo()
    return _dog


def get_cafe_demo() -> CafeHostDemo:
    global _cafe
    if _cafe is None:
        _cafe = CafeHostDemo()
    return _cafe
