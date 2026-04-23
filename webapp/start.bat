@echo off
setlocal
REM Launcher in starts/ — do not use symlink for .bat: %%~dp0 must not point here without start.ps1.
REM Layout: D:\Dev\repos\mcp-central-docs\starts\  ->  D:\Dev\repos\yahboom-mcp\webapp
REM Backend 10892 | Dashboard 10893 | Robot IP default WiFi 192.168.1.11
set "WEBAPP=%~dp0..\..\yahboom-mcp\webapp"
cd /d "%WEBAPP%"
if not exist "start.ps1" (
  echo [ERROR] yahboom-mcp webapp not found. Expected: %CD%\start.ps1
  echo Fix: clone yahboom-mcp next to mcp-central-docs under the same parent folder.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%CD%\start.ps1" %*
if errorlevel 1 (
  pause
  exit /b 1
)
endlocal
