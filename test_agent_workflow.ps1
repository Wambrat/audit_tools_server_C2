#!/usr/bin/env pwsh
<#
.SYNOPSIS
    C2 Agent Workflow - Complete Example
    
.DESCRIPTION
    Demonstrates the complete workflow:
    1. Agent enrolls and sends beacons
    2. Create a task in dashboard
    3. Agent receives and executes task
    4. Results appear in dashboard
    
.EXAMPLE
    # Terminal 1: Start server
    cd server_C2
    . .\venv\Scripts\Activate.ps1
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
    
    # Terminal 2: Start agent
    .\agent_active.ps1 -BeaconInterval 10
    
    # Terminal 3: Create task (this script)
    .\test_agent_workflow.ps1
#>

# Configuration
$API_URL = "http://localhost:8000/api"
$BeaconWaitTime = 15  # seconds to wait for agent to receive task

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "     C2 AGENT WORKFLOW - Complete Demonstration" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check server health
Write-Host "STEP 1: Checking server health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$API_URL/../health" -ErrorAction Stop -UseBasicParsing
    Write-Host "[OK] Server is running" -ForegroundColor Green
}
catch {
    Write-Host "[FAIL] Server not responding" -ForegroundColor Red
    Write-Host "Start the server: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Yellow
    exit 1
}

# Step 2: List current agents
Write-Host ""
Write-Host "STEP 2: Listing enrolled agents..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$API_URL/agents" -UseBasicParsing
    $agents = $response.Content | ConvertFrom-Json
    
    if ($agents.Count -eq 0) {
        Write-Host "[WARN] No agents enrolled yet" -ForegroundColor Yellow
        Write-Host "Make sure agent_active.ps1 is running: .\agent_active.ps1" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Waiting 20 seconds for agent to enroll..." -ForegroundColor Cyan
        Start-Sleep -Seconds 20
        
        $response = Invoke-WebRequest -Uri "$API_URL/agents" -UseBasicParsing
        $agents = $response.Content | ConvertFrom-Json
    }
    
    if ($agents.Count -eq 0) {
        Write-Host "[FAIL] Still no agents. Agent may have failed to enroll." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[OK] Found $($agents.Count) agent(s)" -ForegroundColor Green
    
    # Select first agent
    $agent = $agents[0]
    $AGENT_ID = $agent.agent_id
    $AGENT_NAME = $agent.agent_name
    
    Write-Host "  Agent: $AGENT_NAME" -ForegroundColor White
    Write-Host "  ID: $AGENT_ID" -ForegroundColor White
    Write-Host "  Status: $($agent.status)" -ForegroundColor White
    Write-Host "  Last Beacon: $($agent.last_beacon)" -ForegroundColor White
}
catch {
    Write-Host "[FAIL] Could not list agents" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Yellow
    exit 1
}

# Step 3: Create a task
Write-Host ""
Write-Host "STEP 3: Creating audit task..." -ForegroundColor Yellow

$commands = @(
    @{ cmd = "Get-Process"; desc = "List running processes" },
    @{ cmd = "Get-Service"; desc = "List Windows services" },
    @{ cmd = "Get-LocalUser"; desc = "List local users" }
)

Write-Host ""
Write-Host "Available commands:" -ForegroundColor Cyan
for ($i = 0; $i -lt $commands.Count; $i++) {
    Write-Host "  $($i+1). $($commands[$i].cmd) - $($commands[$i].desc)" -ForegroundColor White
}

# Default to first command (Get-Process)
$selectedCommand = $commands[0].cmd

Write-Host ""
Write-Host "Using command: $selectedCommand" -ForegroundColor Cyan

try {
    $body = @{
        command = $selectedCommand
        parameters = $null
        priority = 0
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest `
        -Uri "$API_URL/tasks/$AGENT_ID" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing `
        -ErrorAction Stop
    
    $result = $response.Content | ConvertFrom-Json
    
    Write-Host "[OK] Task created successfully" -ForegroundColor Green
    Write-Host "  Task ID: $($result.task_id)" -ForegroundColor White
    Write-Host "  Message: $($result.message)" -ForegroundColor White
}
catch {
    Write-Host "[FAIL] Could not create task" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Yellow
    exit 1
}

# Step 4: Wait for agent to receive and execute task
Write-Host ""
Write-Host "STEP 4: Waiting for agent to execute task..." -ForegroundColor Yellow
Write-Host "(Agent beacon interval is 10 seconds + execution time)" -ForegroundColor Gray
Write-Host "Waiting $BeaconWaitTime seconds..." -ForegroundColor Cyan

$waited = 0
while ($waited -lt $BeaconWaitTime) {
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 1
    $waited++
}
Write-Host ""
Write-Host "[OK] Wait complete" -ForegroundColor Green

# Step 5: Check results
Write-Host ""
Write-Host "STEP 5: Checking task results..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "$API_URL/results/$AGENT_ID" -UseBasicParsing
    $results = $response.Content | ConvertFrom-Json
    
    if ($results.Count -eq 0) {
        Write-Host "[WARN] No results yet. Task may still be executing." -ForegroundColor Yellow
    }
    else {
        Write-Host "[OK] Found $($results.Count) result(s)" -ForegroundColor Green
        
        $latestResult = $results[-1]  # Last result
        Write-Host "  Task ID: $($latestResult.task_id)" -ForegroundColor White
        Write-Host "  Status: $($latestResult.status)" -ForegroundColor White
        Write-Host "  Execution Time: $($latestResult.execution_time_ms) ms" -ForegroundColor White
        
        if ($latestResult.result) {
            $resultLength = $latestResult.result.Length
            Write-Host "  Result Size: $resultLength bytes" -ForegroundColor White
            
            # Show first 500 chars of result
            $preview = $latestResult.result.Substring(0, [Math]::Min(500, $resultLength))
            Write-Host ""
            Write-Host "  Result Preview:" -ForegroundColor Cyan
            Write-Host "  $preview..." -ForegroundColor Gray
        }
    }
}
catch {
    Write-Host "[FAIL] Could not retrieve results" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Yellow
}

# Step 6: Summary
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "                    WORKFLOW COMPLETE" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  Server:       Running at $API_URL" -ForegroundColor White
Write-Host "  Agent:        $AGENT_NAME (ID: $AGENT_ID)" -ForegroundColor White
Write-Host "  Task:         $selectedCommand" -ForegroundColor White
Write-Host "  Result:       Available in dashboard" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open dashboard: http://localhost:8000" -ForegroundColor White
Write-Host "  2. Login: admin / changeme" -ForegroundColor White
Write-Host "  3. View Results section for task output" -ForegroundColor White
Write-Host "  4. Create more tasks in Tasks section" -ForegroundColor White
Write-Host ""
