#!/bin/bash
set -e

echo "🔄 JWT Key Rotation Procedure"
echo "=============================="
echo ""
echo "This script will:"
echo "1. Generate new RS256 key pair"
echo "2. Update auth service with new private key"
echo "3. Distribute new public key to all services"
echo "4. Maintain both old and new keys during transition"
echo "5. Remove old keys after token expiration"
echo ""

read -p "Continue with key rotation? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Generate new keys
echo -e "\n📝 Step 1: Generating new key pair..."
KEY_DIR="./keys/rotation" ./scripts/generate_keys.sh

# Upload to AWS Secrets Manager
echo -e "\n📤 Step 2: Uploading new keys to AWS Secrets Manager..."
aws secretsmanager update-secret \
    --secret-id cortex/auth/private-key-new \
    --secret-string file://keys/rotation/private.pem

aws secretsmanager update-secret \
    --secret-id cortex/auth/public-key-new \
    --secret-string file://keys/rotation/public.pem

# Update auth service
echo -e "\n🔄 Step 3: Updating auth service configuration..."
kubectl set env deployment/auth-service \
    AUTH_PRIVATE_KEY_NEW=cortex/auth/private-key-new \
    -n cortex

# Wait for rollout
kubectl rollout status deployment/auth-service -n cortex

# Distribute new public key to all services
echo -e "\n📤 Step 4: Distributing new public key to services..."
kubectl create configmap auth-public-key-new \
    --from-file=public.pem=keys/rotation/public.pem \
    -n cortex \
    --dry-run=client -o yaml | kubectl apply -f -

# Update all service deployments
for service in gateway financial ai procurement hr documents legal presentation; do
    echo "Updating $service service..."
    kubectl set env deployment/${service}-service \
        AUTH_PUBLIC_KEY_NEW=cortex/auth/public-key-new \
        -n cortex
done

echo -e "\n⏱️  Step 5: Transition period (1 hour)..."
echo "Both old and new keys are now active."
echo "Services will validate tokens with both keys."
echo ""
echo "Wait for all existing tokens to expire (max token lifetime: 60 minutes)"
read -p "Press Enter after waiting 1+ hour..."

# Switch to new keys as primary
echo -e "\n🔄 Step 6: Switching to new keys as primary..."
aws secretsmanager update-secret \
    --secret-id cortex/auth/private-key \
    --secret-string file://keys/rotation/private.pem

aws secretsmanager update-secret \
    --secret-id cortex/auth/public-key \
    --secret-string file://keys/rotation/public.pem

# Restart auth service
kubectl rollout restart deployment/auth-service -n cortex
kubectl rollout status deployment/auth-service -n cortex

# Remove old keys
echo -e "\n🗑️  Step 7: Removing old key environment variables..."
kubectl set env deployment/auth-service AUTH_PRIVATE_KEY_NEW- -n cortex

for service in gateway financial ai procurement hr documents legal presentation; do
    kubectl set env deployment/${service}-service AUTH_PUBLIC_KEY_NEW- -n cortex
done

echo -e "\n✅ Key rotation complete!"
echo ""
echo "Next steps:"
echo "1. Monitor auth service logs for errors"
echo "2. Verify token validation working across all services"
echo "3. Document rotation in security log"
echo "4. Schedule next rotation in 90 days"
