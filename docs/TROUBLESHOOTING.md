# Troubleshooting

## Robot not reachable / backend shows "offline"

1. Verify the robot is powered and on the same LAN:
   `ping <YAHBOOM_IP>` (default `192.168.1.11`).
2. Confirm `rosbridge_server` is running on the Pi:
   `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`.
3. Check the bridge port: `YAHBOOM_BRIDGE_PORT` (default `9090`). The Raspbot
   hotspot variant uses port `6000`.
4. `GET /api/v1/health` returns `robot_connection` per-service state; the `hint`
   field explains the most likely cause.

## Port 10892 already in use

```powershell
netstat -ano | findstr 10892
taskkill /F /PID <pid>
```

`start.ps1` clears the port before binding. If a second instance is running via
NSSM, stop the service instead (`sc.exe stop <svc>`) - never kill the child.

## Blank dashboard / white screen

- Ensure the backend is up: `curl http://localhost:10892/api/v1/health`.
- Open the browser console: a `TypeError` usually means the backend port changed
  while the frontend still points at the old one (see `webapp/src/lib/api.ts`).
- Restart both: `start.ps1` then `webapp/start.ps1`.

## Telemetry missing while wheels work

Run `ros_resync` (topic map stale) or tap **Re-Sync** in the webapp. If the ROS
graph only runs inside Docker, the `rosbridge_websocket` node must also be in
that graph (see `docs/ops/STACK_HEALTH_PROBE.md`).

## Vision: no camera stream

- `/stream` falls back through three sources (VideoBridge -> bridge cache ->
  robot demo proxy on port 6001). If all fail, the camera node is down on the
  Pi - check the container: `docker exec yahboom_ros2_final ros2 node list`.
- SSH must be connected for the snapshot fallback path.

## LLM chat errors

- `No model selected` - pick a model in Settings (LLM page).
- `Ollama unreachable` - check `OLLAMA_BASE_URL` (default `http://192.168.1.11:11434`)
  and that Ollama is serving on the robot or host.
- LM Studio must expose the OpenAI-compatible server on `:1234`.

## CORS errors in browser

CORS is configured for localhost, LAN, Tailscale, and Tauri origins (fleet
standard). If a cross-origin call is blocked, check the origin matches
`allow_origin_regex`; do not open `allow_origins` to `*`.

## FastMCP / startup errors

- Use `FastMCP.from_fastapi(app)` - the old `mcp.app` attribute was removed in
  FastMCP 3.x.
- `CORSMiddleware` must be added before `FastMCP.from_fastapi()` is called.

## Robot not in the registry / starts launcher

The fleet Starts launcher entry lives at
`mcp-central-docs/starts/yahboom-start.bat` (see `mcp-central-docs/starts/README.md`).
Missing or broken entries there are managed in the mcp-central-docs repo.
