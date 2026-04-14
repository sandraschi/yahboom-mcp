import logging
from typing import Any

import roslibpy

logger = logging.getLogger("yahboom-mcp.operations.camera_ptz")

# Estimated current angles (centre = 90°)
_camera_state = {"pan": 90, "tilt": 90}

# Yahboom Raspbot v2 servo IDs on the PTZ gimbal
_PAN_SERVO_ID  = 1   # horizontal pan
_TILT_SERVO_ID = 2   # vertical tilt

# Topic used by the Yahboom bringup for servo control.
# yahboomcar_msgs/msg/ServoControl has fields: id (uint8), angle (uint16)
# Falls back to std_msgs/Int32MultiArray [id, angle] if custom msg unavailable.
_SERVO_TOPIC   = "/servo"
_SERVO_MSG     = "yahboomcar_msgs/msg/ServoControl"
_SERVO_MSG_FB  = "std_msgs/Int32MultiArray"   # fallback


async def _publish_servo(ros_bridge, servo_id: int, angle: int) -> bool:
    """
    Publish a servo command.  Tries yahboomcar_msgs first, falls back to
    Int32MultiArray [id, angle] which many Yahboom images also support.
    """
    angle = max(0, min(180, angle))

    # 1. Use bridge helper if available (preferred path)
    if hasattr(ros_bridge, "publish_servo"):
        ok = await ros_bridge.publish_servo(servo_id, angle)
        if ok:
            return True
        logger.warning("publish_servo returned False — trying topic directly")

    # 2. Direct topic publish via roslibpy
    if not ros_bridge.ros or not ros_bridge.ros.is_connected:
        logger.error("Cannot publish servo: ROS not connected")
        return False

    try:
        # Try yahboomcar_msgs first
        servo_topic = roslibpy.Topic(
            ros_bridge.ros, _SERVO_TOPIC, _SERVO_MSG
        )
        servo_topic.publish(roslibpy.Message({"id": servo_id, "angle": angle}))
        logger.info(f"Servo {servo_id} → {angle}° via {_SERVO_MSG}")
        return True
    except Exception as e:
        logger.warning(f"yahboomcar_msgs servo publish failed ({e}), trying fallback")

    try:
        fallback_topic = roslibpy.Topic(
            ros_bridge.ros, _SERVO_TOPIC, _SERVO_MSG_FB
        )
        fallback_topic.publish(roslibpy.Message({"data": [servo_id, angle]}))
        logger.info(f"Servo {servo_id} → {angle}° via {_SERVO_MSG_FB} fallback")
        return True
    except Exception as e2:
        logger.error(f"Servo fallback also failed: {e2}")
        return False


async def _ssh_servo_fallback(ssh_bridge, servo_id: int, angle: int) -> bool:
    """
    Last-resort servo command via SSH direct I2C write to the MCU.
    Uses Yahboom's Rosmaster_Lib protocol which the patched driver may not expose.
    """
    if not ssh_bridge or not ssh_bridge.connected:
        return False

    angle = max(0, min(180, angle))
    # Rosmaster protocol: servo set uses set_pwm_servo(servo_id, angle)
    # Executed inside the Docker container where Rosmaster_Lib is installed
    py_cmd = (
        f"python3 -c \""
        f"import sys; sys.path.insert(0, '/root/yahboomcar_ws/install/yahboomcar_bringup/lib/python3.10/site-packages/yahboomcar_bringup'); "
        f"from Rosmaster_Lib import Rosmaster; "
        f"bot = Rosmaster(); bot.create_receive_threading(); "
        f"import time; time.sleep(0.3); "
        f"bot.set_pwm_servo({servo_id}, {angle}); "
        f"time.sleep(0.2); bot.cancel_receive_threading(); "
        f"print('OK')\""
    )
    cmd = f"docker exec yahboom_ros2 bash -c '{py_cmd}'"
    out, err, _code = await ssh_bridge.execute(cmd)
    ok = "OK" in out
    if not ok:
        logger.error(f"SSH servo fallback failed: out={out!r} err={err!r}")
    return ok


async def camera_move(
    ros_bridge, direction: str, step: int = 10, ssh_bridge=None
) -> dict[str, Any]:
    """
    Move camera incrementally in 4 directions.
    direction: 'up', 'down', 'left', 'right'
    Falls back to SSH/I2C path if ROS topic publish fails.
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

    pan   = _camera_state["pan"]
    tilt  = _camera_state["tilt"]

    ok_pan  = await _publish_servo(ros_bridge, _PAN_SERVO_ID, pan)
    ok_tilt = await _publish_servo(ros_bridge, _TILT_SERVO_ID, tilt)

    # SSH fallback if ROS publish failed
    if not (ok_pan and ok_tilt) and ssh_bridge:
        logger.info("Servo ROS publish failed — trying SSH/I2C fallback")
        ok_pan  = ok_pan  or await _ssh_servo_fallback(ssh_bridge, _PAN_SERVO_ID, pan)
        ok_tilt = ok_tilt or await _ssh_servo_fallback(ssh_bridge, _TILT_SERVO_ID, tilt)

    return {
        "success": ok_pan and ok_tilt,
        "message": f"Moved camera {direction}",
        "state": _camera_state,
        "pan_ok": ok_pan,
        "tilt_ok": ok_tilt,
    }


async def camera_set_pos(
    ros_bridge, pan: int, tilt: int, ssh_bridge=None
) -> dict[str, Any]:
    """Set absolute camera angles (0-180)."""
    pan  = max(0, min(180, pan))
    tilt = max(0, min(180, tilt))

    _camera_state["pan"]  = pan
    _camera_state["tilt"] = tilt

    ok_pan  = await _publish_servo(ros_bridge, _PAN_SERVO_ID, pan)
    ok_tilt = await _publish_servo(ros_bridge, _TILT_SERVO_ID, tilt)

    if not (ok_pan and ok_tilt) and ssh_bridge:
        ok_pan  = ok_pan  or await _ssh_servo_fallback(ssh_bridge, _PAN_SERVO_ID, pan)
        ok_tilt = ok_tilt or await _ssh_servo_fallback(ssh_bridge, _TILT_SERVO_ID, tilt)

    return {
        "success": ok_pan and ok_tilt,
        "message": f"Set camera to pan={pan} tilt={tilt}",
        "state": _camera_state,
    }


async def camera_reset(ros_bridge, ssh_bridge=None) -> dict[str, Any]:
    """Reset camera to centre (90, 90)."""
    return await camera_set_pos(ros_bridge, 90, 90, ssh_bridge=ssh_bridge)


async def camera_center_for_assembly(ros_bridge, ssh_bridge=None) -> dict[str, Any]:
    """
    Centre servos for hardware assembly: mount horns/wings at the 90° position.
    """
    logger.info("Centering servos for hardware assembly...")
    return await camera_set_pos(ros_bridge, 90, 90, ssh_bridge=ssh_bridge)
