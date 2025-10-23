"""Email verification service."""

from typing import Dict, Any
from uuid import UUID
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.services.supabase_client import SupabaseClient
from services.auth.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class VerificationError(Exception):
    """Raised when email verification fails."""
    pass


class EmailVerificationService:
    """Service for handling email verification."""

    def __init__(self, session: AsyncSession):
        """Initialize email verification service.

        Args:
            session: Database session
        """
        self.supabase = SupabaseClient()
        self.user_repo = UserRepository(session)
        self.session = session

    async def verify_email_token(self, token: str) -> Dict[str, Any]:
        """Verify email using token from email link.

        Args:
            token: Email verification token

        Returns:
            Dict containing verification result

        Raises:
            VerificationError: If verification fails
        """
        try:
            # Verify with Supabase
            result = await self.supabase.verify_email(token)

            user_data = result.get("user")
            if not user_data:
                raise VerificationError("Invalid or expired verification token")

            email = user_data.get("email")
            if not email:
                raise VerificationError("No email found in verification response")

            # Update local user
            user = await self.user_repo.get_by_email(email)
            if user:
                await self.user_repo.update(
                    user.id,
                    email_verified=True,
                    verified_at=datetime.utcnow()
                )
                await self.session.commit()

                logger.info(f"email_verified - email={email}")

                return {
                    "success": True,
                    "message": "Email verified successfully",
                    "user_id": str(user.id)
                }

            raise VerificationError("User not found in local database")

        except VerificationError:
            raise
        except Exception as e:
            logger.error(f"email_verification_failed - {str(e)}")
            raise VerificationError(f"Verification failed: {str(e)}")

    async def resend_verification_email(self, email: str) -> Dict[str, Any]:
        """Resend verification email to user.

        Args:
            email: User email address

        Returns:
            Dict containing send result

        Raises:
            VerificationError: If resend fails
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise VerificationError("User not found")

        if user.email_verified:
            return {
                "success": False,
                "message": "Email already verified"
            }

        try:
            await self.supabase.send_verification_email(email)

            return {
                "success": True,
                "message": "Verification email sent"
            }

        except Exception as e:
            logger.error(f"resend_verification_failed - email={email}, error={str(e)}")
            raise VerificationError("Failed to send verification email")
