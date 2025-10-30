#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 RS256 Key Generation Script${NC}"
echo "================================"

# Configuration
KEY_DIR="${KEY_DIR:-./keys}"
KEY_SIZE="${KEY_SIZE:-2048}"
PRIVATE_KEY_FILE="$KEY_DIR/private.pem"
PUBLIC_KEY_FILE="$KEY_DIR/public.pem"
BACKUP_DIR="$KEY_DIR/backup"

# Create directories
mkdir -p "$KEY_DIR"
mkdir -p "$BACKUP_DIR"

# Backup existing keys if they exist
if [ -f "$PRIVATE_KEY_FILE" ]; then
    echo -e "${YELLOW}⚠️  Existing keys found, creating backup...${NC}"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    cp "$PRIVATE_KEY_FILE" "$BACKUP_DIR/private_$TIMESTAMP.pem"
    cp "$PUBLIC_KEY_FILE" "$BACKUP_DIR/public_$TIMESTAMP.pem"
    echo -e "${GREEN}✓ Backup created in $BACKUP_DIR${NC}"
fi

# Generate private key
echo -e "\n${GREEN}Generating ${KEY_SIZE}-bit RSA private key...${NC}"
openssl genrsa -out "$PRIVATE_KEY_FILE" "$KEY_SIZE" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Private key generated${NC}"
else
    echo -e "${RED}✗ Failed to generate private key${NC}"
    exit 1
fi

# Extract public key
echo -e "${GREEN}Extracting public key...${NC}"
openssl rsa -in "$PRIVATE_KEY_FILE" -pubout -out "$PUBLIC_KEY_FILE" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Public key extracted${NC}"
else
    echo -e "${RED}✗ Failed to extract public key${NC}"
    exit 1
fi

# Set secure permissions
chmod 600 "$PRIVATE_KEY_FILE"  # Read/write for owner only
chmod 644 "$PUBLIC_KEY_FILE"   # Read for all

echo -e "\n${GREEN}🔍 Verification${NC}"
echo "================================"

# Verify private key
echo -e "${GREEN}Verifying private key...${NC}"
openssl rsa -in "$PRIVATE_KEY_FILE" -check -noout 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Private key is valid${NC}"
else
    echo -e "${RED}✗ Private key verification failed${NC}"
    exit 1
fi

# Verify public key
echo -e "${GREEN}Verifying public key...${NC}"
openssl rsa -pubin -in "$PUBLIC_KEY_FILE" -text -noout >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Public key is valid${NC}"
else
    echo -e "${RED}✗ Public key verification failed${NC}"
    exit 1
fi

# Display key info
echo -e "\n${GREEN}📝 Key Information${NC}"
echo "================================"
echo "Private key: $PRIVATE_KEY_FILE"
echo "Public key:  $PUBLIC_KEY_FILE"
echo "Key size:    $KEY_SIZE bits"
echo "Permissions: Private (600), Public (644)"

# Display public key for distribution
echo -e "\n${GREEN}📤 Public Key (for distribution to services)${NC}"
echo "================================"
cat "$PUBLIC_KEY_FILE"

# Security warnings
echo -e "\n${YELLOW}⚠️  SECURITY WARNINGS${NC}"
echo "================================"
echo "1. NEVER commit private.pem to version control"
echo "2. Store private key in secrets manager (Vault/AWS Secrets)"
echo "3. Distribute public key via environment variables"
echo "4. Implement key rotation every 90 days"
echo "5. Monitor private key access in production"

# Create .gitignore if it doesn't exist
if [ ! -f "$KEY_DIR/.gitignore" ]; then
    echo -e "\n${GREEN}Creating .gitignore...${NC}"
    cat > "$KEY_DIR/.gitignore" <<EOF
# Ignore all .pem files
*.pem
# Ignore backup directory
backup/
EOF
    echo -e "${GREEN}✓ .gitignore created${NC}"
fi

echo -e "\n${GREEN}✅ Key generation complete!${NC}"
