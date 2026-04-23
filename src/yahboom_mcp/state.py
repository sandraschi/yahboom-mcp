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
