# Yahboom ROS 2 MCP - SOTA 2026 Startup Script
# Author: Sandra Schipal (v1.0.0 - 2026-03-03)

Param(
    [string]$RobotIP = "localhost"
)

if ($RobotIP -ne "localhost") {
    $env:YAHBOOM_IP = $RobotIP
    Write-Host "[YAHBOOM-MCP] Target Robot IP: $RobotIP" -ForegroundColor Cyan
}

$APP_PORT = 10792
$WEBAPP_PORT = 10793

Write-Host "`n[YAHBOOM-MCP] Initializing SOTA 2026 Environment..." -ForegroundColor Cyan

# 1. Port Safety: Cull zombie processes
Write-Host "[1/4] Port Safety Check (Port $APP_PORT)..." -NoNewline
$process = Get-NetTCPConnection -LocalPort $APP_PORT -State Listen -ErrorAction SilentlyContinue
if ($process) {
    Write-Host " [ZOMBIE DETECTED]" -ForegroundColor Yellow
    Stop-Process -Id $process.OwningProcess -Force
    Write-Host "      -> Port $APP_PORT cleared." -ForegroundColor Green
}
else {
    Write-Host " [CLEAN]" -ForegroundColor Green
}

# 2. Dependency Sync
Write-Host "[2/4] Syncing Dependencies..."
uv sync --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host " [ERROR] Failed to sync dependencies." -ForegroundColor Red
    exit 1
}

# 3. Start MCP Server (Background)
Write-Host "[3/4] Starting Yahboom MCP Server on Port $APP_PORT (Dual Mode)..." -ForegroundColor Green
$env:PYTHONPATH = "src"
# Use dual mode to support both stdio and http (needed for dashboard)
$serverProc = Start-Process uv -ArgumentList "run", "yahboom-mcp", "--mode", "dual", "--port", "$APP_PORT" -NoNewWindow -PassThru

# 4. Start Dashboard UI (Background)
Write-Host "[4/4] Starting Dashboard UI on Port $WEBAPP_PORT..." -ForegroundColor Green
if (-not (Test-Path "webapp\node_modules")) {
    Write-Host "      -> node_modules missing. Running npm install..." -ForegroundColor Yellow
    Push-Location webapp
    npm install --quiet
    Pop-Location
}

Push-Location webapp
$dashboardProc = Start-Process cmd -ArgumentList "/c", "npm", "run", "dev" -NoNewWindow -PassThru
Pop-Location

Write-Host "`n[SUCCESS] Yahboom ROS 2 Fleet Integration Active." -ForegroundColor Green
Write-Host "----------------------------------------------------"
Write-Host "Server Port: $APP_PORT (MCP SSE + API)"
Write-Host "Dashboard:   http://localhost:$WEBAPP_PORT"
Write-Host "----------------------------------------------------`n"
Write-Host "Press Ctrl+C to stop both processes..."

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "`n[SHUTDOWN] Stopping processes..." -ForegroundColor Yellow
    Stop-Process -Id $serverProc.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $dashboardProc.Id -Force -ErrorAction SilentlyContinue
    Write-Host "[DONE] Cleanup complete." -ForegroundColor Green
}
