# Cortex-Auth Library

**Shared authentication library for Cortex microservices** providing JWT validation, FastAPI decorators, and dependencies for distributed authentication across multiple services.

## Features

- ✅ **RS256 JWT Validation**: Secure token validation with asymmetric keys
- ✅ **FastAPI Integration**: Decorators and dependencies for route protection
- ✅ **Role-Based Access Control**: Flexible role and permission checking
- ✅ **Wildcard Permissions**: Support for `*:*` and `*:resource` patterns
- ✅ **httpOnly Cookie Support**: XSS-resistant token storage
- ✅ **Type-Safe**: Full Pydantic models with type hints
- ✅ **Comprehensive Testing**: >90% code coverage
- ✅ **Zero Configuration**: Sensible defaults with optional customization

## Installation

### Using UV (Recommended)

```bash
# From project root
uv add --path shared/cortex_auth
```

### Using pip

```bash
pip install -e shared/cortex_auth
```

## Quick Start

### 1. Setup RSA Public Key

Ensure your service has access to the RSA public key for JWT validation:

**Option A: Environment Variable (Recommended)**
```bash
export AUTH_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n..."
```

**Option B: File Path**
```bash
export AUTH_PUBLIC_KEY_PATH="keys/jwt-public.pem"
```

**Option C: Default Location**
The library will look for `keys/jwt-public.pem` in your project root if no configuration is provided.

### 2. Protect Routes with Decorators

```python
from fastapi import FastAPI, Request
from cortex_auth import require_auth, require_admin, get_current_user
from cortex_auth.models import User

app = FastAPI()

@app.get("/protected")
@require_auth
async def protected_route(request: Request):
    user = request.state.user  # User instance attached by decorator
    return {"message": f"Hello {user.name}"}

@app.delete("/admin-only")
@require_admin
async def admin_only_route(request: Request):
    return {"message": "Admin action performed"}
```

### 3. Use FastAPI Dependencies

```python
from fastapi import Depends
from cortex_auth import get_current_user_from_cookie
from cortex_auth.models import User

@app.get("/profile")
async def get_profile(user: User = Depends(get_current_user_from_cookie)):
    return {
        "user_id": user.user_id,
        "email": user.email,
        "roles": user.roles
    }
```

## Usage Patterns

### Authentication Decorators

#### `@require_auth`
Require authentication for a route:

```python
@app.get("/dashboard")
@require_auth
async def dashboard(request: Request):
    user = request.state.user
    return {"message": f"Welcome {user.name}"}
```

#### `@require_roles`
Require specific roles (OR logic by default):

```python
# User must have admin OR manager role
@app.delete("/users/{user_id}")
@require_roles(["admin", "manager"])
async def delete_user(request: Request, user_id: int):
    return {"message": "User deleted"}

# User must have BOTH admin AND manager roles
@app.post("/critical-action")
@require_roles(["admin", "manager"], require_all=True)
async def critical_action(request: Request):
    return {"message": "Action performed"}
```

#### `@require_permissions`
Require specific permissions:

```python
# User must have both permissions (AND logic by default)
@app.put("/documents/{doc_id}")
@require_permissions(["read:documents", "write:documents"])
async def update_document(request: Request, doc_id: int):
    return {"message": "Document updated"}

# User must have ANY of the permissions (OR logic)
@app.get("/reports")
@require_permissions(["read:reports", "admin:reports"], require_all=False)
async def get_reports(request: Request):
    return {"reports": []}
```

#### Convenience Decorators

```python
# Require admin role
@app.delete("/system/reset")
@require_admin
async def reset_system(request: Request):
    return {"message": "System reset"}

# Require manager or admin role
@app.post("/reports")
@require_manager
async def create_report(request: Request):
    return {"message": "Report created"}
```

### FastAPI Dependencies

#### `get_current_user_from_cookie`
Validate JWT from cookie and get user:

```python
from fastapi import Depends
from cortex_auth import get_current_user_from_cookie
from cortex_auth.models import User

@app.get("/me")
async def get_me(user: User = Depends(get_current_user_from_cookie)):
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "roles": user.roles
    }
```

#### `get_current_user`
Get user from request state (after decorator):

```python
from fastapi import Depends
from cortex_auth import require_auth, get_current_user
from cortex_auth.models import User

@app.get("/profile")
@require_auth
async def get_profile(user: User = Depends(get_current_user)):
    return {"user": user}
```

#### `get_optional_user`
Optional authentication (never raises errors):

```python
from typing import Optional
from fastapi import Depends
from cortex_auth import get_optional_user
from cortex_auth.models import User

@app.get("/public")
async def public_route(user: Optional[User] = Depends(get_optional_user)):
    if user:
        return {"message": f"Hello {user.name}"}
    return {"message": "Hello guest"}
```

#### Role-Based Dependencies

```python
from fastapi import Depends
from cortex_auth import require_admin, require_manager

# Require admin role
@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin)
):
    return {"message": "User deleted"}

# Require manager or admin role
@app.post("/reports")
async def create_report(
    manager: User = Depends(require_manager)
):
    return {"message": "Report created"}
```

## Permission System

### Permission Format
Permissions follow the format: `action:resource`

Examples:
- `read:documents` - Read documents
- `write:documents` - Write documents
- `delete:users` - Delete users
- `admin:system` - Admin access to system

### Wildcard Permissions

- `*:*` - All permissions (superuser)
- `*:documents` - All actions on documents
- `read:*` - Read action on all resources

### Checking Permissions

```python
from cortex_auth.models import User

user = User(
    user_id="123",
    email="user@example.com",
    name="Test User",
    roles=["user"],
    permissions=["read:documents", "*:reports"]
)

# Direct permission check
assert user.has_permission("read:documents") is True

# Wildcard permission check
assert user.has_permission("write:reports") is True  # *:reports allows any action
assert user.has_permission("delete:reports") is True

# Multiple permissions check
assert user.has_all_permissions(["read:documents", "write:reports"]) is True
```

## Configuration

### Environment Variables

```bash
# Public key for JWT validation (required)
AUTH_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n..."

# Or path to public key file
AUTH_PUBLIC_KEY_PATH="keys/jwt-public.pem"

# Token issuer validation (default: cortex-auth-service)
AUTH_ISSUER="cortex-auth-service"

# Clock skew tolerance in seconds (default: 60)
AUTH_CLOCK_SKEW_SECONDS=60

# Cookie name for access token (default: cortex_access_token)
AUTH_COOKIE_NAME="cortex_access_token"

# Enable/disable authentication (default: true, useful for testing)
AUTH_ENABLED=true
```

### Custom Settings

```python
from cortex_auth.config import AuthSettings

# Create custom settings instance
settings = AuthSettings(
    auth_public_key_path="/custom/path/to/public_key.pem",
    auth_issuer="my-custom-issuer",
    auth_clock_skew_seconds=120
)
```

## Testing

### Disable Authentication for Tests

```python
# In your test configuration
import os
os.environ["AUTH_ENABLED"] = "false"

# All @require_auth decorators will use a mock user
```

### Using Pytest Fixtures

```python
import pytest
from cortex_auth.models import User

@pytest.fixture
def mock_user():
    return User(
        user_id="test-user-id",
        email="test@example.com",
        name="Test User",
        roles=["user", "admin"],
        permissions=["*:*"]
    )

def test_protected_route(mock_user):
    # Test with mock user
    assert mock_user.has_role("admin")
```

## Error Handling

### Exception Types

```python
from cortex_auth.exceptions import (
    AuthenticationError,
    TokenMissingError,
    TokenExpiredError,
    TokenInvalidError,
    IssuerInvalidError,
    AuthorizationError,
    InsufficientPermissionsError,
    RoleRequiredError
)
```

### HTTP Error Responses

All authentication and authorization errors are automatically converted to HTTP exceptions:

- **401 Unauthorized**: Authentication errors (missing, expired, or invalid tokens)
- **403 Forbidden**: Authorization errors (insufficient permissions or roles)

Error response format:
```json
{
    "detail": {
        "code": "token_expired",
        "message": "Access token has expired"
    }
}
```

## Advanced Usage

### Combining Multiple Decorators

```python
# Require authentication + specific permissions
@app.put("/documents/{doc_id}")
@require_auth
@require_permissions(["write:documents"])
async def update_document(request: Request, doc_id: int):
    return {"message": "Document updated"}

# Note: @require_permissions and @require_roles already include @require_auth
# So this is equivalent:
@app.put("/documents/{doc_id}")
@require_permissions(["write:documents"])
async def update_document(request: Request, doc_id: int):
    return {"message": "Document updated"}
```

### Manual Token Validation

```python
from cortex_auth.utils import decode_token, create_user_from_token

# Decode token manually
token = "eyJ..."
payload = decode_token(token)

# Create user from token
user = create_user_from_token(token)
```

### Role and Permission Utilities

```python
from cortex_auth.utils import (
    verify_roles,
    verify_all_roles,
    verify_permissions,
    verify_any_permission,
    is_admin,
    is_manager
)

# Check if user has any of the roles
assert verify_roles(user, ["admin", "manager"])

# Check if user has all roles
assert verify_all_roles(user, ["user", "manager"])

# Check permissions
assert verify_permissions(user, ["read:documents", "write:documents"])

# Convenience checks
assert is_admin(user)
assert is_manager(user)
```

## Architecture

### JWT Token Structure

```json
{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "name": "John Doe",
    "roles": ["user", "manager"],
    "permissions": ["read:documents", "write:documents"],
    "iss": "cortex-auth-service",
    "iat": 1234567890,
    "exp": 1234571490,
    "jti": "unique-token-id"
}
```

### Security Features

- **RS256 Asymmetric Signing**: Services validate with public key, cannot forge tokens
- **Stateless Validation**: No inter-service calls, enabling horizontal scaling
- **httpOnly Cookies**: XSS-resistant token storage for browser applications
- **Clock Skew Tolerance**: ±60 seconds default for distributed systems
- **Issuer Validation**: Prevents tokens from unauthorized sources

## Development

### Running Tests

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
pytest shared/cortex_auth/tests/ -v

# Run tests with coverage
pytest shared/cortex_auth/tests/ --cov=cortex_auth --cov-report=html
```

### Code Quality

```bash
# Format code
black shared/cortex_auth/
ruff check --fix shared/cortex_auth/

# Type checking (optional)
mypy shared/cortex_auth/
```

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please contact the Cortex Engineering Team.
