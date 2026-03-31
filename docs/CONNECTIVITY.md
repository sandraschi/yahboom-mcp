# Yahboom G1 Connectivity Guide

This guide explains how to connect your Yahboom G1 robot to your WiFi network and how to configure the MCP server to control it.

## 1. WiFi Setup (First Time)

By default, the Yahboom G1 Raspberry Pi is configured to start a WiFi Access Point if it cannot find a known network.

1.  **Power on the robot.** Wait about 60-90 seconds for the system to boot.
2.  **Connect to the Robot AP**: On your PC or phone, look for a WiFi network named `Yahboom_XXXX` or `ROS-XXXX`.
3.  **Default Password**: Usually `12345678` or no password.
4.  **Configure STA Mode**:
    - Open a browser and go to `http://192.168.1.1` (or the gateway IP of the robot AP).
    - Use the Yahboom web interface to enter your home WiFi credentials (SSID and Password).
    - Save and Reboot the robot.

## 2. Finding the Robot IP

Once the robot is on your home WiFi, you need its IP address.

- **Option A (Router)**: Check your router's client list for a device named `raspberrypi` or starting with `Yahboom`.
- **Option B (OLED)**: If your G1 has an OLED screen, the IP address is usually displayed there after it connects to WiFi.
- **Option C (Scan)**: Use a tool like Advanced IP Scanner or `nmap` to find the Pi on your network.

## 3. Connecting the MCP Server

The MCP server runs on your PC and connects to the robot over the network via ROSBridge (Port 9090).

### Using the Startup Script (Recommended)
Pass the robot's IP address directly to the startup script:
```powershell
./start.ps1 -RobotIP "192.168.1.100"
```

### Using Environment Variables
You can set the `YAHBOOM_IP` variable before running the server:
```powershell
$env:YAHBOOM_IP = "192.168.1.100"
uv run yahboom-mcp
```

### Using CLI Arguments
```powershell
uv run yahboom-mcp --robot-ip 192.168.1.100
```

## 4. ROSBridge at boot (no more typing start commands)

The Raspbot v2 image already has ROS 2 and rosbridge installed. Run **once** on the robot to make ROSBridge start automatically when the Pi boots:

1. Copy the script to the Pi: `scp scripts/robot/install-rosbridge-at-boot.sh pi@<robot-ip>:~/`
2. On the Pi: `sudo bash ~/install-rosbridge-at-boot.sh`
3. Reboot (or leave it). After that, power on the robot and ROSBridge is already running.

See [ROSBridge at boot](ROSBRIDGE_AT_BOOT.md) for details.

## 5. Troubleshooting

- **Ping Check**: Ensure you can `ping [robot-ip]` from your PC.
- **Port Check**: The robot must be running the `rosbridge_suite`. If the connection fails, run the one-time install above or start manually: `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`.
- **Firewall**: Ensure your PC's firewall isn't blocking outgoing connections to port 9090.
