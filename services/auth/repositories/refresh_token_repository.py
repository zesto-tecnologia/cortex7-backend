"""Refresh token repository for data access layer."""

from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from services.auth.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Repository for refresh token data access operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(
        self,
        user_id: UUID,
        token_hash: str,
        expires_days: int = 7
    ) -> RefreshToken:
        """Create a new refresh token.

        Args:
            user_id: User UUID
            token_hash: Hashed token string
            expires_days: Number of days until token expires (default: 7)

        Returns:
            Created refresh token instance
        """
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_days)
        )
        self.session.add(token)
        await self.session.flush()
        await self.session.refresh(token)
        return token

    async def create_refresh_token(
        self,
        jti: str,
        user_id: UUID,
        token_hash: str,
        token_family_id: str,
        expires_at: datetime,
        device_id: str | None = None
    ) -> RefreshToken:
        """Create a new refresh token with family tracking.

        Args:
            jti: Token unique identifier
            user_id: User UUID
            token_hash: Hashed token string
            token_family_id: Family identifier for token rotation
            expires_at: Expiration datetime
            device_id: Optional device identifier

        Returns:
            Created refresh token instance
        """
        token = RefreshToken(
            id=UUID(jti),  # Use JTI as the primary key
            user_id=user_id,
            token_hash=token_hash,
            token_family_id=token_family_id,
            expires_at=expires_at,
            device_id=device_id
        )
        self.session.add(token)
        await self.session.flush()
        await self.session.refresh(token)
        return token

    async def get_by_id(self, token_id: UUID) -> RefreshToken | None:
        """Get refresh token by ID.

        Args:
            token_id: Token UUID

        Returns:
            RefreshToken instance or None if not found
        """
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.id == token_id)
        )
        return result.scalar_one_or_none()

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Get valid (non-revoked, non-expired) refresh token by hash.

        Args:
            token_hash: Hashed token string

        Returns:
            RefreshToken instance or None if not found or invalid
        """
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_hash_include_invalid(self, token_hash: str) -> RefreshToken | None:
        """Get refresh token by hash including revoked and expired tokens.

        Useful for audit logging or checking token history.

        Args:
            token_hash: Hashed token string

        Returns:
            RefreshToken instance or None if not found
        """
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def get_user_tokens(
        self,
        user_id: UUID,
        include_revoked: bool = False,
        include_expired: bool = False
    ) -> list[RefreshToken]:
        """Get all refresh tokens for a user.

        Args:
            user_id: User UUID
            include_revoked: Include revoked tokens in results
            include_expired: Include expired tokens in results

        Returns:
            List of refresh tokens
        """
        query = select(RefreshToken).where(RefreshToken.user_id == user_id)

        if not include_revoked:
            query = query.where(RefreshToken.revoked == False)

        if not include_expired:
            query = query.where(RefreshToken.expires_at > datetime.now(timezone.utc))

        query = query.order_by(RefreshToken.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_user_tokens(
        self,
        user_id: UUID,
        include_revoked: bool = False,
        include_expired: bool = False
    ) -> int:
        """Count refresh tokens for a user.

        Args:
            user_id: User UUID
            include_revoked: Include revoked tokens in count
            include_expired: Include expired tokens in count

        Returns:
            Count of tokens
        """
        query = select(func.count(RefreshToken.id)).where(
            RefreshToken.user_id == user_id
        )

        if not include_revoked:
            query = query.where(RefreshToken.revoked == False)

        if not include_expired:
            query = query.where(RefreshToken.expires_at > datetime.now(timezone.utc))

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def revoke(self, token_hash: str) -> bool:
        """Revoke a refresh token by hash.

        Args:
            token_hash: Hashed token string

        Returns:
            True if token was revoked, False if not found
        """
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked=True)
        )
        await self.session.flush()

        return result.rowcount > 0

    async def revoke_by_id(self, token_id: UUID) -> bool:
        """Revoke a refresh token by ID.

        Args:
            token_id: Token UUID

        Returns:
            True if token was revoked, False if not found
        """
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(revoked=True)
        )
        await self.session.flush()

        return result.rowcount > 0

    async def revoke_all_for_user(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user.

        Useful when user logs out from all devices or changes password.

        Args:
            user_id: User UUID

        Returns:
            Number of tokens revoked
        """
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
            .values(revoked=True)
        )
        await self.session.flush()

        return result.rowcount

    async def cleanup_expired(self) -> int:
        """Delete all expired tokens from database.

        This should be run periodically as a maintenance task.

        Returns:
            Number of tokens deleted
        """
        result = await self.session.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            )
        )
        await self.session.flush()

        return result.rowcount

    async def cleanup_revoked(self, older_than_days: int = 30) -> int:
        """Delete old revoked tokens from database.

        Args:
            older_than_days: Delete revoked tokens older than this many days

        Returns:
            Number of tokens deleted
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        result = await self.session.execute(
            delete(RefreshToken).where(
                RefreshToken.revoked == True,
                RefreshToken.created_at < cutoff_date
            )
        )
        await self.session.flush()

        return result.rowcount

    async def is_valid(self, token_hash: str) -> bool:
        """Check if a refresh token is valid (exists, not revoked, not expired).

        Args:
            token_hash: Hashed token string

        Returns:
            True if token is valid, False otherwise
        """
        result = await self.session.execute(
            select(func.count(RefreshToken.id)).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            )
        )
        count = result.scalar() or 0
        return count > 0

    # Token Family Methods for JWT rotation security

    async def is_token_revoked(self, jti: str) -> bool:
        """Check if a token (by JTI) is revoked.

        Args:
            jti: Token unique identifier

        Returns:
            True if token is revoked, False otherwise
        """
        result = await self.session.execute(
            select(func.count(RefreshToken.id)).where(
                RefreshToken.id == jti,
                RefreshToken.revoked == True
            )
        )
        count = result.scalar() or 0
        return count > 0

    async def revoke_token(self, jti: str) -> bool:
        """Revoke a refresh token by JTI.

        Args:
            jti: Token unique identifier

        Returns:
            True if token was revoked, False if not found
        """
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.id == jti)
            .values(revoked=True)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def revoke_family(self, family_id: str) -> int:
        """Revoke all tokens in a family (security breach response).

        Args:
            family_id: Token family identifier

        Returns:
            Number of tokens revoked
        """
        result = await self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_family_id == family_id,
                RefreshToken.revoked == False
            )
            .values(revoked=True)
        )
        await self.session.flush()
        return result.rowcount

    async def get_user(self, user_id: UUID):
        """Get user by ID for token generation.

        Args:
            user_id: User UUID

        Returns:
            User instance or None
        """
        from services.auth.models.user import User
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def cleanup_expired_tokens(self, user_id: UUID, max_tokens: int = 5) -> int:
        """Clean up old tokens for a user, keeping only the most recent ones.

        Args:
            user_id: User UUID
            max_tokens: Maximum number of tokens to keep

        Returns:
            Number of tokens deleted
        """
        # Get all valid tokens for user ordered by creation time
        tokens = await self.get_user_tokens(user_id, include_revoked=False, include_expired=False)

        # If within limit, no cleanup needed
        if len(tokens) <= max_tokens:
            return 0

        # Revoke older tokens beyond the limit
        tokens_to_revoke = tokens[max_tokens:]
        count = 0
        for token in tokens_to_revoke:
            if await self.revoke_by_id(token.id):
                count += 1

        return count
