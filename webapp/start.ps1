# Yahboom ROS 2 MCP - SOTA 2026 Startup Script
# Author: Sandra Schipal (v1.2.0 - 2026-03-04)

Param(
    [string]$RobotIP = "192.168.0.250",
    [int]$BridgePort = 9090
)

$env:YAHBOOM_IP = $RobotIP
$env:YAHBOOM_BRIDGE_PORT = [string]$BridgePort
Write-Host "[YAHBOOM-MCP] Target Robot IP: $RobotIP" -ForegroundColor Cyan
Write-Host "[YAHBOOM-MCP] ROSBridge port: $BridgePort (change with start.bat <IP> <port>)" -ForegroundColor Cyan

$APP_PORT = 10892
$WEBAPP_PORT = 10893

# Helper: kill every process listening on a given port
function Clear-Port {
    param([int]$Port)
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conns) { return $false }

        foreach ($procId in $portPids) {
            if ($procId -and $procId -ne 0) {
                try {
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                    Write-Host "      -> PID $procId culled (port $Port)" -ForegroundColor Gray
                }
                catch { }
            }
        }
        # Wait for the OS to release the socket
        Start-Sleep -Seconds 1
        return $true
    }

Write-Host ""
Write-Host "[YAHBOOM-MCP] Initializing SOTA 2026 Environment..." -ForegroundColor Cyan

# 1. Port safety: cull zombies on BOTH ports
Write-Host "[1/4] Port Safety Check..." -ForegroundColor Cyan
foreach ($port in @($APP_PORT, $WEBAPP_PORT)) {
    Write-Host "      Port $port ..." -NoNewline
    $killed = Clear-Port -Port $port
    if ($killed) {
        Write-Host " [ZOMBIE(S) CLEARED]" -ForegroundColor Yellow
    }
    else {
        Write-Host " [CLEAN]" -ForegroundColor Green
    }
}

# 2. Dependency sync
Write-Host "[2/4] Syncing Python dependencies..." -ForegroundColor Cyan
Push-Location ..
uv sync --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] uv sync failed." -ForegroundColor Red
    exit 1
}
Pop-Location

# 3. Start MCP backend (use splatting -- no backtick line continuation)
Write-Host "[3/4] Starting Yahboom MCP Server on port $APP_PORT (dual mode)..." -ForegroundColor Green
Push-Location ..
$env:PYTHONPATH = "src"
$serverArgs = @("run", "python", "-m", "yahboom_mcp.server", "--mode", "dual", "--host", "127.0.0.1", "--port", "$APP_PORT")
$serverProc = Start-Process uv -ArgumentList $serverArgs -NoNewWindow -PassThru
Pop-Location

# 4. Start Vite dashboard
if (-not (Test-Path "node_modules")) {
    Write-Host "      node_modules missing -- running npm install..." -ForegroundColor Yellow
    cmd /c npm install --quiet --legacy-peer-deps
}
$dashboardProc = Start-Process cmd -ArgumentList "/c", "npm", "run", "dev" -NoNewWindow -PassThru

Write-Host ""
Write-Host "[SUCCESS] Yahboom ROS 2 Fleet Integration Active." -ForegroundColor Green
Write-Host "----------------------------------------------------"
Write-Host "  Backend:   http://localhost:$APP_PORT  (MCP SSE + REST API)"
Write-Host "  Dashboard: http://localhost:$WEBAPP_PORT"
Write-Host "  Swagger:   http://localhost:$APP_PORT/docs"
Write-Host "  ROSBridge: ${RobotIP}:${BridgePort}  (robot must have rosbridge running)"
Write-Host "----------------------------------------------------"
Write-Host "If ROSBridge fails: on robot run 'ros2 launch rosbridge_server rosbridge_websocket_launch.xml' (default 9090). Try: start.bat $RobotIP 9091"
Write-Host "Press Ctrl+C to stop all processes..."

# 5. Open browser (give Vite 2 seconds to initialize the proxy)
Start-Sleep -Seconds 2
Start-Process "http://localhost:$WEBAPP_PORT"

try {
    while ($true) { Start-Sleep -Seconds 1 }
}
finally {
    Write-Host ""
    Write-Host "[SHUTDOWN] Stopping processes..." -ForegroundColor Yellow
    Stop-Process -Id $serverProc.Id    -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $dashboardProc.Id -Force -ErrorAction SilentlyContinue
    Write-Host "[DONE] Cleanup complete." -ForegroundColor Green
}
