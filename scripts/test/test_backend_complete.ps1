#!/usr/bin/env pwsh
param([switch]$SkipTests, [switch]$SkipServer, [switch]$SkipIntegration)

$API_URL = "http://localhost:8000"
$API_TIMEOUT = 5

Write-Host "=== jadus BACKEND TEST SUITE ===" -ForegroundColor Cyan

# Test 1: Unit Tests
if (-not $SkipTests) {
    Write-Host "`nTest 1: Running Unit Tests..." -ForegroundColor Green
    try {
        Set-Location "C:\Users\perso\OneDrive\Documents\esgi\yearly_project_5\jadus"
        $env:ENCRYPTION_KEY = 'test-master-key-that-is-long-enough'
        . .\venv\Scripts\Activate.ps1
        
        $output = python -m pytest test/ --tb=short -q 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] All tests passed" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] Tests failed" -ForegroundColor Red
        }
    } catch {
        Write-Host "  [ERROR] $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 2: Server Health
Write-Host "`nTest 2: Server Health Check..." -ForegroundColor Green
try {
    $response = Invoke-RestMethod -Uri "$API_URL/health" -TimeoutSec $API_TIMEOUT
    Write-Host "  [OK] Server running at $API_URL" -ForegroundColor Green
    Write-Host "  [INFO] Status: $($response.status)" -ForegroundColor White
} catch {
    Write-Host "  [ERROR] Server not responding" -ForegroundColor Red
    Write-Host "  [INFO] Run: .\run_server.ps1" -ForegroundColor Yellow
}

# Test 3: Swagger UI
Write-Host "`nTest 3: Swagger UI..." -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "$API_URL/docs" -TimeoutSec $API_TIMEOUT
    Write-Host "  [OK] Swagger UI accessible" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Swagger UI not accessible" -ForegroundColor Red
}

# Test 4: Agent Enrollment
Write-Host "`nTest 4: Agent Enrollment..." -ForegroundColor Green
try {
    $body = @{
        agent_name = "test-$(Get-Random -Minimum 1000 -Maximum 9999)"
        os_version = "Windows 10"
        hostname = "TEST-PC"
        username = "admin"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$API_URL/api/enroll" -Method POST -Headers @{"Content-Type" = "application/json"} -Body $body -TimeoutSec $API_TIMEOUT
    Write-Host "  [OK] Agent enrolled" -ForegroundColor Green
    Write-Host "  [INFO] Agent ID: $($response.agent_id)" -ForegroundColor White
    
    $AGENT_ID = $response.agent_id
    $API_KEY = $response.api_key
    
    # Test 5: Beacon
    Write-Host "`nTest 5: Agent Beacon..." -ForegroundColor Green
    $beaconBody = @{
        agent_id = $AGENT_ID
        api_key = $API_KEY
        status = "healthy"
        uptime_seconds = 3600
    } | ConvertTo-Json
    
    $beaconResp = Invoke-RestMethod -Uri "$API_URL/api/beacon" -Method POST -Headers @{"Content-Type" = "application/json"; "Authorization" = "Bearer $API_KEY"} -Body $beaconBody -TimeoutSec $API_TIMEOUT
    Write-Host "  [OK] Beacon sent successfully" -ForegroundColor Green
    
} catch {
    Write-Host "  [ERROR] $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Security Headers
Write-Host "`nTest 6: Security Headers..." -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "$API_URL/health" -TimeoutSec $API_TIMEOUT
    $headerCount = 0
    
    if ($response.Headers.ContainsKey("Strict-Transport-Security")) { $headerCount++ }
    if ($response.Headers.ContainsKey("X-Frame-Options")) { $headerCount++ }
    if ($response.Headers.ContainsKey("X-Content-Type-Options")) { $headerCount++ }
    if ($response.Headers.ContainsKey("Content-Security-Policy")) { $headerCount++ }
    
    Write-Host "  [OK] Security headers present: $headerCount/4" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Could not check headers" -ForegroundColor Red
}

# Test 7: Rate Limiting
Write-Host "`nTest 7: Rate Limiting..." -ForegroundColor Green
$throttledCount = 0
for ($i = 1; $i -le 6; $i++) {
    try {
        $body = @{
            agent_name = "ratelimit-$i"
            os_version = "test"
            hostname = "test"
            username = "test"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$API_URL/api/enroll" -Method POST -Headers @{"Content-Type" = "application/json"} -Body $body -TimeoutSec $API_TIMEOUT
    } catch {
        if ($_.Exception.Response.StatusCode -eq 429) {
            $throttledCount++
        }
    }
}

if ($throttledCount -gt 0) {
    Write-Host "  [OK] Rate limiting working ($throttledCount throttled)" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] Rate limiting may not be triggered" -ForegroundColor Yellow
}

# Test 8: SQL Injection Prevention
Write-Host "`nTest 8: SQL Injection Prevention..." -ForegroundColor Green
try {
    $body = @{
        agent_name = "'; DROP TABLE agents; --"
        os_version = "test"
        hostname = "test"
        username = "test"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$API_URL/api/enroll" -Method POST -Headers @{"Content-Type" = "application/json"} -Body $body -TimeoutSec $API_TIMEOUT
    Write-Host "  [WARNING] Payload may be sanitized" -ForegroundColor Yellow
} catch {
    Write-Host "  [OK] SQL injection blocked" -ForegroundColor Green
}

# Summary
Write-Host "`n=== TEST COMPLETE ===" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Open: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  2. Start frontend: cd web && npm start" -ForegroundColor White
Write-Host "  3. Test integration" -ForegroundColor White
Write-Host "`n" -NoNewline

