!macro KillProcesses
  DetailPrint "Stopping yahboom-mcp processes..."
  ExecWait 'taskkill /F /IM "yahboom-mcp-backend.exe" /T' $0
  ExecWait 'taskkill /F /IM "yahboom-mcp-native.exe" /T' $0
  !if "${INSTALLMODE}" == "currentUser"
    nsis_tauri_utils::KillProcessCurrentUser "yahboom-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcessCurrentUser "yahboom-mcp-native.exe"
    Pop $0
  !else
    nsis_tauri_utils::KillProcess "yahboom-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcess "yahboom-mcp-native.exe"
    Pop $0
  !endif
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillProcesses
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillProcesses
!macroend

!macro NSIS_HOOK_POSTINSTALL
  ; Optional: register yahboom-mcp in Cursor / Claude Desktop
  IfFileExists "$INSTDIR\resources\install-mcp-clients.ps1" 0 mcp_hook_done
    DetailPrint "Optional: register yahboom-mcp in Cursor / Claude Desktop"
    ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\resources\install-mcp-clients.ps1" -Interactive'
  mcp_hook_done:
!macroend
