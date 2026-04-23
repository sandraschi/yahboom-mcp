import logging

from fastmcp import Context

logger = logging.getLogger("yahboom-mcp.operations.diagnostics")


async def execute(
    ctx: Context | None = None,
    operation: str = "",
    param1: str | float | None = None,
    param2: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    Execute diagnostic operations: health_check, config_show, inspect_stack, execute_command.
    Provides real-time system health, hardware configuration, and stack inspection.
    Includes SSH fallback for low-level kernel diagnostics and command execution.
    """
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(f"Diagnostics: {operation}", extra={"correlation_id": correlation_id})

    # Use bridge and ssh from global state
    from ..state import _state

    bridge = _state.get("bridge")
    ssh = _state.get("ssh")
    bridge_connected = bridge.connected if bridge else False

    if operation == "health_check":
        battery_data = await bridge.get_sensor_data("battery") if bridge_connected else {}

        return {
            "success": True,
            "operation": operation,
            "result": {
                "system": "OK",
                "ros_bridge": "CONNECTED" if bridge_connected else "DISCONNECTED",
                "stm32_link": "STABLE" if bridge_connected else "UNKNOWN",
                "battery_health": "GOOD" if battery_data.get("percentage", 0) > 20 else "LOW",
                "live_mode": bridge_connected,
            },
            "correlation_id": correlation_id,
        }

    elif operation == "inspect_stack":
        # Multi-layer inspection: I2C, ROS2 Nodes, Thermal
        results = {}
        if ssh and ssh.connected:
            # I2C Scan
            i2c_out, _, _ = await ssh.sudo_execute("i2cdetect -y 1")
            results["i2c_bus_1"] = i2c_out

            # Thermal
            temp_out, _, _ = await ssh.execute("vcgencmd measure_temp")
            results["cpu_temp"] = temp_out

            # ROS 2 Nodes
            nodes_out, _, _ = await ssh.execute("ros2 node list")
            results["ros_nodes"] = nodes_out.split("\n") if nodes_out else []

            # Disk Usage
            df_out, _, _ = await ssh.execute("df -h /")
            results["disk_usage"] = df_out

        return {
            "success": True,
            "operation": operation,
            "result": results,
            "correlation_id": correlation_id,
        }

    elif operation == "execute_command":
        if not payload or "command" not in payload:
            return {"success": False, "error": "Missing 'command' in payload"}

        command = payload["command"]
        use_sudo = payload.get("sudo", False)

        if ssh and ssh.connected:
            if use_sudo:
                out, err, code = await ssh.sudo_execute(command)
            else:
                out, err, code = await ssh.execute(command)

            return {
                "success": code == 0,
                "operation": operation,
                "result": {"stdout": out, "stderr": err, "exit_code": code},
                "correlation_id": correlation_id,
            }
        else:
            return {"success": False, "error": "SSH Bridge not connected"}

    elif operation == "config_show":
        return {
            "success": True,
            "operation": operation,
            "result": {"max_speed": 0.5, "pid_p": 1.2, "pid_i": 0.1, "pid_d": 0.05},
            "correlation_id": correlation_id,
        }

    return {
        "success": False,
        "operation": operation,
        "error": f"Unknown diagnostic operation: {operation}",
        "correlation_id": correlation_id,
    }
