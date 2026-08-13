#Requires -Version 5.0

param(
    [string]$ServerUrl = "http://localhost:8000/api",
    [int]$BeaconInterval = 30,
    [string]$LogFile = "./agent_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
)

$ErrorActionPreference = "Stop"
$WarningPreference = "SilentlyContinue"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    $color = "White"
    if ($Level -eq "ERROR") { $color = "Red" }
    elseif ($Level -eq "SUCCESS") { $color = "Green" }
    elseif ($Level -eq "WARNING") { $color = "Yellow" }
    elseif ($Level -eq "DEBUG") { $color = "Gray" }
    Write-Host $logEntry -ForegroundColor $color
    if ($LogFile) { Add-Content -Path $LogFile -Value $logEntry }
}

function Show-Banner {
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host "        C2 AUTONOMOUS AGENT - PowerShell" -ForegroundColor Cyan
    Write-Host "        Active Monitoring & Audit Execution" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Get-SystemInfo {
    return @{
        hostname = $env:COMPUTERNAME
        username = $env:USERNAME
        os_version = [Environment]::OSVersion.VersionString
        agent_name = "PS-AGENT-$($env:COMPUTERNAME)-$(Get-Random -Min 1000 -Max 9999)"
    }
}

function Invoke-Enrollment {
    param([string]$ServerUrl)
    Write-Log "Attempting enrollment..." "INFO"
    
    $systemInfo = Get-SystemInfo
    $body = $systemInfo | ConvertTo-Json
    
    try {
        $response = Invoke-WebRequest -Uri "$ServerUrl/enroll" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop -UseBasicParsing
        $result = $response.Content | ConvertFrom-Json
        Write-Log "Enrollment successful! Agent ID: $($result.agent_id)" "SUCCESS"
        return @{ agent_id = $result.agent_id; api_key = $result.api_key; agent_name = $systemInfo.agent_name }
    }
    catch {
        Write-Log "Enrollment failed: $_" "ERROR"
        return $null
    }
}

function Execute-Command {
    param([string]$Command)
    
    $result = @{ status = "success"; result = ""; error_message = $null }
    
    try {
        switch -Wildcard ($Command) {
            "Get-Process*" {
                $result.result = (Get-Process | Select-Object Name, Id, WorkingSet | ConvertTo-Json)
            }
            "Get-Service*" {
                $result.result = (Get-Service | Select-Object Name, DisplayName, Status | ConvertTo-Json)
            }
            "Get-AuditPolicy*" {
                $result.result = (auditpol /get /category:* 2>&1 | Out-String)
            }
            "SystemInfo*" {
                $result.result = (systeminfo 2>&1 | Out-String)
            }
            "Get-LocalUser*" {
                $result.result = (Get-LocalUser | Select-Object Name, Enabled | ConvertTo-Json)
            }
            "Get-LocalGroup*" {
                $result.result = (Get-LocalGroup | Select-Object Name | ConvertTo-Json)
            }
            "Get-IPConfig*" {
                $result.result = (ipconfig 2>&1 | Out-String)
            }
            default {
                $result.status = "failed"
                $result.error_message = "Unknown command: $Command"
            }
        }
    }
    catch {
        $result.status = "failed"
        $result.error_message = $_.Exception.Message
    }
    
    return $result
}

function Invoke-Beacon {
    param([string]$ServerUrl, [string]$AgentId, [string]$ApiKey, [string]$LastTaskId)
    
    $body = @{
        agent_id = $AgentId
        api_key = $ApiKey
        status = "online"
        last_task_id = $LastTaskId
        uptime_seconds = [int]((Get-Date) - $script:StartTime).TotalSeconds
    } | ConvertTo-Json
    
    try {
        $response = Invoke-WebRequest -Uri "$ServerUrl/beacon" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop -UseBasicParsing
        $result = $response.Content | ConvertFrom-Json
        Write-Log "Beacon: Tasks=$($result.tasks.Count), Interval=$($result.next_beacon_interval)s" "DEBUG"
        return @{ success = $true; tasks = $result.tasks; next_beacon_interval = $result.next_beacon_interval }
    }
    catch {
        Write-Log "Beacon failed: $_" "WARNING"
        return @{ success = $false; tasks = @(); next_beacon_interval = $BeaconInterval }
    }
}

function Submit-Result {
    param([string]$ServerUrl, [string]$AgentId, [string]$ApiKey, [object]$TaskResult)
    
    $body = @{
        agent_id = $AgentId
        api_key = $ApiKey
        task_id = $TaskResult.task_id
        status = $TaskResult.status
        result = $TaskResult.result
        execution_time_ms = $TaskResult.execution_time_ms
        error_message = $TaskResult.error_message
    } | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-WebRequest -Uri "$ServerUrl/results" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop -UseBasicParsing
        Write-Log "Result submitted for task $($TaskResult.task_id)" "SUCCESS"
        return $true
    }
    catch {
        Write-Log "Result submission failed: $_" "ERROR"
        return $false
    }
}

function Main {
    Show-Banner
    Write-Log "Server URL: $ServerUrl" "INFO"
    Write-Log "Beacon Interval: $BeaconInterval seconds" "INFO"
    Write-Log "Log File: $LogFile" "INFO"
    Write-Log "" "INFO"
    
    $agentInfo = Invoke-Enrollment $ServerUrl
    if (-not $agentInfo) {
        Write-Log "Enrollment failed. Exiting." "ERROR"
        exit 1
    }
    
    $AgentId = $agentInfo.agent_id
    $ApiKey = $agentInfo.api_key
    
    Write-Log "Agent registered: $($agentInfo.agent_name)" "SUCCESS"
    Write-Log "Entering main loop (Ctrl+C to stop)..." "INFO"
    Write-Log "" "INFO"
    
    $script:StartTime = Get-Date
    $beaconCount = 0
    $taskCount = 0
    $lastTaskId = $null
    
    while ($true) {
        try {
            $beaconCount++
            Write-Log "==================================================" "DEBUG"
            Write-Log "Beacon #$beaconCount [$(Get-Date -Format 'HH:mm:ss')]" "INFO"
            
            $beaconResponse = Invoke-Beacon $ServerUrl $AgentId $ApiKey $lastTaskId
            
            if ($beaconResponse.success -and $beaconResponse.tasks.Count -gt 0) {
                Write-Log "Received $($beaconResponse.tasks.Count) task(s)" "INFO"
                
                foreach ($task in $beaconResponse.tasks) {
                    try {
                        $taskCount++
                        $tid = $task.task_id
                        Write-Log "Task #$taskCount`: $tid" "INFO"
                        
                        $startTime = Get-Date
                        $cmdResult = Execute-Command $task.command
                        $executionTime = (Get-Date) - $startTime
                        
                        $taskResult = @{
                            task_id = $task.task_id
                            status = $cmdResult.status
                            result = $cmdResult.result
                            error_message = $cmdResult.error_message
                            execution_time_ms = [int]$executionTime.TotalMilliseconds
                        }
                        
                        $lastTaskId = $task.task_id
                        
                        $submitted = Submit-Result $ServerUrl $AgentId $ApiKey $taskResult
                        if (-not $submitted) {
                            Write-Log "Will retry on next beacon" "WARNING"
                        }
                    }
                    catch {
                        Write-Log "Task error: $_" "ERROR"
                    }
                }
            }
            else {
                Write-Log "No tasks" "DEBUG"
            }
            
            $nextInterval = $beaconResponse.next_beacon_interval
            if ($nextInterval -gt 0) {
                Write-Log "Next beacon in $nextInterval seconds" "DEBUG"
                Start-Sleep -Seconds $nextInterval
            }
        }
        catch {
            Write-Log "Loop error: $_" "ERROR"
            Write-Log "Retrying in $BeaconInterval seconds" "WARNING"
            Start-Sleep -Seconds $BeaconInterval
        }
    }
}

try {
    Main
}
catch {
    Write-Log "Fatal: $_" "ERROR"
    exit 1
}
