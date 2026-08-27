#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick server startup script for jadus Backend
    
.DESCRIPTION
    Starts the FastAPI server with all necessary environment variables
    
.EXAMPLE
    .\run_server.ps1
    .\run_server.ps1 -Port 8080
#>

param(
    [int]$Port = 8000,
    [string]$Host = "0.0.0.0",
    [string]$Env = "development",
    [string]$DatabaseMode = "memory"
)

Write-Host @"

â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘          jadus BACKEND - SERVER STARTUP                      â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

"@ -ForegroundColor Cyan

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Host: $Host" -ForegroundColor White
Write-Host "  Port: $Port" -ForegroundColor White
Write-Host "  Environment: $Env" -ForegroundColor White
Write-Host "  Database Mode: $DatabaseMode" -ForegroundColor White
Write-Host "`n" -ForegroundColor White

try {
    # Navigate to project directory
    $projectPath = "C:\Users\perso\OneDrive\Documents\esgi\yearly_project_5\jadus"
    if (-not (Test-Path $projectPath)) {
        Write-Host "âŒ Project directory not found: $projectPath" -ForegroundColor Red
        exit 1
    }
    
    Set-Location $projectPath
    Write-Host "ðŸ“ Working directory: $projectPath`n" -ForegroundColor Green
    
    # Set environment variables
    Write-Host "ðŸ”§ Setting environment variables..." -ForegroundColor Cyan
    $env:ENCRYPTION_KEY = 'test-master-key-that-is-long-enough'
    $env:DATABASE_MODE = $DatabaseMode
    $env:PORT = $Port
    $env:HOST = $Host
    $env:ENV = $Env
    $env:LOG_LEVEL = "INFO"
    
    Write-Host "   âœ… ENCRYPTION_KEY set" -ForegroundColor Green
    Write-Host "   âœ… DATABASE_MODE set to: $DatabaseMode" -ForegroundColor Green
    Write-Host "   âœ… PORT set to: $Port" -ForegroundColor Green
    Write-Host "   âœ… Environment set to: $Env`n" -ForegroundColor Green
    
    # Activate virtual environment
    Write-Host "ðŸ Activating Python virtual environment..." -ForegroundColor Cyan
    . .\venv\Scripts\Activate.ps1
    Write-Host "   âœ… Virtual environment activated`n" -ForegroundColor Green
    
    # Start server
    Write-Host "ðŸš€ Starting FastAPI server...`n" -ForegroundColor Cyan
    Write-Host "â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€" -ForegroundColor White
    
    python main.py
    
} catch {
    Write-Host "`nâŒ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    Write-Host "`nâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€" -ForegroundColor White
    Write-Host "Server stopped" -ForegroundColor Yellow
}

