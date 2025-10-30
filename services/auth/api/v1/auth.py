"""Authentication endpoints with complete implementations."""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional
from uuid import UUID

from services.auth.schemas.auth import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    LoginResponse,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    MessageResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    ErrorResponse,
    DeleteUserRequest,
    DeleteUserResponse,
)
from services.auth.dependencies import DatabaseDependency
from services.auth.core.logging import get_logger
from services.auth.core.exceptions import (
    AuthenticationError,
    UserExistsError,
    UserNotFoundError,
    InvalidTokenError,
    TokenExpiredError,
    TokenRevokedError,
    TokenReuseError,
)
from services.auth.services.auth_service import AuthService
from services.auth.services.jwt_service import JWTService
from services.auth.services.password_reset import PasswordResetService, ResetPasswordError
from services.auth.config import settings

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        409: {"model": ErrorResponse, "description": "User already exists"},
    },
    summary="Register new user",
    description="Create a new user account with email verification"
)
async def register(
    request: UserRegisterRequest,
    db: DatabaseDependency
) -> UserRegisterResponse:
    """
    Register a new user.

    - **email**: User email address (must be unique)
    - **name**: User full name
    - **password**: Password (min 8 chars, must contain uppercase, lowercase, and digit)
    """
    auth_service = AuthService(db)

    try:
        # Register user through auth service
        result = await auth_service.register_user(request)

        logger.info(f"user_registered - email={request.email}, user_id={result['user_id']}")

        return UserRegisterResponse(
            user_id=result["user_id"],
            email=result["email"],
            message=result["message"]
        )

    except ValueError as e:
        # Handle invalid invite code
        logger.warning(f"invalid_invite_code - email={request.email}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except UserExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except AuthenticationError as e:
        logger.error(f"registration_failed - email={request.email}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please try again."
        )
    except Exception as e:
        logger.error(f"registration_error - email={request.email}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration"
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account not verified"},
    },
    summary="User login",
    description="Authenticate user and receive JWT tokens"
)
async def login(
    request: UserLoginRequest,
    response: Response,
    req: Request,
    db: DatabaseDependency
) -> LoginResponse:
    """
    User login.

    Returns JWT access token and sets refresh token in HTTP-only cookie.
    """
    auth_service = AuthService(db)
    jwt_service = JWTService(db)

    try:
        # Authenticate user
        auth_result = await auth_service.login(request)

        # Generate new JWT access token (our service tokens)
        access_token, _ = await jwt_service.create_access_token(
            user_id=UUID(auth_result["user"]["id"]),
            email=auth_result["user"]["email"],
            role=auth_result["user"]["role"],
            company_id=None,
            permissions=[]
        )

        # Generate refresh token
        refresh_token = await jwt_service.create_refresh_token(
            user_id=UUID(auth_result["user"]["id"]),
            device_id=_get_device_id(req)
        )

        # Set secure HTTP-only cookie for refresh token
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            path="/api/v1/auth"
        )

        # Log login event
        await auth_service.log_login_event(
            user_id=UUID(auth_result["user"]["id"]),
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("User-Agent")
        )

        logger.info(f"user_login - email={request.email}")

        return LoginResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=auth_result["user"]
        )

    except AuthenticationError as e:
        logger.warning(f"failed_login - email={request.email}")

        # Record failed login attempt
        await auth_service.record_failed_login(
            email=request.email,
            ip_address=req.client.host if req.client else None
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"login_error - email={request.email}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
        403: {"model": ErrorResponse, "description": "Token reuse detected"},
    },
    summary="Refresh access token",
    description="Exchange refresh token for new access token pair"
)
async def refresh_token(
    response: Response,
    db: DatabaseDependency,
    refresh_token: Optional[str] = Cookie(None)
) -> TokenResponse:
    """
    Refresh access token.

    Exchange a valid refresh token for new access and refresh tokens.
    Implements automatic token rotation for security.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )

    jwt_service = JWTService(db)

    try:
        # Rotate refresh token and get new access token
        new_access_token, new_refresh_token = await jwt_service.rotate_refresh_token(
            refresh_token
        )

        # Set new refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            path="/api/v1/auth"
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except TokenReuseError as e:
        logger.warning(f"token_reuse_detected - {str(e)}")

        # Clear refresh token cookie on security breach
        response.delete_cookie("refresh_token", path="/api/v1/auth")

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token reuse detected. Please login again."
        )
    except (InvalidTokenError, TokenExpiredError, TokenRevokedError) as e:
        # Clear invalid refresh token cookie
        response.delete_cookie("refresh_token", path="/api/v1/auth")

        logger.error(f"token_refresh_validation_error - {type(e).__name__}: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    except Exception as e:
        logger.error(f"token_refresh_error - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="User logout",
    description="Revoke tokens and clear session"
)
async def logout(
    response: Response,
    db: DatabaseDependency,
    refresh_token: Optional[str] = Cookie(None)
):
    """
    User logout.

    Revokes the current refresh token and clears cookies.
    """
    try:
        if refresh_token:
            jwt_service = JWTService(db)

            # Decode token to get JTI
            try:
                payload = await jwt_service.verify_token(refresh_token, token_type="refresh")
                jti = payload.get("jti")

                if jti:
                    await jwt_service.revoke_token(jti)
            except Exception as e:
                # Continue with logout even if revocation fails
                pass

        # Clear refresh token cookie
        response.delete_cookie("refresh_token", path="/api/v1/auth")

    except Exception as e:
        logger.error(f"logout_error - {str(e)}")
        # Still clear cookies even if there's an error
        response.delete_cookie("refresh_token", path="/api/v1/auth")


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email address",
    description="Verify user email using token from verification email"
)
async def verify_email(
    request: VerifyEmailRequest,
    db: DatabaseDependency
) -> MessageResponse:
    """
    Verify user email address.

    Activates the user account after email verification.
    """
    # TODO: Implement email verification with Supabase
    return MessageResponse(message="Email verification endpoint - to be implemented")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    responses={
        429: {"model": ErrorResponse, "description": "Too many requests"}
    },
    summary="Request password reset",
    description="Send password reset email to user"
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: DatabaseDependency
) -> MessageResponse:
    """
    Request password reset.

    Sends a password reset email to the user.
    Always returns success to prevent email enumeration.
    """
    password_reset_service = PasswordResetService(db)

    try:
        result = await password_reset_service.request_password_reset(request.email)

        # Always return success message (security - prevent email enumeration)
        return MessageResponse(message=result["message"])

    except Exception as e:
        logger.error(f"password_reset_request_error - email={request.email}, error={str(e)}")
        # Still return success message for security
        return MessageResponse(message="If the email exists, a reset link has been sent")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
        422: {"model": ErrorResponse, "description": "Invalid password format"}
    },
    summary="Reset password",
    description="Reset password using token from email"
)
async def reset_password(
    request: ResetPasswordRequest,
    db: DatabaseDependency
) -> MessageResponse:
    """
    Reset user password.

    Sets a new password using the reset token from email.
    """
    password_reset_service = PasswordResetService(db)

    try:
        # Map old schema to new schema
        result = await password_reset_service.confirm_password_reset(
            token=request.token,
            new_password=request.new_password
        )

        logger.info("password_reset_completed")

        return MessageResponse(message=result["message"])

    except ResetPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    except Exception as e:
        logger.error(f"password_reset_error - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )



@router.delete(
    "/delete-user",
    response_model=DeleteUserResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Deletion failed"},
    },
    summary="Delete user from both databases",
    description="Delete user from both Supabase authentication and local database (for testing purposes)"
)
async def delete_user(
    request: DeleteUserRequest,
    db: DatabaseDependency
) -> DeleteUserResponse:
    """
    Delete user from both Supabase and local database.

    **IMPORTANT**: This endpoint is designed for testing and development.
    In production, consider implementing soft delete or account deactivation instead.

    - **email**: User email address to delete
    """
    auth_service = AuthService(db)

    try:
        result = await auth_service.delete_user(request.email)

        return DeleteUserResponse(
            success=result["success"],
            email=result["email"],
            message=result["message"]
        )

    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthenticationError as e:
        logger.error(f"user_deletion_failed - email={request.email}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )
    except Exception as e:
        logger.error(f"user_deletion_error - email={request.email}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during deletion"
        )


def _get_device_id(request: Request) -> str:
    """Generate device ID from request headers."""
    import hashlib

    user_agent = request.headers.get("User-Agent", "")
    ip_address = request.client.host if request.client else ""

    # Create a stable device identifier
    device_string = f"{user_agent}:{ip_address}"
    return hashlib.sha256(device_string.encode()).hexdigest()[:16]
