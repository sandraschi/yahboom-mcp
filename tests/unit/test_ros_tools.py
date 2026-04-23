import pytest
from httpx import AsyncClient

from yahboom_mcp.server import app, ros_restart_bringup, ros_topic_list


@pytest.mark.asyncio
async def test_ros_topic_list_tool(mock_bridge):
    """Verify ros_topic_list returns the expected topic count from the mock bridge."""
    topics = await ros_topic_list()
    assert len(topics) >= 74
    assert ["/cmd_vel", "geometry_msgs/msg/Twist"] in topics
    assert ["/scan", "sensor_msgs/msg/LaserScan"] in topics


@pytest.mark.asyncio
async def test_ros_restart_bringup_tool(mock_bridge, mock_ssh):
    """Verify ros_restart_bringup triggers the correct SSH recovery command."""
    response = await ros_restart_bringup()
    assert "Native bringup triggered" in response
    # Verify SSH execution
    mock_ssh.execute.assert_called_once()
    cmd = mock_ssh.execute.call_args[0][0]
    assert "yahboomcar_bringup" in cmd


@pytest.mark.asyncio
async def test_ros_diagnostics_api(mock_bridge):
    """Verify FastAPI diagnostics endpoint matches the bridge state."""
    from httpx import ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/diagnostics/ros/topics")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["topics"]) >= 74
