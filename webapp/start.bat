@echo off
REM Yahboom ROS 2 MCP - Starts backend (10892) + dashboard (10893). Robot IP default: WiFi 192.168.1.11
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
pause
