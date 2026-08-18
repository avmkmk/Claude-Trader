# Launch TradingView Desktop (Windows Store / MSIX install) with Chrome DevTools
# Protocol remote debugging enabled, so tradingview-mcp-jackson can attach.
#
# Usage:
#   powershell -File scripts\launch_tv_debug.ps1 [-Port 9222]
#
# Why this exists: TradingView Desktop on Windows is usually installed as an
# MSIX/Store package, not a plain .exe under Program Files. That means:
#   - launch_tv_debug.bat's WindowsApps `dir /s /b` search often can't see it
#     (folder ACLs block plain filesystem enumeration)
#   - launch_tv_debug.vbs's ELECTRON_EXTRA_LAUNCH_ARGS + `shell:AppsFolder`
#     activation does not reliably forward the CLI flag on newer builds
#   - tv_launch (the MCP tool) only checks a few hardcoded non-MSIX paths
#
# This script uses Get-AppxPackage (the actual Windows API for querying
# installed packages, not raw folder browsing) to find the real install
# location, then launches TradingView.exe directly with the flag -
# bypassing Store shell activation entirely.

param(
    [int]$Port = 9222
)

Write-Host "Looking up TradingView package..."
$pkg = Get-AppxPackage -Name "*TradingView*" | Select-Object -First 1
if (-not $pkg) {
    Write-Error "TradingView package not found via Get-AppxPackage. Is it installed from the Microsoft Store?"
    exit 1
}

$exePath = Join-Path $pkg.InstallLocation "TradingView.exe"
if (-not (Test-Path $exePath)) {
    Write-Error "Expected TradingView.exe at $exePath but it wasn't there. Package layout may have changed - check $($pkg.InstallLocation) manually."
    exit 1
}
Write-Host "Found: $exePath"

Write-Host "Stopping any running TradingView instance..."
Stop-Process -Name "TradingView" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "Launching with --remote-debugging-port=$Port ..."
Start-Process -FilePath $exePath -ArgumentList "--remote-debugging-port=$Port"

Write-Host "Waiting for CDP to come up..."
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$Port/json/version" -UseBasicParsing -TimeoutSec 3
        Write-Host "`nCDP ready at http://localhost:$Port"
        Write-Host $resp.Content
        $ready = $true
        break
    } catch {
        Write-Host "  still waiting..."
    }
}

if (-not $ready) {
    Write-Error "CDP did not come up after ~40s. TradingView may still be loading (first cold start can be slow) - try tv_health_check again in a bit, or re-run this script."
    exit 1
}
