$ProjectRoot = Split-Path -Parent $PSScriptRoot

$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath

$mcpProcs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'uv.exe'" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*yahboom_mcp.server*"
}
foreach ($p in @($mcpProcs)) {
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}

if (-not (Stop-FleetPortListeners -Ports @(10892, 10893) -Label "yahboom-mcp")) { exit 1 }
