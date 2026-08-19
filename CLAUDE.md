# yahboom-mcp — Claude Code Guide

## Overview
SOTA 2026 Yahboom Raspbot v2 ROS 2 MCP Server (FastMCP 3.4 + FastAPI Unified Gateway).

## Entry Points
- `uv run yahboom-mcp` → `yahboom_mcp:main` (CLI: `--mode stdio|http|dual`, `--port 10892`)
- `start.ps1` → dual-mode gateway on 10892 (webapp 10893)
- `just serve` / `just test` / `just lint` / `just fix`

## Standards
- FastMCP 3.4 portmanteau tool pattern — tools use an `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`--mode dual`)
- Five-gate: `ruff check` + `ruff format --check` + `pyright src/` + `pytest` + webapp `tsc`/`biome`
- Session-context injection lives in `.claude-plugin/` and `.cursorrules`
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files
- `README.md` — full documentation
- `docs/` — CONFIGURATION, DEVELOPMENT, TOOLS, TROUBLESHOOTING, ONBOARDING + ops/hardware
- `pyproject.toml` — build config, entry points, ruff/pyright/coverage gates
- `src/yahboom_mcp/server.py` — Unified Gateway, REST routes, MCP tools, `main()`
- `src/yahboom_mcp/portmanteau.py` — `yahboom_tool` dispatch
- `native/` — Tauri 2 NSIS desktop shell (embedded backend)
- `AGENTS.md` — OpenAI Codex agent context (if present)
