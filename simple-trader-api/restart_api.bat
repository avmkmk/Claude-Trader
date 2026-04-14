@echo off
REM Restart API script for Windows

echo Stopping existing API processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *app.main*" 2>nul
if errorlevel 1 (
    echo No existing API process found
)

timeout /t 2 /nobreak >nul

echo Starting API...
cd /d "%~dp0"
python -m app.main

echo API should now be running on http://localhost:8000
