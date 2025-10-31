"""Validate RS256 key pair functionality."""
import sys
from jose import jwt
from datetime import datetime, timedelta, timezone


def validate_key_pair(private_key_path: str, public_key_path: str) -> bool:
    """
    Validate that key pair can sign and verify JWT tokens.

    Returns:
        True if keys are valid, False otherwise
    """
    try:
        # Read keys
        with open(private_key_path, 'r') as f:
            private_key = f.read()

        with open(public_key_path, 'r') as f:
            public_key = f.read()

        # Create test payload
        payload = {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "roles": ["user"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }

        # Sign token with private key
        print("🔐 Signing test token with private key...")
        token = jwt.encode(payload, private_key, algorithm="RS256")
        print(f"✓ Token signed: {token[:50]}...")

        # Verify token with public key
        print("\n🔍 Verifying token with public key...")
        decoded = jwt.decode(token, public_key, algorithms=["RS256"])
        print(f"✓ Token verified: user_id={decoded['user_id']}")

        # Verify payload matches
        assert decoded['user_id'] == payload['user_id']
        assert decoded['email'] == payload['email']
        print("\n✅ Key pair validation successful!")
        print("   - Keys can sign JWT tokens")
        print("   - Keys can verify JWT tokens")
        print("   - Payload integrity maintained")

        return True

    except Exception as e:
        print(f"\n❌ Key pair validation failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python validate_keys.py <private_key_path> <public_key_path>")
        sys.exit(1)

    private_path = sys.argv[1]
    public_path = sys.argv[2]

    success = validate_key_pair(private_path, public_path)
    sys.exit(0 if success else 1)
