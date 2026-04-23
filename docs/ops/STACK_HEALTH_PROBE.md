# Stack health probe (`/api/v1/health` → `stack`)

**MCP Central Docs (RAG):** full searchable copy with API field tables and layer ids: `mcp-central-docs/docs/robotics/yahboom/STACK_HEALTH_PROBE.md`. This repo file stays aligned for PRs beside **`stack_probe.py`**.

The MCP server builds a **layered snapshot** of how Goliath reaches the robot (TCP, SSH, Pi network, Docker, ROS container, ROS graph inside Docker, rosbridge from the PC, video). Operators see it on the **Dashboard** and **Diagnostic Hub** via the shared **`StackStatusTable`** component.

**Implementation:** `src/yahboom_mcp/stack_probe.py` (cached probes, SSH + TCP). **`GET /api/v1/health`** includes a **`stack`** object when the server can assemble it (same payload shape the webapp types as `StackOverview` in `webapp/src/lib/api.ts`).

---

## Cache TTL

Repeated health polls reuse cached SSH-heavy work for a short window:

| Variable | Default | Meaning |
|----------|---------|--------|
| **`YAHBOOM_STACK_PROBE_SECS`** | `5` | Minimum seconds between full stack recomputes (per server process). |

Lower values increase Pi SSH load; higher values make the UI lag slightly after you fix something on the robot.

---

## ROS container name

Probes and driver checks target the container named by:

| Variable | Default | Meaning |
|----------|---------|--------|
| **`YAHBOOM_ROS2_CONTAINER`** | `yahboom_ros2_final` | Name passed to `docker inspect`, `docker logs`, and `docker exec … ros2 node list`. Must match **`docker ps`** on the Pi. If your compose uses **`yahboom_ros2`**, set the env var on **Goliath** (where `yahboom-mcp` runs) to that exact name. |

When another **`yahboom*`** container is **Up** but the configured name is missing or exited, the stack snapshot may set **`alternate_running_container`** and remediation text suggesting **`YAHBOOM_ROS2_CONTAINER`**.

---

## Lifecycle (`ros_container.lifecycle`)

Derived from Docker **`inspect`** `State` (running flag, status string, started/finished timestamps, exit code, OOM):

- **`running`** — process up at probe time.
- **`never_started`** — typically **`created`**, no meaningful start time yet.
- **`ran_then_stopped`** — exited or dead, or timestamps show a completed run.
- **`restart_loop`** — status contains **`restarting`** (Docker crash loop).
- Other phases include **`no_ssh`**, **`not_found`**, **`paused`**, **`removing`**, **`unknown`**, **`unavailable`**.

The webapp shows a **Run history** block and, for restart loops, an **amber banner** and a highlighted stack table row with a **Loop** badge instead of a generic **FAIL**.

---

## Docker log preview (unhealthy container only)

When SSH is connected and the container is **not** in a steady **running** state **without** a restart loop, the server runs **`docker logs <container> --tail N`** on the Pi and returns a redacted string in **`ros_container.docker_logs_preview`**. This avoids asking the operator to SSH manually for the first pass at an error.

| Variable | Default | Clamp | Meaning |
|----------|---------|-------|--------|
| **`YAHBOOM_DOCKER_LOGS_TAIL`** | `80` | 10–200 | Lines requested from Docker. |
| **`YAHBOOM_DOCKER_LOGS_MAX_CHARS`** | `16000` | 2000–64000 | Max characters after redaction (truncation suffix added if cut). |

**Not fetched** when: container **`not_found`**, or **`running`** is true and **`restart_loop`** is false (healthy steady state).

**Redaction (best effort):** common `password=` / `token=` / `api_key` style pairs, `Authorization: Bearer …`, simple AWS-style key patterns, and PEM **private key** lines are masked or replaced. Each line is capped before the global character cap. **Do not** treat the preview as a security boundary for highly sensitive logs; restrict who can open **`/api/v1/health`** on your network.

If the remote command fails, **`docker_logs_error`** holds a short reason; **`docker_logs_truncated`** is true when the preview was cut for size.

---

## Agent mission planner (`POST /api/v1/agent/mission`)

Natural-language goals (e.g. “find Benny”) become structured JSON via **Ollama** (settings model) or **Gemini** (`YAHBOOM_GEMINI_API_KEY`, `YAHBOOM_GEMINI_MISSION_MODEL`). Invoke from the dashboard with **`POST /api/v1/agent/mission`** or from an MCP IDE with tool **`yahboom_agent_mission`**. Optional publish to **`std_msgs/String`** on **`YAHBOOM_MISSION_TOPIC`** (default **`/boomy/mission`**). **Pi-side:** **`ros2/boomy_mission_executor`**. Operator reference: **`AGENT_MISSION_AND_MCP.md`**; bringup table: **`STARTUP_AND_BRINGUP.md`** §4; planner code: **`src/yahboom_mcp/agent_mission.py`**.

---

## Related

- **[STARTUP_AND_BRINGUP.md](STARTUP_AND_BRINGUP.md)** — Boot order, **`YAHBOOM_ROS2_CONTAINER`** vs factory scripts, dashboard vs diagnostics.
- **MCP Central Docs (full-text RAG):** `mcp-central-docs/docs/robotics/yahboom/STACK_HEALTH_PROBE.md` (API tables, **`layers[].id`**, synonym line).
- **`docs/ops/TESTING.md`** — Manual test notes if present for your branch.
