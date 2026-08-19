# yahboom-mcp — Agent Guide

## Overview
SOTA 2026 Yahboom Raspbot v2 ROS 2 MCP Server (FastMCP 3.4 + FastAPI Unified Gateway).

## Entry Points
- `uv run yahboom-mcp` → `yahboom_mcp:main` (CLI: `--mode stdio|http|dual`, `--port 10892`)
- `start.ps1` → dual-mode gateway on 10892 (webapp 10893)

## Standards
- FastMCP 3.4+ portmanteau tool pattern — tools use an `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`--mode dual`)
- Five-gate: `ruff check` + `ruff format --check` + `pyright src/` + `pytest` + webapp `tsc`/`biome`
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards
- **Voice Command Bus:** entity `boomy` → `yahboom_agent_mission`. See `docs/VOICE_COMMAND_BUS.md`

## Key Files
- `README.md` — full documentation
- `docs/` — CONFIGURATION, DEVELOPMENT, TOOLS, TROUBLESHOOTING, ONBOARDING + ops/hardware
- `pyproject.toml` — build config and entry points
- `CLAUDE.md` — Claude Code context (if present)

Install docs: follow mcp-central-docs/standards/AGENT_INSTALL_REFERENCE.md
