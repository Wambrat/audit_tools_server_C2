#Requires -Version 5.0

<#
.SYNOPSIS
    Script de vérification post-déploiement via GPO

.DESCRIPTION
    Vérifie que l'installation de l'agent C2 via GPO s'est déroulée correctement
    Peut être exécuté manuellement ou via un script de monitoring

.PARAMETER ComputerName
    Ordinateur(s) à vérifier (défaut: localhost)

.PARAMETER Detailed
    Afficher les détails complets

.EXAMPLE
    .\verify-deployment.ps1
    .\verify-deployment.ps1 -ComputerName "PC1", "PC2", "PC3"
    .\verify-deployment.ps1 -ComputerName "PC1" -Detailed
#>

param(
    [string[]]$ComputerName = @($env:COMPUTERNAME),
    [switch]$Detailed
)

$results = @()

function Test-AgentDeployment {
    param(
        [string]$Computer,
        [switch]$Detailed
    )
    
    $result = [PSCustomObject]@{
        Computer = $Computer
        InstallPath = $false
        FilesPresent = @()
        ScheduledTask = $false
        Connectivity = $false
        Logs = $null
    }
    
    Write-Host ""
    Write-Host "📋 Vérification: $Computer" -ForegroundColor Cyan
    Write-Host "─" * 50 -ForegroundColor Gray
    
    # Test 1: Chemin d'installation
    try {
        $exists = Test-Path "\\$Computer\C$\Program Files\C2Agent" -ErrorAction Stop
        $result.InstallPath = $exists
        Write-Host "✅ Chemin installation: $exists" -ForegroundColor $(if ($exists) { "Green" } else { "Red" })
    }
    catch {
        Write-Host "⚠️ Impossible d'accéder à $Computer" -ForegroundColor Yellow
        return $result
    }
    
    if (-not $result.InstallPath) {
        return $result
    }
    
    # Test 2: Fichiers
    $files = @("agent_active.ps1", "launcher.ps1", "config.json")
    $filePath = "\\$Computer\C$\Program Files\C2Agent"
    
    foreach ($file in $files) {
        $exists = Test-Path "$filePath\$file"
        $result.FilesPresent += [PSCustomObject]@{
            File = $file
            Exists = $exists
        }
        $symbol = if ($exists) { "✅" } else { "❌" }
        Write-Host "$symbol Fichier: $file" -ForegroundColor $(if ($exists) { "Green" } else { "Red" })
    }
    
    # Test 3: Tâche planifiée
    try {
        $task = Get-ScheduledTask -ComputerName $Computer -TaskName "C2AgentBeacon" -ErrorAction Stop
        $result.ScheduledTask = $true
        $taskInfo = Get-ScheduledTaskInfo -ComputerName $Computer -TaskName "C2AgentBeacon" -ErrorAction Stop
        Write-Host "✅ Tâche planifiée: Créée" -ForegroundColor Green
        
        if ($Detailed) {
            Write-Host "   - État: $($task.State)" -ForegroundColor Gray
            Write-Host "   - Dernière exécution: $($taskInfo.LastRunTime)" -ForegroundColor Gray
            Write-Host "   - Prochaine exécution: $($taskInfo.NextRunTime)" -ForegroundColor Gray
            Write-Host "   - Dernier résultat: $($taskInfo.LastTaskResult)" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "❌ Tâche planifiée: Non trouvée" -ForegroundColor Red
    }
    
    # Test 4: Connectivité au serveur C2
    try {
        $config = Get-Content "\\$Computer\C$\Program Files\C2Agent\config.json" | ConvertFrom-Json
        $serverUrl = $config.agent.serverUrl
        
        $healthEndpoint = $serverUrl -replace '/api$', '/health'
        
        try {
            $response = Invoke-WebRequest -Uri $healthEndpoint -TimeoutSec 5 -ErrorAction Stop
            $result.Connectivity = ($response.StatusCode -eq 200)
            Write-Host "✅ Connectivité serveur: OK ($serverUrl)" -ForegroundColor Green
        }
        catch {
            Write-Host "⚠️ Connectivité serveur: IMPOSSIBLE" -ForegroundColor Yellow
            Write-Host "   URL: $serverUrl" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "⚠️ Configuration: Impossible à lire" -ForegroundColor Yellow
    }
    
    # Test 5: Logs
    try {
        $logPath = "\\$Computer\C$\Program Files\C2Agent\logs\deploy.log"
        if (Test-Path $logPath) {
            $logContent = Get-Content $logPath -Tail 5
            $result.Logs = $logContent
            Write-Host "✅ Logs trouvés (dernières 5 lignes):" -ForegroundColor Green
            
            if ($Detailed) {
                $logContent | ForEach-Object {
                    Write-Host "   $_" -ForegroundColor Gray
                }
            }
        }
        else {
            Write-Host "⚠️ Logs: Non trouvés" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "⚠️ Logs: Impossible à accéder" -ForegroundColor Yellow
    }
    
    return $result
}

# ===== SCRIPT PRINCIPAL =====

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Vérification Déploiement C2 Agent via GPO       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host ""
Write-Host "Nombre d'ordinateurs à vérifier: $($ComputerName.Count)" -ForegroundColor Cyan

# Vérifier chaque ordinateur
foreach ($computer in $ComputerName) {
    $result = Test-AgentDeployment -Computer $computer -Detailed:$Detailed
    $results += $result
}

# Résumé
Write-Host ""
Write-Host ""
Write-Host "📊 RÉSUMÉ" -ForegroundColor Cyan
Write-Host "─" * 50 -ForegroundColor Gray

$summary = $results | Measure-Object -Property InstallPath, ScheduledTask, Connectivity -Sum

$installed = @($results | Where-Object { $_.InstallPath }).Count
$tasksCreated = @($results | Where-Object { $_.ScheduledTask }).Count
$connected = @($results | Where-Object { $_.Connectivity }).Count

Write-Host "Ordinateurs vérifiés: $($results.Count)" -ForegroundColor White
Write-Host "  ✅ Agent installé: $installed/$($results.Count)" -ForegroundColor Green
Write-Host "  ✅ Tâche planifiée: $tasksCreated/$($results.Count)" -ForegroundColor Green
Write-Host "  ✅ Connecté au serveur: $connected/$($results.Count)" -ForegroundColor Green

if ($installed -eq $results.Count -and $tasksCreated -eq $results.Count) {
    Write-Host ""
    Write-Host "✅ DÉPLOIEMENT RÉUSSI!" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "⚠️ CERTAINS DÉPLOIEMENTS ONT ÉCHOUÉ" -ForegroundColor Yellow
}

Write-Host ""
