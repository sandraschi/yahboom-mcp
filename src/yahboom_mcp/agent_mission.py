"""
LLM-backed mission planner: natural-language goals → structured JSON for ROS / voice.

Supports Ollama (local) and Google Gemini API (optional `YAHBOOM_GEMINI_API_KEY`).
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("yahboom-mcp.agent-mission")

MISSION_JSON_SYSTEM = (
    "You are Boomy's mission planner for a Yahboom Raspbot v2 "
    "(ROS 2 Humble, mecanum holonomic base, USB cameras, optional LIDAR).\n\n"
    "Reply with ONLY one JSON object (no markdown code fences, no commentary). Schema:\n"
    "{\n"
    '  "version": 1,\n'
    '  "intent": "search" | "navigate" | "speak" | "inspect" | "other",\n'
    '  "target_description": "string — what to find or do '
    '(e.g. German Shepherd dog named Benny)",\n'
    '  "behavior": "room_search" | "spin_scan" | "go_to_waypoint" | "idle",\n'
    '  "nav2_goal": null | {\n'
    '    "frame_id": "map",\n'
    '    "x": number,\n'
    '    "y": number,\n'
    '    "yaw_deg": number,\n'
    '    "behavior_tree": "optional string — Nav2 BT XML path if non-default"\n'
    "  },\n"
    '  "suggested_ros_topics": ["optional strings, e.g. /image_raw/compressed"],\n'
    '  "voice_feedback": "short phrase the robot may speak to the operator",\n'
    '  "safety_notes": "string",\n'
    '  "estimated_duration_sec": number\n'
    "}\n\n"
    'Use intent "search" and behavior "room_search" when the user asks to find a '
    "person or animal in the space.\n"
    "When the operator gives explicit map coordinates or a named waypoint that maps "
    'to pose, use behavior "go_to_waypoint" and fill "nav2_goal" '
    '(frame_id usually "map"; yaw_deg is degrees in the map frame).\n'
    "Prefer conservative motion; mention in safety_notes if Nav2 or a map is "
    "assumed unavailable."
)


class MissionPlanV1(BaseModel):
    version: int = 1
    intent: str = "other"
    target_description: str = ""
    behavior: str = "idle"
    nav2_goal: dict[str, Any] | None = None
    suggested_ros_topics: list[str] = Field(default_factory=list)
    voice_feedback: str = ""
    safety_notes: str = ""
    estimated_duration_sec: float = 60.0

    @field_validator("nav2_goal", mode="before")
    @classmethod
    def _nav2_goal(cls, v: Any) -> dict[str, Any] | None:
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        return None

    @field_validator("intent", mode="before")
    @classmethod
    def _intent(cls, v: Any) -> str:
        s = str(v or "").strip().lower()
        return s if s else "other"

    @field_validator("behavior", mode="before")
    @classmethod
    def _behavior(cls, v: Any) -> str:
        s = str(v or "").strip().lower()
        return s if s else "idle"


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse first JSON object from model output (strips optional ```json fences)."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty model output")
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", raw, re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in model output")
    blob = raw[start : end + 1]
    return json.loads(blob)


async def _ollama_plan(
    goal: str,
    model: str,
    post_chat: Callable[[dict], Awaitable[dict | None]],
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": MISSION_JSON_SYSTEM},
            {"role": "user", "content": goal.strip()},
        ],
        "stream": False,
        "options": {"temperature": 0.2},
    }
    data = await post_chat(payload)
    if not data:
        raise RuntimeError("Ollama request failed or returned empty")
    msg = data.get("message") or {}
    content = (msg.get("content") or "").strip()
    return extract_json_object(content)


async def _gemini_plan(goal: str, api_key: str, model: str) -> dict[str, Any]:
    """Gemini generateContent with JSON MIME type (structured output)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    combined = MISSION_JSON_SYSTEM + "\n\nOperator goal:\n" + goal.strip()
    body: dict[str, Any] = {
        "contents": [{"parts": [{"text": combined}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                url,
                params={"key": api_key},
                json=body,
            )
    except Exception as e:
        logger.warning("Gemini mission request failed: %s", e)
        raise RuntimeError(f"Gemini HTTP error: {e}") from e
    if r.status_code != 200:
        logger.warning("Gemini mission non-200: %s %s", r.status_code, r.text[:500])
        raise RuntimeError(f"Gemini API status {r.status_code}")
    data = r.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    if not parts:
        raise RuntimeError("Gemini returned no parts")
    text = (parts[0].get("text") or "").strip()
    if not text:
        raise RuntimeError("Gemini returned empty text")
    return extract_json_object(text)


async def plan_mission(
    goal: str,
    *,
    provider: str,
    ollama_model: str,
    ollama_post_chat: Callable[[dict], Awaitable[dict | None]],
    gemini_api_key: str | None,
    gemini_model: str,
) -> tuple[dict[str, Any], str]:
    """
    Returns (normalized_plan_dict, provider_used).
    Raises RuntimeError on total failure.
    """
    prov = (provider or "auto").strip().lower()
    if prov == "auto":
        if (gemini_api_key or "").strip():
            prov = "gemini"
        else:
            prov = "ollama"

    raw: dict[str, Any]
    used = prov
    if prov == "gemini":
        key = (gemini_api_key or "").strip()
        if not key:
            raise RuntimeError("Gemini selected but YAHBOOM_GEMINI_API_KEY is not set")
        raw = await _gemini_plan(goal, key, gemini_model)
    else:
        model = (ollama_model or "").strip()
        if not model:
            raise RuntimeError("No Ollama model configured (Settings → LLM model)")
        raw = await _ollama_plan(goal, model, ollama_post_chat)

    validated = MissionPlanV1.model_validate(raw)
    return validated.model_dump(), used
