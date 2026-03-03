from fastmcp import FastMCP
import logging
import asyncio
import sys
import os
from contextlib import asynccontextmanager
from typing import Literal

from .state import _state
from .portmanteau import yahboom_tool
from .core.ros2_bridge import ROS2Bridge
from .core.video_bridge import VideoBridge
from .operations.trajectory import TrajectoryManager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

# SOTA 2026 Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("yahboom-mcp")

# Module-level state for access by tools/routes
_state = {
    "bridge": None,
    "video_bridge": None,
    "trajectory_manager": None,
}


class YahboomMCP:
    """SOTA 2026 Yahboom ROS 2 MCP Server."""

    def __init__(self):
        self.mcp = FastMCP("Yahboom ROS 2", lifespan=self.lifespan)
        self.http_app = FastAPI(title="Yahboom ROS 2 SOTA API")
        self._setup_routes()
        self._register_tools()

    @asynccontextmanager
    async def lifespan(self, mcp_instance: FastMCP):
        logger.info("Yahboom ROS 2 server starting up")

        # Initialize and connect ROS 2 bridge
        bridge = ROS2Bridge(host="localhost", port=9090)
        connected = await bridge.connect()

        # Initialize Video Bridge
        video_bridge = VideoBridge(bridge.ros) if connected and bridge.ros else None
        if video_bridge:
            video_bridge.start()

        # Initialize Trajectory Manager
        trajectory_manager = TrajectoryManager()

        if connected:
            logger.info("Yahboom ROS 2 Bridge connected")
        else:
            logger.warning(
                "Yahboom ROS 2 Bridge failed to connect - operating in degraded mode"
            )

        # Store resources in global state for tool access
        _state["bridge"] = bridge
        _state["video_bridge"] = video_bridge
        _state["trajectory_manager"] = trajectory_manager

        yield

        logger.info("Yahboom ROS 2 server shutting down")
        if video_bridge:
            video_bridge.stop()
        await bridge.disconnect()

    def _setup_routes(self):
        """Setup custom HTTP routes."""

        @self.http_app.get("/stream")
        async def video_feed():
            video_bridge = _state.get("video_bridge")
            if not video_bridge or not video_bridge.active:
                return StreamingResponse(
                    iter([b'{"error": "Video bridge not active"}']),
                    status_code=404,
                    media_type="application/json",
                )

            return StreamingResponse(
                video_bridge.mjpeg_generator(),
                media_type="multipart/x-mixed-replace; boundary=frame",
            )

        @self.http_app.get("/api/v1/health")
        async def health():
            return {
                "status": "ok",
                "service": "yahboom-mcp",
                "connected": _state["bridge"].connected if _state["bridge"] else False,
            }

    def _register_tools(self):
        """Register MCP tools."""
        self.mcp.tool()(yahboom_tool)

    def run(
        self,
        mode: Literal["stdio", "sse", "dual"] = "stdio",
        host: str = "0.0.0.0",
        port: int = 10792,
    ):
        """Run the server in SOTA Dual Mode or specific transport."""
        if mode == "stdio":
            self.mcp.run(transport="stdio")
        elif mode == "sse":
            import uvicorn

            # Mount MCP app into our FastAPI app
            self.http_app.mount("/mcp", self.mcp.sse())
            uvicorn.run(self.http_app, host=host, port=port)
        elif mode == "dual":
            logger.info(f"Starting SOTA Dual Mode: stdio + HTTP/SSE on {host}:{port}")
            # Run HTTP in background thread
            import threading
            import uvicorn

            def run_http():
                self.http_app.mount("/mcp", self.mcp.sse())
                uvicorn.run(self.http_app, host=host, port=port, log_level="error")

            thread = threading.Thread(target=run_http, daemon=True)
            thread.start()

            # Run stdio in main thread
            self.mcp.run(transport="stdio")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Yahboom ROS 2 MCP Server")
    parser.add_argument("--mode", choices=["stdio", "sse", "dual"], default="dual")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=10792)
    args = parser.parse_known_args()[0]

    server = YahboomMCP()
    server.run(mode=args.mode, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
