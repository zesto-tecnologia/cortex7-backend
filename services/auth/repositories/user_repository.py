"""User repository for data access layer."""

from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError
from services.auth.models.user import User
from services.auth.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """Repository for user data access operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, user_data: UserCreate) -> User:
        """Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user instance

        Raises:
            IntegrityError: If user with email already exists
        """
        user = User(**user_data.model_dump())
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID (excluding soft-deleted users).

        Args:
            user_id: User UUID

        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email (excluding soft-deleted users).

        Args:
            email: User email address

        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(
                User.email == email,
                User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email_include_deleted(self, email: str) -> User | None:
        """Get user by email including soft-deleted users.

        Useful for checking if email was previously used.

        Args:
            email: User email address

        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: str | None = None,
        email_verified: bool | None = None
    ) -> list[User]:
        """List users with pagination and optional filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Optional role filter
            email_verified: Optional email verification status filter

        Returns:
            List of users
        """
        query = select(User).where(User.deleted_at.is_(None))

        if role is not None:
            query = query.where(User.role == role)

        if email_verified is not None:
            query = query.where(User.email_verified == email_verified)

        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        role: str | None = None,
        email_verified: bool | None = None
    ) -> int:
        """Count users with optional filters.

        Args:
            role: Optional role filter
            email_verified: Optional email verification status filter

        Returns:
            Count of users matching filters
        """
        query = select(func.count(User.id)).where(User.deleted_at.is_(None))

        if role is not None:
            query = query.where(User.role == role)

        if email_verified is not None:
            query = query.where(User.email_verified == email_verified)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def update(self, user_id: UUID, user_data: UserUpdate) -> User | None:
        """Update user information.

        Args:
            user_id: User UUID
            user_data: Update data (only non-None fields will be updated)

        Returns:
            Updated user instance or None if not found
        """
        # Only update fields that are provided (not None)
        update_data = user_data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_by_id(user_id)

        update_data['updated_at'] = datetime.now(timezone.utc)

        await self.session.execute(
            update(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .values(**update_data)
        )
        await self.session.flush()

        return await self.get_by_id(user_id)

    async def update_fields(self, user_id: UUID, **fields) -> User | None:
        """Update specific user fields directly without schema validation.

        Useful for internal operations like updating timestamps.

        Args:
            user_id: User UUID
            **fields: Field names and values to update

        Returns:
            Updated user instance or None if not found
        """
        if not fields:
            return await self.get_by_id(user_id)

        fields['updated_at'] = datetime.now(timezone.utc)

        await self.session.execute(
            update(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .values(**fields)
        )
        await self.session.flush()

        return await self.get_by_id(user_id)

    async def verify_email(self, user_id: UUID) -> User | None:
        """Mark user's email as verified.

        Args:
            user_id: User UUID

        Returns:
            Updated user instance or None if not found
        """
        await self.session.execute(
            update(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .values(email_verified=True, updated_at=datetime.now(timezone.utc))
        )
        await self.session.flush()

        return await self.get_by_id(user_id)

    async def change_role(self, user_id: UUID, new_role: str) -> User | None:
        """Change user's role.

        Args:
            user_id: User UUID
            new_role: New role ('user', 'admin', or 'super_admin')

        Returns:
            Updated user instance or None if not found
        """
        await self.session.execute(
            update(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .values(role=new_role, updated_at=datetime.now(timezone.utc))
        )
        await self.session.flush()

        return await self.get_by_id(user_id)

    async def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete a user (mark as deleted without removing from database).

        Args:
            user_id: User UUID

        Returns:
            True if user was deleted, False if not found
        """
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        )
        await self.session.flush()

        return result.rowcount > 0

    async def restore(self, user_id: UUID) -> User | None:
        """Restore a soft-deleted user.

        Args:
            user_id: User UUID

        Returns:
            Restored user instance or None if not found
        """
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(deleted_at=None, updated_at=datetime.now(timezone.utc))
        )
        await self.session.flush()

        # Use regular get without deleted_at filter to get restored user
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists with given email (excluding deleted).

        Args:
            email: Email address to check

        Returns:
            True if user exists, False otherwise
        """
        result = await self.session.execute(
            select(func.count(User.id))
            .where(User.email == email, User.deleted_at.is_(None))
        )
        count = result.scalar() or 0
        return count > 0


    async def hard_delete(self, user_id: UUID) -> None:
        """Permanently delete user from database (hard delete).

        WARNING: This operation is irreversible. Use with caution.
        For production, prefer soft_delete instead.

        Args:
            user_id: User ID to delete

        Returns:
            None
        """
        await self.session.execute(
            delete(User).where(User.id == user_id)
        )
        await self.session.flush()
