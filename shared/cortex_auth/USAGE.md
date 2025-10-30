# Cortex Auth Library - Usage Guide

**Version**: 0.1.0
**Purpose**: Shared authentication library for Cortex microservices with JWT validation and FastAPI integration

---

## Quick Start

### Installation

```bash
# In your microservice directory
uv add cortex-auth --path ../shared/cortex_auth
```

### Environment Configuration

```bash
# Required environment variables
AUTH_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
# OR
AUTH_PUBLIC_KEY_PATH="./keys/jwt-public.pem"

# Optional (with defaults)
AUTH_ISSUER="cortex-auth-service"  # Token issuer validation
AUTH_COOKIE_NAME="cortex_access_token"  # Cookie name
AUTH_ENABLED="true"  # Set to false for testing
AUTH_CLOCK_SKEW_SECONDS="60"  # Clock skew tolerance
```

---

## Basic Authentication

### Simple Route Protection

```python
from fastapi import FastAPI, Request
from cortex_auth import require_auth

app = FastAPI()

@app.get("/profile")
@require_auth
async def get_profile(request: Request):
    """Protected endpoint - requires valid JWT."""
    user = request.state.user
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "roles": user.roles
    }
```

### With Dependency Injection

```python
from fastapi import Depends
from cortex_auth import require_auth, get_current_user
from cortex_auth.models import User

@app.get("/profile")
@require_auth
async def get_profile(current_user: User = Depends(get_current_user)):
    """Cleaner approach using FastAPI dependencies."""
    return {
        "email": current_user.email,
        "roles": current_user.roles
    }
```

---

## Role-Based Access Control

### Single Role (Admin Only)

```python
from cortex_auth import require_admin

@app.delete("/users/{user_id}")
@require_admin
async def delete_user(request: Request, user_id: str):
    """Only admin users can access this endpoint."""
    return {"deleted": user_id}
```

### Multiple Roles (OR Logic)

```python
from cortex_auth import require_roles

@app.get("/reports")
@require_roles(["admin", "manager"])
async def get_reports(request: Request):
    """User needs admin OR manager role."""
    user = request.state.user
    return {"reports": get_user_reports(user.user_id)}
```

### Multiple Roles (AND Logic)

```python
@app.post("/critical-action")
@require_roles(["admin", "manager"], require_all=True)
async def critical_action(request: Request):
    """User needs BOTH admin AND manager roles."""
    return {"status": "executed"}
```

### Manager or Admin

```python
from cortex_auth import require_manager

@app.post("/approve-order/{order_id}")
@require_manager
async def approve_order(request: Request, order_id: str):
    """Managers and admins can approve orders."""
    return {"order_id": order_id, "status": "approved"}
```

---

## Permission-Based Access Control

### Single Permission

```python
from cortex_auth import require_permissions

@app.get("/documents")
@require_permissions(["read:documents"])
async def list_documents(request: Request):
    """Requires read:documents permission."""
    return {"documents": get_documents()}
```

### Multiple Permissions (AND Logic - Default)

```python
@app.put("/documents/{doc_id}")
@require_permissions(["read:documents", "write:documents"])
async def update_document(request: Request, doc_id: str, data: dict):
    """User needs BOTH read AND write permissions."""
    return {"updated": doc_id}
```

### Multiple Permissions (OR Logic)

```python
@app.get("/reports")
@require_permissions(["read:reports", "admin:reports"], require_all=False)
async def get_reports(request: Request):
    """User needs read:reports OR admin:reports permission."""
    return {"reports": []}
```

### Wildcard Permissions

```python
# Wildcard action on specific resource
@app.get("/admin/users")
@require_permissions(["*:users"])
async def admin_users(request: Request):
    """User needs any action on users (e.g., *:users)."""
    return {"users": get_all_users()}

# All permissions wildcard
@app.get("/admin/dashboard")
@require_permissions(["*:*"])
async def admin_dashboard(request: Request):
    """User needs superadmin permissions (*:*)."""
    return {"dashboard": get_admin_dashboard()}
```

---

## Advanced Usage

### Combining Decorators

```python
from cortex_auth import require_auth, require_roles, require_permissions

# Auth is automatically applied by require_roles
@app.delete("/documents/{doc_id}")
@require_roles(["admin", "manager"])
@require_permissions(["delete:documents"])
async def delete_document(request: Request, doc_id: str):
    """
    Requires:
    1. Valid authentication (automatic with @require_roles)
    2. admin OR manager role
    3. delete:documents permission
    """
    return {"deleted": doc_id}
```

### Custom Authorization Logic

```python
from cortex_auth import require_auth
from cortex_auth.models import User
from fastapi import HTTPException, Depends

async def require_owns_resource(
    resource_id: str,
    current_user: User = Depends(get_current_user)
):
    """Custom dependency for resource ownership."""
    resource = await get_resource(resource_id)
    if resource.owner_id != current_user.user_id and not current_user.has_role("admin"):
        raise HTTPException(
            status_code=403,
            detail={"code": "access_denied", "message": "You don't own this resource"}
        )
    return resource

@app.put("/posts/{post_id}")
@require_auth
async def update_post(
    post_id: str,
    data: dict,
    post = Depends(lambda: require_owns_resource(post_id))
):
    """User must own the post or be an admin."""
    return {"updated": post.id}
```

### Checking Permissions Programmatically

```python
from cortex_auth import require_auth, get_current_user

@app.get("/posts")
@require_auth
async def list_posts(current_user: User = Depends(get_current_user)):
    """Return posts based on user permissions."""
    if current_user.has_permission("read:all_posts"):
        return {"posts": get_all_posts()}
    else:
        return {"posts": get_user_posts(current_user.user_id)}

@app.get("/dashboard")
@require_auth
async def dashboard(current_user: User = Depends(get_current_user)):
    """Customize dashboard based on roles."""
    widgets = ["profile", "settings"]

    if current_user.has_role("admin"):
        widgets.extend(["users", "analytics", "logs"])
    elif current_user.has_role("manager"):
        widgets.extend(["team", "reports"])

    return {"widgets": widgets}
```

---

## Error Handling

### HTTP Status Codes

| Status | Error Code | Description |
|--------|-----------|-------------|
| 401 | token_missing | No authentication token provided |
| 401 | token_expired | JWT token has expired |
| 401 | token_invalid | Malformed JWT or invalid signature |
| 401 | issuer_invalid | Token from wrong issuer |
| 403 | insufficient_permissions | User lacks required roles/permissions |

### Custom Error Handlers

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    """Custom 401 handler."""
    return JSONResponse(
        status_code=401,
        content={
            "error": "Authentication required",
            "detail": exc.detail if hasattr(exc, "detail") else "Unauthorized"
        }
    )

@app.exception_handler(403)
async def forbidden_handler(request: Request, exc):
    """Custom 403 handler."""
    return JSONResponse(
        status_code=403,
        content={
            "error": "Access denied",
            "detail": exc.detail if hasattr(exc, "detail") else "Forbidden"
        }
    )
```

---

## Testing

### Test Configuration

```python
# conftest.py
import pytest
from cortex_auth.config import AuthSettings

@pytest.fixture
def test_settings(rsa_keys, monkeypatch):
    """Configure auth settings for testing."""
    from cortex_auth import config

    test_settings = AuthSettings(
        auth_public_key=rsa_keys["public_key"],
        auth_issuer="cortex-auth-service",
        auth_enabled=True
    )

    monkeypatch.setattr(config, "settings", test_settings)
    return test_settings
```

### Disable Auth for Testing

```bash
# .env.test
AUTH_ENABLED=false
```

```python
# With AUTH_ENABLED=false, decorators create mock users
@app.get("/test")
@require_auth
async def test_route(request: Request):
    # request.state.user will be a mock test user
    return {"user": request.state.user.email}
```

---

## Configuration Reference

### AuthSettings Class

```python
from cortex_auth.config import AuthSettings

# Create custom settings instance
custom_settings = AuthSettings(
    auth_public_key_path="/custom/path/to/public.pem",
    auth_issuer="my-custom-issuer",
    auth_clock_skew_seconds=120,  # 2 minutes tolerance
    auth_enabled=True
)
```

### User Model

```python
from cortex_auth.models import User

# User attributes
user.user_id: str        # Unique user ID (UUID)
user.email: str          # Email address
user.name: str           # Display name
user.roles: List[str]    # List of role names
user.permissions: List[str]  # List of permission strings

# User methods
user.has_role(role: str) -> bool
user.has_any_role(roles: List[str]) -> bool
user.has_all_roles(roles: List[str]) -> bool
user.has_permission(permission: str) -> bool
user.has_all_permissions(permissions: List[str]) -> bool
```

---

## Best Practices

### 1. Use Most Specific Decorator

```python
# ✅ GOOD: Specific decorator
@app.delete("/users/{user_id}")
@require_admin
async def delete_user(...):
    pass

# ❌ AVOID: Generic decorator with manual checks
@app.delete("/users/{user_id}")
@require_auth
async def delete_user(request: Request, ...):
    if not request.state.user.has_role("admin"):
        raise HTTPException(403)
    pass
```

### 2. Order Decorators Correctly

```python
# ✅ CORRECT: Auth decorators first, then route decorator
@app.get("/admin/stats")
@require_admin
async def admin_stats(...):
    pass

# ❌ WRONG: Route decorator before auth
@require_admin
@app.get("/admin/stats")
async def admin_stats(...):
    pass
```

### 3. Use Dependency Injection

```python
# ✅ GOOD: Clean dependency injection
@app.get("/profile")
@require_auth
async def get_profile(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email}

# ❌ AVOID: Accessing request.state directly
@app.get("/profile")
@require_auth
async def get_profile(request: Request):
    user = request.state.user
    return {"email": user.email}
```

### 4. Combine Roles and Permissions

```python
# ✅ GOOD: Use permissions for fine-grained control
@app.put("/documents/{doc_id}")
@require_permissions(["write:documents"])
async def update_document(...):
    pass

# ✅ ALSO GOOD: Combine roles for specific scenarios
@app.post("/admin/bulk-import")
@require_roles(["admin"])
@require_permissions(["write:documents", "import:data"])
async def bulk_import(...):
    pass
```

---

## Troubleshooting

### Common Issues

**Issue**: `ValueError: Public key file not found`
```bash
# Solution: Set AUTH_PUBLIC_KEY or AUTH_PUBLIC_KEY_PATH
export AUTH_PUBLIC_KEY_PATH="./keys/jwt-public.pem"
```

**Issue**: `TokenInvalidError: Invalid token issuer`
```bash
# Solution: Match issuer with auth service
export AUTH_ISSUER="cortex-auth-service"
```

**Issue**: All requests return 401 in production
```bash
# Solution: Ensure AUTH_ENABLED=true in production
export AUTH_ENABLED="true"
```

**Issue**: Tests fail with authentication errors
```python
# Solution: Use test fixtures to configure settings
@pytest.fixture(autouse=True)
def mock_settings(rsa_keys, monkeypatch):
    # ... configure test settings
```

---

## Migration from Other Auth Libraries

### From FastAPI-Users

```python
# Before (fastapi-users)
@app.get("/protected")
async def protected(user: User = Depends(current_active_user)):
    return {"user": user.email}

# After (cortex-auth)
from cortex_auth import require_auth, get_current_user

@app.get("/protected")
@require_auth
async def protected(user: User = Depends(get_current_user)):
    return {"user": user.email}
```

### From Custom JWT Middleware

```python
# Before (custom middleware)
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    # ... validate token ...
    request.state.user = user
    return await call_next(request)

# After (cortex-auth) - simpler!
from cortex_auth import require_auth

@app.get("/protected")
@require_auth
async def protected(request: Request):
    user = request.state.user
    return {"user": user.email}
```

---

## Support

- **Documentation**: `./README.md`
- **API Reference**: `./API.md`
- **Test Examples**: `./tests/test_decorators.py`
- **GitHub Issues**: Create an issue for bugs or feature requests

---

**Last Updated**: 2025-10-30
**Version**: 0.1.0
