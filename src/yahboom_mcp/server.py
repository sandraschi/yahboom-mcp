#!/usr/bin/env python3
"""
SOTA 2026 Yahboom Raspbot v2 ROS 2 MCP Server
**Timestamp**: 2026-04-04
**Standards**: FastMCP 3.2.0, Unified Gateway, SEP-1577

This server implements the Unified Gateway pattern, consolidating MCP SSE transport
and custom API endpoints into a single high-performance FastAPI substrate.
"""

import os
import sys
import logging
import asyncio
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastmcp import FastMCP
import httpx
import time

start_time = time.time()

from .state import _state
from .core.ssh_bridge import SSHBridge
from .core.ros2_bridge import ROS2Bridge
from .core.esp32_bridge import ESP32Bridge
from .core.video_bridge import VideoBridge
from .operations.trajectory import TrajectoryManager
from .operations import voice, lightstrip, missions

# SOTA 2026 Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)


class EndpointFilter(logging.Filter):
    """Filter out high-frequency polling from access logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(path in msg for path in ["/api/v1/telemetry", "/api/v1/health"])


logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
logger = logging.getLogger("yahboom-mcp")

# --- SOTA 3.1.1 Unified Gateway Integration ---



@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """SOTA 2026 Life-cycle management for ROS 2 and Hardware resources."""
    logger.info("Yahboom MCP Unified Gateway starting up")

    robot_host = os.environ.get("YAHBOOM_IP", "192.168.1.11")
    # Ethernet recovery (e.g. 192.168.0.250) is opt-in — WiFi-only setups should leave unset.
    _fb = (os.environ.get("YAHBOOM_FALLBACK_IP") or "").strip()
    fallback_host = _fb if _fb else None
    if fallback_host:
        logger.info("ROSBridge fallback host (ethernet recovery): %s", fallback_host)
    else:
        logger.info(
            "ROSBridge: single host %s (set YAHBOOM_FALLBACK_IP=192.168.0.250 when ethernet is connected)",
            robot_host,
        )
    connection_type = (os.environ.get("YAHBOOM_CONNECTION") or "rosbridge").strip().lower()

    # Initialize placeholders for resources
    video_bridge = None
    watchdog_task = None
    trajectory_manager = TrajectoryManager()
    
    # Store early in state so tools can access even before connected
    _state["trajectory_manager"] = trajectory_manager

    # Setup the appropriate bridge
    if connection_type == "esp32":
        esp32_port = int(os.environ.get("YAHBOOM_ESP32_PORT", 2323))
        bridge = ESP32Bridge(host=robot_host, port=esp32_port)
        ssh = None
    else:
        bridge_port = int(os.environ.get("YAHBOOM_BRIDGE_PORT", 9090))
        bridge = ROS2Bridge(host=robot_host, port=bridge_port, fallback_host=fallback_host)
        ssh = SSHBridge(robot_host)
        bridge.ssh = ssh

    _state["bridge"] = bridge
    _state["ssh"] = ssh

    # Pre-define resync logic so it can be captured by on_reconnect
    async def resync_all_components():
        nonlocal video_bridge
        logger.info("Synchronizing peripherals and video stream...")
        if getattr(bridge, "ros", None) and bridge.ros.is_connected:
            if video_bridge:
                video_bridge.stop()
            video_bridge = VideoBridge(bridge.ros, ssh_bridge=ssh)
            video_bridge.start()
            _state["video_bridge"] = video_bridge
            logger.info("Components successfully re-synchronized with robot.")

    # Reconnection callback for watchdog
    async def on_reconnect():
        logger.info("Watchdog triggered RECONNECT sequence.")
        await resync_all_components()

    async def connect_robot_task():
        """Background task to handle initial connection without blocking API startup."""
        nonlocal video_bridge, watchdog_task
        logger.info(f"Connecting to Yahboom robot at {robot_host} (Async)...")
        
        # ROS/Bridge connection
        connected = await bridge.connect(timeout=15.0)
        
        # SSH connection (secondary)
        if ssh:
            ssh_success = await asyncio.to_thread(ssh.connect)
            if ssh_success:
                logger.info("SSH Bridge established in background.")
            else:
                logger.warning("SSH Bridge failed (check password or connectivity).")

        # Initial video bridge activation if ROS is up
        if connected and getattr(bridge, "ros", None) and bridge.ros.is_connected:
            video_bridge = VideoBridge(bridge.ros, ssh_bridge=ssh)
            video_bridge.start()
            _state["video_bridge"] = video_bridge
            logger.info("Initial VideoBridge activation successful.")

        # Start autonomous connection watchdog
        watchdog_task = asyncio.create_task(
            bridge.monitor_connection(interval=5.0, on_reconnect=on_reconnect)
        )
        logger.info("Connection watchdog active.")

    # Start the connection process but don't AWAIT it here
    # This allows FastAPI to start listening for requests immediately
    connection_task = asyncio.create_task(connect_robot_task())

    yield

    # Cleanup sequence
    logger.info("Yahboom MCP Unified Gateway shutting down...")
    if watchdog_task:
        watchdog_task.cancel()
    if video_bridge:
        video_bridge.stop()
    if bridge:
        await bridge.disconnect()
    if ssh:
        ssh.close()
    if connection_task:
        connection_task.cancel()
    logger.info("Cleanup complete.")


# Create FastAPI app first for the Unified Gateway
app = FastAPI(lifespan=lifespan)

# Add CORS to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MCP from FastAPI (Unified Gateway pattern)
mcp = FastMCP.from_fastapi(app, name="Yahboom ROS 2")


# --- SOTA 3.1.1 Unified Gateway Routes ---

@app.get("/api/v1/health")
async def get_health():
    """Industrial-grade health diagnostics for the robot connection."""
    bridge = _state.get("bridge")
    video = _state.get("video_bridge")
    ssh = _state.get("ssh")
    
    ros_connected = False
    if bridge and getattr(bridge, "ros", None):
        ros_connected = bridge.ros.is_connected

    return {
        "status": "online",
        "robot_connection": {
            "ros": "connected" if ros_connected else "disconnected",
            "video": "active" if video and video.active else "inactive",
            "ssh": "connected" if ssh and ssh.connected else "disconnected",
            "ip": os.environ.get("YAHBOOM_IP", "192.168.1.11")
        },
        "system": {
            "uptime": time.time() - start_time,
            "version": "2.0.0-alpha.1"
        }
    }

# --- Ollama / LLM (webapp Settings + Chat) ---
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
_llm_settings: dict = {"provider": "ollama", "model": ""}


async def _ollama_get(path: str) -> dict | None:
    """GET from Ollama API; returns None on failure."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_BASE_URL.rstrip('/')}{path}")
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logger.debug("Ollama request failed: %s", e)
    return None


async def _ollama_post(path: str, json: dict) -> dict | None:
    """POST to Ollama API; returns None on failure."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{OLLAMA_BASE_URL.rstrip('/')}{path}", json=json)
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logger.debug("Ollama POST failed: %s", e)
    return None



# --- SOTA 2026 Main Robot Tools ---

@mcp.tool()
async def yahboom_tool(
    operation: str,
    param1: str | float | None = None,
    param2: str | float | None = None,
    param3: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    Unified control tool for Yahboom Raspbot v2 (ROS 2 Humble).
    Motion, sensors, diagnostics, trajectory, LEDs, and Voice.

    Operations:
      health_check    -> Get battery, IMU, and connection status
      forward/backward -> linear velocity (param1=speed, param2=duration)
      turn_left/right -> angular velocity (param1=speed, param2=duration)
      strafe_left/right -> lateral velocity (param1=speed, param2=duration)
      stop            -> stop all motion
      read_imu        -> get 9-axis heading/pitch/roll
      read_battery    -> get current voltage and percentage
      light_effect    -> LED patterns (param1=effect_name)
      say             -> Speak text (param1=text)
      play            -> Play sound ID (param1=1-10)
    """
    from .portmanteau import yahboom_tool as portmanteau_exec

    return await portmanteau_exec(
        operation=operation,
        param1=param1,
        param2=param2,
        param3=param3,
        payload=payload,
    )


@mcp.tool()
async def yahboom_agentic_workflow(goal: str) -> str:
    """
    Achieve a high-level robot goal by planning and executing a sequence of operations (SEP-1577).
    Uses get_robot_health, move_robot, read_sensors as sub-tools.
    """
    from .agentic import yahboom_agentic_workflow as workflow_exec

    return await workflow_exec(goal)


@mcp.tool()
async def yahboom_help_tool(category: str | None = None, topic: str | None = None) -> dict:
    """
    Multi-level help system for the Yahboom MCP server.
    Provides hierarchical navigation through categories: motion, sensors, connection, api, mcp_tools, startup, troubleshooting.
    """
    return await yahboom_help(category=category, topic=topic)


# --- ROS 2 Management Tools ---


@mcp.tool()
async def ros_topic_list() -> list:
    """
    List all active ROS 2 topics and their message types.
    Provides full visibility into the robot's sensory and control stack.
    """
    bridge: ROS2Bridge = _state["bridge"]
    if not bridge:
        return ["Error: ROS 2 Bridge not initialized"]

    topics = await bridge.get_all_topics()
    return topics if topics else ["No topics discovered. Is the bringup running?"]


@mcp.tool()
async def ros_node_info(node_name: str) -> str:
    """
    Get detailed information about a specific ROS 2 node.
    Reveals publishers, subscribers, and services for the specified node.
    """
    ssh: SSHBridge = _state["ssh"]
    if not ssh or not ssh.connected:
        return "Error: SSH connection to robot not available."

    cmd = f"docker exec yahboom_ros2 bash -c 'source /opt/ros/humble/setup.bash && source /home/pi/yahboomcar_ws/install/setup.bash && ros2 node info {node_name}'"
    out, err, _ = await ssh.execute(cmd)
    return out if out else f"Error: {err}"


@mcp.tool()
async def ros_resync() -> str:
    """
    Force a re-discovery of all ROS 2 topics and re-subscribe to sensors.
    Use this if telemetry (Battery, IMU) is missing while wheels still work.
    """
    bridge: ROS2Bridge = _state["bridge"]
    if not bridge:
        return "Error: Bridge not initialized"

    success = await bridge.resync_metadata()
    return (
        "Total Synchronization triggered: Topics re-mapped."
        if success
        else "Resync failed."
    )


@mcp.tool()
async def ros_restart_bringup() -> str:
    """
    Remotely restart the Yahboom bringup nodes via SSH.
    Use this as a 'Nuclear Option' if the robot is unresponsive or nodes are missing.
    """
    ssh = _state.get("ssh")
    if not ssh or not ssh.connected:
        return "Error: SSH connection to robot not available."

    logger.info("Triggering remote bringup restart...")
    launch_cmd = (
        'docker exec -d yahboom_ros2 bash -c "'
        "source /opt/ros/humble/setup.bash && "
        "source /home/pi/yahboomcar_ws/install/setup.bash && "
        'ros2 launch yahboomcar_bringup yahboomcar_bringup_launch.py"'
    )
    await ssh.execute(launch_cmd)

    # Give it time to initialize hardware before trying to connect bridge
    await asyncio.sleep(5)
    
    bridge: ROS2Bridge = _state.get("bridge")
    if bridge:
        await bridge.resync_metadata()
        
    return "Native bringup triggered via SSH. Sensory resync in progress."


class LLMSettingsUpdate(BaseModel):
    model: str = ""


class ChatRequest(BaseModel):
    messages: list[
        dict[str, str]
    ]  # [{ "role": "user"|"assistant"|"system", "content": "..." }]


# System preprompt so the chat LLM talks intelligently about Yahboom (hardware, tools, workflows).
YAHBOOM_CHAT_PREPROMPT = """
You are the AI companion for the Yahboom Raspbot v2 dashboard. You help users control and understand the robot.

Platform: Raspberry Pi 5, ROS 2 Humble, four mecanum wheels (holonomic: forward, backward, strafe, rotate). Sensors: LIDAR, camera, IMU, wheel encoders. Battery and telemetry are available via the backend.

You are in the web dashboard chat. You do NOT have direct access to MCP tools here; the user may use Cursor/Claude for that. In this chat you should:
- Answer questions about the robot (hardware, motion, sensors, connection, troubleshooting).
- Suggest next steps: e.g. "Check health and battery in the Dashboard, then try a short forward command from Mission Control."
- If they ask to do something multi-step (patrol, record a path), suggest they use the agentic workflow in an MCP client, or use Mission Control + Dashboard for manual steps.
- Warn if low battery (< 20%): avoid long motions and suggest charging.
- Be concise and technical; avoid filler. When you don't know, say so.
"""


# --- Peripherals Sequencer (Emergency Mode) ---
class EmergencySequencer:
    """Manages the background LED strobe and siren cycle."""

    def __init__(self):
        self._active = False
        self._task = None

    async def _loop(self):
        while self._active:
            # Phase 1: Red Strobe + Siren
            await lightstrip.execute(
                None, operation="set", param1=255, param2=0, param3=0
            )
            await voice.execute(None, operation="play", param1=2)  # Siren ID 2
            await asyncio.sleep(0.5)

            # Phase 2: Blue Strobe
            await lightstrip.execute(
                None, operation="set", param1=0, param2=0, param3=255
            )
            await asyncio.sleep(0.5)

            if not self._active:
                break

    def start(self):
        if not self._active:
            self._active = True
            self._task = asyncio.create_task(self._loop())
            logger.info("Emergency Mode activated")

    async def stop(self):
        self._active = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            # Reset LEDs to OFF
            await lightstrip.execute(
                None, operation="set", param1=0, param2=0, param3=0
            )
            logger.info("Emergency Mode deactivated")

    @property
    def active(self):
        return self._active


_sequencer = EmergencySequencer()
_state["sequencer"] = _sequencer


# ─────────────────────────────────────────────────────────────────────────────
# Help System — multi-level drill-down
# ─────────────────────────────────────────────────────────────────────────────

_HELP: dict = {
    "categories": {
        "motion": {
            "description": "Robot motion control — linear/angular velocity commands via ROS 2.",
            "topics": {
                "forward": "Move forward: yahboom(action='move', linear=0.2, angular=0.0). linear range 0.0–1.0 m/s.",
                "backward": "Move backward: yahboom(action='move', linear=-0.2, angular=0.0). Negative linear values.",
                "turn": "Turn in place: yahboom(action='move', linear=0.0, angular=0.5). Positive=left, negative=right (rad/s).",
                "stop": "Emergency stop: yahboom(action='move', linear=0.0, angular=0.0). Always safe to call.",
                "mecanum": "Mecanum kinematics: 4 independently driven wheels allow omnidirectional movement. Strafe with combined linear+angular.",
                "limits": "Velocity limits: linear max ±1.0 m/s, angular max ±2.0 rad/s. Exceeding limits is clamped by firmware.",
            },
        },
        "sensors": {
            "description": "Telemetry and sensor data — IMU, battery, odometry, LIDAR.",
            "topics": {
                "imu": "IMU data: 9-axis (accel/gyro/mag). heading in degrees 0–360. yahboom(operation='read_imu').",
                "battery": "Battery: percentage 0–100. Below 20% = low warning. yahboom(operation='health_check').",
                "telemetry": "Full telemetry: battery + IMU + velocity. GET http://localhost:10792/api/v1/telemetry — only available when bridge connected.",
                "odometry": "Odometry: wheel encoder-based position estimation via /odom ROS topic (in development).",
                "lidar": "LIDAR: lidar(operation='read', source='yahboom'|'dreame'|'auto'). Yahboom /scan → obstacles (8 sectors) + nearest_m. Dreame D20 Pro map via DREAME_MAP_URL.",
                "camera": "Camera: MJPEG stream at http://localhost:10792/stream — only active when VideoBridge is initialized.",
            },
        },
        "connection": {
            "description": "Connecting the MCP server to the Yahboom Raspbot v2 robot.",
            "topics": {
                "requirements": "Requirements: Yahboom Raspbot v2 powered on, Raspberry Pi running ROS 2 Humble, ROSBridge server running on port 9090.",
                "rosbridge": "Start ROSBridge on the robot: `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`.",
                "env_vars": "Configure robot IP: set YAHBOOM_IP=192.168.x.x and YAHBOOM_BRIDGE_PORT=9090 before starting the server.",
                "cli": "CLI flags: `uv run yahboom-mcp --mode dual --robot-ip 192.168.1.100 --port 10792`.",
                "verify": "Verify: GET http://localhost:10792/api/v1/health — returns {connected: true} when bridge is live.",
                "wifi": "WiFi setup: Robot and workstation on same LAN. Raspbot v2 hotspot: SSID 'raspbot', password '12345678'. Robot IP 192.168.1.11, port 6000. Set YAHBOOM_IP=192.168.1.11 and YAHBOOM_BRIDGE_PORT=6000 (or 9090 for standard rosbridge), then restart server. Use Onboarding page at /onboarding to configure.",
            },
        },
        "api": {
            "description": "REST API endpoints served by the FastAPI Unified Gateway.",
            "topics": {
                "health": "GET /api/v1/health — returns {status, connected, timestamp}. No auth required.",
                "telemetry": "GET /api/v1/telemetry — returns {battery, imu, velocity}. Returns error if bridge offline.",
                "move": "POST /api/v1/control/move?linear=0.2&angular=0.0 — sends Twist command directly to /cmd_vel.",
                "stream": "GET /stream — MJPEG video stream. Usable in <img src> tags. Requires VideoBridge active.",
                "mcp_sse": "MCP over SSE: GET /sse connects AI clients (Claude Desktop, Cursor). Use with mcp_config.json.",
                "docs": "Swagger UI: http://localhost:10792/docs — interactive API explorer for all REST endpoints.",
            },
        },
        "mcp_tools": {
            "description": "MCP tools exposed to AI clients via the portmanteau yahboom() interface.",
            "topics": {
                "yahboom": "Main portmanteau tool. action param routes to sub-operations.",
                "move": "yahboom(action='move', linear=float, angular=float) — velocity command.",
                "health": "yahboom(action='health') — returns bridge connection state and battery.",
                "read_imu": "yahboom(action='read_imu') — returns heading, pitch, roll from 9-axis IMU.",
                "lidar": "lidar(operation='read'|'read_raw'|'read_dreame_map', source='yahboom'|'dreame'|'auto') — Yahboom /scan (optional) or Dreame D20 Pro map (optional, DREAME_MAP_URL).",
                "move_to": "yahboom(action='move_to', x=float, y=float) — autonomous waypoint navigation (requires odometry).",
                "help": "yahboom_help(category=..., topic=...) — this help system.",
            },
        },
        "startup": {
            "description": "Starting the server and dashboard.",
            "topics": {
                "start_script": "Windows: run start.ps1 (double-click start.bat). Clears port 10792, starts Python server + Vite dashboard.",
                "manual": "Manual start: `uv run yahboom-mcp --mode dual --port 10792` for server only.",
                "dashboard": "Dashboard UI runs on http://localhost:10793 (Vite dev server).",
                "modes": "Modes: stdio (MCP only), http (FastAPI+SSE only), dual (both). Default is stdio for MCP clients.",
                "logs": "Logs: server logs to stderr. Vite logs to console. Check start.ps1 output for errors.",
            },
        },
        "troubleshooting": {
            "description": "Common issues and fixes.",
            "topics": {
                "blank_dashboard": "Dashboard blank: ensure BrowserRouter is present in main.tsx. Check browser console for TypeError.",
                "server_down": "Server not on 10792: run start.ps1. If port blocked: `netstat -ano | findstr 10792` to find conflicting process.",
                "bot_offline": "Bot offline banner: ROSBridge not reachable. Check robot IP with ping, confirm rosbridge_server running.",
                "npm_error": "npm Win32 error: start.ps1 uses `cmd /c npm` — do not change to direct npm call.",
                "fastmcp_error": "FastMCP version mismatch: use FastMCP.from_fastapi(app) pattern, not mcp.app (removed in v3.0).",
                "cors": "CORS errors: FastAPI app must have CORSMiddleware before FastMCP.from_fastapi() is called.",
            },
        },
    }
}


async def yahboom_help(
    category: str | None = None,
    topic: str | None = None,
) -> dict:
    """
    Multi-level help system for the Yahboom MCP server.
    Provides hierarchical navigation through categories and specific topics.
    Supported categories: motion, sensors, connection, api, mcp_tools, startup, troubleshooting.
    """
    cats = _HELP["categories"]

    if not category:
        return {
            "help": "Yahboom ROS 2 MCP Help System",
            "usage": "Call with category= to drill down, then category+topic= for full detail.",
            "categories": {k: v["description"] for k, v in cats.items()},
        }

    cat = cats.get(category)
    if not cat:
        return {
            "error": f"Unknown category: '{category}'",
            "available": list(cats.keys()),
        }

    if not topic:
        return {
            "category": category,
            "description": cat["description"],
            "topics": {
                k: v[:80] + "…" if len(v) > 80 else v for k, v in cat["topics"].items()
            },
            "hint": f"Add topic= with one of: {', '.join(cat['topics'].keys())}",
        }

    detail = cat["topics"].get(topic)
    if not detail:
        return {
            "error": f"Unknown topic: '{topic}' in category '{category}'",
            "available": list(cat["topics"].keys()),
        }

    return {
        "category": category,
        "topic": topic,
        "detail": detail,
    }


@app.get("/api/v1/diagnostics/ros/topics")
async def get_ros_topics():
    """Endpoint for webapp Topic Explorer."""
    bridge = _state.get("bridge")
    if not bridge:
        return {"success": False, "error": "Bridge not initialized"}
    topics = await bridge.get_all_topics()
    return {"success": True, "topics": topics}


@app.post("/api/v1/diagnostics/ros/resync")
async def post_ros_resync():
    bridge: ROS2Bridge = _state["bridge"]
    if not bridge:
        return {"success": False, "error": "Bridge not initialized"}
    success = await bridge.resync_metadata()
    return {"success": success}


class LightstripRequest(BaseModel):
    operation: str = "set"
    r: int = 0
    g: int = 0
    b: int = 0
    effect: int | None = None


class ToolRequest(BaseModel):
    operation: str
    param1: str | int | float | None = None
    param2: str | int | float | None = None
    param3: str | int | float | None = None
    payload: dict | None = None


@app.post("/api/v1/control/tool")
async def post_tool_execution(req: ToolRequest):
    """Bridge for the web Dashboard to trigger yahboom_tool operations."""
    return await yahboom_tool(
        operation=req.operation,
        param1=req.param1,
        param2=req.param2,
        param3=req.param3,
        payload=req.payload,
    )


@app.post("/api/v1/diagnostics/ros/restart")
async def restart_ros_bringup():
    """Endpoint for webapp 'Restart Bringup' action."""
    ssh = _state.get("ssh")
    if not ssh or not ssh.connected:
        return {"success": False, "error": "SSH not connected"}

    launch_cmd = (
        'docker exec -d yahboom_ros2 bash -c "'
        "source /opt/ros/humble/setup.bash && "
        "source /home/pi/yahboomcar_ws/install/setup.bash && "
        'ros2 launch yahboomcar_bringup yahboomcar_bringup_launch.py"'
    )
    await ssh.execute(launch_cmd)
    return {"success": True, "message": "Docker bringup triggered"}


# --- LIDAR portmanteau (Yahboom optional + Dreame D20 Pro scan) ---


async def lidar(
    ctx=None,
    operation: str = "read",
    source: str = "auto",
    param1: str | float | None = None,
    param2: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    LIDAR and map data from Yahboom or Dreame D20 Pro.
    Returns obstacle summary (nearest per 8 sectors) or full D20 map data.
    Sources: 'yahboom' for physical ROS scan, 'dreame' for D20 Pro map retrieval.
    """
    from .operations import lidar as lidar_ops

    return await lidar_ops.execute(ctx, operation, source, param1, param2, payload)


# Register LIDAR tool (the only one not already decorated above)
mcp.tool()(lidar)

# --- Prompts (FastMCP 3.1) ---


@mcp.prompt
def yahboom_quick_start(robot_ip: str = "localhost") -> str:
    """Get step-by-step instructions to connect and run the Yahboom Raspbot v2 robot with this MCP server."""
    return f"""You are helping set up the Yahboom Raspbot v2 ROS 2 MCP server.

1. Ensure the robot is powered and on the same LAN. ROSBridge must be running on the robot (e.g. `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`).
2. Set YAHBOOM_IP={robot_ip} (or the robot's actual IP) and start the server: `uv run python -m yahboom_mcp.server --mode dual --port 10792`.
3. Open the dashboard at http://localhost:10793. Use Mission Control for telemetry and the Chat page for natural-language commands.
4. From an MCP client (Cursor, Claude Desktop), use the yahboom tool with operation=health_check first, then motion operations (forward, backward, turn_left, turn_right, stop).
5. For high-level goals use the yahboom_agentic_workflow tool with a natural-language goal."""


@mcp.prompt
def yahboom_patrol(duration_seconds: str = "10") -> str:
    """Generate a patrol plan for the Yahboom robot (e.g. square or figure-8)."""
    return f"""Plan a safe patrol for the Yahboom G1 robot lasting about {duration_seconds} seconds.

Use the yahboom_agentic_workflow tool with a goal like: "Patrol in a square: move forward 2 seconds, turn left 90 degrees, repeat 4 times, then stop and report battery."
Or use individual yahboom(operation=...) calls for forward, turn_left, turn_right, stop. Always check health first."""


@mcp.prompt
def yahboom_diagnostics() -> str:
    """Get a diagnostic checklist for the Yahboom robot and MCP server."""
    return """Run a quick diagnostic on the Yahboom setup:

1. Call yahboom(operation='health_check') to see ROS bridge connection and battery.
2. If connected, call yahboom(operation='read_imu') for orientation and yahboom(operation='read_battery') for power.
3. Check the dashboard at http://localhost:10793 (Mission Control) for live telemetry and the 3D Viz page.
4. If bridge is disconnected, verify YAHBOOM_IP, robot power, and rosbridge_server on the robot."""


@mcp.prompt
def yahboom_patrol_apartment() -> str:
    """Standard action: patrol the apartment (full circuit of main rooms, avoid obstacles, return to start)."""
    return """Execute a patrol of the apartment with the Yahboom Raspbot v2 robot.

1. Call yahboom(operation='health_check') and ensure battery is sufficient (> 20%).
2. Use yahboom_agentic_workflow with a goal like: "Patrol the apartment: do a full circuit of the main rooms. Move forward along walls, turn at corners, avoid obstacles using LIDAR/common sense. Return to the starting position and stop. Report battery when done."
3. Alternatively use a sequence of yahboom(operation='forward', param1=duration), yahboom(operation='turn_left'|'turn_right', param1=duration), and lidar(operation='read') to check obstacles. Prefer agentic_workflow for multi-step patrol."""


@mcp.prompt
def yahboom_go_to_recharge() -> str:
    """Standard action: go to recharge (drive to charging station and stop). Contactless recharger to be equipped later."""
    return """Send the Yahboom Raspbot v2 robot to the charging station.

1. Call yahboom(operation='health_check'). If battery is critical (< 15%), prioritise a short path to the dock.
2. Use yahboom_agentic_workflow with a goal like: "Go to recharge: drive to the charging station and stop. Position the robot so it is aligned with the dock. (Contactless recharger will be equipped later; for now just stop at the dock.)"
3. If the dock position is known (fixed coordinates or landmark), you can use a sequence of forward/turn/strafe and stop. Otherwise instruct the user to guide the robot manually to the dock or to define the dock waypoint."""


# --- Custom API Endpoints (Native to FastMCP App) ---


@app.get("/stream")
async def video_feed():
    """MJPEG stream endpoint for Dashboard visualization with SOTA Fallback."""
    video_bridge = _state.get("video_bridge")
    bridge = _state.get("bridge")

    # Use VideoBridge whenever it is running — mjpeg_generator waits for first frame.
    # (Requiring last_frame here caused a race: no stream until one frame existed, so <img> often failed.)
    if video_bridge and video_bridge.active:
        logger.info("Vision: Streaming from VideoBridge")
        return StreamingResponse(
            video_bridge.mjpeg_generator(),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    # Fallback: ROS bridge JPEG cache (no VideoBridge yet)
    async def bridge_gen():
        while True:
            if not bridge:
                await asyncio.sleep(0.2)
                continue
            img_data = bridge.state.get("last_image")
            if img_data:
                # img_data is base64 string from rosbridge
                import base64

                try:
                    frame_bytes = base64.b64decode(img_data)
                    yield (
                        b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                        + frame_bytes
                        + b"\r\n"
                    )
                except Exception:
                    pass
            await asyncio.sleep(0.1)  # 10 FPS

    logger.info("Vision: Streaming from Bridge Cache fallback")
    return StreamingResponse(
        bridge_gen(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/v1/snapshot")
async def snapshot():
    """Single JPEG frame for embodied AI / VLM. Returns 204 if no frame yet."""
    video_bridge = _state.get("video_bridge")
    if not video_bridge or not video_bridge.active:
        return Response(status_code=204)

    jpeg = video_bridge.get_latest_frame_jpeg()
    if not jpeg:
        return Response(status_code=204)
    return Response(content=jpeg, media_type="image/jpeg")


@app.get("/api/v1/health")
async def health():
    """Standardized SOTA health check."""
    bridge = _state.get("bridge")

    return {
        "status": "ok",
        "service": "yahboom-mcp",
        "connected": bridge.connected if bridge else False,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/v1/telemetry")
async def telemetry():
    """
    Real-time telemetry from all connected ROS 2 sensors.
    """
    bridge = _state.get("bridge")
    # logger.info(
    #    f"Telemetry Check: bridge={bridge}, connected={bridge.connected if bridge else 'N/A'}"
    # )
    if bridge and bridge.connected:
        data = bridge.get_full_telemetry()
        data["status"] = "live"
        data["source"] = "live"
    else:
        # ─────────────────────────────────────────────────────────────────────
        # SOTA v12.0 Integrity: No Silent Mocks.
        # ─────────────────────────────────────────────────────────────────────
        data = {
            "status": "offline",
            "source": "simulated",
            "message": "Robot bridge disconnected",
            "battery": None,
            "voltage": None,
            "imu": {"heading": 0.0},
            "velocity": {"linear": 0.0, "angular": 0.0},
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "scan": {"nearest_m": None},
        }
    return data


# --- Legacy Compatibility Aliases (Dashboard Support) ---


@app.get("/api/v1/sensors")
async def legacy_sensors():
    """Legacy alias for /api/v1/telemetry."""
    return await telemetry()


# --- Hardware Peripheral Controls (Closed-Loop) ---


class DisplayRequest(BaseModel):
    text: str
    line: int = 0
    driver: str = "ssd1306"


@app.post("/api/v1/display")
async def write_display(req: DisplayRequest):
    """Write text to the OLED/LCD display (Closed-Loop)."""
    from .operations import display

    return await display.execute(
        operation="write",
        param1=req.text,
        param2=req.line,
        payload={"driver": req.driver},
    )


@app.post("/api/v1/display/clear")
async def clear_display():
    """Clear the OLED display."""
    from .operations import display

    return await display.execute(operation="clear")


class ScrollRequest(BaseModel):
    text: str


@app.post("/api/v1/display/scroll")
async def scroll_display(req: ScrollRequest):
    """Start background scrolling on the OLED display."""
    from .operations import display

    return await display.execute(operation="scroll", param1=req.text)


@app.post("/api/v1/missions/run/{mission_id}")
async def run_mission(mission_id: str):
    """Start an automated mission."""
    return await missions.execute("run", mission_id=mission_id)


@app.get("/api/v1/missions/status")
async def get_mission_status():
    """Get the status of the current or last mission."""
    return await missions.execute("status")


@app.post("/api/v1/missions/stop")
async def stop_mission():
    """Abort the current mission."""
    return await missions.execute("stop")


class VoiceRequest(BaseModel):
    text: str


@app.post("/api/v1/voice")
async def speak(req: VoiceRequest):
    """Speak text via the Voice Module."""
    from .operations import voice

    return await voice.execute(operation="say", param1=req.text)


class VoicePlayRequest(BaseModel):
    sound_id: int


@app.post("/api/v1/voice/play")
async def play_voice(req: VoicePlayRequest):
    """Play a built-in sound ID via the Voice Module."""
    from .operations import voice

    return await voice.execute(operation="play", param1=req.sound_id)


@app.post("/api/v1/voice/say")
async def legacy_voice_say(req: VoiceRequest):
    """Legacy alias for /api/v1/voice."""
    return await speak(req)


class LEDRequest(BaseModel):
    r: int
    g: int
    b: int


@app.post("/api/v1/led")
async def set_led(req: LEDRequest):
    """Set Lightstrip RGB values."""
    from .operations import lightstrip

    return await lightstrip.execute(
        operation="set", param1=req.r, param2=req.g, param3=req.b
    )


class LightstripPatternRequest(BaseModel):
    operation: str = "set"   # set | off | pattern | stop_pattern | get_status
    r: int = 0
    g: int = 0
    b: int = 0
    pattern: str | None = None   # patrol | rainbow | breathe | fire


@app.post("/api/v1/control/lightstrip")
async def control_lightstrip(req: LightstripPatternRequest):
    """Lightstrip control: static colour, off, or named autochange pattern."""
    from .operations import lightstrip as ls
    if req.operation == "pattern" and req.pattern:
        result = await ls.execute(operation="pattern", param1=req.pattern)
    elif req.operation in ("off", "stop_pattern"):
        result = await ls.execute(operation="off")
    elif req.operation == "get_status":
        result = await ls.execute(operation="get_status")
    else:
        result = await ls.execute(
            operation="set",
            param1=req.r, param2=req.g, param3=req.b,
        )
    return result


class VoiceControlRequest(BaseModel):
    operation: str = "say"   # say | play | volume | get_status
    text: str | None = None
    id: int | None = None
    volume: int | None = None


@app.post("/api/v1/control/voice")
async def control_voice(req: VoiceControlRequest):
    """Voice module: say text, play sound ID, set volume, or probe status."""
    from .operations import voice as v
    if req.operation == "say":
        return await v.execute(operation="say", param1=req.text or "")
    elif req.operation == "play":
        return await v.execute(operation="play", param1=req.id or 1)
    elif req.operation == "volume":
        return await v.execute(operation="volume", param1=req.volume or 20)
    elif req.operation == "get_status":
        return await v.execute(operation="get_status")
    return {"success": False, "error": f"Unknown voice operation: {req.operation}"}


@app.get("/api/v1/control/voice/status")
async def get_voice_status():
    """Probe voice module USB device."""
    from .operations import voice as v
    return await v.execute(operation="get_status")


@app.get("/api/v1/control/display/status")
async def get_display_status():
    """Probe OLED display via I2C."""
    from .operations import display as d
    return await d.execute(operation="get_status")


@app.post("/api/v1/display/status")
async def post_display_status():
    """Probe OLED display via I2C (POST alias for webapp)."""
    from .operations import display as d
    return await d.execute(operation="get_status")


@app.post("/api/v1/display/write")
async def display_write_v2(req: DisplayRequest):
    """Write text to OLED (line param supported)."""
    from .operations import display as d
    return await d.execute(
        operation="write",
        param1=req.text,
        param2=req.line,
        payload={"driver": req.driver},
    )


class LegacyBacklightRequest(BaseModel):
    on: bool
    brightness: int = 100


@app.post("/api/v1/sensors/back_light")
async def legacy_backlight(req: LegacyBacklightRequest):
    """Legacy alias mapping back_light (bool) to Lightstrip RGB."""
    val = req.brightness if req.on else 0
    return await lightstrip.execute(operation="set", param1=val, param2=val, param3=val)



# LightstripRequest and SpeakRequest are already defined above or simplified below.


class EmergencyRequest(BaseModel):
    active: bool


@app.post("/api/v1/emergency")
async def toggle_emergency(req: EmergencyRequest):
    """Toggle the Emergency Mode background sequence."""
    return {"active": _sequencer.active}


@app.post("/api/v1/reconnect")
async def reconnect_hardware():
    """Manually trigger a ROS 2 bridge handshake."""
    bridge = _state.get("bridge")
    if not bridge:
        return {"success": False, "error": "Bridge not initialized"}

    logger.info("Manual reconnection triggered via API")
    connected = await bridge.connect(timeout=10.0)
    
    if connected:
        resync = _state.get("resync_all_components")
        if resync:
            await resync()
            
    return {"success": connected, "status": "online" if connected else "offline"}


@app.post("/api/v1/stop_all")
async def post_stop_all():
    """Global emergency stop: halts all robot activity."""
    from .operations import safety

    return await safety.execute(operation="stop_all")


@app.post("/api/v1/control/move")
async def control_move(
    linear: float = 0.0, angular: float = 0.0, linear_y: float = 0.0
):
    """Direct motion control endpoint for Dashboard UI and embodied loop."""
    bridge = _state.get("bridge")
    if not bridge or not bridge.connected:
        return {"error": "Bridge not connected"}

    ok = await bridge.publish_velocity(
        linear_x=linear, angular_z=angular, linear_y=linear_y
    )
    return {
        "status": "success" if ok else "failed",
        "command": {"linear": linear, "angular": angular, "linear_y": linear_y},
    }


# --- Ollama / LLM (Settings + Chat) ---


@app.get("/api/v1/settings/ollama/status")
async def ollama_status():
    """Check if Ollama is reachable (for Settings page)."""
    data = await _ollama_get("/api/version")
    return {
        "connected": data is not None,
        "base_url": OLLAMA_BASE_URL,
    }


@app.get("/api/v1/settings/ollama/models")
async def ollama_models():
    """List models discovered from Ollama (for Settings page dropdown)."""
    data = await _ollama_get("/api/tags")
    if data is None:
        return {"models": [], "error": "Ollama unreachable"}
    raw = data.get("models") or []
    models = [
        {
            "name": m.get("name") or m.get("model", ""),
            "size": m.get("size"),
            "modified_at": m.get("modified_at"),
        }
        for m in raw
    ]
    return {"models": models}


@app.get("/api/v1/settings/llm")
async def get_llm_settings():
    """Current LLM provider and selected model (for chat/settings)."""
    return {
        "provider": _llm_settings.get("provider", "ollama"),
        "model": _llm_settings.get("model", ""),
    }


@app.put("/api/v1/settings/llm")
async def update_llm_settings(body: LLMSettingsUpdate):
    """Set selected Ollama model (persists in process memory)."""
    _llm_settings["model"] = body.model or ""
    return {"provider": "ollama", "model": _llm_settings["model"]}


@app.post("/api/v1/chat")
async def chat_completion(body: ChatRequest):
    """
    Chat completion via Ollama. Uses model from Settings (GET/PUT /api/v1/settings/llm).
    Injects a Yahboom-specific system preprompt so the LLM answers intelligently about the robot.
    Body: { "messages": [ { "role": "user"|"assistant"|"system", "content": "..." } ] }
    """
    model = (_llm_settings.get("model") or "").strip()
    if not model:
        raise HTTPException(
            status_code=400,
            detail="No model selected. Configure LLM model in Settings.",
        )
    messages = list(body.messages or [])
    if not messages:
        raise HTTPException(status_code=400, detail="messages array is required")
    # Prepend system message so Ollama gets Yahboom context (dashboard chat has no MCP tools).
    preprompt = {"role": "system", "content": YAHBOOM_CHAT_PREPROMPT}
    if messages and messages[0].get("role") == "system":
        messages[0]["content"] = (
            YAHBOOM_CHAT_PREPROMPT + "\n\n" + (messages[0].get("content") or "")
        )
    else:
        messages.insert(0, preprompt)
    payload = {"model": model, "messages": messages, "stream": False}
    data = await _ollama_post("/api/chat", payload)
    if data is None:
        raise HTTPException(
            status_code=502, detail="Ollama unreachable or request failed"
        )
    msg = data.get("message")
    if not msg:
        raise HTTPException(status_code=502, detail="Ollama returned no message")
    return {
        "message": {
            "role": msg.get("role", "assistant"),
            "content": msg.get("content", ""),
        }
    }


# --- Entry Points ---


# Mount FastMCP gateway - redundant in v3.1 if using from_fastapi, but kept for clarity
# mcp.from_fastapi(app)


async def run_stdio():
    """Run via STDIO transport (standard MCP mode)."""
    logger.info("Initializing MCP STDIO transport")
    await mcp.run_stdio_async()


# ─────────────────────────────────────────────────────────────────────────────
# Mandatory Capability Introspection Endpoint (WEBAPP_STANDARDS §1.4)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/capabilities")
async def get_capabilities():
    """Runtime source of truth for server capabilities."""
    return {
        "status": "ok",
        "server": {"name": "yahboom-mcp", "version": "1.0.1", "fastmcp": "3.2.0"},
        "tool_surface": {"total": 4, "portmanteau_count": 1, "atomic_count": 3},
        "available_operations": [
            "forward",
            "backward",
            "turn_left",
            "turn_right",
            "strafe_left",
            "strafe_right",
            "stop",
            "read_imu",
            "read_encoders",
            "read_battery",
            "read_all",
            "read_lidar",
            "display",
            "clear_display",
            "led",
            "led_off",
            "say",
            "play",
            "start_recording",
            "stop_recording",
            "list_trajectories",
            "health_check",
            "config_show",
        ],
    }


def main():
    """Main entry point with CLI argument parsing."""
    import argparse

    parser = argparse.ArgumentParser(description="Yahboom MCP Server")
    parser.add_argument(
        "--mode",
        choices=["stdio", "http", "dual"],
        default="stdio",
        help="Transport mode: stdio (MCP only), http (Dashboard+SSE), dual (Both)",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=10892)
    parser.add_argument("--robot-ip", help="IP address of the Yahboom robot")
    parser.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    if args.robot_ip:
        os.environ["YAHBOOM_IP"] = args.robot_ip

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.mode == "stdio":
        asyncio.run(run_stdio())
    else:
        # In HTTP or Dual mode, we run the FastAPI app via uvicorn
        logger.info("Unified Gateway Routes:")
        for route in app.routes:
            if hasattr(route, "path"):
                logger.info(f"  {route.path} -> {route.name}")

        logger.info(f"Starting Unified Gateway on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
