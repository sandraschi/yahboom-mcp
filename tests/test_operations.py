import asyncio

from yahboom_mcp.portmanteau import yahboom_tool


async def test_operations():
    print("--- Testing Yahboom MCP Operations ---")

    # Test Diagnostics
    print("\n[DIAGNOSTICS] health_check:")
    result = await yahboom_tool(operation="health_check")
    print(result)

    # Test Sensors
    print("\n[SENSORS] read_battery:")
    result = await yahboom_tool(operation="read_battery")
    print(result)

    # Test Motion
    print("\n[MOTION] forward:")
    # Using param1 for speed as per current implementation
    result = await yahboom_tool(operation="forward", param1=0.5)
    print(result)

    print("\n--- Test Completed ---")


if __name__ == "__main__":
    asyncio.run(test_operations())
