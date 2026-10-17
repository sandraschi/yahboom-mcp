# PRD — yahboom-mcp (Yahboom Raspbot v2 "Boomy" control plane)

**Version:** 2.5.0 · **Status:** stable release, production-capable with hardware ·
**Ports:** backend 10892, frontend 10893 · **Owners:** sandraschi

## 1. Problem

The Yahboom Raspbot v2 is a capable ~$300 mecanum robot, but operating it
means juggling SSH terminals, `ros2` CLI incantations, Docker on the Pi, and a
patchwork of vendor scripts. Non-roboticists (and AI agents) cannot drive,
sense, or diagnose it without tribal knowledge. yahboom-mcp collapses all of
that into one MCP server plus one dashboard.

## 2. Users

- **Agent operators** (Claude/Cursor/OpenCode): drive, sense, and run missions
  from chat via 14 MCP tools, 9 prompts, and 4 skill texts.
- **Human operators** (dashboard): manual driving, telemetry, peripherals,
  diagnostics, and skill-first chat across 27 routes.
- **Show operators**: talkbot + chalk demos for visitors and kids.

## 3. Requirements (shipped, v2.5.0)

- R1. Drive + sense over rosbridge/ESP32/mock links with health-first safety
  (battery gates, stop-after-move, LIDAR-gated motion).
- R2. Full peripheral surface: camera PTZ, OLED, lightstrip, buzzer, USB voice
  module, Tapo two-way audio, GPIO, trajectories, gripper (if fitted).
- R3. LLM missions: NL goal → validated MissionPlanV1 → ROS publish + speech
  (Ollama/Gemini); agentic multi-step workflows via MCP sampling.
- R4. Diagnostics ladder: inspect_stack → resync → SSH sandbox → bringup
  restart; SSE logs; ring-buffer query; smoke-test endpoint.
- R5. Dashboard parity: every MCP capability reachable manually; onboarding
  bring-up flow; skill-first chat with 4 personalities.
- R6. Distribution: MCPB bundle (Claude one-liner + uvx config), Tauri/NSIS
  desktop installer with AI-client registration, CI five-gate green.

## 4. Non-goals

No autonomous outdoor navigation, no multi-robot choreography server-side (one
instance per robot; coordination lives in the MCP client), no server-side map
export yet, no PyPI distribution (MCPB + source only).

## 5. Acceptance (assfix-verified 2026-10-16)

- `health_check` green on mock bridge with zero hardware attached.
- Square patrol (agentic) completes: 4 legs, final stop, battery report.
- Abort path: missions/stop + stop_all halts motion < 0.5 s (monthly drill).
- Gates: ruff, format, pyright 0/0/0, pytest 100 passed, tsc, biome clean.
- Pack: `mcpb/pack.ps1` builds 162 KB bundle; entry point launches from clean
  unpack; audit shows no NONSPEC/SIDECAR/POLLUTION.
- Fresh-clone onboarding: README one-liner (Claude) / uvx snippet (others) /
  INSTALL manual path all resolve; dashboard onboarding cue when offline.

## 6. Roadmap (most-asked)

Server-side map/trajectory export, v2.5.0 stable release (flips the
releases/latest one-liner live), Dreame co-mapping UI polish, kid-safe speed
profiles, Pi image upgrade guide automation.
