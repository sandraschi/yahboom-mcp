# Example: ensure server is running, then instruct user to use Chat or MCP client
# to run yahboom_agentic_workflow with goal "Patrol in a square: forward 2s, turn left, repeat 4 times, stop."

$ErrorActionPreference = "Stop"
$base = if ($env:YAHBOOM_API_URL) { $env:YAHBOOM_API_URL } else { "http://localhost:10792" }

Write-Host "[YAHBOOM] Checking server at $base ..." -ForegroundColor Cyan
try {
    $r = Invoke-RestMethod -Uri "$base/api/v1/health" -Method Get -TimeoutSec 3
    if ($r.connected) {
        Write-Host "[OK] Server connected to robot." -ForegroundColor Green
    } else {
        Write-Host "[WARN] Server up but robot bridge disconnected." -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERROR] Server not reachable. Start with: uv run python -m yahboom_mcp.server --mode dual --port 10792" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "To run a square patrol, use the MCP client (Cursor / Claude Desktop) and call:"
Write-Host "  yahboom_agentic_workflow(goal='Patrol in a square: move forward 2 seconds, turn left 90 degrees, repeat 4 times, then stop and report battery.')"
Write-Host ""
Write-Host "Or open the dashboard Chat at http://localhost:10793/chat and type the same goal." -ForegroundColor Cyan
