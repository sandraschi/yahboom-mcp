# Product Requirements Document (PRD): Robotics Fleet Expansion

## 1. Goal
Expand the single-robot MCP ecosystem into a federated robotics fleet. Enable high-density agentic workflows where specialized robots (Yahboom, Dreame, drones) collaborate through shared spatial intelligence and coordinated task allocation.

## 2. Key Features

### 2.1 Unified Fleet Registry
- Centralized registry of all available robot MCP servers.
- Dynamic capability discovery (manipulation, mapping, navigation).

### 2.2 Shared Spatial Data Pipeline
- Standardized map export (OBJ/PLY) from LIDAR-equipped robots (Dreame).
- Map ingestion by navigation-focused robots (Yahboom).
- Collaborative SLAM merging ground and aerial perspectives.

### 2.3 Intelligent Orchestration
- Multi-robot task sampling via `robotics_agentic_workflow`.
- Proximity-based telemetry and collision avoidance.
- Status-aware scheduling (battery levels, mission priority).

### 2.4 SOTA Visual Hub
- Unified dashboard showing real-time telemetry for the entire fleet.
- Multi-camera feed integration.
- 3D world view of the shared spatial map.

## 3. Success Metrics
- **Interoperability**: Successful cross-server tool calling between 3+ robots.
- **Efficiency**: 30% reduction in mapping time via collaborative SLAM.
- **Reliability**: 99.9% uptime for the fleet coordination layer.

## 4. Roadmap
- **Phase 4**: Documentation migration and Fleet Registry setup (Current).
- **Phase 5**: Cross-robot workflow implementation and sampling logic.
- **Phase 6**: Unitree Go2/G1 high-performance integration.
