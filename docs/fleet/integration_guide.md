# Integration Guide: Cross-Robot Workflows

## 1. Fleet Discovery Integration

All servers must register themselves in the central `fleet-registry.json`.

```json
{
  "id": "yahboom-mcp",
  "name": "Yahboom ROSMASTER MCP",
  "type": "physical_robot",
  "url": "http://localhost:10760",
  "capabilities": ["manipulation", "camera", "navigation"]
}
```

## 2. Using Cross-Server Tools

To call a tool on another fleet member, use the `call_peer_tool` pattern:

```python
# From Yahboom-MCP calling Dreame-MCP
result = await call_peer_tool("dreame-mcp", "get_map", {"robot_id": "vacuum_01"})
```

## 3. Spatial Data Sharing

Maps exported from `dreame-control` should be saved to the shared documentation directory for processing by `yahboom-navigation`.

## 4. OSC Synchronization

Use the standard OSC address space for real-time telemetry:
- `/robot/{id}/telemetry`
- `/robot/{id}/path`
- `/robot/{id}/status`
