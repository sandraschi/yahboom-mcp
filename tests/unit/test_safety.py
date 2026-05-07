import pytest

from yahboom_mcp.operations import safety
from yahboom_mcp.state import _state


@pytest.mark.asyncio
async def test_stop_all_stops_motion(mock_bridge):
    mock_bridge.cmd_vel_history.clear()
    result = await safety.execute(operation="stop_all")
    assert result["success"]
    assert result["status"] == "system_halted"
    assert "motion_stopped" in result["actions"]
    assert len(mock_bridge.cmd_vel_history) == 1
    twist = mock_bridge.cmd_vel_history[0]
    assert twist["linear"]["x"] == 0.0
    assert twist["angular"]["z"] == 0.0


@pytest.mark.asyncio
async def test_stop_all_stops_trajectory():
    from yahboom_mcp.operations.trajectory import TrajectoryManager

    tm = TrajectoryManager()
    tm.start_recording()
    old = _state.get("trajectory_manager")
    _state["trajectory_manager"] = tm
    try:
        result = await safety.execute(operation="stop_all")
        assert result["success"]
        assert "recording_finalized" in result["actions"]
    finally:
        _state["trajectory_manager"] = old


@pytest.mark.asyncio
async def test_stop_all_disconnected_bridge(disconnected_bridge):
    result = await safety.execute(operation="stop_all")
    assert result["success"]
    assert "motion_stopped" not in result["actions"]


@pytest.mark.asyncio
async def test_unknown_operation():
    result = await safety.execute(operation="bogus_op")
    assert not result["success"]
    assert "Unknown safety operation" in result["error"]
