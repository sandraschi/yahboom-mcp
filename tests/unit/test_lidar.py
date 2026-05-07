import os

import pytest

from yahboom_mcp.operations import lidar


@pytest.mark.asyncio
async def test_read_lidar_yahboom_connected(mock_bridge):
    mock_bridge.state["scan"] = {
        "obstacles": {"front": 1.2, "left": None},
        "nearest_m": 0.8,
        "range_max_m": 12.0,
        "num_points": 360,
    }
    result = await lidar.execute(operation="read", source="yahboom")
    assert result["success"]
    assert result["source"] == "yahboom"
    assert result["scan"]["nearest_m"] == 0.8
    assert result["scan"]["obstacles"]["front"] == 1.2


@pytest.mark.asyncio
async def test_read_lidar_yahboom_disconnected(disconnected_bridge):
    result = await lidar.execute(operation="read", source="yahboom")
    assert not result["success"]
    assert "not connected" in result["error"]


@pytest.mark.asyncio
async def test_read_lidar_auto_fallback_disconnected(disconnected_bridge):
    old_url = os.environ.pop("DREAME_MAP_URL", None)
    try:
        result = await lidar.execute(operation="read", source="auto")
        assert not result["success"]
        assert "No LIDAR source available" in result["error"]
    finally:
        if old_url:
            os.environ["DREAME_MAP_URL"] = old_url


@pytest.mark.asyncio
async def test_read_dreame_map_not_configured():
    old_url = os.environ.pop("DREAME_MAP_URL", None)
    try:
        result = await lidar.execute(operation="read_dreame_map")
        assert not result["success"]
        assert "DREAME_MAP_URL not set" in result["error"]
    finally:
        if old_url:
            os.environ["DREAME_MAP_URL"] = old_url


@pytest.mark.asyncio
async def test_read_raw_yahboom_connected(mock_bridge):
    mock_bridge.state["scan"] = {"obstacles": {}, "nearest_m": None, "range_max_m": 8.0, "num_points": 200}
    result = await lidar.execute(operation="read_raw", source="yahboom")
    assert result["success"]
    assert result["source"] == "yahboom"
    assert result["scan"]["num_points"] == 200


@pytest.mark.asyncio
async def test_read_raw_yahboom_disconnected(disconnected_bridge):
    result = await lidar.execute(operation="read_raw", source="yahboom")
    assert not result["success"]


@pytest.mark.asyncio
async def test_unknown_operation():
    result = await lidar.execute(operation="bogus")
    assert not result["success"]
    assert "Unknown operation" in result["error"]
