# Robotics Fleet Overview

This document provides a high-level overview of the Robotics MCP ecosystem, of which `yahboom-mcp` is a core component.

## 🚀 The Vision: A Federated Robotics Fleet

The goal is to create a seamless, multi-robot coordination platform where specialized MCP servers (Yahboom, Dreame, drones, virtual bots) collaborate through shared spatial data, joint SLAM, and coordinated agentic workflows.

## 🤖 Supported Platforms

- **Yahboom Raspbot v2 (Boomy)**: The entry-level multimodal AI robot car (~1.0kg, ~$300).
- **Yahboom DOFBOT**: The affordable 6-DOF "Pure Arm" alternative (~$340) for stationary manipulation and computer vision research.
- **Yahboom ROSMASTER X3 PLUS**: The professional scaling path with LiDAR and 6-DOF arm (See [Scaling to X3 PLUS](SCALING_TO_X3_PLUS.md)).
- **Dreame D20 Pro**: LIDAR mapping and autonomous floorspace coverage.
- **Unity3D/VRChat**: Virtual robotics for simulation and social VR testing.

## 🧪 Experimental Branch (SOTA v16.15)
Research-grade hardware configurations currently in Virtual Twin development:
- [Butlerbot v0.1](../experimental/BUTLERBOT_V0.1.md): Mobile manipulation (Bumi + DOFBOT).
- [Battlebot v0.1](../experimental/BATTLEBOT_V0.1.md): Defensive/Culinary "Dark Bumi" prototype.
- **PX4/ArduPilot Drones**: Aerial reconnaissance and mapping.

## 🗺️ Shared Capabilities

- **LIDAR Map Sharing**: Maps from Dreame/Yahboom are shared across the fleet.
- **Collaborative SLAM**: Distributed mapping from multiple perspectives.
- **Agentic Workflows**: Cross-robot task allocation using LLM sampling.
- **Fleet Discovery**: Automatic detection of peer MCP servers via the Fleet Registry.

## 🛡️ Enterprise Crash Protection

All fleet components are protected by `watchfiles` for zero-downtime operation and automatic recovery.
