from fastmcp import FastMCP
import logging
from contextlib import asynccontextmanager
from .portmanteau import yahboom_tool
from .core.ros2_bridge import ROS2Bridge
from .core.video_bridge import VideoBridge
from .operations.trajectory import TrajectoryManager
from fastapi.responses import StreamingResponse

# SOTA 2026 Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yahboom-mcp")


@asynccontextmanager
async def lifespan(mcp_instance: FastMCP):
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

    # Store resources in context for tool access
    mcp_instance.context["bridge"] = bridge
    mcp_instance.context["video_bridge"] = video_bridge
    mcp_instance.context["trajectory_manager"] = trajectory_manager

    yield

    logger.info("Yahboom ROS 2 server shutting down")
    if video_bridge:
        video_bridge.stop()
    await bridge.disconnect()


mcp = FastMCP("Yahboom ROS 2", lifespan=lifespan)


# SOTA 2026: Direct FastAPI route for video streaming
@mcp.app.get("/stream")
async def video_feed():
    video_bridge = mcp.context.get("video_bridge")
    if not video_bridge or not video_bridge.active:
        return {"error": "Video bridge not active"}

    return StreamingResponse(
        video_bridge.mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# Register the unified portmanteau tool
mcp.tool()(yahboom_tool)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
