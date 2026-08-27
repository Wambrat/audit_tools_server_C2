#Requires -Version 5.0
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Launcher script pour l'agent Jadus
    Exécute agent_active.ps1 avec les paramètres injectés lors du build

.DESCRIPTION
    Ce script :
    - Exécute l'agent principal avec les paramètres pré-configurés
    - Les paramètres sont injectés lors de la compilation du MSI
    - Gère les logs structurés
    - S'assure que la tâche planifiée existe

.NOTES
    Ce script doit être exécuté en tant qu'administrateur
    Les paramètres sont injectés lors du build via build-msi.ps1
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
    
    # Écriture dans fichier
    if ($LogFile -and (Test-Path (Split-Path -Path $LogFile))) {
        Add-Content -Path $LogFile -Value $logEntry
    }
}

function Ensure-ScheduledTask {
    param(
        [string]$LauncherPath,
        [string]$LogFilePath
    )
    
    # NOTE: La tâche planifiée devrait être créée par la Custom Action du MSI pendant l'installation.
    # Cette fonction est un fallback au cas où :
    # - La Custom Action aurait échoué
    # - Le script est exécuté manuellement ou via d'autres moyens
    # - La tâche aurait été supprimée
    
    $taskName = "JadusAgentBeacon"
    
    Write-Log "Checking scheduled task: $taskName" "INFO" $LogFilePath
    
    # Vérifier si la tâche existe
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    if ($existingTask) {
        Write-Log "Scheduled task already exists" "SUCCESS" $LogFilePath
        return $true
    }
    
    Write-Log "Scheduled task does not exist, creating it (FALLBACK)..." "WARNING" $LogFilePath
    
    try {
        # Créer l'action
        $action = New-ScheduledTaskAction `
            -Execute "powershell.exe" `
            -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$LauncherPath`""
        
        # Créer le trigger (au démarrage de l'ordinateur)
        $trigger = New-ScheduledTaskTrigger -AtStartup
        
        # Paramètres de la tâche
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RunOnlyIfNetworkAvailable `
            -MultipleInstances IgnoreNew
        
        # Créer la tâche
        $task = Register-ScheduledTask `
            -TaskName $taskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -RunLevel Highest `
            -User "SYSTEM" `
            -Description "Jadus Agent - Beacon execution" `
            -ErrorAction Stop
        
        Write-Log "✅ Scheduled task created successfully" "SUCCESS" $LogFilePath
        
        # Test d'exécution
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
Write-Host "        JADUS AGENT - Launcher" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Créer le répertoire des logs s'il n'existe pas
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

# Vérifier que le script agent existe
$agentScriptPath = "$PSScriptRoot\agent_active.ps1"

if (-not (Test-Path -Path $agentScriptPath)) {
    Write-Log "Agent script not found: $agentScriptPath" "ERROR" $logFilePath
    exit 1
}

Write-Log "Starting agent..." "INFO" $logFilePath

# NB : le cycle de vie (démarrage/redémarrage) est géré par le SERVICE Windows
# (wrapper WinSW) ou la tâche planifiée. launcher.ps1 ne doit donc PAS créer/
# démarrer de tâche lui-même, sous peine de lancer une 2e instance de l'agent
# en parallèle (double enrôlement). L'ancien fallback Ensure-ScheduledTask est
# volontairement désactivé.

# Exécuter l'agent avec les paramètres injectés
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
