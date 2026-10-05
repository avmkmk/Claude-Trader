# Registers (or removes) the Windows Task Scheduler job that runs the Daily ATH Scan.
#
#   powershell -ExecutionPolicy Bypass -File scripts\register_daily_task.ps1            # morning run at 08:00 + at logon
#   powershell -ExecutionPolicy Bypass -File scripts\register_daily_task.ps1 -Time 07:45
#   powershell -ExecutionPolicy Bypass -File scripts\register_daily_task.ps1 -Status     # last/next run result
#   powershell -ExecutionPolicy Bypass -File scripts\register_daily_task.ps1 -Remove
#
# How the "turn the PC on late" requirement is met - three layers, all harmless to repeat because
# run_daily.py exits immediately when the newest watchlist is already current:
#   1. Daily trigger at -Time (local time; keep the PC clock on IST) - the normal pre-market run.
#   2. "At log on" trigger (3 min delay) - if the PC was off at the daily time, the run starts the moment you sign in.
#   3. StartWhenAvailable - if the PC was off/asleep at the daily time, Windows runs the missed task as soon as it can.
# The script itself decides what "latest" means: the last COMPLETED NSE session (see trading_calendar.py), so running
# after the close and running the next morning before the open produce the same stamp.
#
# The job runs only while you are logged on (TradingView is a desktop app and is relaunched with remote debugging).
# -Mode Script (default): the pure-script routine. -Mode Claude: runs `claude -p "/daily-ath-scan"` instead, which also
# does Gate 7 (news + government stance); that headless mode is NOT tested yet - try it manually first.

param(
    [string]$Time = "08:00",
    [ValidateSet("Script", "Claude")] [string]$Mode = "Script",
    [switch]$Remove,
    [switch]$Status
)

$taskName = "SimpleTrader-DailyATH"
$root = Split-Path -Parent $PSScriptRoot
$api = Join-Path $root "simple-trader-api"

if ($Remove) {
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Output "Removed scheduled task $taskName"
    } else { Write-Output "No task named $taskName" }
    exit 0
}

if ($Status) {
    $t = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if (-not $t) { Write-Output "Task $taskName is not registered."; exit 0 }
    $i = Get-ScheduledTaskInfo -TaskName $taskName
    Write-Output ("State: {0}; last run: {1} (result {2}); next run: {3}" -f $t.State, $i.LastRunTime, $i.LastTaskResult, $i.NextRunTime)
    exit 0
}

if ($Mode -eq "Script") {
    $py = (Get-Command python -ErrorAction Stop).Source
    $cmd = "Set-Location '$api'; & '$py' scripts/run_daily.py --open"
} else {
    $claude = (Get-Command claude -ErrorAction Stop).Source
    $cmd = "Set-Location '$root'; & '$claude' -p '/daily-ath-scan' --permission-mode acceptEdits"
}
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command `"$cmd`""

$daily = New-ScheduledTaskTrigger -Daily -At $Time
$logon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$logon.Delay = "PT3M"

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 5) -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 10)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($daily, $logon) -Settings $settings -Principal $principal `
    -Description "SimpleTrader Daily ATH Scan ($Mode mode): runs before market open and at logon if the watchlist is stale." -Force | Out-Null
Write-Output "Registered $taskName ($Mode mode): daily at $Time + at logon (+3 min), run ASAP if missed."
Write-Output "Check: scripts\register_daily_task.ps1 -Status   Remove: scripts\register_daily_task.ps1 -Remove"
