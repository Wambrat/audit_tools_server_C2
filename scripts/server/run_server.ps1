#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick server startup script for C2 Backend
    
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

╔════════════════════════════════════════════════════════════╗
║          C2 BACKEND - SERVER STARTUP                      ║
╚════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Host: $Host" -ForegroundColor White
Write-Host "  Port: $Port" -ForegroundColor White
Write-Host "  Environment: $Env" -ForegroundColor White
Write-Host "  Database Mode: $DatabaseMode" -ForegroundColor White
Write-Host "`n" -ForegroundColor White

try {
    # Navigate to project directory
    $projectPath = "C:\Users\perso\OneDrive\Documents\esgi\yearly_project_5\server_C2"
    if (-not (Test-Path $projectPath)) {
        Write-Host "❌ Project directory not found: $projectPath" -ForegroundColor Red
        exit 1
    }
    
    Set-Location $projectPath
    Write-Host "📁 Working directory: $projectPath`n" -ForegroundColor Green
    
    # Set environment variables
    Write-Host "🔧 Setting environment variables..." -ForegroundColor Cyan
    $env:ENCRYPTION_KEY = 'test-master-key-that-is-long-enough'
    $env:DATABASE_MODE = $DatabaseMode
    $env:PORT = $Port
    $env:HOST = $Host
    $env:ENV = $Env
    $env:LOG_LEVEL = "INFO"
    
    Write-Host "   ✅ ENCRYPTION_KEY set" -ForegroundColor Green
    Write-Host "   ✅ DATABASE_MODE set to: $DatabaseMode" -ForegroundColor Green
    Write-Host "   ✅ PORT set to: $Port" -ForegroundColor Green
    Write-Host "   ✅ Environment set to: $Env`n" -ForegroundColor Green
    
    # Activate virtual environment
    Write-Host "🐍 Activating Python virtual environment..." -ForegroundColor Cyan
    . .\venv\Scripts\Activate.ps1
    Write-Host "   ✅ Virtual environment activated`n" -ForegroundColor Green
    
    # Start server
    Write-Host "🚀 Starting FastAPI server...`n" -ForegroundColor Cyan
    Write-Host "────────────────────────────────────────────────────────────" -ForegroundColor White
    
    python main.py
    
} catch {
    Write-Host "`n❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    Write-Host "`n────────────────────────────────────────────────────────────" -ForegroundColor White
    Write-Host "Server stopped" -ForegroundColor Yellow
}
