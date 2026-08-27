#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Master test orchestration script for jadus Backend
    
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

â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘       jadus BACKEND - MASTER TEST ORCHESTRATION              â•‘
â•‘                                                            â•‘
â•‘  This script will:                                         â•‘
â•‘  1ï¸âƒ£  Start the FastAPI server in background               â•‘
â•‘  2ï¸âƒ£  Run comprehensive test suite                         â•‘
â•‘  3ï¸âƒ£  Generate detailed report                             â•‘
â•‘                                                            â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

"@ -ForegroundColor Cyan

$projectPath = "C:\Users\perso\OneDrive\Documents\esgi\yearly_project_5\jadus"

# ========== PHASE 1: START SERVER ==========
Write-Host "PHASE 1: Starting Server" -ForegroundColor Yellow
Write-Host "â”€" * 60 -ForegroundColor Cyan

try {
    Set-Location $projectPath
    
    if ($NoBackground) {
        Write-Host "âš ï¸  Running server in foreground (new terminal may open)" -ForegroundColor Yellow
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
        
        Write-Host "âœ… Server started (PID: $($serverProcess.Id))" -ForegroundColor Green
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
                Write-Host "âœ… Server is ready!" -ForegroundColor Green
            } catch {
                $retry++
                Write-Host "   Attempt $retry/$maxRetries..." -ForegroundColor Gray
            }
        }
        
        if (-not $serverReady) {
            Write-Host "âŒ Server failed to start" -ForegroundColor Red
            Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
            exit 1
        }
    }
    
} catch {
    Write-Host "âŒ Error starting server: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ========== PHASE 2: RUN TESTS ==========
if (-not $NoAutoTest) {
    Write-Host "`n`nPHASE 2: Running Test Suite" -ForegroundColor Yellow
    Write-Host "â”€" * 60 -ForegroundColor Cyan
    Write-Host "`n" -NoNewline
    
    try {
        $testScriptPath = Join-Path $projectPath "test_backend_complete.ps1"
        
        if (Test-Path $testScriptPath) {
            # Run tests with server already running
            & $testScriptPath -SkipTests -SkipServer
        } else {
            Write-Host "âŒ Test script not found: $testScriptPath" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "âŒ Error running tests: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# ========== PHASE 3: SUMMARY ==========
Write-Host "`n`nPHASE 3: Summary" -ForegroundColor Yellow
Write-Host "â”€" * 60 -ForegroundColor Cyan

Write-Host @"

âœ… Backend Testing Complete!

Next Steps:
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

1. ðŸŒ Open Swagger UI:
   http://localhost:8000/docs

2. ðŸ§ª Test API endpoints manually in Swagger

3. ðŸŽ¨ Start frontend:
   cd .\web
   npm install
   npm start

4. ðŸ”— Verify frontend-backend integration:
   - Check CORS headers working
   - Verify auth endpoints
   - Test data flow

5. ðŸ“Š Monitor logs:
   Get-Content logs/*.log -Tail 20

Resources:
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
- API Documentation:  http://localhost:8000/redoc
- Health Check:       http://localhost:8000/health
- Root:               http://localhost:8000/

To stop the server:
   1. Find it: Get-Process python
   2. Stop it: Stop-Process -Name python -Force
   (Or just close the minimized window)

"@ -ForegroundColor Green

Write-Host "â•" * 60 -ForegroundColor Cyan

