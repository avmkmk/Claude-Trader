# Preflight check for the Daily ATH Scan. Run automatically at Claude session start
# (see .claude/settings.json). Prints what is installed / missing and how to fix it.
# Always exits 0 so it never blocks a session.

$root = Split-Path -Parent $PSScriptRoot
$missing = @()
$warn = @()

function Report($ok, $name, $detail, $fix) {
    if ($ok) {
        Write-Output ("[OK]      {0} - {1}" -f $name, $detail)
    } else {
        Write-Output ("[MISSING] {0} - install: {1}" -f $name, $fix)
        $script:missing += $name
    }
}

function ToolVersion($cmd, $verArgs) {
    $c = Get-Command $cmd -ErrorAction SilentlyContinue
    if (-not $c) { return $null }
    try { return ((& $cmd $verArgs 2>&1) | Select-Object -First 1).ToString().Trim() } catch { return "found" }
}

Write-Output "=== SimpleTrader preflight (Daily ATH Scan prerequisites) ==="

if ($env:OS -ne "Windows_NT") {
    Write-Output "[MISSING] Windows - the TradingView launch script (launch_tv_debug.ps1) is Windows-only"
    $missing += "Windows"
}

$v = ToolVersion "git" "--version"
Report ($null -ne $v) "Git" $v "winget install --id Git.Git -e"

$py = ToolVersion "python" "--version"
$pyOk = $false
if ($py -match "Python (\d+)\.(\d+)") { $pyOk = ([int]$Matches[1] -gt 3) -or ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 11) }
Report $pyOk "Python 3.11+" $py "winget install --id Python.Python.3.13 -e"

$node = ToolVersion "node" "--version"
$nodeOk = $false
if ($node -match "v(\d+)\.") { $nodeOk = [int]$Matches[1] -ge 18 }
Report $nodeOk "Node.js 18+" $node "winget install --id OpenJS.NodeJS.LTS -e"

$npm = ToolVersion "npm" "--version"
Report ($null -ne $npm) "npm" $npm "(installed with Node.js)"

$chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe", "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
Report ($null -ne $chrome) "Google Chrome (Selenium scrapes Chartink with it)" $chrome "winget install --id Google.Chrome -e"

$tv = Get-AppxPackage -Name "*TradingView*" -ErrorAction SilentlyContinue | Select-Object -First 1
Report ($null -ne $tv) "TradingView Desktop (Microsoft Store build)" ("v" + $tv.Version) "winget install --id 9NDJWKSTBT25 --source msstore --accept-package-agreements --accept-source-agreements"

$tvcli = Get-Command "tradingview-cli" -ErrorAction SilentlyContinue
Report ($null -ne $tvcli) "tradingview-cli (market cap / price lookups)" $tvcli.Source "npm install -g tradingview-mcp-server"

if ($pyOk) {
    $pkgs = @{ "selenium" = "selenium"; "webdriver_manager" = "webdriver-manager"; "openpyxl" = "openpyxl"; "requests" = "requests"; "bs4" = "beautifulsoup4"; "pytest" = "pytest" }
    $absent = @()
    foreach ($m in $pkgs.Keys) {
        & python -c "import $m" 2>$null
        if ($LASTEXITCODE -ne 0) { $absent += $pkgs[$m] }
    }
    Report ($absent.Count -eq 0) "Python packages" "selenium, webdriver-manager, openpyxl, requests, beautifulsoup4, pytest" "pip install -r simple-trader-api/requirements.txt  (missing: $($absent -join ', '))"
}

$nm = Test-Path (Join-Path $root "tradingview-mcp-jackson\node_modules")
Report $nm "tradingview-mcp-jackson npm dependencies" "node_modules present" "cd tradingview-mcp-jackson; npm install"

# .mcp.json hard-codes an absolute path; warn if it does not match this clone.
$mcp = Join-Path $root ".mcp.json"
if (Test-Path $mcp) {
    $m = Get-Content $mcp -Raw | ConvertFrom-Json
    $p = $m.mcpServers."tradingview-desktop".args | Select-Object -First 1
    if ($p -and -not (Test-Path $p)) {
        $warn += ".mcp.json points to '$p', which does not exist on this machine. Edit the path to match this clone."
    }
}

# TradingView CDP state (informational: the scan launches it when needed).
$cdp = $false
try { Invoke-WebRequest -Uri "http://localhost:9222/json/version" -UseBasicParsing -TimeoutSec 2 | Out-Null; $cdp = $true } catch {}
if ($cdp) {
    Write-Output "[OK]      TradingView is running with remote debugging (CDP on port 9222)"
} else {
    Write-Output "[INFO]    TradingView is not running with CDP on 9222. Start it with: powershell -ExecutionPolicy Bypass -File tradingview-mcp-jackson/scripts/launch_tv_debug.ps1"
}

foreach ($w in $warn) { Write-Output "[WARN]    $w" }

Write-Output ""
if ($missing.Count -gt 0) {
    Write-Output ("PREFLIGHT RESULT: {0} missing: {1}" -f $missing.Count, ($missing -join "; "))
} else {
    Write-Output "PREFLIGHT RESULT: all prerequisites present"
}
exit 0
