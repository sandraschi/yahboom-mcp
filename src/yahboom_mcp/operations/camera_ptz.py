import logging
from typing import Any

import roslibpy

logger = logging.getLogger("yahboom-mcp.operations.camera_ptz")

# Tracked current angles — centre = 90°.
# Both angles are sent on every publish; use this to fill the "other" channel.
_camera_state = {"pan": 90, "tilt": 90}

_SERVO_TOPIC = "/servo"
_SERVO_MSG = "yahboomcar_msgs/msg/ServoControl"


async def _publish_both(ros_bridge, pan: int, tilt: int) -> bool:
    """
    Publish a ServoControl message setting both servo channels at once.

    The Yahboom driver's servo_callback does:
        Ctrl_Servo(1, msg.servo_s1)   ← pan
        Ctrl_Servo(2, msg.servo_s2)   ← tilt

    Both fields are written on every incoming message, so we must always
    send both current angles. Sending only one field leaves the other at
    the message default (0), which drives that servo to 0° — this was the
    original bug (wrong field names "id"/"angle" instead of "servo_s1"/"servo_s2").
    """
    pan = max(0, min(180, pan))
    tilt = max(0, min(180, tilt))

    # Preferred: bridge helper (signature updated to match)
    if hasattr(ros_bridge, "publish_servo"):
        ok = await ros_bridge.publish_servo(servo_s1=pan, servo_s2=tilt)
        if ok:
            return True
        logger.warning("publish_servo returned False — trying direct topic")

    # Direct roslibpy fallback
    if not ros_bridge or not ros_bridge.ros or not ros_bridge.ros.is_connected:
        logger.error("Cannot publish servo: ROS not connected")
        return False

    try:
        topic = roslibpy.Topic(ros_bridge.ros, _SERVO_TOPIC, _SERVO_MSG)
        topic.publish(roslibpy.Message({"servo_s1": pan, "servo_s2": tilt}))
        logger.info(f"Servo direct publish: servo_s1={pan} (pan), servo_s2={tilt} (tilt)")
        return True
    except Exception as e:
        logger.error(f"Direct servo publish failed: {e}")
        return False


async def _ssh_servo_fallback(ssh_bridge, pan: int, tilt: int) -> bool:
    """
    Last-resort: set both servos via Rosmaster_Lib over SSH.
    Used when ROSBridge is disconnected but the Pi is still reachable.
    """
    if not ssh_bridge or not ssh_bridge.connected:
        return False

    pan = max(0, min(180, pan))
    tilt = max(0, min(180, tilt))

    py_cmd = (
        f'python3 -c "'
        f"import sys; sys.path.insert(0, '/root/yahboomcar_ws/install/yahboomcar_bringup/lib/python3.10/site-packages/yahboomcar_bringup'); "
        f"from Rosmaster_Lib import Rosmaster; "
        f"bot = Rosmaster(); bot.create_receive_threading(); "
        f"import time; time.sleep(0.3); "
        f"bot.set_pwm_servo(1, {pan}); "
        f"bot.set_pwm_servo(2, {tilt}); "
        f"time.sleep(0.2); bot.cancel_receive_threading(); "
        f"print('OK')\""
    )
    cmd = f"docker exec yahboom_ros2 bash -c '{py_cmd}'"
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

    ok = await _publish_both(ros_bridge, pan, tilt)
    if not ok and ssh_bridge:
        logger.info("ROS servo publish failed — trying SSH fallback")
        ok = await _ssh_servo_fallback(ssh_bridge, pan, tilt)

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

    ok = await _publish_both(ros_bridge, pan, tilt)
    if not ok and ssh_bridge:
        ok = await _ssh_servo_fallback(ssh_bridge, pan, tilt)

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
