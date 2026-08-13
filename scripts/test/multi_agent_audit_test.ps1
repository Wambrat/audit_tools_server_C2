# =====================================================
# Multi-Agent Audit Testing Script
# Test l'API avec plusieurs agents simultanés
# =====================================================

param(
    [int]$NumAgents = 3,
    [string]$ServerUrl = "http://localhost:8000",
    [int]$AuditDelaySeconds = 5
)

Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║     Multi-Agent Audit Testing Suite            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  • Agents: $NumAgents"
Write-Host "  • Server: $ServerUrl"
Write-Host "  • Audit Delay: $AuditDelaySeconds seconds"
Write-Host ""

# =====================================================
# 1. REGISTER MULTIPLE AGENTS
# =====================================================
Write-Host "`n[STEP 1] Enregistrer $NumAgents agents..." -ForegroundColor Yellow
Write-Host "═" * 50

$agents = @()

for ($i = 1; $i -le $NumAgents; $i++) {
    $agentName = "MULTI-AGENT-$i"
    $hostname = "AUDIT-PC-$i"
    $username = "DOMAIN\agent$i"
    
    Write-Host "`n  Agent $i/$NumAgents: $agentName" -ForegroundColor Cyan
    
    try {
        $body = @{
            agent_name = $agentName
            os_version = "Windows Server 2022"
            hostname = $hostname
            username = $username
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod `
            -Uri "$ServerUrl/api/enroll" `
            -Method POST `
            -Headers @{"Content-Type" = "application/json"} `
            -Body $body `
            -TimeoutSec 5
        
        $agents += @{
            Index = $i
            Name = $agentName
            AgentId = $response.agent_id
            ApiKey = $response.api_key
            Hostname = $hostname
            Status = "registered"
        }
        
        Write-Host "    ✓ ID: $($response.agent_id)" -ForegroundColor Green
        Write-Host "    ✓ Key: $($response.api_key.Substring(0,10))..." -ForegroundColor Green
    } catch {
        Write-Host "    ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n  Result: $($agents.Count)/$NumAgents agents registered" -ForegroundColor Cyan

# =====================================================
# 2. SEND BEACONS FROM ALL AGENTS
# =====================================================
Write-Host "`n[STEP 2] Envoyer des beacons depuis tous les agents..." -ForegroundColor Yellow
Write-Host "═" * 50

foreach ($agent in $agents) {
    try {
        $body = @{
            agent_id = $agent.AgentId
            api_key = $agent.ApiKey
            status = "healthy"
            uptime_seconds = (Get-Random -Minimum 3600 -Maximum 86400)
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod `
            -Uri "$ServerUrl/api/beacon" `
            -Method POST `
            -Headers @{"Content-Type" = "application/json"} `
            -Body $body `
            -TimeoutSec 5
        
        $taskCount = $response.tasks.Count
        Write-Host "  ✓ Agent $($agent.Index) beacon OK (Tasks: $taskCount)" -ForegroundColor Green
        
        $agent.Status = "active"
        $agent.TaskCount = $taskCount
    } catch {
        Write-Host "  ✗ Agent $($agent.Index) beacon failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# =====================================================
# 3. CREATE AUDIT TASKS
# =====================================================
Write-Host "`n[STEP 3] Créer des tâches d'audit pour chaque agent..." -ForegroundColor Yellow
Write-Host "═" * 50

$tasks = @()
$auditCommands = @(
    "Get-Process | ConvertTo-Json",
    "Get-Service | Select-Object Name, Status | ConvertTo-Json",
    "Get-LocalUser | ConvertTo-Json",
    "Get-NetAdapter | ConvertTo-Json",
    "Get-WindowsUpdate | ConvertTo-Json",
    "Get-Hotfix | ConvertTo-Json"
)

foreach ($agent in $agents) {
    $command = $auditCommands[($agent.Index - 1) % $auditCommands.Count]
    $commandShort = if ($command.Length -gt 40) { "$($command.Substring(0, 40))..." } else { $command }
    
    Write-Host "`n  Agent $($agent.Index): $commandShort"
    
    # Simuler l'exécution de la tâche localement (normalement l'agent la recevrait via beacon)
    try {
        $output = Invoke-Expression $command -ErrorAction SilentlyContinue
        $executionTime = Get-Random -Minimum 100 -Maximum 2000
        
        # Soumettre le résultat
        $body = @{
            agent_id = $agent.AgentId
            api_key = $agent.ApiKey
            task_id = "task-$($agent.Index)-$(Get-Random -Minimum 1000 -Maximum 9999)"
            status = "success"
            output = $output
            execution_time_ms = $executionTime
        } | ConvertTo-Json -Depth 5
        
        $response = Invoke-RestMethod `
            -Uri "$ServerUrl/api/results" `
            -Method POST `
            -Headers @{"Content-Type" = "application/json"} `
            -Body $body `
            -TimeoutSec 5
        
        $tasks += @{
            AgentIndex = $agent.Index
            ResultId = $response.result_id
            Command = $commandShort
            Status = "submitted"
            ExecutionTime = $executionTime
        }
        
        Write-Host "    ✓ Résultat soumis (ID: $($response.result_id))" -ForegroundColor Green
        Write-Host "    ✓ Temps d'exécution: $executionTime ms" -ForegroundColor Green
    } catch {
        Write-Host "    ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Petit délai entre les tâches
    Start-Sleep -Milliseconds 500
}

# =====================================================
# 4. WAIT FOR TASK PROCESSING
# =====================================================
Write-Host "`n[STEP 4] Attendre le traitement des tâches..." -ForegroundColor Yellow
Write-Host "═" * 50

Write-Host "`n  Attente de $AuditDelaySeconds secondes..." -ForegroundColor Cyan

for ($i = $AuditDelaySeconds; $i -gt 0; $i--) {
    Write-Host -NoNewline "`r  Temps restant: $i secondes   "
    Start-Sleep -Seconds 1
}
Write-Host "`r  Prêt!                     `n" -ForegroundColor Green

# =====================================================
# 5. CHECK SYSTEM STATUS
# =====================================================
Write-Host "[STEP 5] Vérifier l'état du système..." -ForegroundColor Yellow
Write-Host "═" * 50

try {
    $overview = Invoke-RestMethod `
        -Uri "$ServerUrl/api/monitoring/overview" `
        -Method GET `
        -TimeoutSec 5
    
    Write-Host "`n  📊 Vue d'ensemble du système:" -ForegroundColor Cyan
    Write-Host "    • Total Agents: $($overview.agents.total)" -ForegroundColor Gray
    Write-Host "    • Agents Actifs: $($overview.agents.active)" -ForegroundColor Green
    Write-Host "    • Agents Inactifs: $($overview.agents.inactive)" -ForegroundColor Yellow
    Write-Host "    • Total Tâches: $($overview.tasks.total)" -ForegroundColor Gray
    Write-Host "    • Tâches Complétées: $($overview.tasks.completed)" -ForegroundColor Green
    Write-Host "    • Tâches Échouées: $($overview.tasks.failed)" -ForegroundColor Red
    Write-Host "    • Total Résultats: $($overview.results.total)" -ForegroundColor Gray
    Write-Host "    • Taux de Succès: $([Math]::Round($overview.results.success_rate * 100, 2))%" -ForegroundColor Cyan
    Write-Host "    • Temps d'exécution moyen: $($overview.execution_time_avg_ms)ms" -ForegroundColor Gray
} catch {
    Write-Host "`n  ✗ Error fetching overview: $($_.Exception.Message)" -ForegroundColor Red
}

# =====================================================
# 6. SHOW AGENTS DASHBOARD
# =====================================================
Write-Host "`n[STEP 6] Dashboard des Agents..." -ForegroundColor Yellow
Write-Host "═" * 50

try {
    $dashboard = Invoke-RestMethod `
        -Uri "$ServerUrl/api/monitoring/agents" `
        -Method GET `
        -TimeoutSec 5
    
    Write-Host "`n  👥 État détaillé des agents:`n" -ForegroundColor Cyan
    
    $dashboard.agents | ForEach-Object {
        $bar = if ($_.beacon_stats.total_beacons -gt 0) {
            $percentage = [Math]::Round(($_.beacon_stats.successful_beacons / $_.beacon_stats.total_beacons) * 100)
            "$percentage%"
        } else {
            "0%"
        }
        
        Write-Host "    Agent: $($_.agent_name)" -ForegroundColor Cyan
        Write-Host "      • Status: $($_.status)" -ForegroundColor Gray
        Write-Host "      • Hostname: $($_.hostname)" -ForegroundColor Gray
        Write-Host "      • Beacons: $($_.beacon_stats.total_beacons) (Succès: $bar)" -ForegroundColor Gray
        Write-Host "      • Tâches: $($_.assigned_tasks)/$($_.completed_tasks) complétées" -ForegroundColor Gray
        Write-Host "      • Taux Succès: $($_.success_rate)%" -ForegroundColor Green
        Write-Host ""
    }
} catch {
    Write-Host "`n  ✗ Error fetching agents dashboard: $($_.Exception.Message)" -ForegroundColor Red
}

# =====================================================
# 7. SHOW TASKS DASHBOARD
# =====================================================
Write-Host "[STEP 7] Dashboard des Tâches..." -ForegroundColor Yellow
Write-Host "═" * 50

try {
    $tasksDashboard = Invoke-RestMethod `
        -Uri "$ServerUrl/api/monitoring/tasks" `
        -Method GET `
        -TimeoutSec 5
    
    Write-Host "`n  📋 Résumé des tâches:`n" -ForegroundColor Cyan
    Write-Host "    • En attente: $($tasksDashboard.pending_tasks)" -ForegroundColor Yellow
    Write-Host "    • Assignées: $($tasksDashboard.assigned_tasks)" -ForegroundColor Cyan
    Write-Host "    • Complétées: $($tasksDashboard.completed_tasks)" -ForegroundColor Green
    Write-Host "    • Échouées: $($tasksDashboard.failed_tasks)" -ForegroundColor Red
    Write-Host "    • Délai moyen: $($tasksDashboard.average_execution_time_ms)ms" -ForegroundColor Gray
} catch {
    Write-Host "`n  ✗ Error fetching tasks dashboard: $($_.Exception.Message)" -ForegroundColor Red
}

# =====================================================
# 8. SHOW ALERTS
# =====================================================
Write-Host "`n[STEP 8] Alertes du Système..." -ForegroundColor Yellow
Write-Host "═" * 50

try {
    $alerts = Invoke-RestMethod `
        -Uri "$ServerUrl/api/monitoring/alerts" `
        -Method GET `
        -TimeoutSec 5
    
    Write-Host "`n  🚨 Alertes:`n" -ForegroundColor Cyan
    
    if ($alerts.alerts.Count -eq 0) {
        Write-Host "    ✓ Aucune alerte - Système OK!" -ForegroundColor Green
    } else {
        $alerts.alerts | ForEach-Object {
            $color = if ($_.level -eq "critical") { "Red" } else { "Yellow" }
            Write-Host "    [$($_.level.ToUpper())] $($_.type): $($_.message)" -ForegroundColor $color
        }
    }
    
    Write-Host "`n    Niveau global: $($alerts.overall_level.ToUpper())" -ForegroundColor Cyan
} catch {
    Write-Host "`n  ✗ Error fetching alerts: $($_.Exception.Message)" -ForegroundColor Red
}

# =====================================================
# 9. SUMMARY REPORT
# =====================================================
Write-Host "`n[STEP 9] Rapport Final..." -ForegroundColor Yellow
Write-Host "═" * 50

Write-Host "`n  📊 Résumé du Test:`n" -ForegroundColor Cyan

Write-Host "  Agents:" -ForegroundColor Cyan
Write-Host "    • Enregistrés: $($agents.Count)" -ForegroundColor Green
Write-Host "    • Actifs: $($agents | Where-Object { $_.Status -eq 'active' } | Measure-Object).Count" -ForegroundColor Green
Write-Host ""

Write-Host "  Tâches Auditées:" -ForegroundColor Cyan
Write-Host "    • Soumises: $($tasks.Count)" -ForegroundColor Green
foreach ($task in $tasks) {
    Write-Host "      → Agent $($task.AgentIndex): $($task.Command)" -ForegroundColor Gray
}
Write-Host ""

Write-Host "  Performance:" -ForegroundColor Cyan
if ($tasks.Count -gt 0) {
    $avgTime = [Math]::Round(($tasks.ExecutionTime | Measure-Object -Average).Average)
    $maxTime = ($tasks.ExecutionTime | Measure-Object -Maximum).Maximum
    $minTime = ($tasks.ExecutionTime | Measure-Object -Minimum).Minimum
    
    Write-Host "    • Temps moyen: $avgTime ms" -ForegroundColor Green
    Write-Host "    • Temps max: $maxTime ms" -ForegroundColor Yellow
    Write-Host "    • Temps min: $minTime ms" -ForegroundColor Yellow
}

# =====================================================
# 10. NEXT STEPS
# =====================================================
Write-Host "`n[INFO] Prochaines Étapes..." -ForegroundColor Cyan
Write-Host "═" * 50

Write-Host "`n  Voir les résultats en détail:" -ForegroundColor Yellow
Write-Host "    • Dashboard Web: http://localhost:8080"
Write-Host "    • Swagger UI: $ServerUrl/docs"
Write-Host ""

Write-Host "  Lancer d'autres tests:" -ForegroundColor Yellow
Write-Host "    • Tests simples: .\scripts\test\quick_api_test.ps1"
Write-Host "    • Tests complets: .\scripts\test\test_backend_complete.ps1"
Write-Host ""

Write-Host "  Tester avec plus d'agents:" -ForegroundColor Yellow
Write-Host "    • .\scripts\test\multi_agent_audit_test.ps1 -NumAgents 5"
Write-Host "    • .\scripts\test\multi_agent_audit_test.ps1 -NumAgents 10"
Write-Host ""

Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║     ✅ Test Multi-Agents Complété!             ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════╝`n" -ForegroundColor Green
