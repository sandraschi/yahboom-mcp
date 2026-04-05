from fastmcp import Context
import logging
import asyncio
import time
import roslibpy

logger = logging.getLogger("yahboom-mcp.operations.lightstrip")

# ──────────────────────────────────────────────────────────────────
# Built-in autochange patterns
# ──────────────────────────────────────────────────────────────────
PATTERNS = {
    "patrol":      "patrol_car",    # red/blue alternating flash
    "patrol_car":  "patrol_car",
    "rainbow":     "rainbow",
    "breathe":     "breathe",
    "fire":        "fire",
    "off":         "off",
}

# Active background pattern task (one at a time)
_pattern_task: asyncio.Task | None = None


async def _run_patrol_car(bridge, interval: float = 0.25):
    """Red/blue alternating flash — police/patrol car effect."""
    topic = getattr(bridge, "rgblight_topic", None)
    if not topic:
        topic = roslibpy.Topic(bridge.ros, "/rgblight", "std_msgs/Int32MultiArray")
    while True:
        topic.publish(roslibpy.Message({"data": [255, 0, 0]}))
        await asyncio.sleep(interval)
        topic.publish(roslibpy.Message({"data": [0, 0, 255]}))
        await asyncio.sleep(interval)


async def _run_rainbow(bridge, interval: float = 0.08):
    """Cycle through hue wheel."""
    import math
    topic = getattr(bridge, "rgblight_topic", None)
    if not topic:
        topic = roslibpy.Topic(bridge.ros, "/rgblight", "std_msgs/Int32MultiArray")
    step = 0
    while True:
        h = (step % 360) / 360.0
        # HSV→RGB (saturation=1, value=1)
        i = int(h * 6)
        f = h * 6 - i
        q = int((1 - f) * 255)
        t = int(f * 255)
        colors = [
            (255, t, 0), (q, 255, 0), (0, 255, t),
            (0, q, 255), (t, 0, 255), (255, 0, q),
        ]
        r, g, b = colors[i % 6]
        topic.publish(roslibpy.Message({"data": [r, g, b]}))
        step += 3
        await asyncio.sleep(interval)


async def _run_breathe(bridge, color=(0, 100, 255), period: float = 2.0):
    """Sine-wave brightness breathe on a base colour."""
    import math
    topic = getattr(bridge, "rgblight_topic", None)
    if not topic:
        topic = roslibpy.Topic(bridge.ros, "/rgblight", "std_msgs/Int32MultiArray")
    while True:
        t = time.time()
        brightness = (math.sin(2 * math.pi * t / period) + 1) / 2  # 0-1
        r = int(color[0] * brightness)
        g = int(color[1] * brightness)
        b = int(color[2] * brightness)
        topic.publish(roslibpy.Message({"data": [r, g, b]}))
        await asyncio.sleep(0.05)


async def _run_fire(bridge):
    """Random orange/red flicker simulating fire."""
    import random
    topic = getattr(bridge, "rgblight_topic", None)
    if not topic:
        topic = roslibpy.Topic(bridge.ros, "/rgblight", "std_msgs/Int32MultiArray")
    while True:
        r = random.randint(200, 255)
        g = random.randint(30, 100)
        b = 0
        topic.publish(roslibpy.Message({"data": [r, g, b]}))
        await asyncio.sleep(random.uniform(0.04, 0.15))


_PATTERN_RUNNERS = {
    "patrol_car": _run_patrol_car,
    "rainbow":    _run_rainbow,
    "breathe":    _run_breathe,
    "fire":       _run_fire,
}


async def _stop_pattern():
    global _pattern_task
    if _pattern_task and not _pattern_task.done():
        _pattern_task.cancel()
        try:
            await _pattern_task
        except asyncio.CancelledError:
            pass
    _pattern_task = None


async def execute(
    ctx: Context | None = None,
    operation: str = "",
    param1: str | float | None = None,
    param2: str | float | None = None,
    param3: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    Lightstrip (RGB) operations via ROS 2 topic /rgblight.

    Operations:
      set           → Static RGB colour (param1=r, param2=g, param3=b, 0-255)
      off           → Turn off, cancel any running pattern
      pattern       → Start autochange pattern (param1=name: patrol|rainbow|breathe|fire)
      stop_pattern  → Stop running pattern, leave LEDs in current state
      get_status    → Connection and pattern status

    Pattern names: patrol (patrol_car), rainbow, breathe, fire
    """
    global _pattern_task

    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(f"Lightstrip: {operation}", extra={"correlation_id": correlation_id})

    from ..state import _state
    bridge = _state.get("bridge")

    if not bridge or not bridge.connected:
        return {
            "success": False,
            "operation": operation,
            "error": "Bridge not connected",
            "correlation_id": correlation_id,
        }

    topic = getattr(bridge, "rgblight_topic", None)
    if not topic:
        topic = roslibpy.Topic(bridge.ros, "/rgblight", "std_msgs/Int32MultiArray")

    result: dict = {}

    if operation == "set":
        await _stop_pattern()
        r = max(0, min(255, int(param1))) if param1 is not None else 0
        g = max(0, min(255, int(param2))) if param2 is not None else 0
        b = max(0, min(255, int(param3))) if param3 is not None else 0
        topic.publish(roslibpy.Message({"data": [r, g, b]}))
        result = {"success": True, "rgb": [r, g, b], "status": "published"}

    elif operation in ("off", "stop_pattern"):
        await _stop_pattern()
        topic.publish(roslibpy.Message({"data": [0, 0, 0]}))
        result = {"success": True, "status": "off"}

    elif operation == "pattern":
        pattern_key = str(param1).lower() if param1 else "patrol"
        canonical = PATTERNS.get(pattern_key)
        if not canonical or canonical == "off":
            await _stop_pattern()
            topic.publish(roslibpy.Message({"data": [0, 0, 0]}))
            result = {"success": True, "status": "off"}
        else:
            runner_fn = _PATTERN_RUNNERS.get(canonical)
            if not runner_fn:
                result = {"success": False, "error": f"Unknown pattern: {pattern_key}"}
            else:
                await _stop_pattern()
                _pattern_task = asyncio.create_task(runner_fn(bridge))
                result = {
                    "success": True,
                    "pattern": canonical,
                    "status": "running",
                    "available": list(PATTERNS.keys()),
                }

    elif operation == "get_status":
        running = _pattern_task is not None and not _pattern_task.done()
        result = {
            "success": True,
            "connected": bridge.connected,
            "pattern_running": running,
            "available_patterns": list(PATTERNS.keys()),
        }

    else:
        result = {"success": False, "error": f"Unknown lightstrip operation: {operation}"}

    return {
        "success": result.get("success", False),
        "operation": operation,
        "result": result,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
    }
