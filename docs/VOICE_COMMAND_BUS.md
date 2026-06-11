# Voice Command Bus (Boomy / yahboom-mcp)

Canonical standard: **`D:\Dev\repos\mcp-central-docs\standards\VOICE_COMMAND_BUS.md`**

## Spoken example

> **wakeywakey** — *"boomy go on patrol and report what you found"*

| Step | Component |
|------|-----------|
| speech-mcp | Wake + STT |
| fleet-agent | Entity `boomy` → server `yahboom` |
| yahboom-mcp | `yahboom_agent_mission(goal=…, speak=true, publish_to_ros=true)` |

Mission executor on the Pi subscribes `/boomy/mission`; vision on `/boomy/detections_json`.

## MCP tools used by router

- **`yahboom_agent_mission`** — natural-language goals (patrol, find, report, room search)
- **`yahboom_patrol`** — simple patrol enable (keyword: move, forward, stop)

## Prerequisites

- speech-mcp + fleet-agent backends running (NSSM or `start.ps1 -Headless -BackendOnly`)
- yahboom-mcp reachable at `http://127.0.0.1:10892/mcp`
- Pi / Docker stack up for ROS missions when `publish_to_ros=true`
