from fastmcp import FastMCP


def register_prompts(app: FastMCP):
    """Register native SOTA 2026 prompts for robot orchestration."""

    @app.prompt()
    def yahboom_quick_start(robot_ip: str = "localhost") -> str:
        """Step-by-step instructions to connect and run the Yahboom Raspbot v2."""
        return f"""You are helping set up the Yahboom Raspbot v2 ROS 2 MCP server.

1. Ensure the robot is powered and on the same LAN. ROSBridge must be running on the robot (e.g. `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`).
2. Set YAHBOOM_IP={robot_ip} (or the robot's actual IP) and start the server: `uv run python -m yahboom_mcp.server --mode dual --port 10792`.
3. Open the dashboard at http://localhost:10793. Use Mission Control for telemetry and the Chat page for natural-language commands.
4. From an MCP client (Cursor, Claude Desktop), use the yahboom tool with operation=health_check first, then motion operations (forward, backward, turn_left, turn_right, stop).
5. For high-level goals use the yahboom_agentic_workflow tool with a natural-language goal."""

    @app.prompt()
    def yahboom_patrol(duration_seconds: str = "10") -> str:
        """Generate a patrol plan for the Yahboom robot (e.g. square or figure-8)."""
        return f"""Plan a safe patrol for the Yahboom G1 robot lasting about {duration_seconds} seconds.

Use the yahboom_agentic_workflow tool with a goal like: "Patrol in a square: move forward 2 seconds, turn left 90 degrees, repeat 4 times, then stop and report battery."
Or use individual yahboom(operation=...) calls for forward, turn_left, turn_right, stop. Always check health first."""

    @app.prompt()
    def yahboom_diagnostics() -> str:
        """Get a diagnostic checklist for the Yahboom robot and MCP server."""
        return """Run a quick diagnostic on the Yahboom setup:

1. Call yahboom(operation='health_check') to see ROS bridge connection and battery.
2. If connected, call yahboom(operation='read_imu') for orientation and yahboom(operation='read_battery') for power.
3. Check the dashboard at http://localhost:10793 (Mission Control) for live telemetry and the 3D Viz page.
4. If bridge is disconnected, verify YAHBOOM_IP, robot power, and rosbridge_server on the robot."""

    @app.prompt()
    def yahboom_patrol_apartment() -> str:
        """Standard action: patrol the apartment (full circuit of main rooms, avoid obstacles)."""
        return """Execute a patrol of the apartment with the Yahboom Raspbot v2 robot.

1. Call yahboom(operation='health_check') and ensure battery is sufficient (> 20%).
2. Use yahboom_agentic_workflow with a goal like: "Patrol the apartment: do a full circuit of the main rooms. Move forward along walls, turn at corners, avoid obstacles using LIDAR/common sense. Return to the starting position and stop. Report battery when done."
3. Alternatively use a sequence of yahboom(operation='forward', param1=duration), yahboom(operation='turn_left'|'turn_right', param1=duration), and lidar(operation='read') to check obstacles."""

    @app.prompt()
    def yahboom_go_to_recharge() -> str:
        """Standard action: drive to charging station and stop."""
        return """Send the Yahboom Raspbot v2 robot to the charging station.

1. Call yahboom(operation='health_check'). If battery is critical (< 15%), prioritise a short path to the dock.
2. Use yahboom_agentic_workflow with a goal like: "Go to recharge: drive to the charging station and stop. Position the robot so it is aligned with the dock. (Contactless recharger will be equipped later; for now just stop at the dock.)"
3. If the dock position is known (fixed coordinates or landmark), you can use a sequence of forward/turn/strafe and stop. Otherwise instruct the user to guide the robot manually." """
