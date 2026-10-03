# Launching TradingView Desktop with CDP on Windows (MSIX install)

If TradingView Desktop was installed from the Microsoft Store, it's an MSIX
package. That breaks the usual launch methods:

| Method | Why it fails on MSIX |
|---|---|
| `tv_launch` (MCP tool) | Only checks a few hardcoded non-MSIX paths (`%LOCALAPPDATA%\TradingView\...`, `%PROGRAMFILES%\TradingView\...`); doesn't know about `WindowsApps` |
| `scripts/launch_tv_debug.bat` | Its `WindowsApps` search uses `dir /s /b`, which is blocked by folder ACLs for most accounts |
| `scripts/launch_tv_debug.vbs` | Sets `ELECTRON_EXTRA_LAUNCH_ARGS` then activates via `shell:AppsFolder\...` — Store shell activation doesn't reliably forward the flag on newer TradingView builds |
| `explorer.exe shell:AppsFolder\...` directly | Same problem — no way to pass `--remote-debugging-port` through Store activation |

## The fix: `Get-AppxPackage` + direct launch

`Get-AppxPackage` is the actual Windows API for querying installed
packages — it doesn't require raw filesystem browsing permissions, so it
works even though `Get-ChildItem`/`dir` on `C:\Program Files\WindowsApps`
gets access-denied. Once you have the real install path, launch
`TradingView.exe` directly (bypassing the Store activation layer
entirely) with the CDP flag.

### One command

```powershell
powershell -ExecutionPolicy Bypass -File scripts\launch_tv_debug.ps1
```

Optionally pass a different port: `-Port 9333`.

This will:
1. Resolve the real install path via `Get-AppxPackage -Name "*TradingView*"`
2. Kill any running TradingView instance
3. Launch `TradingView.exe --remote-debugging-port=9222` directly
4. Poll `http://localhost:9222/json/version` until CDP responds (or ~40s timeout)

### Manual equivalent

If you want to do it by hand or the script fails:

```powershell
# 1. Find the real install path
Get-AppxPackage -Name "*TradingView*" | Select-Object PackageFullName, InstallLocation

# 2. Kill the running instance and relaunch directly with the flag
Stop-Process -Name "TradingView" -Force -ErrorAction SilentlyContinue
Start-Process -FilePath "C:\Program Files\WindowsApps\<PackageFullName>\TradingView.exe" -ArgumentList "--remote-debugging-port=9222"

# 3. Verify
curl http://localhost:9222/json/version
```

A successful response looks like:
```json
{
  "Browser": "Chrome/...",
  "Protocol-Version": "1.3",
  "webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/<id>"
}
```

Once that's up, `tv_health_check` (MCP tool) should report `cdp_connected: true`.

## Notes

- The exact package folder name (e.g. `TradingView.Desktop_3.3.0.7992_x64__n534cwy3pjxzj`) includes a version number and will change on updates — always resolve it fresh via `Get-AppxPackage` rather than hardcoding it.
- If TradingView was installed the traditional way (not via Store), `launch_tv_debug.bat` should work fine and this workaround isn't needed.
- Cold start after being killed can take 10-20+ seconds before CDP responds; the script polls for up to ~40s.
