@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ==> Starting backend with PowerShell script
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1"
if errorlevel 1 (
  echo.
  echo Backend failed to start. Check the logs above.
  pause
  exit /b 1
)

endlocal
