#!/bin/bash
# Script pour générer les certificats auto-signés pour développement TLS

set -e

echo "🔐 Generating self-signed certificates for development..."

CERT_DIR="./certs"
mkdir -p "$CERT_DIR"

# Paramètres
DAYS=365
COUNTRY="FR"
STATE="Ile-de-France"
CITY="Paris"
ORG="C2 Server Dev"

# 1. Générer CA privée key
echo "1️⃣ Generating CA private key..."
openssl genrsa -out "$CERT_DIR/ca-key.pem" 2048 2>/dev/null

# 2. Générer certificat CA
echo "2️⃣ Generating CA certificate..."
openssl req -new -x509 -days $DAYS -key "$CERT_DIR/ca-key.pem" -out "$CERT_DIR/ca.pem" \
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=C2-CA"

# 3. Générer MongoDB server key
echo "3️⃣ Generating MongoDB server key..."
openssl genrsa -out "$CERT_DIR/mongodb-key.pem" 2048 2>/dev/null

# 4. Générer MongoDB certificate signing request
echo "4️⃣ Generating MongoDB CSR..."
openssl req -new -key "$CERT_DIR/mongodb-key.pem" -out "$CERT_DIR/mongodb.csr" \
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=mongodb"

# 5. Signer le certificat MongoDB
echo "5️⃣ Signing MongoDB certificate..."
openssl x509 -req -in "$CERT_DIR/mongodb.csr" -CA "$CERT_DIR/ca.pem" \
  -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial -out "$CERT_DIR/mongodb.pem" \
  -days $DAYS -sha256 2>/dev/null

# 6. Combiner key + cert pour MongoDB (format PEM requis)
echo "6️⃣ Combining MongoDB key and certificate..."
cat "$CERT_DIR/mongodb-key.pem" "$CERT_DIR/mongodb.pem" > "$CERT_DIR/mongodb-combined.pem"
chmod 600 "$CERT_DIR/mongodb-combined.pem"

# 7. Générer Nginx/API server key
echo "7️⃣ Generating API server key..."
openssl genrsa -out "$CERT_DIR/api-key.pem" 2048 2>/dev/null

# 8. Générer config pour SAN (Subject Alternative Names)
cat > "$CERT_DIR/api-san.conf" << EOF
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
EOF

# 9. Générer API certificate signing request
echo "8️⃣ Generating API CSR..."
openssl req -new -key "$CERT_DIR/api-key.pem" -out "$CERT_DIR/api.csr" \
  -config "$CERT_DIR/api-san.conf"

# 10. Signer le certificat API
echo "9️⃣ Signing API certificate..."
openssl x509 -req -in "$CERT_DIR/api.csr" -CA "$CERT_DIR/ca.pem" \
  -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial -out "$CERT_DIR/api.pem" \
  -days $DAYS -sha256 -extensions v3_req -extfile "$CERT_DIR/api-san.conf" 2>/dev/null

# 11. Nettoyer fichiers temporaires
rm -f "$CERT_DIR/mongodb.csr" "$CERT_DIR/api.csr" "$CERT_DIR/ca.srl"

# 12. Définir permissions
chmod 600 "$CERT_DIR"/*.pem

echo ""
echo "✅ Certificates generated successfully!"
echo ""
echo "📁 Generated files:"
ls -lh "$CERT_DIR"/*.pem
echo ""
echo "📝 Files:"
echo "  - ca.pem                  : CA certificate (for clients)"
echo "  - mongodb-combined.pem    : MongoDB server cert + key"
echo "  - api.pem                 : API/Nginx certificate"
echo "  - api-key.pem             : API/Nginx private key"
echo ""
echo "🔑 To trust the CA locally (optional):"
echo "  Windows: certutil -addstore -f 'Root' $CERT_DIR/ca.pem"
echo "  macOS:   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain $CERT_DIR/ca.pem"
echo "  Linux:   sudo cp $CERT_DIR/ca.pem /usr/local/share/ca-certificates/ && sudo update-ca-certificates"
