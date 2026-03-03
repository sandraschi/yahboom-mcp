"""Yahboom MCP Shared State."""

from typing import Dict, Any, Optional

# Global state for resource sharing between lifespan and tools/routes
_state: Dict[str, Any] = {
    "bridge": None,
    "video_bridge": None,
    "trajectory_manager": None,
}
