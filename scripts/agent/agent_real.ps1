#Requires -Version 5.0

param(
    [string]$ServerUrl = "http://localhost:8000/api",
    [int]$BeaconInterval = 30
)

$ErrorActionPreference = "Stop"
$WarningPreference = "SilentlyContinue"

function Write-Log {
    param([string]$Message, [string]$Level = "Info")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

function Get-SystemInfo {
    Write-Log "Collecting system information..." "Info"
    return @{
        hostname = $env:COMPUTERNAME
        username = $env:USERNAME
        os_version = [Environment]::OSVersion.VersionString
        agent_name = "PS-AUDIT-$($env:COMPUTERNAME)"
    }
}

function Invoke-Enrollment {
    param([string]$ServerUrl)
    
    Write-Log "Attempting enrollment..." "Info"
    
    $systemInfo = Get-SystemInfo
    $body = $systemInfo | ConvertTo-Json
    
    try {
        $response = Invoke-WebRequest -Uri "$ServerUrl/enroll" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop
        $result = $response.Content | ConvertFrom-Json
        Write-Log "Enrollment successful! Agent ID: $($result.agent_id)" "Success"
        
        return @{
            agent_id = $result.agent_id
            api_key = $result.api_key
            agent_name = $systemInfo.agent_name
        }
    }
    catch {
        Write-Log "Enrollment failed: $_" "Error"
        return $null
    }
}

function Get-AuditPolicyOutput {
    Write-Log "Executing Get-AuditPolicy..." "Info"
    try {
        $output = auditpol /get /category:*
        return $output -join "`n"
    }
    catch {
        return "Error: Failed to retrieve audit policy"
    }
}

function Get-ServicesOutput {
    Write-Log "Executing Get-Services..." "Info"
    try {
        $services = Get-Service | Where-Object { $_.Status -eq 'Running' } | Format-Table -AutoSize | Out-String
        return $services
    }
    catch {
        return "Error: Failed to retrieve services"
    }
}

function Invoke-Task {
    param([PSObject]$Task)
    
    Write-Log "Executing task: $($Task.task_id) - $($Task.command)" "Info"
    
    $startTime = Get-Date
    $output = ""
    $errorMessage = $null
    
    try {
        switch ($Task.command) {
            "Get-AuditPolicy" {
                $output = Get-AuditPolicyOutput
            }
            { $_ -in "Get-Services", "Get-Service" } {
                $output = Get-ServicesOutput
            }
            { $_ -in "Get-Processes", "Get-Process" } {
                $output = (Get-Process | Format-Table -AutoSize | Out-String)
            }
            default {
                $errorMessage = "Unknown command: $($Task.command)"
                $output = $errorMessage
            }
        }
        
        $executionTime = (Get-Date) - $startTime
        
        return @{
            status = if ($errorMessage) { "failed" } else { "success" }
            result = $output
            error_message = $errorMessage
            execution_time_ms = [int]$executionTime.TotalMilliseconds
        }
    }
    catch {
        Write-Log "Task execution error: $_" "Error"
        $executionTime = (Get-Date) - $startTime
        
        return @{
            status = "failed"
            result = ""
            error_message = $_.Exception.Message
            execution_time_ms = [int]$executionTime.TotalMilliseconds
        }
    }
}

function Invoke-Beacon {
    param(
        [string]$ServerUrl,
        [string]$AgentId,
        [string]$ApiKey,
        [string]$LastTaskId = $null
    )
    
    try {
        $body = @{
            agent_id = $AgentId
            api_key = $ApiKey
            status = "online"
            uptime_seconds = [int]((Get-Date) - $script:StartTime).TotalSeconds
            last_task_id = $LastTaskId
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri "$ServerUrl/beacon" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop
        $result = $response.Content | ConvertFrom-Json
        
        if ($result.tasks -and $result.tasks.Count -gt 0) {
            Write-Log "Beacon received: $($result.tasks.Count) task(s)" "Success"
            return $result.tasks
        }
        else {
            Write-Log "Beacon received: No tasks" "Info"
            return @()
        }
    }
    catch {
        Write-Log "Beacon failed: $_" "Error"
        return @()
    }
}

function Submit-Result {
    param(
        [string]$ServerUrl,
        [string]$AgentId,
        [string]$ApiKey,
        [string]$TaskId,
        [PSObject]$TaskResult
    )
    
    Write-Log "Submitting result for task $TaskId..." "Info"
    
    try {
        $body = @{
            agent_id = $AgentId
            api_key = $ApiKey
            task_id = $TaskId
            status = $TaskResult.status
            result = $TaskResult.result
            execution_time_ms = $TaskResult.execution_time_ms
            error_message = $TaskResult.error_message
        } | ConvertTo-Json -Depth 10
        
        $response = Invoke-WebRequest -Uri "$ServerUrl/results" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop
        $result = $response.Content | ConvertFrom-Json
        Write-Log "Result submitted: $($result.message)" "Success"
        
        return $true
    }
    catch {
        Write-Log "Result submission failed: $_" "Error"
        return $false
    }
}

# === MAIN LOOP ===

Write-Host ""
Write-Host "========================================================" 
Write-Host "           C2 AGENT - PowerShell Audit"
Write-Host "     Autonomous Agent with Periodic Beacon"
Write-Host "========================================================"
Write-Host ""

$script:StartTime = Get-Date

Write-Log "Starting C2 Agent..." "Info"
Write-Log "Server: $ServerUrl" "Info"
Write-Log "Beacon interval: $BeaconInterval seconds" "Info"

$agentInfo = Invoke-Enrollment $ServerUrl
if (-not $agentInfo) {
    Write-Log "Failed to enroll. Exiting." "Error"
    exit 1
}

$AgentId = $agentInfo.agent_id
$ApiKey = $agentInfo.api_key

Write-Log "Agent enrolled successfully!" "Success"
Write-Log "Agent Name: $($agentInfo.agent_name)" "Info"
Write-Log "Agent ID: $AgentId" "Info"

Write-Log "Entering beacon loop (Ctrl+C to stop)..." "Info"
Write-Host ""

$lastTaskId = $null
$beaconCount = 0
$taskCount = 0

while ($true) {
    try {
        $beaconCount++
        Write-Log "Beacon #$beaconCount - Checking for tasks..." "Info"
        
        $tasks = Invoke-Beacon -ServerUrl $ServerUrl -AgentId $AgentId -ApiKey $ApiKey -LastTaskId $lastTaskId
        
        foreach ($task in $tasks) {
            $taskCount++
            Write-Log "Processing task $($taskCount): $($task.task_id)" "Info"
            
            $taskResult = Invoke-Task $task
            
            $submitted = Submit-Result -ServerUrl $ServerUrl -AgentId $AgentId -ApiKey $ApiKey -TaskId $task.task_id -TaskResult $taskResult
            
            if ($submitted) {
                $lastTaskId = $task.task_id
            }
        }
        
        Write-Log "Waiting $BeaconInterval seconds until next beacon..." "Info"
        Start-Sleep -Seconds $BeaconInterval
    }
    catch {
        Write-Log "Unexpected error in beacon loop: $_" "Error"
        Write-Log "Retrying in $BeaconInterval seconds..." "Warning"
        Start-Sleep -Seconds $BeaconInterval
    }
}
