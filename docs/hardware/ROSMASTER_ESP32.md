# ESP32-S3 Rosmaster Co-Processor — Technical Profile

The **Yahboom Rosmaster ESP32-S3** board is the real-time "Central Nervous System" of the Raspbot v2. It bridges the high-level cognitive commands from the Raspberry Pi 5 to the low-level physical world.

## Hardware Specifications

- **Processor**: Dual-core Xtensa® 32-bit LX7 ESP32-S3 (Up to 240MHz).
- **RAM**: 512KB SRAM + 2MB/8MB PSRAM (varies by board rev).
- **Interface**: Silicon Labs CP2102 USB-to-UART (Standard serial bridge).
- **Peripherals**:
  - **Motor Control**: 4-way pulse width modulation (PWM) for DC motors + encoder feedback processing.
  - **IMU**: Integrated 6-axis MPU6050/ICM-42605 on the board.
  - **Servos**: 6-channel PWM servo interface for 2-DOF PTZ gimbal and expansion.
  - **Status LEDS**: RGB WS2812B lightstrip controller.

## Software Architecture (Micro-ROS)

The board runs a custom Micro-ROS firmware that enables the ESP32 to appear as a first-class node in the ROS 2 graph.

### Communication Interface
- **Protocol**: Micro-ROS Custom Serial Transport.
- **Baud Rate**: `921600` (High-speed handshake) or `115200` (Legacy/Debug).
- **Device Node**: `/dev/ttyUSB0` (Primary) or `/dev/ttyACM0`.

### Node Configuration
- **Node Name**: `yahboom_rosmaster` (or similar).
- **Transporters**:
  - **Static Link**: `libmicroros.a` (compiled for ESP-IDF).
  - **Agent Requirements**: Requires `micro_ros_agent` running on the Pi 5 host to bridge the serial packets to the ROS 2 DDS.

## Dual-Control Risk: "The Master Lockout"

> [!WARNING]
> The ESP32-S3 can only maintain **one** serial session at a time. If a host-side Python script (like the factory `raspbot.pyc`) claims the port, the Micro-ROS agent will fail to synchronize, leading to a "disconnected" state in the ROS 2 stack.

## Maintenance & Recovery

- **Flashing**: Firmware is typically updated via the Type-C port using the ESP-IDF `idf.py flash` command or the Yahboom serial utility.
- **Diagnostics**: If the IMU is noisy or motors drift, recalibration must be initiated via the `/yahboomcar/commands` service (if using the full factory ROS 2 stack).
