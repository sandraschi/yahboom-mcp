"""Gripper (servo claw) control for Yahboom Boomy.

Hardware: Servo connected to Rosmaster board servo channel 3.
PTZ uses channels 1 (pan) and 2 (tilt) — channel 3 is free for the gripper.

Control paths (tried in order):
1. ROS `/servo` topic (adds s3 field)
2. SSH I2C `Ctrl_Servo(3, angle)` via Pi (proven pattern from camera_ptz.py)
"""

import logging
from typing import Any

from .. import fail_response

logger = logging.getLogger("yahboom-mcp.operations.gripper")

_GRIPPER_STATE = {"angle": 90}

_OPEN_ANGLE = 0
_CLOSED_ANGLE = 180


async def _ssh_gripper_set(ssh_bridge, channel: int, angle: int) -> bool:
    """Set gripper servo via direct I2C over SSH."""
    if not ssh_bridge or not ssh_bridge.connected:
        return False

    angle = max(0, min(180, angle))
    cmd = (
        'docker exec yahboom_ros2_final python3 -c "'
        "import sys; sys.path.insert(0,'/home/pi/project_demo/raspbot'); "
        "from Raspbot_Lib import Raspbot; "
        f"c = Raspbot(); c.Ctrl_Servo({channel}, {angle}); print('OK')"
        '"'
    )
    out, err, _code = await ssh_bridge.execute(cmd)
    ok = "OK" in out
    if not ok:
        logger.error("SSH gripper set channel=%d angle=%d: out=%r err=%r", channel, angle, out, err)
    return ok


async def gripper_set(ros_bridge, angle: int, ssh_bridge=None) -> dict[str, Any]:
    """Set gripper to absolute angle (0 = open, 180 = closed)."""
    angle = max(0, min(180, int(angle)))

    # Try ROS topic path
    ros_ok = False
    if ros_bridge and ros_bridge.ros and ros_bridge.ros.is_connected:
        try:
            import roslibpy

            topic = roslibpy.Topic(ros_bridge.ros, "/gripper", "std_msgs/Int32")
            topic.publish(roslibpy.Message({"data": angle}))
            ros_ok = True
        except Exception as e:
            logger.warning("ROS gripper publish failed: %s", e)

    if not ros_ok:
        ok = await _ssh_gripper_set(ssh_bridge, 3, angle)
        if not ok:
            return fail_response(
                "Gripper command failed — no ROS bridge and SSH I2C unavailable. "
                "Ensure the robot is powered on and the Pi is reachable.",
            )

    _GRIPPER_STATE["angle"] = angle
    return {
        "success": True,
        "message": f"Gripper → {angle}° (0=open, 180=closed)",
        "state": dict(_GRIPPER_STATE),
    }


async def gripper_open(ros_bridge, ssh_bridge=None) -> dict[str, Any]:
    """Open gripper fully (0°)."""
    return await gripper_set(ros_bridge, _OPEN_ANGLE, ssh_bridge=ssh_bridge)


async def gripper_close(ros_bridge, ssh_bridge=None) -> dict[str, Any]:
    """Close gripper fully (180°)."""
    return await gripper_set(ros_bridge, _CLOSED_ANGLE, ssh_bridge=ssh_bridge)


async def gripper_status() -> dict[str, Any]:
    """Return current gripper state."""
    return {
        "success": True,
        "state": dict(_GRIPPER_STATE),
        "open_angle": _OPEN_ANGLE,
        "closed_angle": _CLOSED_ANGLE,
    }
