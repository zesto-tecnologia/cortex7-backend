"""Admin endpoints for invite code and user management."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query, Request
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from datetime import datetime, timezone

from services.auth.dependencies import (
    DatabaseDependency,
    CurrentUserDependency,
    AdminDependency,
    AdminOrManagerDependency,
    AuditServiceDependency
)
from services.auth.core.logging import get_logger
from services.auth.repositories.invite_repository import InviteCodeRepository
from services.auth.repositories.user_repository import UserRepository

router = APIRouter()
logger = get_logger(__name__)


# Schemas
class InviteCodeCreate(BaseModel):
    """Request schema for creating invite codes."""

    expires_in_days: int = Field(default=7, ge=1, le=365, description="Number of days until expiration")


class InviteCodeResponse(BaseModel):
    """Response schema for invite code."""

    id: str
    code: str
    creator_id: str
    created_at: datetime
    expires_at: datetime
    used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    used_by_id: Optional[str] = None
    status: str


class InviteCodeListResponse(BaseModel):
    """Response schema for list of invite codes."""

    invites: list[InviteCodeResponse]
    total: int
    limit: int
    offset: int


class UserListResponse(BaseModel):
    """Response schema for user list."""

    id: str
    email: str
    name: str
    role: str
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UsersListResponse(BaseModel):
    """Response schema for list of users."""

    users: list[UserListResponse]
    total: int
    limit: int
    offset: int


class UpdateUserRoleRequest(BaseModel):
    """Request schema for updating user role."""

    role: str = Field(description="New role for the user (user, admin, super_admin)")


@router.post(
    "/invites",
    response_model=InviteCodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate invite code (Admin only)",
    description="Generate a new invite code for user registration"
)
async def create_invite_code(
    invite_request: InviteCodeCreate,
    request: Request,
    admin_user: AdminDependency,
    db: DatabaseDependency,
    audit_service: AuditServiceDependency
) -> InviteCodeResponse:
    """
    Generate a new invite code.

    Requires admin role.
    - **expires_in_days**: Number of days until expiration (1-365, default: 7)
    """
    current_user_id = admin_user.id

    invite_repo = InviteCodeRepository(db)

    try:
        invite = await invite_repo.create(
            creator_id=current_user_id,
            expires_in_days=invite_request.expires_in_days
        )

        # Log audit event
        await audit_service.log_invite_created(
            admin_id=current_user_id,
            invite_code=invite.code,
            expires_in_days=invite_request.expires_in_days,
            request=request
        )

        # Determine status
        status_str = "pending"
        if invite.used_at:
            status_str = "used"
        elif invite.revoked_at:
            status_str = "revoked"
        elif invite.expires_at < datetime.now(timezone.utc):
            status_str = "expired"

        logger.info(f"invite_code_created - creator_id={current_user_id}, code={invite.code[:8]}...")

        return InviteCodeResponse(
            id=str(invite.id),
            code=invite.code,
            creator_id=str(invite.creator_id),
            created_at=invite.created_at,
            expires_at=invite.expires_at,
            used_at=invite.used_at,
            revoked_at=invite.revoked_at,
            used_by_id=str(invite.used_by_id) if invite.used_by_id else None,
            status=status_str
        )

    except Exception as e:
        logger.error(f"invite_creation_failed - creator_id={current_user_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invite code"
        )


@router.get(
    "/invites",
    response_model=InviteCodeListResponse,
    summary="List invite codes (Admin only)",
    description="List all invite codes with optional filtering"
)
async def list_invite_codes(
    admin_user: AdminOrManagerDependency,
    db: DatabaseDependency,
    status_filter: Optional[str] = Query(
        None,
        description="Filter by status: pending, used, expired, revoked"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> InviteCodeListResponse:
    """
    List all invite codes.

    Requires admin or manager role.
    - **status_filter**: Filter by status (optional)
    - **limit**: Maximum number of results (1-100)
    - **offset**: Offset for pagination
    """

    invite_repo = InviteCodeRepository(db)

    try:
        # Get invites
        invites = await invite_repo.list_all(
            status_filter=status_filter,
            limit=limit,
            offset=offset
        )

        # Get total count for the same filter
        all_invites = await invite_repo.list_all(status_filter=status_filter)
        total = len(all_invites)

        # Convert to response format
        invite_responses = []
        for invite in invites:
            status_str = "pending"
            if invite.used_at:
                status_str = "used"
            elif invite.revoked_at:
                status_str = "revoked"
            elif invite.expires_at < datetime.utcnow():
                status_str = "expired"

            invite_responses.append(InviteCodeResponse(
                id=str(invite.id),
                code=invite.code,
                creator_id=str(invite.creator_id),
                created_at=invite.created_at,
                expires_at=invite.expires_at,
                used_at=invite.used_at,
                revoked_at=invite.revoked_at,
                used_by_id=str(invite.used_by_id) if invite.used_by_id else None,
                status=status_str
            ))

        return InviteCodeListResponse(
            invites=invite_responses,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"invite_listing_failed - error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list invite codes"
        )


@router.delete(
    "/invites/{code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke invite code (Admin only)",
    description="Revoke an invite code to prevent its use"
)
async def revoke_invite_code(
    code: str,
    request: Request,
    admin_user: AdminDependency,
    db: DatabaseDependency,
    audit_service: AuditServiceDependency
):
    """
    Revoke an invite code.

    Requires admin role.
    - **code**: The invite code to revoke
    """
    current_user_id = admin_user.id

    invite_repo = InviteCodeRepository(db)

    try:
        await invite_repo.revoke(code)

        # Log audit event
        await audit_service.log_invite_revoked(
            admin_id=current_user_id,
            invite_code=code,
            request=request
        )

        logger.info(f"invite_code_revoked - code={code[:8]}..., revoked_by={current_user_id}")
        return None

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"invite_revocation_failed - code={code[:8]}..., error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke invite code"
        )


@router.get(
    "/users",
    response_model=UsersListResponse,
    summary="List users (Admin/Manager)",
    description="List all users with pagination and filtering"
)
async def list_users(
    admin_user: AdminOrManagerDependency,
    db: DatabaseDependency,
    role: Optional[str] = Query(None, description="Filter by role"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> UsersListResponse:
    """
    List all users.

    Requires admin or manager role.
    - **role**: Filter by role (optional)
    - **search**: Search by email or name (optional)
    - **limit**: Maximum number of results (1-100)
    - **offset**: Offset for pagination
    """

    user_repo = UserRepository(db)

    try:
        # Get users (TODO: implement filtering in repository)
        users = await user_repo.list_all(limit=limit, offset=offset)

        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            users = [
                u for u in users
                if search_lower in u.email.lower() or search_lower in u.name.lower()
            ]

        # Apply role filter if provided
        if role:
            users = [u for u in users if u.role == role]

        total = len(users)

        # Convert to response format
        user_responses = [
            UserListResponse(
                id=str(user.id),
                email=user.email,
                name=user.name,
                role=user.role,
                email_verified=user.email_verified,
                created_at=user.created_at,
                last_login=user.last_login
            )
            for user in users
        ]

        return UsersListResponse(
            users=user_responses,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"user_listing_failed - error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.put(
    "/users/{user_id}/roles",
    response_model=UserListResponse,
    summary="Update user role (Admin only)",
    description="Update a user's role"
)
async def update_user_role(
    user_id: UUID,
    role_request: UpdateUserRoleRequest,
    request: Request,
    admin_user: AdminDependency,
    db: DatabaseDependency,
    audit_service: AuditServiceDependency
) -> UserListResponse:
    """
    Update user role.

    Requires admin role.
    - **user_id**: UUID of the user to update
    - **role**: New role (user, admin, super_admin)
    """
    current_user_id = admin_user.id

    # Validate role
    valid_roles = ["user", "admin", "super_admin"]
    if role_request.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    user_repo = UserRepository(db)

    try:
        # Check if user exists
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Store old role for audit logging
        old_role = user.role

        # Update role
        from services.auth.schemas.user import UserUpdate
        update_data = UserUpdate(role=role_request.role)
        updated_user = await user_repo.update(user_id, update_data)

        # Log audit event
        await audit_service.log_role_updated(
            admin_id=current_user_id,
            target_user_id=user_id,
            old_role=old_role,
            new_role=role_request.role,
            request=request
        )

        logger.info(f"user_role_updated - user_id={user_id}, new_role={role_request.role}, updated_by={current_user_id}")

        return UserListResponse(
            id=str(updated_user.id),
            email=updated_user.email,
            name=updated_user.name,
            role=updated_user.role,
            email_verified=updated_user.email_verified,
            created_at=updated_user.created_at,
            last_login=updated_user.last_login
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"role_update_failed - user_id={user_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )
