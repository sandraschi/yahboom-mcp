# Yahboom ROS 2 MCP - SOTA 2026 Startup Script
# Author: Sandra Schipal (v1.0.0 - 2026-03-03)

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
Write-Host "[3/4] Starting Yahboom MCP Server on Port $APP_PORT..." -ForegroundColor Green
$env:PYTHONPATH = "src"
Start-Process uv -ArgumentList "run", "yahboom-mcp" -NoNewWindow -PassThru

# 4. Webapp Handshake (Future Phase 3 integration)
Write-Host "[4/4] Note: Dashboard UI (Port $WEBAPP_PORT) is in scaffold phase." -ForegroundColor Gray

Write-Host "`n[SUCCESS] Yahboom ROS 2 Fleet Integration Active." -ForegroundColor Green
Write-Host "----------------------------------------------------"
Write-Host "Server Port: $APP_PORT"
Write-Host "Dashboard: http://localhost:$WEBAPP_PORT"
Write-Host "----------------------------------------------------`n"
