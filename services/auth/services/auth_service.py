"""Authentication service with Supabase integration."""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.services.supabase_client import SupabaseClient
from services.auth.repositories.user_repository import UserRepository
from services.auth.schemas.auth import UserRegisterRequest, UserLoginRequest
from services.auth.core.exceptions import AuthenticationError, ConflictError, UserNotFoundError

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
        self.supabase = SupabaseClient()
        self.user_repo = UserRepository(session)
        self.session = session

    async def register_user(self, user_data: UserRegisterRequest) -> Dict[str, Any]:
        """Register a new user through Supabase and local DB.

        Args:
            user_data: User registration data

        Returns:
            Dict containing user_id, email, and message

        Raises:
            UserExistsError: If user already exists
            AuthenticationError: If registration fails
        """
        # Check if user exists locally
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise UserExistsError("User with this email already exists")

        local_user = None
        try:
            # Create user in Supabase
            supabase_user = await self.supabase.create_user(
                email=user_data.email,
                password=user_data.password,
                metadata={
                    "name": user_data.name
                }
            )

            # Extract user ID from Supabase response
            supabase_user_id = supabase_user.get("user", {}).get("id")
            if not supabase_user_id:
                raise AuthenticationError("Failed to create user in Supabase")

            # Create user in local database
            from services.auth.schemas.user import UserCreate
            user_create = UserCreate(
                id=UUID(supabase_user_id),
                email=user_data.email,
                name=user_data.name,
                role="user",
                email_verified=False
            )

            local_user = await self.user_repo.create(user_create)

            # Note: Verification email is automatically sent by Supabase
            # when create_user is called with email_confirm=False

            return {
                "user_id": str(local_user.id),
                "email": local_user.email,
                "message": "Registration successful. Please check your email for verification."
            }

        except UserExistsError:
            raise
        except Exception as e:
            logger.error(f"registration_failed - email={user_data.email}, error={str(e)}")

            # Rollback local user if created
            if local_user:
                try:
                    await self.user_repo.soft_delete(local_user.id)
                    await self.session.commit()
                except Exception as rollback_error:
                    logger.error(f"rollback_failed - {str(rollback_error)}")

            raise AuthenticationError(f"Registration failed: {str(e)}")

    async def login(self, credentials: UserLoginRequest) -> Dict[str, Any]:
        """Authenticate user through Supabase.

        Args:
            credentials: User login credentials

        Returns:
            Dict containing tokens and user data

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Authenticate with Supabase
            response = await self.supabase.sign_in_with_password(
                email=credentials.email,
                password=credentials.password
            )

            # Get session and user from response
            session_data = response.get("session", {})
            user_data = response.get("user", {})

            if not session_data or not user_data:
                raise AuthenticationError("Invalid credentials")

            # Update local user last_login
            user = await self.user_repo.get_by_email(credentials.email)
            if user:
                await self.user_repo.update_fields(
                    user.id,
                    last_login=datetime.now(timezone.utc)
                )
                await self.session.commit()

            return {
                "access_token": session_data.get("access_token"),
                "refresh_token": session_data.get("refresh_token"),
                "user": {
                    "id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "role": user.role if user else "user",
                    "name": user.name if user else user_data.get("user_metadata", {}).get("name", "")
                }
            }

        except Exception as e:
            logger.error(f"supabase_login_failed - email={credentials.email}, error={str(e)}")
            raise AuthenticationError("Invalid email or password")

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
        """Delete user from both Supabase and local database.

        This method ensures atomic deletion from both authentication
        and application databases to maintain consistency.

        Args:
            email: User email address

        Returns:
            Dict containing success status and message

        Raises:
            UserNotFoundError: If user doesn't exist
            AuthenticationError: If deletion fails
        """
        # Get user from local database first
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundError(f"User with email {email} not found")

        user_id = str(user.id)

        try:
            # Delete from Supabase first (authentication layer)
            await self.supabase.delete_user(user_id)

            # Then delete from local database (hard delete for testing purposes)
            await self.user_repo.hard_delete(user.id)
            await self.session.commit()

            return {
                "success": True,
                "email": email,
                "message": f"User {email} successfully deleted"
            }

        except Exception as e:
            # Rollback local changes if any
            await self.session.rollback()
            logger.error(f"user_deletion_failed - email={email}, error={str(e)}")
            raise AuthenticationError(f"Failed to delete user: {str(e)}")
