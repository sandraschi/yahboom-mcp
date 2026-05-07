import logging
from typing import Any

import roslibpy

logger = logging.getLogger("yahboom-mcp.operations.camera_ptz")

_camera_state = {"pan": 90, "tilt": 90}

_SERVO_TOPIC = "/servo"
_SERVO_MSG = "yahboomcar_msgs/msg/ServoControl"


async def _publish_both(ros_bridge, pan: int, tilt: int, ssh_bridge=None) -> bool:
    pan = max(0, min(180, pan))
    tilt = max(0, min(180, tilt))

    # Preferred: bridge helper (roslibpy)
    if hasattr(ros_bridge, "publish_servo"):
        ok = await ros_bridge.publish_servo(servo_s1=pan, servo_s2=tilt)
        if ok:
            return True

    # Direct roslibpy fallback
    if ros_bridge and ros_bridge.ros and ros_bridge.ros.is_connected:
        try:
            topic = roslibpy.Topic(ros_bridge.ros, _SERVO_TOPIC, _SERVO_MSG)
            topic.publish(roslibpy.Message({"servo_s1": pan, "servo_s2": tilt}))
            logger.info("Servo direct publish: pan=%d tilt=%d", pan, tilt)
            return True
        except Exception as e:
            logger.error("Direct servo publish failed: %s", e)

    # SSH I2C fallback
    ok = await _ssh_servo_fallback(ssh_bridge, pan, tilt)
    if ok:
        return True

    logger.warning("All servo publish paths failed")
    return False


async def _ssh_servo_fallback(ssh_bridge, pan: int, tilt: int) -> bool:
    """Set both servos via direct I2C over SSH (Raspbot_Lib.Ctrl_Servo)."""
    if not ssh_bridge or not ssh_bridge.connected:
        return False

    pan = max(0, min(180, pan))
    tilt = max(0, min(180, tilt))

    py_cmd = (
        f'import sys; sys.path.insert(0,"/home/pi/project_demo/raspbot"); '
        f'from Raspbot_Lib import Raspbot; '
        f'c = Raspbot(); '
        f'c.Ctrl_Servo(1, {pan}); '
        f'c.Ctrl_Servo(2, {tilt}); '
        f'print("OK")'
    )
    cmd = f'docker exec yahboom_ros2_final python3 -c "{py_cmd}"'
    out, err, _code = await ssh_bridge.execute(cmd)
    ok = "OK" in out
    if not ok:
        logger.error(f"SSH servo fallback: out={out!r} err={err!r}")
    return ok


async def camera_move(ros_bridge, direction: str, step: int = 10, ssh_bridge=None) -> dict[str, Any]:
    """
    Move camera incrementally.
    direction: 'up' | 'down' | 'left' | 'right'
    step: degrees per call (default 10)
    """
    if direction == "up":
        _camera_state["tilt"] = max(0, _camera_state["tilt"] - step)
    elif direction == "down":
        _camera_state["tilt"] = min(180, _camera_state["tilt"] + step)
    elif direction == "left":
        _camera_state["pan"] = min(180, _camera_state["pan"] + step)
    elif direction == "right":
        _camera_state["pan"] = max(0, _camera_state["pan"] - step)
    else:
        return {"success": False, "error": f"Invalid direction: {direction}"}

    pan = _camera_state["pan"]
    tilt = _camera_state["tilt"]

    ok = await _publish_both(ros_bridge, pan, tilt, ssh_bridge=ssh_bridge)

    return {
        "success": ok,
        "message": f"Camera {direction} → pan={pan}° tilt={tilt}°",
        "state": dict(_camera_state),
    }


async def camera_set_pos(ros_bridge, pan: int, tilt: int, ssh_bridge=None) -> dict[str, Any]:
    """Set absolute camera angles (0–180°)."""
    _camera_state["pan"] = max(0, min(180, pan))
    _camera_state["tilt"] = max(0, min(180, tilt))

    pan = _camera_state["pan"]
    tilt = _camera_state["tilt"]

    ok = await _publish_both(ros_bridge, pan, tilt, ssh_bridge=ssh_bridge)

    return {
        "success": ok,
        "message": f"Camera set to pan={pan}° tilt={tilt}°",
        "state": dict(_camera_state),
    }


async def camera_reset(ros_bridge, ssh_bridge=None) -> dict[str, Any]:
    """Reset camera to centre (90°, 90°)."""
    return await camera_set_pos(ros_bridge, 90, 90, ssh_bridge=ssh_bridge)


async def camera_center_for_assembly(ros_bridge, ssh_bridge=None) -> dict[str, Any]:
    """Centre servos for hardware assembly (mount horns at 90° position)."""
    logger.info("Centering servos for hardware assembly...")
    return await camera_set_pos(ros_bridge, 90, 90, ssh_bridge=ssh_bridge)
