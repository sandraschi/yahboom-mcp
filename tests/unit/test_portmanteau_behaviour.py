"""Tool behaviour with an injected mock bridge (no FastAPI)."""

from __future__ import annotations

import pytest

from yahboom_mcp.portmanteau import yahboom_tool


@pytest.mark.mock
@pytest.mark.asyncio
async def test_health_check_with_bridge(mock_bridge) -> None:
    r = await yahboom_tool(operation="health_check")
    assert r["success"] is True
    assert r["result"]["ros_bridge"] == "CONNECTED"


@pytest.mark.mock
@pytest.mark.asyncio
async def test_motion_forward_records_cmd_vel(mock_bridge) -> None:
    await yahboom_tool(operation="forward", param1=0.3)
    assert len(mock_bridge.cmd_vel_history) == 1
    t = mock_bridge.cmd_vel_history[0]
    assert t["linear"]["x"] == 0.3


@pytest.mark.mock
@pytest.mark.asyncio
async def test_read_battery_live(mock_bridge) -> None:
    r = await yahboom_tool(operation="read_battery")
    assert r["success"] is True
    assert r["status"] == "live_data"
    assert r["result"]["percentage"] == 88.0


@pytest.mark.mock
@pytest.mark.asyncio
async def test_read_battery_offline_when_disconnected(clear_bridge) -> None:
    """Verify that we return 'offline' status, not mock data, when bridge is missing."""
    r = await yahboom_tool(operation="read_battery")
    assert r["success"] is True
    assert r["status"] == "offline"
