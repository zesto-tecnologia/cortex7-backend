"""Authentication service with local password authentication."""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.repositories.user_repository import UserRepository
from services.auth.repositories.invite_repository import InviteCodeRepository
from services.auth.schemas.auth import UserRegisterRequest, UserLoginRequest
from services.auth.core.exceptions import AuthenticationError, ConflictError, UserNotFoundError
from services.auth.core.password import hash_password, verify_password

logger = logging.getLogger(__name__)


class UserExistsError(Exception):
    """Raised when attempting to register a user that already exists."""
    pass


class AuthService:
    """Authentication service integrating Supabase with local database."""

    def __init__(self, session: AsyncSession):
        """Initialize auth service.

        Args:
            session: Database session
        """
        self.user_repo = UserRepository(session)
        self.invite_repo = InviteCodeRepository(session)
        self.session = session

    async def register_user(self, user_data: UserRegisterRequest) -> Dict[str, Any]:
        """Register a new user with local password authentication and invite code validation.

        Args:
            user_data: User registration data (includes invite_code)

        Returns:
            Dict containing user_id, email, and message

        Raises:
            UserExistsError: If user already exists
            AuthenticationError: If registration fails
            ValueError: If invite code is invalid
        """
        # Step 1: Validate invite code FIRST before any other operations
        try:
            invite = await self.invite_repo.get_by_code(user_data.invite_code)
            if not invite:
                raise ValueError("Invalid invite code")

            if not invite.is_valid():
                if invite.used_at:
                    raise ValueError("This invite code has already been used")
                elif invite.revoked_at:
                    raise ValueError("This invite code has been revoked")
                elif invite.expires_at < datetime.now(timezone.utc):
                    raise ValueError("This invite code has expired")
                else:
                    raise ValueError("Invalid invite code")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"invite_validation_failed - code={user_data.invite_code[:8]}..., error={str(e)}")
            raise ValueError("Failed to validate invite code")

        # Step 2: Check if user exists locally
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise UserExistsError("User with this email already exists")

        local_user = None
        try:
            # Step 3: Hash password with bcrypt (cost factor 12)
            password_hash = hash_password(user_data.password)

            # Step 4: Create user in local database
            from services.auth.schemas.user import UserCreate
            user_create = UserCreate(
                email=user_data.email,
                name=user_data.name,
                password_hash=password_hash,
                role="user",
                email_verified=True,  # Auto-verify for now (no email confirmation required)
                auth_provider=None  # Local authentication
            )

            local_user = await self.user_repo.create(user_create)

            # Step 5: Mark invite code as used
            try:
                await self.invite_repo.validate_and_mark_used(
                    user_data.invite_code,
                    local_user.id
                )
            except ValueError as e:
                # If marking invite as used fails, rollback user creation
                logger.error(f"invite_marking_failed - code={user_data.invite_code[:8]}..., error={str(e)}")
                raise AuthenticationError("Failed to process invite code")

            # Step 6: Set verified_at timestamp since email is auto-verified
            await self.user_repo.update_fields(
                local_user.id,
                verified_at=datetime.now(timezone.utc)
            )

            # Step 7: Commit transaction
            await self.session.commit()

            logger.info(f"user_registered_with_invite - email={user_data.email}, user_id={local_user.id}")

            return {
                "user_id": str(local_user.id),
                "email": local_user.email,
                "message": "Registration successful. You can now log in."
            }

        except (UserExistsError, ValueError):
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"registration_failed - email={user_data.email}, error={str(e)}")

            # Rollback is already handled by exception above
            raise AuthenticationError(f"Registration failed: {str(e)}")

    async def login(self, credentials: UserLoginRequest) -> Dict[str, Any]:
        """Authenticate user with local password verification.

        Args:
            credentials: User login credentials

        Returns:
            Dict containing user data (tokens generated by JWT service in endpoint)

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Get user from local database
            user = await self.user_repo.get_by_email(credentials.email)

            if not user:
                # Don't reveal if email exists
                logger.warning(f"login_attempt_invalid_email - email={credentials.email}")
                raise AuthenticationError("Invalid email or password")

            # Check if user has local password (not OAuth)
            if not user.password_hash:
                logger.warning(f"login_attempt_no_local_password - email={credentials.email}")
                raise AuthenticationError("This account uses external authentication")

            # Verify password with bcrypt
            if not verify_password(credentials.password, user.password_hash):
                logger.warning(f"login_attempt_invalid_password - email={credentials.email}")
                raise AuthenticationError("Invalid email or password")

            # Check if user account is active
            if user.is_deleted():
                logger.warning(f"login_attempt_deleted_account - email={credentials.email}")
                raise AuthenticationError("Account is disabled")

            # Update last_login timestamp
            await self.user_repo.update_fields(
                user.id,
                last_login=datetime.now(timezone.utc)
            )
            await self.session.commit()

            logger.info(f"user_authenticated - email={credentials.email}, user_id={user.id}")

            # Return user data for JWT generation
            return {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "role": user.role,
                    "name": user.name
                }
            }

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"login_failed - email={credentials.email}, error={str(e)}")
            raise AuthenticationError("Login failed. Please try again.")

    async def logout(self, user_id: UUID) -> Dict[str, str]:
        """Logout user (placeholder for future token revocation).

        Args:
            user_id: User ID

        Returns:
            Dict with logout confirmation message
        """
        return {"message": "Logged out successfully"}

    async def log_login_event(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log login event for audit.

        Args:
            user_id: User ID
            ip_address: Request IP address
            user_agent: User agent string
        """
        try:
            from services.auth.repositories.audit_log_repository import AuditLogRepository
            audit_repo = AuditLogRepository(self.session)

            await audit_repo.create({
                "user_id": user_id,
                "event_type": "login",
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.now(timezone.utc)
            })
            await self.session.commit()

        except Exception as e:
            logger.error(f"audit_log_failed - {str(e)}")
            # Don't fail login if audit logging fails

    async def record_failed_login(
        self,
        email: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Record failed login attempt.

        Args:
            email: Email address
            ip_address: Request IP address
        """
        try:
            # Get user if exists
            user = await self.user_repo.get_by_email(email)
            user_id = user.id if user else None

            from services.auth.repositories.audit_log_repository import AuditLogRepository
            audit_repo = AuditLogRepository(self.session)

            await audit_repo.create(
                user_id=user_id,
                action="failed_login",
                ip_address=ip_address,
                user_agent="",
                metadata={"email": email}
            )
            await self.session.commit()

        except Exception as e:
            logger.error(f"audit_log_failed - {str(e)}")


    async def delete_user(self, email: str) -> Dict[str, Any]:
        """Delete user from local database.

        This performs a hard delete (for testing purposes). In production,
        soft delete is recommended.

        Args:
            email: User email address

        Returns:
            Dict containing success status and message

        Raises:
            UserNotFoundError: If user doesn't exist
            AuthenticationError: If deletion fails
        """
        # Get user from local database
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundError(f"User with email {email} not found")

        try:
            # Hard delete from local database (for testing purposes)
            await self.user_repo.hard_delete(user.id)
            await self.session.commit()

            logger.info(f"user_deleted - email={email}, user_id={user.id}")

            return {
                "success": True,
                "email": email,
                "message": f"User {email} successfully deleted"
            }

        except Exception as e:
            # Rollback changes
            await self.session.rollback()
            logger.error(f"user_deletion_failed - email={email}, error={str(e)}")
            raise AuthenticationError(f"Failed to delete user: {str(e)}")
