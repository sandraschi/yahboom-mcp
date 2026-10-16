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

!define MCP_REG_NAME "yahboom-mcp"                 ; key written into the AI client configs
!define MCP_REG_EXE  "yahboom-mcp-backend.exe"     ; stdio-capable exe under $INSTDIR\resources\
!include "mcp-clients.nsh"

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillProcesses
  !insertmacro McpClientsUnregister
!macroend

!macro NSIS_HOOK_POSTINSTALL
  !insertmacro McpClientsRegister
!macroend
