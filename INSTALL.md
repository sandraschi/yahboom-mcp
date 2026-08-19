# Installation

## Option A — Drag and Drop (Recommended, Claude Desktop)

Download `yahboom-mcp-v2.5.0b1.mcpb` from GitHub Releases and drag it into
Claude Desktop. No Python, uv, git, or Node required. The bundle ships the
server, prompts, and config; point `YAHBOOM_IP` at your robot via the server's
`env` block afterward (see `docs/CONFIGURATION.md`).

> **Why not `pip install`?** MCP servers bundle webapps, configs, project scaffolding, and tooling that a flat Python package can't deliver. PyPI offers no safety advantage — it doesn't audit packages either. `just` gives you the complete, ready-to-run stack.

## Option B — mcpb CLI

Requires Node.js (`winget install OpenJS.NodeJS`). From the repo:

```powershell
npx --yes @anthropic-ai/mcpb pack . dist/yahboom-mcp-v2.5.0b1.mcpb
```

> Never `uvx mcpb` — mcpb is an npm package, not on PyPI.

## Option C — Manual Configuration

1. Install [Python 3.12+](https://python.org) and [uv](https://docs.astral.sh/uv/)
   (`winget install astral-sh.uv`).
2. Clone and enter the repo:
   ```powershell
   git clone https://github.com/sandraschi/yahboom-mcp
   cd yahboom-mcp
   ```
3. Install dependencies:
   ```powershell
   uv sync --extra dev
   ```
4. Start the server:
   ```powershell
   # stdio mode (for MCP clients like Claude Desktop)
   uv run python -m yahboom_mcp.server

   # dual mode (REST + MCP SSE, web dashboard)
   uv run python -m yahboom_mcp.server --mode dual --port 10892
   ```
5. (optional) Start the frontend:
   ```powershell
   cd webapp
   npm install
   npm run dev
   ```
6. Open `http://localhost:10892` or the frontend URL on `10893`.

## Option D — Developer Mode

See `docs/DEVELOPMENT.md`: `just`, ruff, pyright, pytest, Tauri `just build-native`,
and `just mcpb-pack`.

---

## LLM setup (chat + agent missions)

The webapp Chat and mission planner need an LLM. Two tiers:

- **Tier A — Local (recommended)**: [Ollama](https://ollama.com)
  (`winget install Ollama.Ollama`) on the robot or host, or LM Studio (`:1234`).
  The Settings page auto-detects both. Pick a model, e.g. `ollama pull gemma3:1b`.
- **Tier B — Cloud**: set `OLLAMA_BASE_URL` to an OpenAI-compatible endpoint, or
  add `YAHBOOM_GEMINI_API_KEY` for Gemini mission planning. Configure via
  `docs/CONFIGURATION.md`.

Models are never bundled — pull/configure them yourself.

## Claude Desktop config (Option C)

Add the server to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "yahboom-mcp": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\yahboom-mcp", "run", "yahboom-mcp"],
      "env": { "YAHBOOM_IP": "192.168.1.11", "PYTHONUNBUFFERED": "1" }
    }
  }
}
```

---

## ❓ Troubleshooting

| Issue | Fix |
|---|---|
| `just` not found | Install via `winget install Casey.Just`, `scoop install just`, or `brew install just` |
| Port 10892 in use | `start.ps1` clears it; or `netstat -ano | findstr 10892` + `taskkill /F /PID <pid>` |
| Dependencies out of sync | `uv sync --extra dev` |
| Something else | [Open a GitHub issue](https://github.com/sandraschi/yahboom-mcp/issues) |

---

*See the main [README](README.md) for feature overview and documentation.*
