"""
Unit tests — motion, lightstrip, servo, sensors, display, voice.
All tests use MockROS2Bridge + mock SSH; no hardware required.
Run: pytest tests/unit/ -v
"""
import pytest

from yahboom_mcp.operations import display, lightstrip, motion, voice
from yahboom_mcp.operations.camera_ptz import camera_move, camera_reset, camera_set_pos
from yahboom_mcp.portmanteau import yahboom_tool

# ── Motion ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_motion_forward(mock_bridge):
    result = await motion.execute(operation="forward", param1=0.3)
    assert result["success"]
    assert len(mock_bridge.cmd_vel_history) == 1
    twist = mock_bridge.cmd_vel_history[0]
    assert twist["linear"]["x"] == pytest.approx(0.3)
    assert twist["angular"]["z"] == 0.0


@pytest.mark.asyncio
async def test_motion_backward(mock_bridge):
    result = await motion.execute(operation="backward", param1=0.2)
    assert result["success"]
    twist = mock_bridge.cmd_vel_history[-1]
    assert twist["linear"]["x"] == pytest.approx(-0.2)


@pytest.mark.asyncio
async def test_motion_turn_left(mock_bridge):
    result = await motion.execute(operation="turn_left", param1=0.5)
    assert result["success"]
    twist = mock_bridge.cmd_vel_history[-1]
    assert twist["angular"]["z"] == pytest.approx(0.5)
    assert twist["linear"]["x"] == 0.0


@pytest.mark.asyncio
async def test_motion_turn_right(mock_bridge):
    result = await motion.execute(operation="turn_right", param1=0.5)
    assert result["success"]
    twist = mock_bridge.cmd_vel_history[-1]
    assert twist["angular"]["z"] == pytest.approx(-0.5)


@pytest.mark.asyncio
async def test_motion_strafe_left(mock_bridge):
    result = await motion.execute(operation="strafe_left", param1=0.3)
    assert result["success"]
    twist = mock_bridge.cmd_vel_history[-1]
    assert twist["linear"]["y"] == pytest.approx(0.3)


@pytest.mark.asyncio
async def test_motion_strafe_right(mock_bridge):
    result = await motion.execute(operation="strafe_right", param1=0.3)
    assert result["success"]
    twist = mock_bridge.cmd_vel_history[-1]
    assert twist["linear"]["y"] == pytest.approx(-0.3)


@pytest.mark.asyncio
async def test_motion_stop(mock_bridge):
    result = await motion.execute(operation="stop")
    assert result["success"]
    twist = mock_bridge.cmd_vel_history[-1]
    assert twist["linear"]["x"] == 0.0
    assert twist["angular"]["z"] == 0.0


@pytest.mark.asyncio
async def test_motion_disconnected(disconnected_bridge):
    # Should still return success=True (mock_command_sent), just not publish
    result = await motion.execute(operation="forward", param1=0.2)
    assert result["success"]
    assert result["result"]["status"] == "mock_command_sent"


# ── Lightstrip ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_lightstrip_set(mock_bridge):
    result = await lightstrip.execute(operation="set", param1=255, param2=0, param3=128)
    assert result["success"]
    last = mock_bridge.rgblight_topic.published[-1]
    assert last.data == {"data": [255, 0, 128]}


@pytest.mark.asyncio
async def test_lightstrip_off(mock_bridge):
    result = await lightstrip.execute(operation="off")
    assert result["success"]
    last = mock_bridge.rgblight_topic.published[-1]
    assert last.data == {"data": [0, 0, 0]}


@pytest.mark.asyncio
async def test_lightstrip_pattern_start_cancel(mock_bridge):
    r = await lightstrip.execute(operation="pattern", param1="patrol")
    assert r["success"]
    assert r["result"]["pattern"] == "patrol_car"
    r2 = await lightstrip.execute(operation="off")
    assert r2["success"]


@pytest.mark.asyncio
async def test_lightstrip_pattern_rainbow(mock_bridge):
    r = await lightstrip.execute(operation="pattern", param1="rainbow")
    assert r["success"]
    assert r["result"]["pattern"] == "rainbow"
    await lightstrip.execute(operation="off")


@pytest.mark.asyncio
async def test_lightstrip_unknown_op(mock_bridge):
    r = await lightstrip.execute(operation="blink_purple_unicorn")
    assert not r["success"]


@pytest.mark.asyncio
async def test_lightstrip_disconnected(disconnected_bridge):
    r = await lightstrip.execute(operation="set", param1=255, param2=0, param3=0)
    assert not r["success"]
    assert "not connected" in r["error"].lower()


# ── Servo / PTZ ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_servo_camera_move_up(mock_bridge_with_servo):
    result = await camera_move(mock_bridge_with_servo, direction="up", step=15)
    assert result["success"]
    tilt_cmd = next(c for c in mock_bridge_with_servo.servo_history if c["id"] == 2)
    assert tilt_cmd["angle"] == 90 - 15  # started at 90, moved up 15


@pytest.mark.asyncio
async def test_servo_camera_move_left(mock_bridge_with_servo):
    result = await camera_move(mock_bridge_with_servo, direction="left", step=20)
    assert result["success"]
    pan_cmd = next(c for c in mock_bridge_with_servo.servo_history if c["id"] == 1)
    assert pan_cmd["angle"] == 90 + 20


@pytest.mark.asyncio
async def test_servo_camera_set_pos(mock_bridge_with_servo):
    result = await camera_set_pos(mock_bridge_with_servo, pan=45, tilt=135)
    assert result["success"]
    pan_cmd  = next(c for c in mock_bridge_with_servo.servo_history if c["id"] == 1)
    tilt_cmd = next(c for c in mock_bridge_with_servo.servo_history if c["id"] == 2)
    assert pan_cmd["angle"] == 45
    assert tilt_cmd["angle"] == 135


@pytest.mark.asyncio
async def test_servo_camera_reset(mock_bridge_with_servo):
    result = await camera_reset(mock_bridge_with_servo)
    assert result["success"]
    pan_cmd  = next(c for c in mock_bridge_with_servo.servo_history if c["id"] == 1)
    tilt_cmd = next(c for c in mock_bridge_with_servo.servo_history if c["id"] == 2)
    assert pan_cmd["angle"] == 90
    assert tilt_cmd["angle"] == 90


@pytest.mark.asyncio
async def test_servo_clamp_bounds(mock_bridge_with_servo):
    result = await camera_set_pos(mock_bridge_with_servo, pan=-50, tilt=999)
    assert result["success"]
    pan_cmd  = next(c for c in mock_bridge_with_servo.servo_history if c["id"] == 1)
    tilt_cmd = next(c for c in mock_bridge_with_servo.servo_history if c["id"] == 2)
    assert pan_cmd["angle"] == 0    # clamped
    assert tilt_cmd["angle"] == 180  # clamped


@pytest.mark.asyncio
async def test_servo_invalid_direction(mock_bridge_with_servo):
    result = await camera_move(mock_bridge_with_servo, direction="sideways")
    assert not result["success"]


# ── Sensors ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_portmanteau_health(mock_bridge):
    result = await yahboom_tool(operation="health_check")
    assert isinstance(result, dict)
    assert "connected" in str(result).lower() or "bridge" in str(result).lower()


@pytest.mark.asyncio
async def test_portmanteau_read_battery(mock_bridge):
    result = await yahboom_tool(operation="read_battery")
    assert isinstance(result, dict)
    # MockROS2Bridge has 88% battery
    assert "88" in str(result) or "battery" in str(result).lower()


@pytest.mark.asyncio
async def test_portmanteau_read_imu(mock_bridge):
    result = await yahboom_tool(operation="read_imu")
    assert isinstance(result, dict)


# ── Display ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_display_no_ssh(disconnected_bridge):
    # No SSH → offline
    result = await display.execute(operation="write", param1="Hello")
    assert not result["success"]
    assert result["status"] == "offline"


@pytest.mark.asyncio
async def test_display_write_ssh(mock_bridge, mock_ssh):
    mock_ssh.execute.return_value = ("VERIFIED", "", 0)
    result = await display.execute(operation="write", param1="Patrol Active", param2=1)
    assert result["success"]
    assert result["status"] == "written"


@pytest.mark.asyncio
async def test_display_clear_ssh(mock_bridge, mock_ssh):
    mock_ssh.execute.return_value = ("VERIFIED", "", 0)
    result = await display.execute(operation="clear")
    assert result["success"]


@pytest.mark.asyncio
async def test_display_get_status_not_found(mock_bridge, mock_ssh):
    # i2cdetect output without 3c → not active
    mock_ssh.execute.return_value = ("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f\n00:\n", "", 0)
    result = await display.execute(operation="get_status")
    assert result["success"]  # operation succeeded even if display not found
    assert not result["result"]["active"]


@pytest.mark.asyncio
async def test_display_get_status_found(mock_bridge, mock_ssh):
    # i2cdetect with 3c present, then VERIFIED from probe
    mock_ssh.execute.side_effect = [
        ("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f\n30: -- -- -- -- -- -- -- -- -- -- -- -- 3c --\n", "", 0),
        ("VERIFIED", "", 0),
    ]
    result = await display.execute(operation="get_status")
    assert result["success"]
    assert result["result"]["active"]
    assert result["result"]["driver_responding"]


# ── Voice ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_voice_no_ssh(disconnected_bridge):
    result = await voice.execute(operation="get_status")
    assert not result["success"]
    assert result["status"] == "offline"


@pytest.mark.asyncio
async def test_voice_get_status_not_found(mock_bridge, mock_ssh):
    mock_ssh.execute.return_value = ("Bus 001 Device 002: ID 1234:5678 SomeOtherDevice\n", "", 0)
    result = await voice.execute(operation="get_status")
    assert result["success"]
    assert not result["result"]["detected"]


@pytest.mark.asyncio
async def test_voice_get_status_found(mock_bridge, mock_ssh):
    # lsusb, pyserial probe, then _resolve_device script returns /dev/ttyUSB0
    mock_ssh.execute.side_effect = [
        ("Bus 001 Device 002: ID 1a86:7523 QinHeng Electronics\n", "", 0),  # lsusb
        ("PY_SERIAL_OK\n", "", 0),  # pyserial probe
        ("/dev/ttyUSB0\n", "", 0),  # find device script
    ]
    result = await voice.execute(operation="get_status")
    assert result["success"]
    assert result["result"]["detected"]
    assert result["result"]["device"] == "/dev/ttyUSB0"


@pytest.mark.asyncio
async def test_voice_say(mock_bridge, mock_ssh):
    # Device found, serial write succeeds
    mock_ssh.execute.side_effect = [
        ("/dev/ttyUSB0", "", 0),  # _resolve_device
        ("OK", "", 0),             # serial write
    ]
    result = await voice.execute(operation="say", param1="Hello Boomy")
    assert result["success"]
    assert result["result"]["text"] == "Hello Boomy"
