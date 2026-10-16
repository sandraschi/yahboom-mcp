"""JSON Schemas for MCP ``output_schema`` — dialogic returns (success + message + data)."""

from __future__ import annotations

# Every yahboom MCP tool returns {"success": bool, "message": str, ...}.
# additionalProperties stays True: per-tool payload keys vary by path.
DIALOGIC_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["success"],
    "properties": {
        "success": {"type": "boolean"},
        "message": {"type": "string"},
        "error": {"type": "string"},
        "correlation_id": {"type": "string"},
    },
    "additionalProperties": True,
}

PORTMANTEAU_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["success"],
    "properties": {
        "success": {"type": "boolean"},
        "message": {"type": "string"},
        "error": {"type": "string"},
        "operation": {"type": "string"},
        "result": {"type": "object"},
        "correlation_id": {"type": "string"},
    },
    "additionalProperties": True,
}

MISSION_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["success"],
    "properties": {
        "success": {"type": "boolean"},
        "message": {"type": "string"},
        "error": {"type": "string"},
        "provider": {"type": "string"},
        "plan": {"type": "object"},
        "published_to_ros": {"type": "boolean"},
        "mission_topic": {"type": "string"},
        "publish_error": {"type": ["string", "null"]},
        "spoke": {"type": "boolean"},
    },
    "additionalProperties": True,
}

LOGS_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["success"],
    "properties": {
        "success": {"type": "boolean"},
        "message": {"type": "string"},
        "logs": {"type": "array"},
        "count": {"type": "integer"},
        "total_matching": {"type": "integer"},
    },
    "additionalProperties": True,
}

TOPICS_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["success"],
    "properties": {
        "success": {"type": "boolean"},
        "message": {"type": "string"},
        "topics": {"type": "array"},
        "count": {"type": "integer"},
    },
    "additionalProperties": True,
}
