#Requires -Version 5.0
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Script d'installation de la tÃ¢che planifiÃ©e pour l'agent jadus

.DESCRIPTION
    Ce script crÃ©e une tÃ¢che planifiÃ©e qui exÃ©cute rÃ©guliÃ¨rement l'agent jadus
    Il doit Ãªtre exÃ©cutÃ© aprÃ¨s l'installation du MSI

.PARAMETER InstallPath
    Chemin d'installation de l'agent jadus (par dÃ©faut: C:\Program Files\jadusAgent)

.PARAMETER TaskName
    Nom de la tÃ¢che planifiÃ©e (par dÃ©faut: jadusAgentBeacon)

.PARAMETER IntervalMinutes
    Intervalle en minutes entre chaque exÃ©cution (par dÃ©faut: 0.5 = 30 secondes)

.EXAMPLE
    .\install-scheduled-task.ps1 -InstallPath "C:\Program Files\jadusAgent" -TaskName "jadusAgentBeacon"
#>

param(
    [string]$InstallPath = "C:\Program Files\jadusAgent",
    [string]$TaskName = "jadusAgentBeacon",
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

# VÃ©rifier les prÃ©requis
Write-Log "VÃ©rification des prÃ©requis..." "INFO"

if (-not (Test-Path -Path $InstallPath)) {
    Write-Log "RÃ©pertoire d'installation non trouvÃ©: $InstallPath" "ERROR"
    exit 1
}

$launcherPath = Join-Path -Path $InstallPath -ChildPath "launcher.ps1"
if (-not (Test-Path -Path $launcherPath)) {
    Write-Log "Fichier launcher.ps1 non trouvÃ©: $launcherPath" "ERROR"
    exit 1
}

Write-Log "RÃ©pertoire d'installation trouvÃ©: $InstallPath" "SUCCESS"

# Suppression de la tÃ¢che existante si elle existe
Write-Log "VÃ©rification de tÃ¢che existante: $TaskName" "INFO"

$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Log "Suppression de la tÃ¢che existante..." "WARNING"
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Start-Sleep -Milliseconds 500
}

# CrÃ©er l'action de la tÃ¢che
Write-Log "CrÃ©ation de l'action de la tÃ¢che..." "INFO"

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$launcherPath`""

# CrÃ©er le trigger (toutes les 30 secondes ou selon IntervalMinutes)
Write-Log "CrÃ©ation du trigger (intervalle: $IntervalMinutes minutes)..." "INFO"

$trigger = New-ScheduledTaskTrigger `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -At (Get-Date) `
    -Once

# CrÃ©er les paramÃ¨tres de la tÃ¢che
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

# CrÃ©er la tÃ¢che avec privilÃ¨ges Ã©levÃ©s
Write-Log "Enregistrement de la tÃ¢che planifiÃ©e..." "INFO"

try {
    $task = Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -RunLevel Highest `
        -User "SYSTEM" `
        -Description "jadus Autonomous Agent - Beacon execution"
    
    Write-Log "TÃ¢che planifiÃ©e crÃ©Ã©e avec succÃ¨s: $TaskName" "SUCCESS"
    Write-Log "Prochaine exÃ©cution: $(($task.Triggers[0]).StartBoundary)" "INFO"
}
catch {
    Write-Log "Erreur lors de la crÃ©ation de la tÃ¢che: $_" "ERROR"
    exit 1
}

# Test d'exÃ©cution manuelle (optionnel)
Write-Log "DÃ©marrage manuel de la tÃ¢che pour test..." "INFO"

try {
    Start-ScheduledTask -TaskName $TaskName
    Write-Log "TÃ¢che dÃ©marrÃ©e manuellement" "SUCCESS"
    
    # Attendre un moment et vÃ©rifier le statut
    Start-Sleep -Seconds 2
    $taskStatus = Get-ScheduledTask -TaskName $TaskName
    Write-Log "Ã‰tat de la tÃ¢che: $($taskStatus.State)" "INFO"
}
catch {
    Write-Log "Attention: La tÃ¢che n'a pas pu Ãªtre dÃ©marrÃ©e manuellement: $_" "WARNING"
}

Write-Log "" "INFO"
Write-Log "Installation complÃ©tÃ©e !" "SUCCESS"
Write-Log "TÃ¢che planifiÃ©e: $TaskName" "INFO"
Write-Log "Intervalle d'exÃ©cution: $IntervalMinutes minutes" "INFO"
Write-Log "Chemin du lanceur: $launcherPath" "INFO"
Write-Log "" "INFO"
Write-Log "Pour vÃ©rifier la tÃ¢che:" "INFO"
Write-Log "  Get-ScheduledTask -TaskName '$TaskName'" "INFO"
Write-Log "" "INFO"
Write-Log "Pour voir les logs:" "INFO"
Write-Log "  Get-Content '$InstallPath\logs\agent.log' -Tail 50" "INFO"
Write-Log "" "INFO"

