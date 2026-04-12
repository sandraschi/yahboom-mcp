# Fleet Scaling: ROSMASTER X3 PLUS

As your robotics requirements evolve from basic demonstration and vision testing (Boomy/Raspbot v2) to complex manipulation and industrial-grade research, the **ROSMASTER X3 PLUS** is the recommended SOTA progression path.

## 🏎️ Hardware Specifications

| Component | Raspbot v2 (Boomy) | ROSMASTER X3 PLUS |
| :--- | :--- | :--- |
| **Logic Core** | Raspberry Pi 5 (16GB) | NVIDIA Jetson Orin NX (8GB/16GB) |
| **Motion** | Mecanum Wheels | Omnidirectional / Mecanum Hybrid |
| **Manipulation** | None (Shrouded) | **6-DOF Mechanical Arm** |
| **Sensors** | Ultrasonic + Camera | **LiDAR** + Depth Camera + 10-axis IMU |
| **Weight** | ~1.0 kg | ~3.5 kg |
| **Payload Capacity** | < 0.5 kg | ~5.0 kg |
| **Price Point** | ~$300 (w/ Pi 5) | ~$1,200 - $1,500 |

## 🕹️ Key Advantages for Agentic Fleets

1.  **Inverse Kinematics (IK)**: The 6-DOF arm allows for complex object manipulation (grabbing, sorting, stacking) powered by the MoveIt! ROS 2 stack.
2.  **3D SLAM**: Integrated LiDAR enables high-fidelity 3D mapping and autonomous navigation in dynamic environments.
3.  **High-Level Inference**: The Jetson Orin NX delivers massive GPU acceleration for running larger LLMs and real-time YOLOv8 vision models directly on the "edge".
4.  **Power Delivery**: Industrial-grade battery management system (BMS) for extended high-load research sessions.

## 🏗️ Integration Protocol

Our unified MCP Server architecture is designed to scale horizontally to the X3 PLUS. The `yahboom-mcp` stack can be deployed to the Jetson Orin with minimal configuration adjustments to the node graph, allowing for a seamless transition from Boomy to the "Heavy Duty" fleet.
