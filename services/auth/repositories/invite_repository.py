"""Invite code repository for database operations."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.models.invite import InviteCode
from services.auth.core.logging import get_logger

logger = get_logger(__name__)


class InviteCodeRepository:
    """Repository for invite code database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize invite code repository.

        Args:
            session: Database session
        """
        self.session = session

    async def create(
        self,
        creator_id: UUID,
        expires_in_days: int = 7
    ) -> InviteCode:
        """Generate a new invite code.

        Args:
            creator_id: UUID of the user creating the invite
            expires_in_days: Number of days until expiration (default: 7)

        Returns:
            InviteCode: Created invite code
        """
        # Generate cryptographically secure 32-byte invite code
        code = secrets.token_urlsafe(32)

        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        invite = InviteCode(
            code=code,
            creator_id=creator_id,
            expires_at=expires_at
        )

        self.session.add(invite)
        await self.session.commit()
        await self.session.refresh(invite)

        logger.info(f"invite_code_created - creator_id={creator_id}, code={code[:8]}...")

        return invite

    async def get_by_code(self, code: str) -> Optional[InviteCode]:
        """Get invite code by code string.

        Args:
            code: Invite code string

        Returns:
            Optional[InviteCode]: Invite code if found, None otherwise
        """
        stmt = select(InviteCode).where(InviteCode.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def validate_and_mark_used(
        self,
        code: str,
        user_id: UUID
    ) -> InviteCode:
        """Validate invite code and mark as used.

        Args:
            code: Invite code string
            user_id: UUID of the user using the invite

        Returns:
            InviteCode: The invite code that was marked as used

        Raises:
            ValueError: If invite code is invalid, expired, or already used
        """
        invite = await self.get_by_code(code)

        if not invite:
            raise ValueError("Invalid invite code")

        if not invite.is_valid():
            if invite.used_at:
                raise ValueError("Invite code has already been used")
            elif invite.revoked_at:
                raise ValueError("Invite code has been revoked")
            elif invite.expires_at < datetime.now(timezone.utc):
                raise ValueError("Invite code has expired")
            else:
                raise ValueError("Invalid invite code")

        # Mark as used
        invite.mark_as_used(user_id)
        await self.session.commit()
        await self.session.refresh(invite)

        logger.info(f"invite_code_used - code={code[:8]}..., user_id={user_id}")

        return invite

    async def revoke(self, code: str) -> InviteCode:
        """Revoke an invite code.

        Args:
            code: Invite code string

        Returns:
            InviteCode: The revoked invite code

        Raises:
            ValueError: If invite code not found
        """
        invite = await self.get_by_code(code)

        if not invite:
            raise ValueError("Invite code not found")

        invite.revoke()
        await self.session.commit()
        await self.session.refresh(invite)

        logger.info(f"invite_code_revoked - code={code[:8]}...")

        return invite

    async def list_by_creator(
        self,
        creator_id: UUID,
        include_used: bool = True,
        include_expired: bool = True,
        include_revoked: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> list[InviteCode]:
        """List invite codes created by a specific user.

        Args:
            creator_id: UUID of the creator
            include_used: Include used invite codes
            include_expired: Include expired invite codes
            include_revoked: Include revoked invite codes
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            list[InviteCode]: List of invite codes
        """
        stmt = (
            select(InviteCode)
            .where(InviteCode.creator_id == creator_id)
            .order_by(InviteCode.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        # Apply filters
        if not include_used:
            stmt = stmt.where(InviteCode.used_at.is_(None))
        if not include_expired:
            stmt = stmt.where(InviteCode.expires_at > datetime.now(timezone.utc))
        if not include_revoked:
            stmt = stmt.where(InviteCode.revoked_at.is_(None))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(
        self,
        status_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[InviteCode]:
        """List all invite codes with optional filtering.

        Args:
            status_filter: Filter by status ("pending", "used", "expired", "revoked")
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            list[InviteCode]: List of invite codes
        """
        stmt = (
            select(InviteCode)
            .order_by(InviteCode.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        now = datetime.now(timezone.utc)

        if status_filter == "pending":
            stmt = stmt.where(
                InviteCode.used_at.is_(None),
                InviteCode.revoked_at.is_(None),
                InviteCode.expires_at > now
            )
        elif status_filter == "used":
            stmt = stmt.where(InviteCode.used_at.isnot(None))
        elif status_filter == "expired":
            stmt = stmt.where(
                InviteCode.used_at.is_(None),
                InviteCode.expires_at <= now
            )
        elif status_filter == "revoked":
            stmt = stmt.where(InviteCode.revoked_at.isnot(None))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_creator(self, creator_id: UUID) -> int:
        """Count invite codes created by a specific user.

        Args:
            creator_id: UUID of the creator

        Returns:
            int: Total count of invite codes
        """
        stmt = select(func.count()).select_from(InviteCode).where(
            InviteCode.creator_id == creator_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def cleanup_expired(self, days_old: int = 90) -> int:
        """Delete expired invite codes older than specified days.

        Args:
            days_old: Delete invites older than this many days (default: 90)

        Returns:
            int: Number of deleted invites
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

        stmt = select(InviteCode).where(
            InviteCode.expires_at < cutoff_date
        )
        result = await self.session.execute(stmt)
        invites = list(result.scalars().all())

        count = len(invites)

        for invite in invites:
            await self.session.delete(invite)

        await self.session.commit()

        logger.info(f"cleaned_up_expired_invites - count={count}, days_old={days_old}")

        return count
