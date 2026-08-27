#Requires -Version 5.0
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Launcher script pour l'agent jadus
    ExÃ©cute agent_active.ps1 avec les paramÃ¨tres injectÃ©s lors du build

.DESCRIPTION
    Ce script :
    - ExÃ©cute l'agent principal avec les paramÃ¨tres prÃ©-configurÃ©s
    - Les paramÃ¨tres sont injectÃ©s lors de la compilation du MSI
    - GÃ¨re les logs structurÃ©s
    - S'assure que la tÃ¢che planifiÃ©e existe

.NOTES
    Ce script doit Ãªtre exÃ©cutÃ© en tant qu'administrateur
    Les paramÃ¨tres sont injectÃ©s lors du build via build-msi.ps1
#>

$ErrorActionPreference = "Stop"

# ===== PARAMÈTRES INJECTÉS LORS DU BUILD =====
# Les placeholders ci-dessous sont remplacés par build-msi.ps1 (.Replace)
# à partir de config.json lors de la compilation du MSI.
# %VAR% dans le chemin de log est développé au runtime, côté Windows.
$serverUrl      = '__SERVER_URL__'
$beaconInterval = [int]'__BEACON_INTERVAL__'
$logFilePath    = [System.Environment]::ExpandEnvironmentVariables('__LOG_FILE__')
# ============================================

# Fonctions utilitaires
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$LogFile
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Affichage console
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "DEBUG" { "Gray" }
        default { "White" }
    }
    
    Write-Host $logEntry -ForegroundColor $color
    
    # Ã‰criture dans fichier
    if ($LogFile -and (Test-Path (Split-Path -Path $LogFile))) {
        Add-Content -Path $LogFile -Value $logEntry
    }
}

function Ensure-ScheduledTask {
    param(
        [string]$LauncherPath,
        [string]$LogFilePath
    )
    
    # NOTE: La tÃ¢che planifiÃ©e devrait Ãªtre crÃ©Ã©e par la Custom Action du MSI pendant l'installation.
    # Cette fonction est un fallback au cas oÃ¹ :
    # - La Custom Action aurait Ã©chouÃ©
    # - Le script est exÃ©cutÃ© manuellement ou via d'autres moyens
    # - La tÃ¢che aurait Ã©tÃ© supprimÃ©e
    
    $taskName = "jadusAgentBeacon"
    
    Write-Log "Checking scheduled task: $taskName" "INFO" $LogFilePath
    
    # VÃ©rifier si la tÃ¢che existe
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    if ($existingTask) {
        Write-Log "Scheduled task already exists" "SUCCESS" $LogFilePath
        return $true
    }
    
    Write-Log "Scheduled task does not exist, creating it (FALLBACK)..." "WARNING" $LogFilePath
    
    try {
        # CrÃ©er l'action
        $action = New-ScheduledTaskAction `
            -Execute "powershell.exe" `
            -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$LauncherPath`""
        
        # CrÃ©er le trigger (au dÃ©marrage de l'ordinateur)
        $trigger = New-ScheduledTaskTrigger -AtStartup
        
        # ParamÃ¨tres de la tÃ¢che
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RunOnlyIfNetworkAvailable `
            -MultipleInstances IgnoreNew
        
        # CrÃ©er la tÃ¢che
        $task = Register-ScheduledTask `
            -TaskName $taskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -RunLevel Highest `
            -User "SYSTEM" `
            -Description "jadus Autonomous Agent - Beacon execution" `
            -ErrorAction Stop
        
        Write-Log "âœ… Scheduled task created successfully" "SUCCESS" $LogFilePath
        
        # Test d'exÃ©cution
        Write-Log "Starting scheduled task for verification..." "INFO" $LogFilePath
        Start-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        
        return $true
    }
    catch {
        Write-Log "Failed to create scheduled task: $_" "ERROR" $LogFilePath
        return $false
    }
}

# ===== SCRIPT PRINCIPAL =====

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "        jadus AGENT - Launcher" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# CrÃ©er le rÃ©pertoire des logs s'il n'existe pas
$logDir = Split-Path -Parent -Path $logFilePath

if (-not (Test-Path -Path $logDir)) {
    try {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Write-Log "Created log directory: $logDir" "INFO"
    }
    catch {
        Write-Log "Failed to create log directory: $_" "ERROR"
        $logFilePath = "$PSScriptRoot\agent.log"
        Write-Log "Using fallback log path: $logFilePath" "WARNING"
    }
}

Write-Log "Server URL: $serverUrl" "INFO" $logFilePath
Write-Log "Beacon Interval: $beaconInterval seconds" "INFO" $logFilePath
Write-Log "Log File: $logFilePath" "INFO" $logFilePath

# VÃ©rifier que le script agent existe
$agentScriptPath = "$PSScriptRoot\agent_active.ps1"

if (-not (Test-Path -Path $agentScriptPath)) {
    Write-Log "Agent script not found: $agentScriptPath" "ERROR" $logFilePath
    exit 1
}

Write-Log "Starting agent..." "INFO" $logFilePath

# VÃ©rifier et crÃ©er la tÃ¢che planifiÃ©e si nÃ©cessaire (fallback)
$taskReady = Ensure-ScheduledTask -LauncherPath $PSCommandPath -LogFilePath $logFilePath

if (-not $taskReady) {
    Write-Log "Warning: Scheduled task could not be created or verified" "WARNING" $logFilePath
}

# ExÃ©cuter l'agent avec les paramÃ¨tres injectÃ©s
try {
    & $agentScriptPath `
        -ServerUrl $serverUrl `
        -BeaconInterval $beaconInterval `
        -LogFile $logFilePath
}
catch {
    Write-Log "Agent execution failed: $_" "ERROR" $logFilePath
    exit 1
}

