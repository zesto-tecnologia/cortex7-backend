"""OAuth authentication service."""

from typing import Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.services.supabase_client import SupabaseClient
from services.auth.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"


class OAuthError(Exception):
    """Raised when OAuth operations fail."""
    pass


class OAuthService:
    """Service for handling OAuth authentication flows."""

    def __init__(self, session: AsyncSession):
        """Initialize OAuth service.

        Args:
            session: Database session
        """
        self.supabase = SupabaseClient()
        self.user_repo = UserRepository(session)
        self.session = session

    async def get_oauth_url(
        self,
        provider: OAuthProvider,
        redirect_url: str
    ) -> Dict[str, str]:
        """Get OAuth provider URL for authentication.

        Args:
            provider: OAuth provider enum
            redirect_url: URL to redirect after authentication

        Returns:
            Dict containing provider and auth URL

        Raises:
            OAuthError: If URL generation fails
        """
        try:
            result = await self.supabase.get_oauth_url(
                provider=provider.value,
                redirect_to=redirect_url,
                scopes="email profile"
            )

            auth_url = result.get("url")
            if not auth_url:
                raise OAuthError(f"No URL returned for provider {provider}")

            return {
                "provider": provider.value,
                "auth_url": auth_url
            }

        except OAuthError:
            raise
        except Exception as e:
            logger.error(f"oauth_url_failed - provider={provider.value}, error={str(e)}")
            raise OAuthError(f"OAuth initialization failed for {provider.value}")

    async def handle_oauth_callback(
        self,
        provider: OAuthProvider,
        code: str
    ) -> Dict[str, Any]:
        """Handle OAuth callback and create/update user.

        Args:
            provider: OAuth provider enum
            code: OAuth authorization code

        Returns:
            Dict containing tokens and user data

        Raises:
            OAuthError: If OAuth callback processing fails
        """
        try:
            # Exchange code for session
            result = await self.supabase.exchange_oauth_code(code)

            session_data = result.get("session", {})
            oauth_user = result.get("user", {})

            if not oauth_user:
                raise OAuthError("OAuth authentication failed - no user data")

            email = oauth_user.get("email")
            if not email:
                raise OAuthError("No email in OAuth response")

            user_id = oauth_user.get("id")
            user_metadata = oauth_user.get("user_metadata", {})
            full_name = user_metadata.get("full_name") or user_metadata.get("name", "")

            # Check if user exists locally
            user = await self.user_repo.get_by_email(email)

            if not user:
                # Create new user
                from services.auth.schemas.user import UserCreate
                user_create = UserCreate(
                    id=UUID(user_id),
                    email=email,
                    name=full_name or email.split('@')[0],
                    role="user",
                    email_verified=True,  # OAuth users are pre-verified
                    auth_provider=provider.value
                )

                user = await self.user_repo.create(user_create)
                logger.info(f"oauth_user_created - provider={provider.value}, email={email}")

            else:
                # Update existing user
                await self.user_repo.update(
                    user.id,
                    last_login=datetime.utcnow(),
                    auth_provider=provider.value
                )

            await self.session.commit()

            # Log OAuth login
            from services.auth.repositories.audit_log_repository import AuditLogRepository
            audit_repo = AuditLogRepository(self.session)

            await audit_repo.create({
                "user_id": user.id,
                "event_type": f"oauth_login_{provider.value}",
                "timestamp": datetime.utcnow()
            })
            await self.session.commit()

            return {
                "access_token": session_data.get("access_token"),
                "refresh_token": session_data.get("refresh_token"),
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "role": user.role
                }
            }

        except OAuthError:
            raise
        except Exception as e:
            logger.error(f"oauth_callback_failed - provider={provider.value}, error={str(e)}")
            raise OAuthError(f"OAuth authentication failed: {str(e)}")
