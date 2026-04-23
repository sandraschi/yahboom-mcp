# Yahboom ROS 2 MCP - SOTA 2026 Startup Script
# Author: Sandra Schipal (v1.2.0 - 2026-03-04)

Param(
    [Parameter(Position = 0)]
    [string]$RobotIP = "192.168.1.11",
    [Parameter(Position = 1)]
    [int]$BridgePort = 9090,
    [Parameter(Position = 2)]
    [string]$FallbackIP = "",
    [switch]$Headless
)

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
$WindowStyle = if ($Headless) { 'Hidden' } else { 'Normal' }
# ------------------------------

$env:YAHBOOM_IP = $RobotIP
$env:YAHBOOM_BRIDGE_PORT = [string]$BridgePort
$env:YAHBOOM_FALLBACK_IP = $FallbackIP
Write-Host "[YAHBOOM-MCP] Target Robot IP: $RobotIP" -ForegroundColor Cyan
Write-Host "[YAHBOOM-MCP] ROSBridge port: $BridgePort (start.bat <IP> <port> [fallback_ip])" -ForegroundColor Cyan
if ($FallbackIP) {
    Write-Host "[YAHBOOM-MCP] Fallback (ethernet recovery): $FallbackIP" -ForegroundColor DarkGray
}

$APP_PORT = 10892
$WEBAPP_PORT = 10893

# Helper: kill every process listening on a given port
function Clear-Port {
    param([int]$Port)
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conns) { return $false }

    $portPids = $conns.OwningProcess | Select-Object -Unique
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

# 1. Port safety: cull zombies on BOTH ports and kill any existing MCP server processes
Write-Host "[1/4] Port Safety & Process Cleanup..." -ForegroundColor Cyan

# Kill any existing uv/python processes running the yahboom_mcp server module (to clear ghost stdio instances)
$mcpProcs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'uv.exe'" -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -like "*yahboom_mcp.server*" 
}
if ($mcpProcs) {
    Write-Host "      Found $($mcpProcs.Count) ghost MCP processes. Cleaning up..." -ForegroundColor Yellow
    foreach ($p in $mcpProcs) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

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
Push-Location "$PSScriptRoot/.."
uv sync --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] uv sync failed." -ForegroundColor Red
    exit 1
}
Pop-Location

# 3. Start MCP backend (use splatting -- no backtick line continuation)
Write-Host "[3/4] Starting Yahboom MCP Server on port $APP_PORT (dual mode)..." -ForegroundColor Green
Push-Location "$PSScriptRoot/.."
$env:PYTHONPATH = "src"
$serverArgs = @("run", "python", "-m", "yahboom_mcp.server", "--mode", "dual", "--host", "127.0.0.1", "--port", "$APP_PORT")
$serverProc = Start-Process uv -ArgumentList $serverArgs -NoNewWindow -PassThru
Pop-Location

# 4. Start Vite dashboard (always use webapp folder — npm cwd was wrong when script invoked from repo root)
if (-not (Test-Path (Join-Path $PSScriptRoot "node_modules"))) {
    Write-Host "      node_modules missing -- running npm install..." -ForegroundColor Yellow
    Start-Process cmd -WorkingDirectory $PSScriptRoot -ArgumentList "/c", "npm", "install", "--quiet", "--legacy-peer-deps" -Wait -NoNewWindow
}
$dashboardProc = Start-Process cmd -WorkingDirectory $PSScriptRoot -ArgumentList "/c", "npm", "run", "dev" -NoNewWindow -PassThru

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

# 4b. Launch background task to open browser once frontend is ready (Auto-opened by Antigravity)
$frontendUrl = "http://127.0.0.1:$WEBAPP_PORT/"
$pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen

    while ($true) { Start-Sleep -Seconds 1 }
}
finally {
    Write-Host ""
    Write-Host "[SHUTDOWN] Stopping processes..." -ForegroundColor Yellow
    Stop-Process -Id $serverProc.Id    -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $dashboardProc.Id -Force -ErrorAction SilentlyContinue
    Write-Host "[DONE] Cleanup complete." -ForegroundColor Green
}



