# Legacy Factory Demo Audit (Bypass Mode)

This document records the discovery of the host-level Python demo that enabled hardware control independently of the ROS 2 / Docker environment.

## Overview

- **Binary Location**: `/home/pi/project_demo/raspbot/raspbot.pyc`
- **Secondary Discovery**: `/home/pi/project_demo/raspbot/yb-discover.py`
- **Runtime Environment**: Python 3.x on the Raspberry Pi 5 host.
- **Role**: Provides a direct serial link to the ESP32-S3 co-processor, enabling wheels, lightstrip, and camera streaming without requiring a ROS 2 graph.

## Communication Pattern (Observed)

The `raspbot.pyc` process (PID 1359) maintains an exclusive lock on `/dev/ttyUSB0`. It sends byte-coded commands for:
- **Velocity**: Mapping UI joystick inputs to motor RPM.
- **RGB Control**: Sending color hex codes to the onboard WS2812B strip.
- **Camera**: Spawning a local V4L2 stream.

## Deactivation Protocol

To transition to the ROS 2 SOTA control plane, this demo must be halted to release the serial hardware.

1. **Stop the process**:
   ```bash
   sudo pkill -f raspbot.pyc
   ```
2. **Verify Serial Port Ownership**:
   ```bash
   sudo fuser /dev/ttyUSB0
   ```
   (Should return no output).

## Archival Note

> [!NOTE]
> Do NOT delete the `project_demo` directory. It serves as our "Hardware Baseline." If ROS 2 connectivity is lost, this demo can be restarted to verify that the ESP32 and physical motors are still operational.
