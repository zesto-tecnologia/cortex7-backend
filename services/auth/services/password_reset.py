"""Password reset service."""

from typing import Dict, Any
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.services.supabase_client import SupabaseClient
from services.auth.repositories.user_repository import UserRepository
from services.auth.config import settings

logger = logging.getLogger(__name__)


class ResetPasswordError(Exception):
    """Raised when password reset fails."""
    pass


class PasswordResetService:
    """Service for handling password reset operations."""

    def __init__(self, session: AsyncSession):
        """Initialize password reset service.

        Args:
            session: Database session
        """
        self.supabase = SupabaseClient()
        self.user_repo = UserRepository(session)
        self.session = session

    async def request_password_reset(self, email: str) -> Dict[str, Any]:
        """Send password reset email.

        Args:
            email: User email address

        Returns:
            Dict containing request result

        Note:
            Always returns success to prevent email enumeration
        """
        # Check if user exists (but don't reveal in response)
        user = await self.user_repo.get_by_email(email)

        if user:
            try:
                # Generate frontend reset URL
                frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
                redirect_url = f"{frontend_url}/reset-password"

                await self.supabase.reset_password_for_email(
                    email,
                    redirect_to=redirect_url
                )

                # Log password reset request
                from services.auth.repositories.audit_log_repository import AuditLogRepository
                audit_repo = AuditLogRepository(self.session)

                await audit_repo.create({
                    "user_id": user.id,
                    "event_type": "password_reset_requested",
                    "timestamp": datetime.utcnow()
                })
                await self.session.commit()

            except Exception as e:
                logger.error(f"password_reset_request_failed - email={email}, error={str(e)}")
                # Don't reveal error to user

        # Always return success to prevent email enumeration
        return {
            "success": True,
            "message": "If the email exists, a reset link has been sent"
        }

    async def confirm_password_reset(
        self,
        token: str,
        new_password: str
    ) -> Dict[str, Any]:
        """Confirm password reset with token and new password.

        Args:
            token: Password reset token from email
            new_password: New password

        Returns:
            Dict containing reset result

        Raises:
            ResetPasswordError: If password reset fails
        """
        try:
            # Update password in Supabase
            result = await self.supabase.update_user_password(
                access_token=token,
                new_password=new_password
            )

            user_data = result.get("user")
            if not user_data:
                raise ResetPasswordError("Invalid or expired reset token")

            email = user_data.get("email")
            if not email:
                raise ResetPasswordError("No email found in reset response")

            # Log successful password reset
            user = await self.user_repo.get_by_email(email)
            if user:
                from services.auth.repositories.audit_log_repository import AuditLogRepository
                audit_repo = AuditLogRepository(self.session)

                await audit_repo.create(
                    user_id=user.id,
                    action="password_reset_completed",
                    ip_address="",
                    user_agent=""
                )
                await self.session.commit()

            logger.info(f"password_reset_completed - email={email}")

            return {
                "success": True,
                "message": "Password reset successful"
            }

        except ResetPasswordError:
            raise
        except Exception as e:
            logger.error(f"password_reset_confirm_failed - {str(e)}")
            raise ResetPasswordError("Failed to reset password")
