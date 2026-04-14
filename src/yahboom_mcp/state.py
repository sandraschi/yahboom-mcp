"""Yahboom MCP Shared State."""

from typing import Any

# Global state for resource sharing between lifespan and tools/routes
_state: dict[str, Any] = {
    "bridge": None,
    "video_bridge": None,
    "trajectory_manager": None,
    "ssh_bridge": None,
}
