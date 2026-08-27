@echo off
REM ===================================================================
REM  Script de DEMARRAGE GPO -- a placer dans l'onglet "Scripts"
REM  (PAS "Scripts PowerShell"), Configuration ORDINATEUR.
REM
REM  Il tourne en SYSTEM au boot et lance register-task.ps1 en
REM  contournant l'ExecutionPolicy (-ExecutionPolicy Bypass), ce qui
REM  evite le blocage quand la machine est en ExecutionPolicy Restricted.
REM
REM  register-task.ps1 (installe par le MSI) cree la tache C2AgentBeacon
REM  sous le gMSA (machine du domaine) ou SYSTEM (repli).
REM ===================================================================

set "PS1=%ProgramFiles(x86)%\C2Agent\register-task.ps1"
if not exist "%PS1%" set "PS1=%ProgramFiles%\C2Agent\register-task.ps1"

if exist "%PS1%" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%"
)
