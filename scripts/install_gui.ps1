# Yahboom Raspbot v2: Remote GUI Setup (Deferred)
# Usage: Run this from the project root on your Windows PC.
# This script installs XFCE4 and xrdp on the Pi at 192.168.0.250.

$PI_IP = "192.168.0.250"
$SSH_CMD = "ssh pi@$PI_IP"

Write-Host "--- Yahboom Raspbot v2 Remote GUI Setup ---" -ForegroundColor Cyan
Write-Host "Warning: This will install ~1.5GB of packages. Estimated time: 10-15 mins." -ForegroundColor Yellow

# 1. Update and Install XFCE4 + xrdp
Write-Host "[1/4] Installing XFCE4 and xrdp..." -ForegroundColor Gray
& $SSH_CMD "sudo apt update && sudo apt install -y xfce4 xfce4-goodies xrdp"

# 2. Configure xrdp to use XFCE
Write-Host "[2/4] Configuring xrdp for XFCE..." -ForegroundColor Gray
& $SSH_CMD "echo 'xfce4-session' > ~/.xsession"

# 3. Prevent 'Authentication Required' popups in Remote Desktop
Write-Host "[3/4] Tuning system policies..." -ForegroundColor Gray
& $SSH_CMD "sudo bash -c 'cat <<EOF > /etc/polkit-1/localauthority/50-local.d/45-allow-colord.pkla
[Allow Colord all Users]
Identity=unix-user:*
Action=org.freedesktop.color-manager.create-device;org.freedesktop.color-manager.create-profile;org.freedesktop.color-manager.delete-device;org.freedesktop.color-manager.delete-profile;org.freedesktop.color-manager.modify-device;org.freedesktop.color-manager.modify-profile
ResultAny=no
ResultInactive=no
ResultActive=yes
EOF'"

# 4. Set boot to GUI and restart xrdp
Write-Host "[4/4] Finalizing and Restarting services..." -ForegroundColor Gray
& $SSH_CMD "sudo systemctl set-default graphical.target"
& $SSH_CMD "sudo systemctl restart xrdp"

Write-Host "`nSetup Complete!" -ForegroundColor Green
Write-Host "You can now connect via Windows Remote Desktop (MSTSC) to $PI_IP" -ForegroundColor Cyan
