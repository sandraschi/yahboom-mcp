@echo off
REM Yahboom ROS 2 MCP - Double-Click Launcher (works when run via symlink from starts/)
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0start.ps1"
pause
