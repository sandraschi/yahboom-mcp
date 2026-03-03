# Robotics Fleet Overview

This document provides a high-level overview of the Robotics MCP ecosystem, of which `yahboom-mcp` is a core component.

## 🚀 The Vision: A Federated Robotics Fleet

The goal is to create a seamless, multi-robot coordination platform where specialized MCP servers (Yahboom, Dreame, drones, virtual bots) collaborate through shared spatial data, joint SLAM, and coordinated agentic workflows.

## 🤖 Supported Platforms

- **Yahboom ROSMASTER (Primary)**: This repository focus. ROS2-based multimodal AI robots.
- **Dreame D20 Pro**: LIDAR mapping and autonomous floorspace coverage.
- **Unity3D/VRChat**: Virtual robotics for simulation and social VR testing.
- **PX4/ArduPilot Drones**: Aerial reconnaissance and mapping.

## 🗺️ Shared Capabilities

- **LIDAR Map Sharing**: Maps from Dreame/Yahboom are shared across the fleet.
- **Collaborative SLAM**: Distributed mapping from multiple perspectives.
- **Agentic Workflows**: Cross-robot task allocation using LLM sampling.
- **Fleet Discovery**: Automatic detection of peer MCP servers via the Fleet Registry.

## 🛡️ Enterprise Crash Protection

All fleet components are protected by `watchfiles` for zero-downtime operation and automatic recovery.
