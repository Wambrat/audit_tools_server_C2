#!/usr/bin/env powershell
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "jadus Server - TLS Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "[1/5] Verification Docker..." -ForegroundColor Yellow
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERREUR: Docker non installe" -ForegroundColor Red
    exit 1
}
Write-Host "OK - Docker trouve" -ForegroundColor Green

Write-Host ""
Write-Host "[2/5] Verification Docker Compose..." -ForegroundColor Yellow
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "ERREUR: Docker Compose non installe" -ForegroundColor Red
    exit 1
}
Write-Host "OK - Docker Compose trouve" -ForegroundColor Green

Write-Host ""
Write-Host "[3/5] Gestion certificats TLS..." -ForegroundColor Yellow
$certsPath = "./certs"
$apiCertPath = "./certs/api.pem"

if ((Test-Path $certsPath) -and (Test-Path $apiCertPath)) {
    Write-Host "OK - Certificats existent" -ForegroundColor Green
}
else {
    Write-Host "Generation certificats auto-signes..." -ForegroundColor Yellow
    if (Test-Path ".\generate-certs.ps1") {
        & ".\generate-certs.ps1"
        Write-Host "OK - Certificats generes" -ForegroundColor Green
    }
    else {
        Write-Host "ERREUR: generate-certs.ps1 non trouve" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "[4/5] Configuration variables environnement..." -ForegroundColor Yellow
if (Test-Path ".\.env") {
    Write-Host "OK - .env existe" -ForegroundColor Green
}
else {
    if (Test-Path ".\.env.example") {
        Copy-Item ".\.env.example" ".\.env"
        Write-Host "OK - .env cree depuis .env.example" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[5/5] Demarrage services Docker..." -ForegroundColor Yellow
Write-Host "Arret services precedents..." -ForegroundColor Gray
$ErrorActionPreference = "Continue"
docker-compose down 2>&1 | Out-Null
$ErrorActionPreference = "Stop"
Write-Host "Construction et demarrage..." -ForegroundColor Gray
$ErrorActionPreference = "Continue"
docker-compose up -d --build
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "OK - Services en demarrage" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host ""
Write-Host "Attente demarrage..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "Etat services:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "URLs d acces:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Frontend/Panel : https://localhost" -ForegroundColor Green
Write-Host "  API Docs       : https://localhost/api/docs" -ForegroundColor Green
Write-Host "  Health         : https://localhost/health" -ForegroundColor Green
Write-Host ""
Write-Host "Logs (Ctrl+C pour arreter):" -ForegroundColor Yellow
Write-Host ""
docker-compose logs -f

