Param([switch]$Headless)

# Fast port helpers (scripts/PortHelpers.ps1)
Param([switch]$Headless)

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
# ------------------------------

$WebPort = 10892

# Clear port zombie
$procIds = Get-PortListenerPidsFast -Port $port
if ($conns) {
    $portPids = $conns.OwningProcess | Select-Object -Unique
    foreach ($pid in $portPids) {
        if ($pid -and $pid -ne 0) {
            try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch { }
        }
    }
    Start-Sleep -Seconds 1
}

$env:FASTMCP_LOG_LEVEL = 'WARNING'
$env:PYTHONPATH = "src"

Write-Host "[YAHBOOM-MCP] Starting Unified Gateway (dual) on http://127.0.0.1:${WebPort} ..." -ForegroundColor Cyan

Push-Location $PSScriptRoot
uv run python -m yahboom_mcp.server --mode dual --host 127.0.0.1 --port $WebPort
Pop-Location
_PortHelpers = Join-Path $PSScriptRoot 'scripts\PortHelpers.ps1'
if (Test-Path -LiteralPath Param([switch]$Headless)

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
# ------------------------------

$WebPort = 10892

# Clear port zombie
$procIds = Get-PortListenerPidsFast -Port $port
if ($conns) {
    $portPids = $conns.OwningProcess | Select-Object -Unique
    foreach ($pid in $portPids) {
        if ($pid -and $pid -ne 0) {
            try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch { }
        }
    }
    Start-Sleep -Seconds 1
}

$env:FASTMCP_LOG_LEVEL = 'WARNING'
$env:PYTHONPATH = "src"

Write-Host "[YAHBOOM-MCP] Starting Unified Gateway (dual) on http://127.0.0.1:${WebPort} ..." -ForegroundColor Cyan

Push-Location $PSScriptRoot
uv run python -m yahboom_mcp.server --mode dual --host 127.0.0.1 --port $WebPort
Pop-Location
_PortHelpers) { . Param([switch]$Headless)

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
# ------------------------------

$WebPort = 10892

# Clear port zombie
$procIds = Get-PortListenerPidsFast -Port $port
if ($conns) {
    $portPids = $conns.OwningProcess | Select-Object -Unique
    foreach ($pid in $portPids) {
        if ($pid -and $pid -ne 0) {
            try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch { }
        }
    }
    Start-Sleep -Seconds 1
}

$env:FASTMCP_LOG_LEVEL = 'WARNING'
$env:PYTHONPATH = "src"

Write-Host "[YAHBOOM-MCP] Starting Unified Gateway (dual) on http://127.0.0.1:${WebPort} ..." -ForegroundColor Cyan

Push-Location $PSScriptRoot
uv run python -m yahboom_mcp.server --mode dual --host 127.0.0.1 --port $WebPort
Pop-Location
_PortHelpers }

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
# ------------------------------

$WebPort = 10892

# Clear port zombie
$procIds = Get-PortListenerPidsFast -Port $port
if ($conns) {
    $portPids = $conns.OwningProcess | Select-Object -Unique
    foreach ($pid in $portPids) {
        if ($pid -and $pid -ne 0) {
            try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch { }
        }
    }
    Start-Sleep -Seconds 1
}

$env:FASTMCP_LOG_LEVEL = 'WARNING'
$env:PYTHONPATH = "src"

Write-Host "[YAHBOOM-MCP] Starting Unified Gateway (dual) on http://127.0.0.1:${WebPort} ..." -ForegroundColor Cyan

Push-Location $PSScriptRoot
uv run python -m yahboom_mcp.server --mode dual --host 127.0.0.1 --port $WebPort
Pop-Location

