import pytest

from yahboom_mcp.agentic import _get_robot_health, _move_robot, _read_sensors


@pytest.mark.asyncio
async def test_get_robot_health_connected(mock_bridge):
    mock_bridge._battery_data = {"percentage": 85.0, "voltage": 11.6}
    result = await _get_robot_health()
    assert isinstance(result, str)
    assert "success" in result.lower() or "True" in result


@pytest.mark.asyncio
async def test_move_robot_forward(mock_bridge):
    mock_bridge.cmd_vel_history.clear()
    result = await _move_robot("forward", 1.0)
    assert isinstance(result, str)
    assert len(mock_bridge.cmd_vel_history) == 1


@pytest.mark.asyncio
async def test_move_robot_stop(mock_bridge):
    mock_bridge.cmd_vel_history.clear()
    result = await _move_robot("stop")
    assert isinstance(result, str)
    assert len(mock_bridge.cmd_vel_history) == 1
    twist = mock_bridge.cmd_vel_history[0]
    assert twist["linear"]["x"] == 0.0
    assert twist["angular"]["z"] == 0.0


@pytest.mark.asyncio
async def test_move_robot_unknown_direction():
    result = await _move_robot("fly_up")
    assert "Unknown direction" in result


@pytest.mark.asyncio
async def test_read_sensors_imu(mock_bridge):
    result = await _read_sensors("imu")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_read_sensors_battery(mock_bridge):
    mock_bridge._battery_data = {"percentage": 72.0, "voltage": 11.2}
    result = await _read_sensors("battery")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_read_sensors_all(mock_bridge):
    result = await _read_sensors("all")
    assert isinstance(result, str)
