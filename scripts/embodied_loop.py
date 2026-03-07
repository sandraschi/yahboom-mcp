#!/usr/bin/env python3
"""
Embodied AI control loop: observe (telemetry + optional image) -> LLM -> act.

Uses yahboom-mcp REST API for observation and control, and Ollama for the
"brain". Run with the server in dual mode (e.g. start.ps1) and a vision-capable
model (e.g. llava) if using --use-vision.

Usage:
  python scripts/embodied_loop.py [--instruction "go forward"] [--max-steps 60] [--use-vision]
  YAHBOOM_BASE_URL=http://localhost:10792 OLLAMA_BASE_URL=http://127.0.0.1:11434
"""

import argparse
import asyncio
import base64
import json
import logging
import os
import re
import sys

try:
    import httpx
except ImportError:
    print("Requires httpx: pip install httpx")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("embodied_loop")

BASE_URL = os.environ.get("YAHBOOM_BASE_URL", "http://localhost:10792").rstrip("/")
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")

ACTIONS = [
    "FORWARD",
    "BACK",
    "TURN_LEFT",
    "TURN_RIGHT",
    "STRAFE_LEFT",
    "STRAFE_RIGHT",
    "STOP",
]

ACTION_TO_CMD = {
    "FORWARD": {"linear": 0.2, "angular": 0.0, "linear_y": 0.0},
    "BACK": {"linear": -0.2, "angular": 0.0, "linear_y": 0.0},
    "TURN_LEFT": {"linear": 0.0, "angular": 0.5, "linear_y": 0.0},
    "TURN_RIGHT": {"linear": 0.0, "angular": -0.5, "linear_y": 0.0},
    "STRAFE_LEFT": {"linear": 0.0, "angular": 0.0, "linear_y": 0.2},
    "STRAFE_RIGHT": {"linear": 0.0, "angular": 0.0, "linear_y": -0.2},
    "STOP": {"linear": 0.0, "angular": 0.0, "linear_y": 0.0},
}

SYSTEM_PROMPT = """You control a mobile robot. Reply with exactly one action per turn from this list: FORWARD, BACK, TURN_LEFT, TURN_RIGHT, STRAFE_LEFT, STRAFE_RIGHT, STOP.
Output only the action word, nothing else. If unsure or no clear move, say STOP."""


def build_observation_text(telemetry: dict) -> str:
    """Summarize telemetry for the LLM."""
    battery = telemetry.get("battery")
    pos = telemetry.get("position") or {}
    vel = telemetry.get("velocity") or {}
    imu = (telemetry.get("imu") or {}).get("heading")
    scan = (telemetry.get("scan") or {}).get("obstacles") or {}
    nearest = (telemetry.get("scan") or {}).get("nearest_m")

    parts = [
        f"Battery: {battery}%",
        f"Position: x={pos.get('x', 0):.2f} y={pos.get('y', 0):.2f}",
        f"Velocity: linear={vel.get('linear', 0):.2f} angular={vel.get('angular', 0):.2f}",
        f"Heading: {imu} deg",
    ]
    if nearest is not None:
        parts.append(f"Nearest obstacle: {nearest:.2f} m")
    else:
        parts.append("Obstacles: front=%s left=%s right=%s" % (
            scan.get("front"), scan.get("left"), scan.get("right"),
        ))
    return "\n".join(parts)


def parse_action(reply: str) -> str:
    """Extract one action from LLM reply."""
    reply_upper = reply.strip().upper()
    for a in ACTIONS:
        if a in reply_upper or a.replace("_", " ") in reply_upper:
            return a
    if not reply.strip():
        return "STOP"
    return "STOP"


async def get_telemetry(client: httpx.AsyncClient) -> dict | None:
    """Fetch telemetry from yahboom-mcp."""
    try:
        r = await client.get(f"{BASE_URL}/api/v1/telemetry", timeout=5.0)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logger.warning("Telemetry request failed: %s", e)
    return None


async def get_snapshot(client: httpx.AsyncClient) -> bytes | None:
    """Fetch single JPEG frame (for vision). Returns None if no frame."""
    try:
        r = await client.get(f"{BASE_URL}/api/v1/snapshot", timeout=3.0)
        if r.status_code == 200 and r.content:
            return r.content
    except Exception as e:
        logger.debug("Snapshot request failed: %s", e)
    return None


async def ollama_chat(
    client: httpx.AsyncClient,
    model: str,
    user_content: str,
    image_b64: str | None = None,
) -> str:
    """Call Ollama /api/chat. If image_b64, use vision message format."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if image_b64:
        messages.append({
            "role": "user",
            "content": user_content,
            "images": [image_b64],
        })
    else:
        messages.append({"role": "user", "content": user_content})

    payload = {"model": model, "messages": messages, "stream": False}
    try:
        r = await client.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=30.0)
        if r.status_code != 200:
            logger.warning("Ollama returned %s: %s", r.status_code, r.text[:200])
            return "STOP"
        data = r.json()
        msg = data.get("message", {})
        return (msg.get("content") or "").strip()
    except Exception as e:
        logger.warning("Ollama request failed: %s", e)
        return "STOP"


async def send_move(client: httpx.AsyncClient, linear: float, angular: float, linear_y: float = 0.0) -> bool:
    """Send velocity command to yahboom-mcp."""
    try:
        r = await client.post(
            f"{BASE_URL}/api/v1/control/move",
            params={"linear": linear, "angular": angular, "linear_y": linear_y},
            timeout=3.0,
        )
        if r.status_code == 200:
            return (r.json() or {}).get("status") == "success"
    except Exception as e:
        logger.warning("Move request failed: %s", e)
    return False


async def run_loop(
    model: str,
    instruction: str | None,
    max_steps: int,
    interval: float,
    use_vision: bool,
) -> None:
    """Main observe -> LLM -> act loop."""
    async with httpx.AsyncClient() as client:
        for step in range(max_steps):
            telemetry = await get_telemetry(client)
            if not telemetry:
                logger.warning("Step %s: no telemetry, skipping", step + 1)
                await asyncio.sleep(interval)
                continue

            obs_text = build_observation_text(telemetry)
            user_content = obs_text
            if instruction:
                user_content = f"Instruction: {instruction}\n\nCurrent state:\n{obs_text}\n\nWhat action?"

            image_b64 = None
            if use_vision:
                jpeg = await get_snapshot(client)
                if jpeg:
                    image_b64 = base64.b64encode(jpeg).decode("ascii")
                    user_content = (user_content or "What action?") + "\n\n(Refer to the image from the robot's camera.)"

            reply = await ollama_chat(client, model, user_content, image_b64)
            action = parse_action(reply)
            cmd = ACTION_TO_CMD.get(action, ACTION_TO_CMD["STOP"])

            logger.info("Step %s: action=%s (raw: %s)", step + 1, action, reply[:50] if reply else "")
            await send_move(
                client,
                cmd["linear"],
                cmd["angular"],
                cmd["linear_y"],
            )
            await asyncio.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Embodied AI loop: observe -> LLM -> act")
    parser.add_argument("--model", default=os.environ.get("OLLAMA_MODEL", "llava"), help="Ollama model (vision: llava)")
    parser.add_argument("--instruction", default=None, help="Optional high-level instruction (e.g. 'go forward')")
    parser.add_argument("--max-steps", type=int, default=60, help="Max control steps")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between steps")
    parser.add_argument("--use-vision", action="store_true", help="Use camera snapshot (requires vision model)")
    args = parser.parse_args()

    logger.info("Base URL: %s | Ollama: %s | model: %s", BASE_URL, OLLAMA_URL, args.model)
    asyncio.run(run_loop(args.model, args.instruction, args.max_steps, args.interval, args.use_vision))


if __name__ == "__main__":
    main()
