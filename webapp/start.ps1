param(
    [Parameter(Position = 0)]
    [string]$RobotIP = "192.168.1.11",
    [Parameter(Position = 1)]
    [int]$BridgePort = 9090,
    [Parameter(Position = 2)]
    [string]$FallbackIP = "",
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser,
    [switch]$ReuseIfRunning
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$APP_PORT = 10892
$WEBAPP_PORT = 10893

$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
$FleetStart = Initialize-FleetStartMode @PSBoundParameters
Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly:$BackendOnly

$portResolve = @{
    Ports      = @($APP_PORT, $WEBAPP_PORT)
    Label      = "yahboom-mcp"
    AllowReuse = $ReuseIfRunning
}
if ($ReuseIfRunning) {
    $portResolve.HealthChecks = @{
        $APP_PORT     = "http://127.0.0.1:$APP_PORT/api/v1/health"
        $WEBAPP_PORT  = "http://127.0.0.1:$WEBAPP_PORT/"
    }
}
$portState = Resolve-FleetPortConflict @portResolve
if ($portState.Action -eq 'Blocked') { exit 1 }
if ($portState.Reuse) {
    if (-not $FleetStart.SkipBrowser -and $FleetStart.RunFrontend) {
        Start-Process "http://127.0.0.1:$WEBAPP_PORT/"
    }
    return
}

# Yahboom ROS 2 MCP - SOTA 2026 Startup Script
$env:YAHBOOM_BRIDGE_PORT = [string]$BridgePort
$env:YAHBOOM_FALLBACK_IP = $FallbackIP
Write-Host "[YAHBOOM-MCP] Target Robot IP: $RobotIP" -ForegroundColor Cyan
Write-Host "[YAHBOOM-MCP] ROSBridge port: $BridgePort (start.bat <IP> <port> [fallback_ip])" -ForegroundColor Cyan
if ($FallbackIP) {
    Write-Host "[YAHBOOM-MCP] Fallback (ethernet recovery): $FallbackIP" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "[YAHBOOM-MCP] Initializing SOTA 2026 Environment..." -ForegroundColor Cyan

Write-Host "[1/4] Process cleanup..." -ForegroundColor Cyan
$mcpProcs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'uv.exe'" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*yahboom_mcp.server*"
}
if ($mcpProcs) {
    Write-Host "      Found $($mcpProcs.Count) ghost MCP processes. Cleaning up..." -ForegroundColor Yellow
    foreach ($p in $mcpProcs) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
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

if (-not $FleetStart.RunFrontend) {
    try { while ($true) { Start-Sleep -Seconds 1 } } finally { Stop-Process -Id $serverProc.Id -Force -ErrorAction SilentlyContinue }
    return
}

# 4. Start Vite dashboard (always use webapp folder - npm cwd was wrong when script invoked from repo root)
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

# 5. Open browser once frontend is reachable (polling, not fixed sleep)
if (-not $FleetStart.SkipBrowser) {
    $frontendUrl = "http://127.0.0.1:$WEBAPP_PORT/"
    $pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
    Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen
}

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
