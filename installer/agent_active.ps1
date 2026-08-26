#Requires -Version 5.0

param(
    [string]$ServerUrl = "http://localhost:8000/api",
    [int]$BeaconInterval = 30,
    [string]$LogFile = "./agent_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
)

$ErrorActionPreference = "Stop"
$WarningPreference = "SilentlyContinue"

# --- TLS : forcer TLS 1.2/1.3 et accepter le certificat auto-signe du serveur ---
# Necessaire pour joindre nginx en https avec un certificat auto-signe.
# NB securite : en production, deployer plutot le certificat/CA de confiance sur
# les postes (GPO) et retirer ce contournement.
try {
    [System.Net.ServicePointManager]::SecurityProtocol = `
        [System.Net.SecurityProtocolType]::Tls12 -bor [System.Net.SecurityProtocolType]::Tls13
} catch {
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
}
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

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
        $statusCode = if ($_.Exception -and $_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { $null }
        $errorMessage = if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $_.ErrorDetails.Message } else { $_.Exception.Message }

        if ($statusCode -eq 409) {
            Write-Log "Enrollment blocked: Agent already active on this host. Please wait for the current session to disconnect before re-enrolling." "WARNING"
            return $null
        }

        Write-Log "Enrollment failed: $errorMessage" "ERROR"
        return $null
    }
}

function Invoke-EnrollmentWithRetry {
    param([string]$ServerUrl)
    
    $retryIntervalSeconds = 30
    $maxRetryDurationMinutes = 5
    $longRetryIntervalMinutes = 30
    
    while ($true) {
        $cycleStartTime = Get-Date
        $cycleEndTime = $cycleStartTime.AddMinutes($maxRetryDurationMinutes)
        $attemptCount = 0
        
        Write-Log "Starting enrollment retry cycle (will try for $maxRetryDurationMinutes minutes)..." "INFO"
        
        while ((Get-Date) -lt $cycleEndTime) {
            $attemptCount++
            Write-Log "Enrollment attempt #$attemptCount..." "INFO"
            
            $result = Invoke-Enrollment -ServerUrl $ServerUrl
            
            if ($result) {
                Write-Log "✅ Enrollment successful after $attemptCount attempt(s)" "SUCCESS"
                return $result
            }
            
            $timeRemaining = New-TimeSpan -Start (Get-Date) -End $cycleEndTime
            
            if ((Get-Date) -lt $cycleEndTime) {
                Write-Log "Retrying in $retryIntervalSeconds seconds (time remaining in cycle: $([int]$timeRemaining.TotalSeconds)s)..." "WARNING"
                Start-Sleep -Seconds $retryIntervalSeconds
            }
        }
        
        Write-Log "Enrollment cycle failed after $maxRetryDurationMinutes minutes ($attemptCount attempts)" "WARNING"
        Write-Log "Waiting $longRetryIntervalMinutes minutes before next retry cycle..." "WARNING"
        
        # Afficher une barre de progression pour les 30 minutes
        for ($i = 0; $i -lt $longRetryIntervalMinutes; $i++) {
            $minutesRemaining = $longRetryIntervalMinutes - $i
            Write-Log "Next retry in $minutesRemaining minute(s)..." "DEBUG"
            Start-Sleep -Seconds 60
        }
    }
}

function ConvertTo-Hashtable {
    param([object]$InputObject)

    if ($null -eq $InputObject) {
        return @{}
    }

    if ($InputObject -is [System.Collections.IDictionary] -or $InputObject -is [hashtable]) {
        return [hashtable]$InputObject
    }

    $normalized = [ordered]@{}
    foreach ($property in $InputObject.PSObject.Properties) {
        $normalized[$property.Name] = $property.Value
    }

    return [hashtable]$normalized
}

function New-ExecutionEnvelope {
    param(
        [string]$Command,
        [string]$ExecutionStatus,
        [string]$OutputType,
        [string]$Output,
        [string]$ErrorMessage,
        [string]$EmptyReason
    )

    return [ordered]@{
        schema_version = 1
        command = $Command
        execution_status = $ExecutionStatus
        output_type = $OutputType
        output = if ($null -eq $Output) { "" } else { [string]$Output }
        error_message = if ($null -eq $ErrorMessage) { $null } else { [string]$ErrorMessage }
        empty_reason = if ($null -eq $EmptyReason) { $null } else { [string]$EmptyReason }
    }
}

function Execute-Command {
    param(
        [string]$Command,
        [object]$Parameters = @{}
    )

    $result = New-ExecutionEnvelope -Command $Command -ExecutionStatus "success" -OutputType "empty" -Output "" -ErrorMessage $null -EmptyReason $null

    try {
        $normalizedParameters = ConvertTo-Hashtable -InputObject $Parameters
        $commandToRun = $null
        $scriptBody = $null

        if ($normalizedParameters -and $normalizedParameters.ContainsKey('script') -and $normalizedParameters['script']) {
            $scriptBody = [string]$normalizedParameters['script']
        }
        elseif ($normalizedParameters -and $normalizedParameters.ContainsKey('script_body') -and $normalizedParameters['script_body']) {
            $scriptBody = [string]$normalizedParameters['script_body']
        }
        elseif ($normalizedParameters -and $normalizedParameters.ContainsKey('code') -and $normalizedParameters['code']) {
            $scriptBody = [string]$normalizedParameters['code']
        }

        if ($scriptBody) {
            $commandToRun = [ScriptBlock]::Create($scriptBody)
            $output = (& $commandToRun 2>&1 | Out-String)
        }
        elseif (Get-Command -Name $Command -ErrorAction SilentlyContinue) {
            $commandToRun = $Command
            $output = (& $commandToRun 2>&1 | Out-String)
        }
        elseif ($Command -match '^[A-Za-z0-9_\-\\/\.]+\.ps1$') {
            if (Test-Path -Path $Command -PathType Leaf) {
                $output = (& $Command 2>&1 | Out-String)
            }
            else {
                throw "Command not available on agent: $Command"
            }
        }
        else {
            throw "Command not available on agent: $Command"
        }
        if ($null -eq $output) {
            $output = ""
        }

        if ([string]::IsNullOrWhiteSpace([string]$output)) {
            $result.output_type = "empty"
            $result.empty_reason = "No output captured by the command."
            $result.output = ""
        }
        else {
            $result.output_type = "text"
            $result.output = [string]$output
        }
    }
    catch {
        $result.execution_status = "failed"
        $result.output_type = "error"
        $result.output = ""
        $result.error_message = $_.Exception.Message
        $result.empty_reason = $null
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

function ConvertTo-JsonStringLiteral {
    param([AllowNull()][string]$Value)

    if ($null -eq $Value) {
        return "null"
    }

    $escaped = [string]$Value
    $escaped = $escaped.Replace('\\', '\\\\')
    $escaped = $escaped.Replace('"', '\\"')
    $escaped = $escaped.Replace("`r", '\\r')
    $escaped = $escaped.Replace("`n", '\\n')
    $escaped = $escaped.Replace("`t", '\\t')
    $escaped = $escaped.Replace("`b", '\\b')
    $escaped = $escaped.Replace("`f", '\\f')

    $builder = New-Object System.Text.StringBuilder
    foreach ($char in $escaped.ToCharArray()) {
        $code = [int][char]$char
        if ($code -lt 0x20) {
            [void]$builder.Append("\\u")
            [void]$builder.Append($code.ToString("x4"))
        }
        else {
            [void]$builder.Append($char)
        }
    }

    return '"' + $builder.ToString() + '"'
}

function Normalize-ResultForJson {
    param([object]$Value)

    if ($null -eq $Value) {
        return ""
    }

    if ($Value -is [string]) {
        return [string]$Value
    }

    try {
        if ($Value -is [System.Collections.IDictionary] -or
            ($Value -is [System.Collections.IEnumerable] -and -not ($Value -is [string])) -or
            $Value -is [System.Management.Automation.PSCustomObject]) {
            return ($Value | ConvertTo-Json -Depth 25 -Compress)
        }
    }
    catch {
        # Fall back to string form if the object cannot be JSON serialized cleanly.
    }

    try {
        return [string]$Value
    }
    catch {
        return ($Value | Out-String).Trim()
    }
}

function Submit-Result {
    param([string]$ServerUrl, [string]$AgentId, [string]$ApiKey, [object]$TaskResult)

    try {
        $payload = [ordered]@{
            agent_id = $AgentId
            api_key = $ApiKey
            task_id = [string]$TaskResult.task_id
            status = [string]$TaskResult.status
            result = if ($null -eq $TaskResult.result) { $null } else { $TaskResult.result }
            execution_time_ms = [int]$TaskResult.execution_time_ms
            error_message = if ($null -eq $TaskResult.error_message) { $null } else { [string]$TaskResult.error_message }
        }

        $body = $payload | ConvertTo-Json -Depth 25 -Compress
        $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)

        $response = Invoke-WebRequest -Uri "$ServerUrl/results" -Method POST -ContentType "application/json; charset=utf-8" -Body $bodyBytes -ErrorAction Stop -UseBasicParsing
        Write-Log "Result submitted for task $($TaskResult.task_id)" "SUCCESS"
        return $true
    }
    catch {
        Write-Log "Result submission failed: $_" "ERROR"
        Write-Log "Body sent: $body" "DEBUG"
        return $false
    }
}

function Main {
    Show-Banner
    Write-Log "Server URL: $ServerUrl" "INFO"
    Write-Log "Beacon Interval: $BeaconInterval seconds" "INFO"
    Write-Log "Log File: $LogFile" "INFO"
    Write-Log "" "INFO"
    
    $agentInfo = Invoke-EnrollmentWithRetry $ServerUrl
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
                        $taskParameters = @{}
                        if ($task.parameters) {
                            $taskParameters = ConvertTo-Hashtable -InputObject $task.parameters
                        }

                        $cmdResult = Execute-Command -Command $task.command -Parameters $taskParameters
                        $executionTime = (Get-Date) - $startTime
                        
                        $taskResult = @{
                            task_id = $task.task_id
                            status = if ($cmdResult.execution_status -eq 'failed') { 'failed' } else { 'success' }
                            result = $cmdResult
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
