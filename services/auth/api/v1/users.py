"""User management endpoints."""

from fastapi import APIRouter, status, HTTPException
from services.auth.schemas.auth import UserProfile, UserProfileUpdate, PasswordChangeRequest
from services.auth.schemas.user import UserWithCompanies, UserUpdate
from services.auth.dependencies import DatabaseDependency, CurrentUserDependency
from services.auth.core.logging import get_logger
from services.auth.repositories.user_repository import UserRepository

router = APIRouter()
logger = get_logger(__name__)


@router.get("/me", response_model=UserProfile)
async def get_current_user(
    current_user_id: CurrentUserDependency,
    db: DatabaseDependency
):
    """
    Get current user profile.

    Returns the authenticated user's profile information.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(current_user_id)

    if not user:
        logger.warning(f"User not found: {current_user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserProfile.model_validate(user)


@router.patch("/me", response_model=UserProfile)
async def update_current_user(
    request: UserProfileUpdate,
    current_user_id: CurrentUserDependency,
    db: DatabaseDependency
):
    """
    Update current user profile.

    Allows users to update their name and email.
    """
    user_repo = UserRepository(db)

    # Convert UserProfileUpdate to UserUpdate
    update_data = UserUpdate(
        name=request.name,
        email=request.email
    )

    # Update the user
    updated_user = await user_repo.update(current_user_id, update_data)

    if not updated_user:
        logger.warning(f"User not found for update: {current_user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    logger.info(f"User profile updated: {current_user_id}")
    return UserProfile.model_validate(updated_user)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: PasswordChangeRequest,
    current_user_id: CurrentUserDependency,
    db: DatabaseDependency
):
    """
    Change user password.

    Requires current password verification.
    """
    # TODO: Implement password change
    return None


@router.get("/permissions")
async def get_user_permissions(
    current_user_id: CurrentUserDependency,
    db: DatabaseDependency
):
    """
    Get user permissions.

    Returns the list of permissions for the current user based on their role.
    """
    # TODO: Implement get permissions
    return {
        "permissions": [
            "read:own_data",
            "write:own_data",
            "delete:own_data"
        ]
    }