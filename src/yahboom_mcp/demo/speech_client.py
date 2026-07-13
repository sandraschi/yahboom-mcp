"""HTTP client for speech-mcp (FunASR STT + TTS on the workstation)."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .. import fail_response


class SpeechMcpClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("YAHBOOM_SPEECH_MCP_URL") or "http://127.0.0.1:10909").rstrip("/")

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                r = await client.get(f"{self.base_url}/api/v1/health")
                if r.status_code == 200:
                    return {"success": True, "reachable": True, "url": self.base_url, "body": r.json()}
            except httpx.HTTPError as exc:
                return fail_response(str(exc), reachable=False, url=self.base_url)
        return fail_response("Speech MCP unreachable", reachable=False, url=self.base_url)

    async def speak(self, text: str, *, voice_id: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"text": text}
        if voice_id:
            payload["voice_id"] = voice_id
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                r = await client.post(f"{self.base_url}/api/v1/tts", json=payload)
                r.raise_for_status()
                return {"success": True, "message": "TTS dispatched via speech-mcp", "response": r.json()}
            except httpx.HTTPError as exc:
                return fail_response(str(exc), url=self.base_url)

    async def transcribe_file(self, file_path: str, *, language: str | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                with open(file_path, "rb") as fh:
                    files = {"file": (os.path.basename(file_path), fh, "audio/wav")}
                    data = {}
                    if language:
                        data["language"] = language
                    r = await client.post(f"{self.base_url}/api/v1/transcribe", files=files, data=data)
                r.raise_for_status()
                body = r.json()
                text = body.get("text") or body.get("transcript") or ""
                return {"success": True, "text": text, "raw": body}
            except httpx.HTTPError as exc:
                return fail_response(str(exc))
