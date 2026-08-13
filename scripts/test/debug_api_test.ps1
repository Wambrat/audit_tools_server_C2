#!/usr/bin/env pwsh

Write-Host "=== Debug API Test ===" -ForegroundColor Cyan

$API = "http://127.0.0.1:8000"

Write-Host "Testing with: $API`n" -ForegroundColor Yellow

# Test 1: Health
Write-Host "1. Health Check..." -ForegroundColor Green
try {
    $r = Invoke-RestMethod -Uri "$API/health" -TimeoutSec 5
    Write-Host "   [OK] Status: $($r.status)" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Root
Write-Host "`n2. Root Endpoint..." -ForegroundColor Green
try {
    $r = Invoke-RestMethod -Uri "$API/" -TimeoutSec 5
    Write-Host "   [OK] Service: $($r.service) v$($r.version)" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Docs (with full response)
Write-Host "`n3. Swagger UI (/docs)..." -ForegroundColor Green
try {
    $r = Invoke-WebRequest -Uri "$API/docs" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "   [OK] HTTP $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "   [DEBUG] Full error: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Test 4: OpenAPI
Write-Host "`n4. OpenAPI Schema..." -ForegroundColor Green
try {
    $r = Invoke-RestMethod -Uri "$API/openapi.json" -TimeoutSec 5
    Write-Host "   [OK] Schema title: $($r.info.title)" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Agent Enrollment (with verbose error)
Write-Host "`n5. Agent Enrollment..." -ForegroundColor Green
try {
    $rand = Get-Random -Minimum 10000 -Maximum 99999
    $agentName = "debug-$rand"
    $hostname = "HOST-$rand"
    $username = "USER-$rand"
    
    Write-Host "   [DEBUG] Agent: $agentName" -ForegroundColor Gray
    Write-Host "   [DEBUG] Hostname: $hostname" -ForegroundColor Gray
    
    $body = @{
        agent_name = $agentName
        os_version = "Windows 10"
        hostname = $hostname
        username = $username
    } | ConvertTo-Json
    
    Write-Host "   [DEBUG] Body: $body" -ForegroundColor Gray
    
    $r = Invoke-RestMethod -Uri "$API/api/enroll" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $body `
        -TimeoutSec 5
    
    Write-Host "   [OK] Agent ID: $($r.agent_id)" -ForegroundColor Green
    $script:AGENT_ID = $r.agent_id
    $script:API_KEY = $r.api_key
} catch {
    Write-Host "   [ERROR] Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "   [ERROR] Message: $($_.Exception.Message)" -ForegroundColor Red
    try {
        $errorBody = $_.Exception.Response.Content.ReadAsStream() | ForEach-Object { [System.IO.StreamReader]::new($_).ReadToEnd() }
        Write-Host "   [DEBUG] Response: $errorBody" -ForegroundColor Yellow
    } catch {}
}

# Test 6: Beacon (if enrollment worked)
if ($AGENT_ID) {
    Write-Host "`n6. Agent Beacon..." -ForegroundColor Green
    try {
        $body2 = @{
            agent_id = $AGENT_ID
            api_key = $API_KEY
            status = "healthy"
            uptime_seconds = 3600
        } | ConvertTo-Json
        
        $r2 = Invoke-RestMethod -Uri "$API/api/beacon" `
            -Method POST `
            -Headers @{"Content-Type"="application/json"; "Authorization"="Bearer $API_KEY"} `
            -Body $body2 `
            -TimeoutSec 5
        
        Write-Host "   [OK] Beacon sent (Tasks: $($r2.tasks.Count))" -ForegroundColor Green
    } catch {
        Write-Host "   [ERROR] $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        Write-Host "   [ERROR] $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 7: Security Headers
Write-Host "`n7. Security Headers..." -ForegroundColor Green
try {
    $r = Invoke-WebRequest -Uri "$API/health" -TimeoutSec 5 -UseBasicParsing
    $count = 0
    if ($r.Headers.ContainsKey("Strict-Transport-Security")) { $count++ }
    if ($r.Headers.ContainsKey("X-Frame-Options")) { $count++ }
    if ($r.Headers.ContainsKey("Content-Security-Policy")) { $count++ }
    if ($r.Headers.ContainsKey("X-Content-Type-Options")) { $count++ }
    Write-Host "   [OK] Found $count/4 security headers" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] Could not check: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Debug Complete ===" -ForegroundColor Cyan
