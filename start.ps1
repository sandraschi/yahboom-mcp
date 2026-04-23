Param([switch]$Headless)

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
$WindowStyle = if ($Headless) { 'Hidden' } else { 'Normal' }
# ------------------------------

$env:FASTMCP_LOG_LEVEL = 'WARNING'
# yahboom-mcp Start — HTTP + MCP SSE on 10892 (same as webapp\start.ps1 backend).
# Do not use `python -m yahboom_mcp` here: there is no __main__, and stdio-only mode has no REST for the dashboard.
Write-Host 'Starting yahboom-mcp Unified Gateway (dual) on http://127.0.0.1:10892 ...' -ForegroundColor Cyan

Push-Location $PSScriptRoot
$env:PYTHONPATH = "src"
uv run python -m yahboom_mcp.server --mode dual --host 127.0.0.1 --port 10892
Pop-Location