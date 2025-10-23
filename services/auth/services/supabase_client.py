"""Supabase client with retry logic and error handling."""

from typing import Dict, Any, Optional
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from services.auth.config import settings
from services.auth.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase client with retry logic."""

    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    _admin_client: Optional[Client] = None

    def __new__(cls) -> 'SupabaseClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._client is None:
            try:
                # Public client with anon key for user operations
                self._client = create_client(
                    str(settings.SUPABASE_URL),
                    settings.SUPABASE_KEY
                )
                # Admin client with service role key for admin operations
                self._admin_client = create_client(
                    str(settings.SUPABASE_URL),
                    settings.SUPABASE_SERVICE_ROLE_KEY
                )
            except Exception as e:
                logger.error(f"supabase_init_failed - {str(e)}")
                raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        reraise=True
    )
    async def create_user(
        self,
        email: str,
        password: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new user with retry logic.

        In development: Uses admin API with email_confirm=True to skip verification.
        In production: Uses signUp() which sends verification email.

        Args:
            email: User email address
            password: User password
            metadata: Optional user metadata (name, company_id, etc.)

        Returns:
            Dict containing user data

        Raises:
            Exception: If user creation fails after retries
        """
        try:
            # Development: Auto-confirm emails to skip verification
            if settings.ENVIRONMENT == "development":
                response = self._admin_client.auth.admin.create_user({
                    "email": email,
                    "password": password,
                    "email_confirm": True,  # Auto-confirm in development
                    "user_metadata": metadata or {}
                })
            else:
                # Production: Send verification email
                response = self._client.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": metadata or {}
                    }
                })
            return response.model_dump() if hasattr(response, 'model_dump') else response
        except Exception as e:
            logger.error(f"supabase_create_user_failed - email={email}, error={str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        reraise=True
    )
    async def verify_email(self, token: str) -> Dict[str, Any]:
        """Verify user email with token.

        Args:
            token: Email verification token

        Returns:
            Dict containing verification result

        Raises:
            Exception: If verification fails after retries
        """
        try:
            response = self._client.auth.verify_otp({
                "token": token,
                "type": "email"
            })
            return response.model_dump() if hasattr(response, 'model_dump') else response
        except Exception as e:
            logger.error(f"supabase_verify_email_failed - {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        reraise=True
    )
    async def send_verification_email(self, email: str) -> Dict[str, Any]:
        """Send verification email to user.

        Note: When using admin.create_user with email_confirm=False,
        Supabase automatically sends the verification email.
        This method can be used to resend verification emails.

        Args:
            email: User email address

        Returns:
            Dict containing send result

        Raises:
            Exception: If sending fails after retries
        """
        try:
            # Use admin API to resend email verification
            response = self._admin_client.auth.admin.generate_link({
                "type": "signup",
                "email": email
            })
            return response
        except Exception as e:
            logger.error(f"supabase_send_verification_failed - email={email}, error={str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        reraise=True
    )
    async def sign_in_with_password(
        self,
        email: str,
        password: str
    ) -> Dict[str, Any]:
        """Sign in user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Dict containing session and user data

        Raises:
            Exception: If authentication fails
        """
        try:
            response = self._client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response.model_dump() if hasattr(response, 'model_dump') else response
        except Exception as e:
            logger.error(f"supabase_signin_failed - email={email}, error={str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        reraise=True
    )
    async def reset_password_for_email(
        self,
        email: str,
        redirect_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send password reset email.

        Args:
            email: User email
            redirect_to: Optional redirect URL after reset

        Returns:
            Dict containing reset request result

        Raises:
            Exception: If reset request fails
        """
        try:
            response = self._client.auth.reset_password_for_email(
                email,
                options={"redirect_to": redirect_to} if redirect_to else None
            )
            return response
        except Exception as e:
            logger.error(f"supabase_password_reset_failed - email={email}, error={str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        reraise=True
    )
    async def update_user_password(
        self,
        access_token: str,
        new_password: str
    ) -> Dict[str, Any]:
        """Update user password with access token.

        Args:
            access_token: User's access token from reset email
            new_password: New password

        Returns:
            Dict containing update result

        Raises:
            Exception: If password update fails
        """
        try:
            # Use the access token directly to update password
            # Note: This requires the access token from the password reset email
            response = self._client.auth.update_user(
                attributes={"password": new_password},
                access_token=access_token
            )
            return response.model_dump() if hasattr(response, 'model_dump') else response
        except Exception as e:
            logger.error(f"supabase_password_update_failed - {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        reraise=True
    )
    async def get_oauth_url(
        self,
        provider: str,
        redirect_to: str,
        scopes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get OAuth provider authentication URL.

        Args:
            provider: OAuth provider name (google, github, etc.)
            redirect_to: Redirect URL after authentication
            scopes: Optional OAuth scopes

        Returns:
            Dict containing OAuth URL

        Raises:
            Exception: If URL generation fails
        """
        try:
            response = self._client.auth.sign_in_with_oauth({
                "provider": provider,
                "options": {
                    "redirect_to": redirect_to,
                    "scopes": scopes
                }
            })
            return response
        except Exception as e:
            logger.error(f"supabase_oauth_url_failed - provider={provider}, error={str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        reraise=True
    )
    async def exchange_oauth_code(self, code: str) -> Dict[str, Any]:
        """Exchange OAuth code for session.

        Args:
            code: OAuth authorization code

        Returns:
            Dict containing session and user data

        Raises:
            Exception: If code exchange fails
        """
        try:
            response = self._client.auth.exchange_code_for_session(code)
            return response.model_dump() if hasattr(response, 'model_dump') else response
        except Exception as e:
            logger.error(f"supabase_oauth_exchange_failed - {str(e)}")
            raise

    def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user from access token.

        Args:
            access_token: User's access token

        Returns:
            Dict containing user data or None
        """
        try:
            response = self._client.auth.get_user(access_token)
            return response.model_dump() if hasattr(response, 'model_dump') else response
        except Exception as e:
            logger.error(f"supabase_get_user_failed - {str(e)}")
            return None

    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete user from Supabase authentication.

        Args:
            user_id: User ID to delete

        Returns:
            Dict containing success status

        Raises:
            AuthenticationError: If deletion fails
        """
        try:
            # Use admin client to delete user
            self._admin_client.auth.admin.delete_user(user_id)
            return {"success": True, "user_id": user_id}
        except Exception as e:
            logger.error(f"supabase_delete_user_failed - user_id={user_id}, error={str(e)}")
            raise AuthenticationError(f"Failed to delete user: {str(e)}")
