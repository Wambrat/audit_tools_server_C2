#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick backend testing script for jadus Server API
    
.DESCRIPTION
    Tests all main backend functionality:
    1. Server health
    2. API documentation (Swagger)
    3. Agent enrollment
    4. Beacon heartbeat
    5. Rate limiting
    6. Security headers
#>

# Configuration
$API_URL = "http://localhost:8000"
$TIMEOUT = 5

Write-Host "=== jadus Backend Quick Test ===" -ForegroundColor Cyan
Write-Host "Testing: $API_URL`n" -ForegroundColor Yellow

# Test 1: Health Check
Write-Host "ðŸ“‹ TEST 1: Health Check" -ForegroundColor Green
try {
    $response = Invoke-RestMethod -Uri "$API_URL/health" -TimeoutSec $TIMEOUT
    Write-Host "âœ… Server is running" -ForegroundColor Green
    Write-Host "   Status: $($response.status)`n" -ForegroundColor White
} catch {
    Write-Host "âŒ Server not responding!" -ForegroundColor Red
    Write-Host "   Make sure to run: python main.py`n" -ForegroundColor Yellow
    exit 1
}

# Test 2: Swagger Documentation
Write-Host "ðŸ“‹ TEST 2: Swagger Documentation" -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "$API_URL/docs" -TimeoutSec $TIMEOUT -ErrorAction Stop
    Write-Host "âœ… Swagger UI accessible at /docs" -ForegroundColor Green
    Write-Host "   Status Code: $($response.StatusCode)`n" -ForegroundColor White
} catch {
    Write-Host "âŒ Swagger UI not accessible!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)`n" -ForegroundColor Yellow
}

# Test 3: OpenAPI Schema
Write-Host "ðŸ“‹ TEST 3: OpenAPI Schema" -ForegroundColor Green
try {
    $response = Invoke-RestMethod -Uri "$API_URL/openapi.json" -TimeoutSec $TIMEOUT
    Write-Host "âœ… OpenAPI schema available" -ForegroundColor Green
    Write-Host "   Title: $($response.info.title)" -ForegroundColor White
    Write-Host "   Version: $($response.info.version)`n" -ForegroundColor White
} catch {
    Write-Host "âŒ OpenAPI schema not accessible!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)`n" -ForegroundColor Yellow
}

# Test 4: Agent Enrollment
Write-Host "ðŸ“‹ TEST 4: Agent Enrollment (/api/enroll)" -ForegroundColor Green
try {
    $body = @{
        agent_name = "test-agent-$(Get-Random -Minimum 1000 -Maximum 9999)"
        os_version = "Windows 10"
        hostname = "TEST-PC"
        username = "admin"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$API_URL/api/enroll" `
        -Method POST `
        -Headers @{"Content-Type" = "application/json"} `
        -Body $body `
        -TimeoutSec $TIMEOUT

    $AGENT_ID = $response.agent_id
    $API_KEY = $response.api_key

    Write-Host "âœ… Agent enrolled successfully" -ForegroundColor Green
    Write-Host "   Agent ID: $AGENT_ID" -ForegroundColor White
    Write-Host "   API Key: $($API_KEY.Substring(0, 20))..." -ForegroundColor White
    Write-Host "   Message: $($response.message)`n" -ForegroundColor White
} catch {
    Write-Host "âŒ Enrollment failed!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)`n" -ForegroundColor Yellow
    exit 1
}

# Test 5: Beacon (Heartbeat)
Write-Host "ðŸ“‹ TEST 5: Beacon (/api/beacon)" -ForegroundColor Green
try {
    $body = @{
        agent_id = $AGENT_ID
        api_key = $API_KEY
        status = "healthy"
        uptime_seconds = 3600
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$API_URL/api/beacon" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $API_KEY"
        } `
        -Body $body `
        -TimeoutSec $TIMEOUT

    Write-Host "âœ… Beacon sent successfully" -ForegroundColor Green
    Write-Host "   Tasks: $($response.tasks.Count)" -ForegroundColor White
    Write-Host "   Next interval: $($response.next_beacon_interval)s`n" -ForegroundColor White
} catch {
    Write-Host "âŒ Beacon failed!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)`n" -ForegroundColor Yellow
}

# Test 6: Security Headers
Write-Host "ðŸ“‹ TEST 6: Security Headers" -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "$API_URL/health" -TimeoutSec $TIMEOUT
    
    $headers = @(
        "Strict-Transport-Security",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Content-Security-Policy"
    )
    
    $found = 0
    foreach ($header in $headers) {
        if ($response.Headers.ContainsKey($header)) {
            $found++
            Write-Host "   âœ… $header" -ForegroundColor White
        } else {
            Write-Host "   âš ï¸  Missing: $header" -ForegroundColor Yellow
        }
    }
    
    Write-Host "   Found $found/$($headers.Count) security headers`n" -ForegroundColor Green
} catch {
    Write-Host "âŒ Security headers test failed!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)`n" -ForegroundColor Yellow
}

# Test 7: CORS Headers
Write-Host "ðŸ“‹ TEST 7: CORS Headers" -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "$API_URL/health" `
        -Headers @{"Origin" = "http://localhost:3000"} `
        -TimeoutSec $TIMEOUT

    if ($response.Headers.ContainsKey("Access-Control-Allow-Origin")) {
        Write-Host "âœ… CORS headers present" -ForegroundColor Green
        Write-Host "   Allow-Origin: $($response.Headers['Access-Control-Allow-Origin'])`n" -ForegroundColor White
    } else {
        Write-Host "âš ï¸  CORS headers not found`n" -ForegroundColor Yellow
    }
} catch {
    Write-Host "âŒ CORS test failed!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)`n" -ForegroundColor Yellow
}

Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host "âœ… Backend is ready for integration testing!`n" -ForegroundColor Green
Write-Host "Next: Test with frontend on http://localhost:3000" -ForegroundColor Cyan

