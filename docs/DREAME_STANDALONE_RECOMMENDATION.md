# Dreame D20 Pro: standalone MCP server and webapp

The Dreame D20 Pro robot hoover is currently integrated inside **robotics-mcp** (federated fleet). This note summarizes the recommendation for giving it its own repo and stack.

## Recommendation: yes, give it its own MCP server and webapp

**Suggested repo:** `D:\Dev\repos\dreame-mcp` (or `d:/dev/repos/dreame-mcp`).

### Why split

| Reason | Detail |
|--------|--------|
| **Focus** | One codebase = one product (Dreame D20 Pro). Easier to maintain, release, and document. |
| **Audience** | People who only care about the hoover don’t need to pull the rest of robotics-mcp. |
| **Port / deploy** | Dedicated port and webapp; no conflict with Yahboom, Gazebo, or other robotics-mcp clients. |
| **Fleet** | robotics-mcp can remain the “hub” that orchestrates multiple MCPs (Yahboom, Dreame, etc.) and optionally calls dreame-mcp or uses its map/LIDAR via URL (e.g. DREAME_MAP_URL). |

### What to put in dreame-mcp

- **MCP server**: Dreame-specific tools (map, status, start/stop, etc.) and prompts.
- **Webapp**: Dashboard for map, cleaning runs, battery, and controls (same stack as other SOTA webapps: React + Tailwind, port in 10700–10800).
- **API**: REST for map/status so yahboom-mcp (and others) can keep using `DREAME_MAP_URL` to pull the Dreame map into the Lidar Map page.

### Migration path

1. Create `dreame-mcp` repo; move Dreame-specific code and config from robotics-mcp into it.
2. Expose map/status endpoints in dreame-mcp; point `DREAME_MAP_URL` from yahboom-mcp (or robotics-mcp) to the new server.
3. robotics-mcp: remove or thin Dreame-specific logic; keep fleet orchestration and optional “proxy” to dreame-mcp if needed.

No change required to yahboom-mcp except ensuring `DREAME_MAP_URL` points to wherever the Dreame map is served (today: robotics-mcp; later: dreame-mcp).
