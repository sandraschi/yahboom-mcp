# Boomy Sensory Hub (RPi 5 Expansion)

Boomy's sensory substrate is expanded via a local bridge running on the Raspberry Pi 5. This allows for high-frequency polling of physical buttons, ultrasound distance sensors, and infrared cliff/line sensors.

## 🛰️ Technical Specification

### ROS 2 Topics

| Topic | Message Type | Purpose | Source |
|-------|--------------|---------|--------|
| `/sonar` | `sensor_msgs/Range` | Ultrasound distance (metres) | RPi 5 Bridge |
| `/infrared_line` | `std_msgs/Int32MultiArray` | [Left, Mid, Right] IR sensors (0=Void, 1=Line) | Transferred from STM32 → RPi 5 |
| `/button` | `std_msgs/Bool` | Top-mounted "KEY" button state (True=Pressed) | RPi 5 GPIO 18 |

### Hardware Mapping (RPi 5 GPIO)

| Peripheral | Board Pin | GPIO (BCM) | Logic |
|------------|-----------|------------|-------|
| **KEY Button** | Pin 12 | GPIO 18 | Pull-Up / Active Low |

## 🚀 Deployment (Robot-Side)

The bridge is implemented in `scripts/robot/peripheral_bridge.py`. It should be deployed to the robot and managed via `systemd`.

### Manual Startup
```bash
python3 ~/yahboom-mcp/scripts/robot/peripheral_bridge.py
```

### Automation (systemd)
Deploy the service file to allow Boomy's senses to start on boot:

```bash
# 1. Copy service file
sudo cp ~/yahboom-mcp/scripts/robot/yahboom-peripheral-bridge.service /etc/systemd/system/

# 2. Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable yahboom-peripheral-bridge.service
sudo systemctl start yahboom-peripheral-bridge.service
```

## 🛠️ Auto-Discovery
The `peripheral_bridge.py` includes a lightweight I2C scanning module that identifies:
- **SSD1306 / SH1106**: OLED displays (typically 0x3C).
- **BME280 / SGP40**: Environmental sensors (coming soon).

> [!NOTE]
> Ensure the `lgpio` library is installed on your Pi 5 for robust GPIO interaction without relying on legacy `RPi.GPIO` sysfs.
