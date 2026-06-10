param(
    [switch]$Headless,
    [switch]$ReuseIfRunning
)

$ProjectRoot = $PSScriptRoot
$WebPort = 10892

$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
$FleetStart = Initialize-FleetStartMode @PSBoundParameters
Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly

$portResolve = @{
    Ports      = @($WebPort)
    Label      = "yahboom-mcp"
    AllowReuse = $ReuseIfRunning
}
if ($ReuseIfRunning) {
    $portResolve.HealthChecks = @{
        $WebPort = "http://127.0.0.1:$WebPort/api/v1/health"
    }
}
$portState = Resolve-FleetPortConflict @portResolve
if ($portState.Action -eq 'Blocked') { exit 1 }
if ($portState.Reuse) { return }

$env:FASTMCP_LOG_LEVEL = 'WARNING'
$env:PYTHONPATH = "src"

Write-Host "[YAHBOOM-MCP] Starting Unified Gateway (dual) on http://127.0.0.1:${WebPort} ..." -ForegroundColor Cyan

Push-Location $PSScriptRoot
uv run python -m yahboom_mcp.server --mode dual --host 127.0.0.1 --port $WebPort
Pop-Location
