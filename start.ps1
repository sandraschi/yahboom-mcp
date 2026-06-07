
# Fast port helpers (scripts/PortHelpers.ps1)
$__PortHelpers = Join-Path $PSScriptRoot 'scripts\PortHelpers.ps1'
if (Test-Path -LiteralPath $__PortHelpers) { . $__PortHelpers }
Param([switch]$Headless)  # --- SOTA Headless Standard --- if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {     Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden     exit } # ------------------------------  $WebPort = 10892  # Clear port zombie $procIds = Get-PortListenerPidsFast -Port $port
