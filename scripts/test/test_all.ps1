#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Master test orchestration script for C2 Backend
    
.DESCRIPTION
    Coordinates server startup and comprehensive testing in one go
    Runs server in background and executes complete test suite
    
.EXAMPLE
    .\test_all.ps1
    .\test_all.ps1 -NoAutoTest
#>

param(
    [switch]$NoAutoTest,
    [switch]$NoBackground
)

$ErrorActionPreference = "Stop"

Write-Host @"

╔════════════════════════════════════════════════════════════╗
║       C2 BACKEND - MASTER TEST ORCHESTRATION              ║
║                                                            ║
║  This script will:                                         ║
║  1️⃣  Start the FastAPI server in background               ║
║  2️⃣  Run comprehensive test suite                         ║
║  3️⃣  Generate detailed report                             ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

$projectPath = "C:\Users\perso\OneDrive\Documents\esgi\yearly_project_5\server_C2"

# ========== PHASE 1: START SERVER ==========
Write-Host "PHASE 1: Starting Server" -ForegroundColor Yellow
Write-Host "─" * 60 -ForegroundColor Cyan

try {
    Set-Location $projectPath
    
    if ($NoBackground) {
        Write-Host "⚠️  Running server in foreground (new terminal may open)" -ForegroundColor Yellow
        Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor White
        
        $env:ENCRYPTION_KEY = 'test-master-key-that-is-long-enough'
        $env:DATABASE_MODE = 'memory'
        . .\venv\Scripts\Activate.ps1
        
        python main.py
        exit 0
    } else {
        # Start in background
        Write-Host "Starting server in background..." -ForegroundColor Green
        
        $serverScript = @"
            Set-Location "$projectPath"
            `$env:ENCRYPTION_KEY = 'test-master-key-that-is-long-enough'
            `$env:DATABASE_MODE = 'memory'
            `$env:LOG_LEVEL = 'INFO'
            . .\venv\Scripts\Activate.ps1
            python main.py
"@
        
        $serverProcess = Start-Process -FilePath "powershell" `
            -ArgumentList "-NoExit", "-Command", $serverScript `
            -PassThru `
            -WindowStyle Minimized
        
        Write-Host "✅ Server started (PID: $($serverProcess.Id))" -ForegroundColor Green
        Write-Host "   Waiting for server to initialize..." -ForegroundColor White
        
        # Wait for server to be ready
        $maxRetries = 30
        $retry = 0
        $serverReady = $false
        
        while ($retry -lt $maxRetries -and -not $serverReady) {
            Start-Sleep -Seconds 1
            try {
                $response = Invoke-RestMethod -Uri "http://localhost:8000/health" `
                    -TimeoutSec 2 `
                    -ErrorAction SilentlyContinue
                $serverReady = $true
                Write-Host "✅ Server is ready!" -ForegroundColor Green
            } catch {
                $retry++
                Write-Host "   Attempt $retry/$maxRetries..." -ForegroundColor Gray
            }
        }
        
        if (-not $serverReady) {
            Write-Host "❌ Server failed to start" -ForegroundColor Red
            Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
            exit 1
        }
    }
    
} catch {
    Write-Host "❌ Error starting server: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ========== PHASE 2: RUN TESTS ==========
if (-not $NoAutoTest) {
    Write-Host "`n`nPHASE 2: Running Test Suite" -ForegroundColor Yellow
    Write-Host "─" * 60 -ForegroundColor Cyan
    Write-Host "`n" -NoNewline
    
    try {
        $testScriptPath = Join-Path $projectPath "test_backend_complete.ps1"
        
        if (Test-Path $testScriptPath) {
            # Run tests with server already running
            & $testScriptPath -SkipTests -SkipServer
        } else {
            Write-Host "❌ Test script not found: $testScriptPath" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ Error running tests: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# ========== PHASE 3: SUMMARY ==========
Write-Host "`n`nPHASE 3: Summary" -ForegroundColor Yellow
Write-Host "─" * 60 -ForegroundColor Cyan

Write-Host @"

✅ Backend Testing Complete!

Next Steps:
──────────

1. 🌐 Open Swagger UI:
   http://localhost:8000/docs

2. 🧪 Test API endpoints manually in Swagger

3. 🎨 Start frontend:
   cd .\web
   npm install
   npm start

4. 🔗 Verify frontend-backend integration:
   - Check CORS headers working
   - Verify auth endpoints
   - Test data flow

5. 📊 Monitor logs:
   Get-Content logs/*.log -Tail 20

Resources:
──────────
- API Documentation:  http://localhost:8000/redoc
- Health Check:       http://localhost:8000/health
- Root:               http://localhost:8000/

To stop the server:
   1. Find it: Get-Process python
   2. Stop it: Stop-Process -Name python -Force
   (Or just close the minimized window)

"@ -ForegroundColor Green

Write-Host "═" * 60 -ForegroundColor Cyan
