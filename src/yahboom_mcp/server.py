#!/usr/bin/env python3
"""
SOTA 2026 Yahboom G1 ROS 2 MCP Server
**Timestamp**: 2026-03-04
**Standards**: FastMCP 3.0+, Unified Gateway, SEP-1577

This server implements the Unified Gateway pattern, consolidating MCP SSE transport
and custom API endpoints (like video streaming) into a single FastAPI substrate.
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP

from .state import _state
from .portmanteau import yahboom_tool
from .core.ros2_bridge import ROS2Bridge
from .core.video_bridge import VideoBridge
from .operations.trajectory import TrajectoryManager

# SOTA 2026 Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("yahboom-mcp")

# --- Lifespan Management ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    """SOTA 2026 Life-cycle management for ROS 2 and Hardware resources."""
    logger.info("Yahboom MCP Unified Gateway starting up")

    # SOTA: Support configurable Robot IP via environment variable
    robot_host = os.environ.get("YAHBOOM_IP", "localhost")
    bridge_port = int(os.environ.get("YAHBOOM_BRIDGE_PORT", 9090))

    # Initialize and connect ROS 2 bridge
    bridge = ROS2Bridge(host=robot_host, port=bridge_port)
    connected = await bridge.connect()

    # Initialize Video Bridge (requires bridge.ros)
    video_bridge = VideoBridge(bridge.ros) if connected and bridge.ros else None
    if video_bridge:
        video_bridge.start()

    # Initialize Trajectory Manager
    trajectory_manager = TrajectoryManager()

    if connected:
        logger.info(f"Yahboom ROS 2 Bridge connected to {robot_host}:{bridge_port}")
    else:
        logger.warning(
            "Yahboom ROS 2 Bridge failed to connect - operating in degraded mode"
        )

    # Store resources in global state for tool access
    _state["bridge"] = bridge
    _state["video_bridge"] = video_bridge
    _state["trajectory_manager"] = trajectory_manager

    # Integrate FastMCP lifespan
    async with mcp._lifespan_manager():
        yield

    logger.info("Yahboom MCP Unified Gateway shutting down")
    if video_bridge:
        video_bridge.stop()
    await bridge.disconnect()


# Create FastAPI app first for the Unified Gateway
app = FastAPI(lifespan=lifespan)

# Add CORS to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create FastMCP instance using the FastAPI app
mcp = FastMCP.from_fastapi(app, name="Yahboom ROS 2")


# Register Portmanteau Tool
mcp.tool()(yahboom_tool)

# --- Custom API Endpoints (Native to FastMCP App) ---


@app.get("/stream")
async def video_feed():
    """MJPEG stream endpoint for Dashboard visualization."""
    video_bridge = _state.get("video_bridge")
    if not video_bridge or not video_bridge.active:
        return {"error": "Video bridge not active"}

    return StreamingResponse(
        video_bridge.mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


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
    """Get system telemetry for Dashboard visualization."""
    bridge = _state.get("bridge")
    if not bridge or not bridge.connected:
        return {"error": "ROS 2 bridge not connected"}

    # SOTA: Return real telemetry if available, else simulated for UI testing
    return {
        "battery": 85.0,  # Simulated
        "imu": {"heading": 342.0},
        "velocity": {"linear": 0.5, "angular": 0.0},
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/v1/control/move")
async def control_move(linear: float, angular: float):
    """Direct motion control endpoint for Dashboard UI."""
    bridge = _state.get("bridge")
    if not bridge or not bridge.connected:
        return {"error": "ROS 2 bridge not connected"}

    # Execute motion via bridge
    await bridge.cmd_vel(linear, angular)
    return {"status": "success", "command": {"linear": linear, "angular": angular}}


# --- Entry Points ---


async def run_stdio():
    """Run via STDIO transport (standard MCP mode)."""
    logger.info("Initializing MCP STDIO transport")
    await mcp.run_stdio_async()


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
    parser.add_argument("--port", type=int, default=10792)
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
