# One-time setup: copy install script to Raspbot v2 and run it so ROSBridge starts at boot.
# Usage: .\Install-RosbridgeOnRobot.ps1 [-RobotIP 192.168.1.11] [-User pi] [-Reboot]
# You will be prompted for the Pi user password (unless you use SSH keys).

param(
    [string]$RobotIP = "192.168.1.11",
    [string]$User = "pi",
    [switch]$Reboot
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$InstallScript = Join-Path $RepoRoot "scripts\robot\install-rosbridge-at-boot.sh"

if (-not (Test-Path $InstallScript)) {
    Write-Host "[ERROR] Not found: $InstallScript" -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Copying install script to ${User}@${RobotIP}..." -ForegroundColor Cyan
scp $InstallScript "${User}@${RobotIP}:~/install-rosbridge-at-boot.sh"
if (-not $?) {
    Write-Host "[ERROR] SCP failed. Is the robot on and reachable? ping $RobotIP" -ForegroundColor Red
    exit 1
}

Write-Host "[2/3] Running install on robot (sudo - you may be prompted for password)..." -ForegroundColor Cyan
ssh "${User}@${RobotIP}" "sudo bash ~/install-rosbridge-at-boot.sh"
if (-not $?) {
    Write-Host "[ERROR] SSH or install failed." -ForegroundColor Red
    exit 1
}

Write-Host "[SUCCESS] ROSBridge service installed and started on the robot." -ForegroundColor Green
if ($Reboot) {
    Write-Host "[3/3] Rebooting robot..." -ForegroundColor Cyan
    ssh "${User}@${RobotIP}" "sudo reboot"
    Write-Host "Robot rebooting. Wait ~60s then start the dashboard with: .\start.ps1 -RobotIP $RobotIP" -ForegroundColor Yellow
} else {
    Write-Host "[3/3] Skip reboot. To reboot later: ssh ${User}@${RobotIP} 'sudo reboot'" -ForegroundColor Gray
    Write-Host "Start the dashboard with: .\start.ps1 -RobotIP $RobotIP" -ForegroundColor Yellow
}
