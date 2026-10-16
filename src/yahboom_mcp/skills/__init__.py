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


_skill_preprompt_cache: str | None = None


def skill_preprompt() -> str:
    """Combined skill text for skill-first chat system prompts.

    Calls the registered skill functions (plain ``() -> str``) and joins
    them under one header. Cached after first build; skills are static text.
    """
    global _skill_preprompt_cache
    if _skill_preprompt_cache is None:
        parts = [
            ("quick-pilot", yahboom_quick_pilot()),
            ("patrol-sweep", yahboom_patrol_sweep()),
            ("emergency-halt", yahboom_emergency_halt()),
            ("diagnostic-triage", yahboom_diagnostic_triage()),
        ]
        _skill_preprompt_cache = "\n\n".join(f"### Skill: {name}\n{text}" for name, text in parts)
    return _skill_preprompt_cache


__all__ = ["register_skills", "skill_preprompt"]
