#!/usr/bin/env pwsh

Write-Host "=== Quick API Test ===" -ForegroundColor Cyan

$API = "http://localhost:8000"

# Test 1: Health
Write-Host "`n1. Health Check..." -ForegroundColor Green
try {
    $r = Invoke-RestMethod -Uri "$API/health" -TimeoutSec 5
    Write-Host "   [OK] Status: $($r.status)" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Swagger UI
Write-Host "`n2. Swagger UI..." -ForegroundColor Green
try {
    $r = Invoke-WebRequest -Uri "$API/docs" -TimeoutSec 5 -UseBasicParsing
    Write-Host "   [OK] HTTP $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] Not accessible" -ForegroundColor Red
}

# Test 3: Agent Enrollment
Write-Host "`n3. Agent Enrollment..." -ForegroundColor Green
try {
    $rand = Get-Random -Minimum 10000 -Maximum 99999
    $body = @{
        agent_name = "test-$rand"
        os_version = "Windows 10"
        hostname = "HOST-$rand"
        username = "USER-$rand"
    } | ConvertTo-Json
    
    $r = Invoke-RestMethod -Uri "$API/api/enroll" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body -TimeoutSec 5
    Write-Host "   [OK] Agent ID: $($r.agent_id)" -ForegroundColor Green
    
    $AGENT_ID = $r.agent_id
    $API_KEY = $r.api_key
    
    # Test 4: Beacon
    Write-Host "`n4. Agent Beacon..." -ForegroundColor Green
    $body2 = @{
        agent_id = $AGENT_ID
        api_key = $API_KEY
        status = "healthy"
        uptime_seconds = 3600
    } | ConvertTo-Json
    
    $r2 = Invoke-RestMethod -Uri "$API/api/beacon" -Method POST -Headers @{"Content-Type"="application/json"; "Authorization"="Bearer $API_KEY"} -Body $body2 -TimeoutSec 5
    Write-Host "   [OK] Beacon sent (Tasks: $($r2.tasks.Count))" -ForegroundColor Green
    
} catch {
    Write-Host "   [ERROR] $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Security Headers
Write-Host "`n5. Security Headers..." -ForegroundColor Green
try {
    $r = Invoke-WebRequest -Uri "$API/health" -TimeoutSec 5 -UseBasicParsing
    $count = 0
    if ($r.Headers.ContainsKey("Strict-Transport-Security")) { $count++ }
    if ($r.Headers.ContainsKey("X-Frame-Options")) { $count++ }
    if ($r.Headers.ContainsKey("Content-Security-Policy")) { $count++ }
    if ($r.Headers.ContainsKey("X-Content-Type-Options")) { $count++ }
    Write-Host "   [OK] Found $count/4 security headers" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] Could not check" -ForegroundColor Red
}

Write-Host "`n=== All Tests Complete ===" -ForegroundColor Cyan
Write-Host "`nAccess API: http://localhost:8000/docs" -ForegroundColor Yellow
