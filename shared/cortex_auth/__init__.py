"""
cortex-auth: Shared authentication library for Cortex microservices.

This library provides JWT validation, FastAPI decorators, and dependencies
for implementing distributed authentication across multiple services.

Usage:
    # In any microservice
    from cortex_auth import require_auth, require_roles, get_current_user
    from cortex_auth.models import User

    @app.get("/protected")
    @require_auth
    async def protected_route(user: User = Depends(get_current_user)):
        return {"message": f"Hello {user.name}"}

    @app.delete("/admin-only")
    @require_admin
    async def admin_route(request: Request):
        return {"message": "Admin action"}
"""

__version__ = "0.1.0"
__author__ = "Cortex Engineering Team"

# Core models
from .models import TokenPayload, User

# Exceptions
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    InsufficientPermissionsError,
    IssuerInvalidError,
    RoleRequiredError,
    TokenExpiredError,
    TokenInvalidError,
    TokenMissingError,
)

# Configuration
from .config import AuthSettings, settings

# Utilities
from .utils import (
    create_user_from_token,
    decode_token,
    extract_token_from_cookie,
    is_admin,
    is_manager,
    verify_all_roles,
    verify_any_permission,
    verify_permissions,
    verify_roles,
)

# FastAPI decorators
from .decorators import (
    require_admin,
    require_auth,
    require_manager,
    require_permissions,
    require_roles,
)

# FastAPI dependencies
from .dependencies import (
    get_current_user,
    get_current_user_from_cookie,
    get_optional_user,
    require_admin as require_admin_dep,
    require_manager as require_manager_dep,
)

# Public API
__all__ = [
    # Version
    "__version__",
    "__author__",
    # Models
    "User",
    "TokenPayload",
    # Exceptions
    "AuthenticationError",
    "AuthorizationError",
    "TokenMissingError",
    "TokenExpiredError",
    "TokenInvalidError",
    "IssuerInvalidError",
    "InsufficientPermissionsError",
    "RoleRequiredError",
    # Configuration
    "AuthSettings",
    "settings",
    # Utilities
    "decode_token",
    "create_user_from_token",
    "extract_token_from_cookie",
    "verify_roles",
    "verify_all_roles",
    "verify_permissions",
    "verify_any_permission",
    "is_admin",
    "is_manager",
    # Decorators (most common usage)
    "require_auth",
    "require_roles",
    "require_permissions",
    "require_admin",
    "require_manager",
    # Dependencies (alternative to decorators)
    "get_current_user",
    "get_current_user_from_cookie",
    "get_optional_user",
    "require_admin_dep",
    "require_manager_dep",
]
