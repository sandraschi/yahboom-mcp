# ROSBridge at boot (one-time setup on the robot)

The **Raspbot v2 image already includes ROS 2 and rosbridge_suite**. You do not install packages on the bot; you only make ROSBridge **start automatically at boot**. Run the steps below once on the Pi; after that, power on the robot and ROSBridge is already running.

## One-time install on the robot (enables at-boot only)

1. Copy the install script to the robot. From your **PC** (PowerShell), with the robot's IP (e.g. 192.168.1.11 or 192.168.0.250):

   ```powershell
   scp D:\Dev\repos\yahboom-mcp\scripts\robot\install-rosbridge-at-boot.sh pi@192.168.1.11:~/
   ```

   (Use your Pi username if not `pi`, and the correct path to the script.)

2. SSH into the robot and run it **once** with sudo:

   ```bash
   ssh pi@192.168.1.11
   sudo bash ~/install-rosbridge-at-boot.sh
   ```

3. Reboot the robot (or leave it running). From then on, ROSBridge starts at boot.

## Check

On the Pi:

```bash
systemctl status rosbridge.service
```

You should see `active (running)`. Port 9090 will be listening.

On your PC, start the dashboard with the robot's IP (e.g. `.\start.ps1 -RobotIP 192.168.1.11`) and Mission Control should show **connected**.

## Disable or remove

```bash
sudo systemctl stop rosbridge.service
sudo systemctl disable rosbridge.service
```

To remove the service file: `sudo rm /etc/systemd/system/rosbridge.service` and `sudo systemctl daemon-reload`. The wrapper script remains at `/usr/local/bin/rosbridge-launch.sh` (optional: `sudo rm /usr/local/bin/rosbridge-launch.sh`).
