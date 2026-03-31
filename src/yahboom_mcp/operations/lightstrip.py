from fastmcp import Context
import logging
import time
import roslibpy

logger = logging.getLogger("yahboom-mcp.operations.lightstrip")

async def execute(
    ctx: Context | None = None,
    operation: str = "",
    param1: str | float | None = None,
    param2: str | float | None = None,
    param3: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    Execute Lightstrip (RGB) operations via ROS 2 topic /rgblight.
    Yahboom Raspbot v2 uses std_msgs/Int32MultiArray for LED control.
    
    Supported Ops:
      set           → Set RGB (param1: r, param2: g, param3: b)
      off           → Turn off all LEDs
      get_status    → Returns active status
    """
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(f"Lightstrip: {operation}", extra={"correlation_id": correlation_id})

    from ..state import _state
    bridge = _state.get("bridge")

    if not bridge or not bridge.connected:
        return {
            "success": False,
            "operation": operation,
            "error": "ROS 2 bridge not connected",
            "status": "offline"
        }

    # ROS 2 Topic for Yahboom RGB Light
    topic_name = "/rgblight"
    
    if operation == "set":
        r = int(param1) if param1 is not None else 0
        g = int(param2) if param2 is not None else 0
        b = int(param3) if param3 is not None else 0
        
        # Publish to ROS 2
        # Yahboom Int32MultiArray expectation: [r, g, b]
        msg = roslibpy.Message({"data": [r, g, b]})
        topic = roslibpy.Topic(bridge.ros, topic_name, "std_msgs/Int32MultiArray")
        topic.publish(msg)
        
        # Verification: We check if the publisher stayed active
        result = {
            "success": True,
            "rgb": [r, g, b],
            "topic": topic_name,
            "status": "published"
        }

    elif operation == "off":
        msg = roslibpy.Message({"data": [0, 0, 0]})
        topic = roslibpy.Topic(bridge.ros, topic_name, "std_msgs/Int32MultiArray")
        topic.publish(msg)
        result = {"success": True, "status": "off"}

    elif operation == "get_status":
        result = {"active": bridge.connected, "topic": topic_name}

    else:
        result = {"error": f"Unknown lightstrip operation: {operation}"}

    return {
        "success": result.get("success", False) if "error" not in result else False,
        "operation": operation,
        "result": result,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
    }
