# Yahboom ROS 2 MCP - SOTA 2026 Startup Script
# Author: Sandra Schipal (v1.2.0 - 2026-03-04)

Param(
    [string]$RobotIP = "localhost"
)

if ($RobotIP -ne "localhost") {
    $env:YAHBOOM_IP = $RobotIP
    Write-Host "[YAHBOOM-MCP] Target Robot IP: $RobotIP" -ForegroundColor Cyan
}

$APP_PORT = 10792
$WEBAPP_PORT = 10793

# Helper: kill every process listening on a given port
function Clear-Port {
    param([int]$Port)
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conns) { return $false }

    $portPids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $portPids) {
        if ($procId -and $procId -ne 0) {
            try {
                Stop-Process -Id $procId -Force -ErrorAction Stop
                Write-Host "      -> PID $procId killed (port $Port)" -ForegroundColor DarkGray
            }
            catch {
                Write-Host "      -> PID $procId could not be killed" -ForegroundColor DarkYellow
            }
        }
    }
    Start-Sleep -Milliseconds 400
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
$serverArgs = @("run", "python", "-m", "yahboom_mcp.server", "--mode", "dual", "--port", "$APP_PORT")
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
Write-Host "----------------------------------------------------"
Write-Host "Press Ctrl+C to stop all processes..."

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
