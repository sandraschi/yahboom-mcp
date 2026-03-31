@echo off
REM Yahboom ROS 2 MCP - Starts backend (10792) + dashboard (10793). Robot IP default: 192.168.0.250
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
pause
