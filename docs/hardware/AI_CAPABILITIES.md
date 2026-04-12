# AI & Vision Capabilities: ROS 2 on Raspberry Pi 5 (16GB)

The combination of **ROS 2 Humble**, a **Raspberry Pi 5 (16GB)**, and the **Yahboom Raspbot v2** hardware provides a surprisingly powerful platform for local AI and advanced computer vision.

## 1. Local LLMs (The "Voice/Brain" of the Bot)

With 16GB of RAM, your Pi 5 can run several modern "Small Language Models" (SLMs) entirely offline.

| Model | Size | Speed (approx) | Capability |
| :--- | :--- | :--- | :--- |
| **Gemma 2 2B** | 2.6GB | 10-15 tokens/sec | Very fast, good for basic intent extraction. |
| **Phi-3 Mini** | 2.3GB | 8-12 tokens/sec | Excellent reasoning for its size. |
| **Llama 3 8B** | 4.7GB | 2-4 tokens/sec | Smarter, but slower. Good for complex dialogue. |
| **Llama 3 1B** | 0.8GB | 20+ tokens/sec | Blazing fast for simple command parsing. |

### How to use with ROS 2:
Use the `ollama` ROS 2 node or a custom Python node that calls a `llama.cpp` backend. You can feed robot sensor data (IMU, battery, Lidar) into the LLM as part of the system prompt to give it "physical awareness."

## 2. Advanced Video Processing

Pi 5 is significantly faster than Pi 4 at image handling. ROS 2 provides the `cv_bridge` package to pass video frames into **OpenCV**.

### Face Recognition & Tracking
- **Frameworks**: `Mediapipe` (Google) or `Dlib`.
- **Performance**:
    - **Face Detection**: Fast (30+ FPS).
    - **Face Recognition**: Good (5-15 FPS).
    - **Gesture Control**: Hand tracking is very efficient on Pi 5.
- **Workflow**: A ROS 2 node subscribes to `/camera/image_raw`, performs recognition, and publishes coordinate data to `/cmd_vel` to follow a specific person.

## 3. Computer Vision (CV) Tools

ROS 2 integrates natively with:
- **YoloV8/V10**: Real-time object detection (detecting "coffee mugs", "chairs", "people").
- **OpenCV**: Standard filtering, edge detection, and line following.
- **ALVAR / AprilTags**: High-precision marker tracking for docking or specialized navigation.

## 4. Why ROS 2 is "Powerful"

ROS 2 isn't just about running code; it's about **distributed coordination**:
1.  **Node Isolation**: Your LLM can run in one process, Face Recognition in another, and Motor Control in a third. If the LLM crashes, the robot can still "Stop" safely.
2.  **DDS Transport**: It handles the complexities of networking. You could run the heavy LLM on your **PC** and the Face Detection on the **Pi**, and ROS 2 makes them talk as if they were in the same script.
3. **Standardization**: Every robot uses the same messages (`sensor_msgs/Image`, `geometry_msgs/Twist`). You can swap a Yahboom Raspbot v2 for another ROS 2 platform, and your high-level AI code stays the same.

## 5. Summary: Coffee Shop Scenario
For a "Coffee Shop" bot, you would likely use:
- **Local Vision**: Raspberry Pi 5 (Face recognition of customers).
- **Local Nav**: Raspberry Pi 5 (Lidar-based SLAM).
- **Voice/Brain**: Central PC (Large LLM for conversation via WiFi) **OR** local Phi-3 (if offline).
