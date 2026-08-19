"""Yahboom MCP Shared State."""

from typing import Any

# Global state for resource sharing between lifespan and tools/routes
_state: dict[str, Any] = {
    "bridge": None,
    "video_bridge": None,
    "trajectory_manager": None,
    "ssh": None,  # SSHBridge instance (primary key used everywhere)
    "ssh_bridge": None,  # alias kept for any legacy references
    "sequencer": None,
    "resync_all_components": None,
}


def ctx_request_id(ctx: Any) -> str:
    """Best-effort request id from a FastMCP Context.

    FastMCP 3.4 Context exposes ``request_id`` (not ``correlation_id``).
    Returned dicts keep the ``correlation_id`` key for back-compat.
    """
    return getattr(ctx, "request_id", None) or "manual-execution"
