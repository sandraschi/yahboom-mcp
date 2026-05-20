"""Yahboom MCP Skills — Fleet-standard robot operation guides (FastMCP 3.2)."""

from fastmcp import FastMCP

from .diagnostic_triage import yahboom_diagnostic_triage
from .emergency_halt import yahboom_emergency_halt
from .patrol_sweep import yahboom_patrol_sweep
from .quick_pilot import yahboom_quick_pilot


def register_skills(app: FastMCP) -> None:
    """Register all yahboom fleet skills as FastMCP 3.2 prompt-based skills."""
    app.prompt()(yahboom_quick_pilot)
    app.prompt()(yahboom_patrol_sweep)
    app.prompt()(yahboom_emergency_halt)
    app.prompt()(yahboom_diagnostic_triage)


__all__ = ["register_skills"]
