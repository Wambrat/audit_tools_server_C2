#!/usr/bin/env powershell
# Script PowerShell pour generer certificats auto-signes pour developpement TLS

param(
    [int]$Days = 365
)

$ErrorActionPreference = "Stop"

# Pour OpenSSL, on ignore les non-zéros à cause des avertissements
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "Generating self-signed certificates for development..." -ForegroundColor Cyan

$CERT_DIR = ".\certs"
if (-not (Test-Path $CERT_DIR)) {
    New-Item -ItemType Directory -Path $CERT_DIR -Force | Out-Null
}

$COUNTRY = "FR"
$STATE = "Ile-de-France"
$CITY = "Paris"
$ORG = "C2 Server Dev"

$openssl = 'C:\Program Files\Git\usr\bin\openssl.exe'
if (-not (Test-Path $openssl)) {
    Write-Host "ERROR: OpenSSL not found at $openssl" -ForegroundColor Red
    Write-Host "Please install Git for Windows or OpenSSL" -ForegroundColor Red
    exit 1
}

Write-Host "[1/10] Generating CA private key..." -ForegroundColor Yellow
& $openssl genrsa -out "$CERT_DIR\ca-key.pem" 2048 2>&1 | Where-Object { $_ -notmatch "^[0-9]+\sB" } | Out-Null

Write-Host "[2/10] Generating CA certificate..." -ForegroundColor Yellow
& $openssl req -new -x509 -days $Days `
  -key "$CERT_DIR\ca-key.pem" `
  -out "$CERT_DIR\ca.pem" `
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=C2-CA" 2>&1 | Out-Null

Write-Host "[3/10] Generating MongoDB server key..." -ForegroundColor Yellow
& $openssl genrsa -out "$CERT_DIR\mongodb-key.pem" 2048 2>&1 | Where-Object { $_ -notmatch "^[0-9]+\sB" } | Out-Null

Write-Host "[4/10] Generating MongoDB CSR..." -ForegroundColor Yellow
& $openssl req -new `
  -key "$CERT_DIR\mongodb-key.pem" `
  -out "$CERT_DIR\mongodb.csr" `
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=mongodb" 2>&1 | Out-Null

Write-Host "[5/10] Signing MongoDB certificate..." -ForegroundColor Yellow
& $openssl x509 -req `
  -in "$CERT_DIR\mongodb.csr" `
  -CA "$CERT_DIR\ca.pem" `
  -CAkey "$CERT_DIR\ca-key.pem" `
  -CAcreateserial `
  -out "$CERT_DIR\mongodb.pem" `
  -days $Days -sha256 2>&1 | Out-Null

Write-Host "[6/10] Combining MongoDB key and certificate..." -ForegroundColor Yellow
$mongodbKey = Get-Content "$CERT_DIR\mongodb-key.pem" -Raw
$mongodbCert = Get-Content "$CERT_DIR\mongodb.pem" -Raw
Set-Content -Path "$CERT_DIR\mongodb-combined.pem" -Value ($mongodbKey + $mongodbCert)

Write-Host "[7/10] Generating API server key..." -ForegroundColor Yellow
& $openssl genrsa -out "$CERT_DIR\api-key.pem" 2048 2>&1 | Where-Object { $_ -notmatch "^[0-9]+\sB" } | Out-Null

Write-Host "[8/10] Generating SAN configuration..." -ForegroundColor Yellow
$sanConfig = @"
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = $COUNTRY
ST = $STATE
L = $CITY
O = $ORG
CN = localhost

[v3_req]
subjectAltName = DNS:localhost,DNS:api,DNS:frontend,DNS:127.0.0.1,DNS:*.c2-network
"@

Set-Content -Path "$CERT_DIR\api-san.conf" -Value $sanConfig

Write-Host "[9/10] Generating API CSR..." -ForegroundColor Yellow
& $openssl req -new `
  -key "$CERT_DIR\api-key.pem" `
  -out "$CERT_DIR\api.csr" `
  -config "$CERT_DIR\api-san.conf" 2>&1 | Out-Null

Write-Host "[10/10] Signing API certificate..." -ForegroundColor Yellow
& $openssl x509 -req `
  -in "$CERT_DIR\api.csr" `
  -CA "$CERT_DIR\ca.pem" `
  -CAkey "$CERT_DIR\ca-key.pem" `
  -CAcreateserial `
  -out "$CERT_DIR\api.pem" `
  -days $Days -sha256 `
  -extensions v3_req `
  -extfile "$CERT_DIR\api-san.conf" 2>&1 | Out-Null

Write-Host "Cleaning temporary files..." -ForegroundColor Gray
Remove-Item "$CERT_DIR\mongodb.csr" -Force -ErrorAction SilentlyContinue
Remove-Item "$CERT_DIR\api.csr" -Force -ErrorAction SilentlyContinue
Remove-Item "$CERT_DIR\ca.srl" -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "SUCCESS - Certificates generated!" -ForegroundColor Green
Write-Host ""
Write-Host "Generated files:" -ForegroundColor Cyan
Get-ChildItem "$CERT_DIR\*.pem" | ForEach-Object {
    $sizeKB = [Math]::Round($_.Length / 1KB, 2)
    Write-Host "  - $($_.Name) ($sizeKB KB)"
}

Write-Host ""
Write-Host "Files summary:" -ForegroundColor Cyan
Write-Host "  - ca.pem                  : CA certificate (for clients)"
Write-Host "  - mongodb-combined.pem    : MongoDB server cert + key"
Write-Host "  - api.pem                 : API/Nginx certificate"
Write-Host "  - api-key.pem             : API/Nginx private key"

Write-Host ""
Write-Host "To trust the CA locally on Windows:" -ForegroundColor Yellow
Write-Host "  certutil -addstore -f 'Root' $CERT_DIR\ca.pem"
Write-Host ""
Write-Host "Next step: docker-compose up -d --build" -ForegroundColor Green
