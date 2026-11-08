@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
if errorlevel 1 (
    echo.
    echo Setup stopped. Check the error above. Run this file again to retry.
    pause
    exit /b 1
)
