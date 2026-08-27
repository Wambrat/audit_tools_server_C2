#Requires -Version 5.0

<#
.SYNOPSIS
    Script de vÃ©rification post-dÃ©ploiement via GPO

.DESCRIPTION
    VÃ©rifie que l'installation de l'agent jadus via GPO s'est dÃ©roulÃ©e correctement
    Peut Ãªtre exÃ©cutÃ© manuellement ou via un script de monitoring

.PARAMETER ComputerName
    Ordinateur(s) Ã  vÃ©rifier (dÃ©faut: localhost)

.PARAMETER Detailed
    Afficher les dÃ©tails complets

.EXAMPLE
    .\verify-deployment.ps1
    .\verify-deployment.ps1 -ComputerName "PC1", "Pjadus", "PC3"
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
    Write-Host "ðŸ“‹ VÃ©rification: $Computer" -ForegroundColor Cyan
    Write-Host "â”€" * 50 -ForegroundColor Gray
    
    # Test 1: Chemin d'installation
    try {
        $exists = Test-Path "\\$Computer\C$\Program Files\jadusAgent" -ErrorAction Stop
        $result.InstallPath = $exists
        Write-Host "âœ… Chemin installation: $exists" -ForegroundColor $(if ($exists) { "Green" } else { "Red" })
    }
    catch {
        Write-Host "âš ï¸ Impossible d'accÃ©der Ã  $Computer" -ForegroundColor Yellow
        return $result
    }
    
    if (-not $result.InstallPath) {
        return $result
    }
    
    # Test 2: Fichiers
    $files = @("agent_active.ps1", "launcher.ps1", "config.json")
    $filePath = "\\$Computer\C$\Program Files\jadusAgent"
    
    foreach ($file in $files) {
        $exists = Test-Path "$filePath\$file"
        $result.FilesPresent += [PSCustomObject]@{
            File = $file
            Exists = $exists
        }
        $symbol = if ($exists) { "âœ…" } else { "âŒ" }
        Write-Host "$symbol Fichier: $file" -ForegroundColor $(if ($exists) { "Green" } else { "Red" })
    }
    
    # Test 3: TÃ¢che planifiÃ©e
    try {
        $task = Get-ScheduledTask -ComputerName $Computer -TaskName "jadusAgentBeacon" -ErrorAction Stop
        $result.ScheduledTask = $true
        $taskInfo = Get-ScheduledTaskInfo -ComputerName $Computer -TaskName "jadusAgentBeacon" -ErrorAction Stop
        Write-Host "âœ… TÃ¢che planifiÃ©e: CrÃ©Ã©e" -ForegroundColor Green
        
        if ($Detailed) {
            Write-Host "   - Ã‰tat: $($task.State)" -ForegroundColor Gray
            Write-Host "   - DerniÃ¨re exÃ©cution: $($taskInfo.LastRunTime)" -ForegroundColor Gray
            Write-Host "   - Prochaine exÃ©cution: $($taskInfo.NextRunTime)" -ForegroundColor Gray
            Write-Host "   - Dernier rÃ©sultat: $($taskInfo.LastTaskResult)" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "âŒ TÃ¢che planifiÃ©e: Non trouvÃ©e" -ForegroundColor Red
    }
    
    # Test 4: ConnectivitÃ© au serveur jadus
    try {
        $config = Get-Content "\\$Computer\C$\Program Files\jadusAgent\config.json" | ConvertFrom-Json
        $serverUrl = $config.agent.serverUrl
        
        $healthEndpoint = $serverUrl -replace '/api$', '/health'
        
        try {
            $response = Invoke-WebRequest -Uri $healthEndpoint -TimeoutSec 5 -ErrorAction Stop
            $result.Connectivity = ($response.StatusCode -eq 200)
            Write-Host "âœ… ConnectivitÃ© serveur: OK ($serverUrl)" -ForegroundColor Green
        }
        catch {
            Write-Host "âš ï¸ ConnectivitÃ© serveur: IMPOSSIBLE" -ForegroundColor Yellow
            Write-Host "   URL: $serverUrl" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "âš ï¸ Configuration: Impossible Ã  lire" -ForegroundColor Yellow
    }
    
    # Test 5: Logs
    try {
        $logPath = "\\$Computer\C$\Program Files\jadusAgent\logs\deploy.log"
        if (Test-Path $logPath) {
            $logContent = Get-Content $logPath -Tail 5
            $result.Logs = $logContent
            Write-Host "âœ… Logs trouvÃ©s (derniÃ¨res 5 lignes):" -ForegroundColor Green
            
            if ($Detailed) {
                $logContent | ForEach-Object {
                    Write-Host "   $_" -ForegroundColor Gray
                }
            }
        }
        else {
            Write-Host "âš ï¸ Logs: Non trouvÃ©s" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "âš ï¸ Logs: Impossible Ã  accÃ©der" -ForegroundColor Yellow
    }
    
    return $result
}

# ===== SCRIPT PRINCIPAL =====

Write-Host ""
Write-Host "â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—" -ForegroundColor Cyan
Write-Host "â•‘   VÃ©rification DÃ©ploiement jadus Agent via GPO       â•‘" -ForegroundColor Cyan
Write-Host "â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•" -ForegroundColor Cyan

Write-Host ""
Write-Host "Nombre d'ordinateurs Ã  vÃ©rifier: $($ComputerName.Count)" -ForegroundColor Cyan

# VÃ©rifier chaque ordinateur
foreach ($computer in $ComputerName) {
    $result = Test-AgentDeployment -Computer $computer -Detailed:$Detailed
    $results += $result
}

# RÃ©sumÃ©
Write-Host ""
Write-Host ""
Write-Host "ðŸ“Š RÃ‰SUMÃ‰" -ForegroundColor Cyan
Write-Host "â”€" * 50 -ForegroundColor Gray

$summary = $results | Measure-Object -Property InstallPath, ScheduledTask, Connectivity -Sum

$installed = @($results | Where-Object { $_.InstallPath }).Count
$tasksCreated = @($results | Where-Object { $_.ScheduledTask }).Count
$connected = @($results | Where-Object { $_.Connectivity }).Count

Write-Host "Ordinateurs vÃ©rifiÃ©s: $($results.Count)" -ForegroundColor White
Write-Host "  âœ… Agent installÃ©: $installed/$($results.Count)" -ForegroundColor Green
Write-Host "  âœ… TÃ¢che planifiÃ©e: $tasksCreated/$($results.Count)" -ForegroundColor Green
Write-Host "  âœ… ConnectÃ© au serveur: $connected/$($results.Count)" -ForegroundColor Green

if ($installed -eq $results.Count -and $tasksCreated -eq $results.Count) {
    Write-Host ""
    Write-Host "âœ… DÃ‰PLOIEMENT RÃ‰USSI!" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "âš ï¸ CERTAINS DÃ‰PLOIEMENTS ONT Ã‰CHOUÃ‰" -ForegroundColor Yellow
}

Write-Host ""

