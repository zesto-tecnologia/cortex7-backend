"""Tests for authentication service database models."""

import pytest
from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from services.auth.database import Base
from services.auth.models.user import User
from services.auth.models.role import Role, Permission, UserRole
from services.auth.models.invite import InviteCode
from services.auth.models.refresh_token import RefreshToken


@pytest.fixture
async def db_session():
    """Create test database session."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_user_creation(db_session):
    """Test creating a user."""
    user = User(
        email="test@example.com",
        name="Test User",
        role="user",
        email_verified=True,
        verified_at=datetime.now(timezone.utc)
    )

    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
    assert user.created_at is not None
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.is_active() is True


@pytest.mark.asyncio
async def test_user_soft_delete(db_session):
    """Test soft delete functionality."""
    user = User(
        email="test@example.com",
        name="Test User",
        role="user",
        email_verified=True
    )

    db_session.add(user)
    await db_session.commit()

    # Soft delete user
    user.soft_delete()
    await db_session.commit()

    assert user.is_deleted() is True
    assert user.deleted_at is not None
    assert user.is_active() is False


@pytest.mark.asyncio
async def test_role_creation(db_session):
    """Test creating a role."""
    role = Role(
        name="admin",
        description="System administrator"
    )

    db_session.add(role)
    await db_session.commit()

    assert role.id is not None
    assert role.name == "admin"
    assert role.created_at is not None


@pytest.mark.asyncio
async def test_permission_creation(db_session):
    """Test creating a permission."""
    permission = Permission(
        name="read:users",
        resource="users",
        action="read",
        description="Read user data"
    )

    db_session.add(permission)
    await db_session.commit()

    assert permission.id is not None
    assert permission.name == "read:users"
    assert permission.resource == "users"
    assert permission.action == "read"


@pytest.mark.asyncio
async def test_user_role_assignment(db_session):
    """Test assigning roles to users."""
    user = User(
        email="user@test.com",
        name="Test User",
        role="user",
        email_verified=True
    )
    role = Role(name="admin", description="Administrator")

    db_session.add_all([user, role])
    await db_session.flush()

    user_role = UserRole(
        user_id=user.id,
        role_id=role.id
    )
    db_session.add(user_role)
    await db_session.commit()

    # Reload user to get relationships
    await db_session.refresh(user)

    assert len(user.user_roles) == 1
    assert user.user_roles[0].role.name == "admin"


@pytest.mark.asyncio
async def test_role_permission_assignment(db_session):
    """Test assigning permissions to roles."""
    role = Role(name="manager", description="Manager")
    permission = Permission(
        name="write:users",
        resource="users",
        action="write"
    )

    db_session.add_all([role, permission])
    await db_session.flush()

    role.permissions.append(permission)
    await db_session.commit()

    # Reload role to get relationships
    await db_session.refresh(role)

    assert len(role.permissions) == 1
    assert role.permissions[0].name == "write:users"


@pytest.mark.asyncio
async def test_invite_code_validity(db_session):
    """Test invite code is_valid property."""
    # Create admin user for foreign key
    admin = User(
        email="admin@test.com",
        name="Admin User",
        role="admin",
        email_verified=True
    )
    db_session.add(admin)
    await db_session.flush()

    # Valid invite
    valid_invite = InviteCode(
        code="VALID123",
        creator_id=admin.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db_session.add(valid_invite)
    await db_session.commit()

    assert valid_invite.is_valid() is True

    # Expired invite
    expired_invite = InviteCode(
        code="EXPIRED123",
        creator_id=admin.id,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    db_session.add(expired_invite)
    await db_session.commit()

    assert expired_invite.is_valid() is False


@pytest.mark.asyncio
async def test_invite_code_revocation(db_session):
    """Test invite code revocation."""
    admin = User(
        email="admin@test.com",
        name="Admin User",
        role="admin",
        email_verified=True
    )
    db_session.add(admin)
    await db_session.flush()

    invite = InviteCode(
        code="TEST123",
        creator_id=admin.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db_session.add(invite)
    await db_session.commit()

    assert invite.is_valid() is True

    # Revoke invite
    invite.revoke()
    await db_session.commit()

    assert invite.is_valid() is False
    assert invite.revoked_at is not None


@pytest.mark.asyncio
async def test_invite_code_usage(db_session):
    """Test marking invite code as used."""
    admin = User(
        email="admin@test.com",
        name="Admin User",
        role="admin",
        email_verified=True
    )
    user = User(
        email="user@test.com",
        name="Regular User",
        role="user",
        email_verified=True
    )
    db_session.add_all([admin, user])
    await db_session.flush()

    invite = InviteCode(
        code="TEST123",
        creator_id=admin.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db_session.add(invite)
    await db_session.flush()

    assert invite.is_valid() is True

    # Mark as used
    invite.mark_as_used(user.id)
    await db_session.commit()

    assert invite.is_valid() is False
    assert invite.used_at is not None
    assert invite.used_by_id == user.id


@pytest.mark.asyncio
async def test_refresh_token_validity(db_session):
    """Test refresh token is_valid property."""
    user = User(
        email="user@test.com",
        name="Regular User",
        role="user",
        email_verified=True
    )
    db_session.add(user)
    await db_session.flush()

    # Valid refresh token
    valid_token = RefreshToken(
        user_id=user.id,
        jti=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db_session.add(valid_token)
    await db_session.commit()

    assert valid_token.is_valid() is True

    # Revoke token
    valid_token.revoke()
    await db_session.commit()

    assert valid_token.is_valid() is False


@pytest.mark.asyncio
async def test_user_cascade_delete(db_session):
    """Test that deleting a user cascades to related records."""
    user = User(
        email="user@test.com",
        name="Regular User",
        role="user",
        email_verified=True
    )
    db_session.add(user)
    await db_session.flush()

    # Add refresh token
    token = RefreshToken(
        user_id=user.id,
        jti=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db_session.add(token)
    await db_session.commit()

    user_id = user.id

    # Delete user
    await db_session.delete(user)
    await db_session.commit()

    # Verify refresh token was also deleted
    from sqlalchemy import select
    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user_id)
    )
    tokens = result.scalars().all()

    assert len(tokens) == 0
