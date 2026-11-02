@echo off
cd /d "%~dp0"
echo Starting AeroLoad Vercel Server & Wi-Fi Host...
start "AeroLoad Server" /b py server.py
timeout /t 1 /nobreak >nul
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:5050 --window-size=1180,820 --no-first-run
) else (
    start http://localhost:5050
)
