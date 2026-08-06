# Dreame D20 Pro: standalone MCP server and webapp

The Dreame D20 Pro robot hoover now runs as a **standalone MCP server and webapp**
(`D:\Dev\repos\dreame-mcp`, backend **10894** / frontend **10895**) with live
status, control, and LIDAR map via the Dreame-native cloud (see
`dreame-mcp/docs/ROBO_HOOVER_SAGA.md` for the full history).

> **Migration status: COMPLETE (2026-08-06).** robotics-mcp no longer hosts the
> Dreame logic; yahboom-mcp consumes the standalone server directly.

## How yahboom-mcp uses the Dreame map

| Layer | Mechanism |
|---|---|
| **MCP tool** | `lidar(operation="read_dreame_map", source="dreame"|"auto")` → GETs `DREAME_MAP_URL` |
| **REST proxy** | `GET /api/v1/lidar/dreame-map` (used by the webapp Lidar Map page) |
| **Webapp** | Lidar Map page → `getDreameMap()` → `/api/v1/lidar/dreame-map` → floorplan PNG |
| **ROS2 / Nav2** | `ros2/boomy_dreame_map_bridge` → GETs `http://127.0.0.1:10894/api/v1/map` → publishes `nav_msgs/OccupancyGrid` on `/dreame_floorplan` |

`DREAME_MAP_URL` defaults to `http://127.0.0.1:10894/api/v1/map` (the standalone
server) — no config needed when both servers run on the same host.

## Original rationale (kept for history)

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

## ROS 2 on the Pi (Nav2 / Raspbot)

For **Nav2** (not just the MCP HTTP `DREAME_MAP_URL` panel), use the sibling package **`ros2/boomy_dreame_map_bridge`**: it subscribes to nothing; it **GET**s `http://<dreame-mcp-host>:10894/api/v1/map` and publishes `nav_msgs/OccupancyGrid` for a static layer. See that package’s **README.md**. The Raspbot’s own **MS200** `/scan` remains the local obstacle source when you add it; the Dreame floor plan is a separate, manually aligned layer.
