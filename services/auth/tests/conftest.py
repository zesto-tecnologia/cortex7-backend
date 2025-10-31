"""Pytest configuration and shared fixtures for all tests."""

import pytest
import asyncio
from typing import AsyncGenerator
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from services.auth.database import Base
from services.auth.config import settings
from services.auth.models.user import User
from services.auth.models.refresh_token import RefreshToken
from services.auth.repositories.refresh_token_repository import RefreshTokenRepository
from services.auth.core.cache import RedisClient


# Pytest asyncio configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Database fixtures
@pytest.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# Repository fixtures
@pytest.fixture
def refresh_token_repo(db_session: AsyncSession) -> RefreshTokenRepository:
    """Create refresh token repository instance."""
    return RefreshTokenRepository(db_session)


# Redis fixtures
@pytest.fixture
async def redis_client() -> AsyncGenerator[RedisClient, None]:
    """Create test Redis client."""
    client = RedisClient()
    await client.connect()

    yield client

    # Cleanup: flush test database
    if client.redis:
        await client.redis.flushdb()
    await client.disconnect()


# User fixtures
@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user."""
    user = User(
        email="test@example.com",
        name="Test User",
        role="user",
        is_active=True,
        supabase_id=str(uuid4())
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create admin user."""
    user = User(
        email="admin@example.com",
        name="Admin User",
        role="admin",
        is_active=True,
        supabase_id=str(uuid4())
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def super_admin_user(db_session: AsyncSession) -> User:
    """Create super admin user."""
    user = User(
        email="superadmin@example.com",
        name="Super Admin",
        role="super_admin",
        is_active=True,
        supabase_id=str(uuid4())
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# Helper fixtures
@pytest.fixture
def mock_token_claims():
    """Mock JWT token claims."""
    return {
        "sub": str(uuid4()),
        "email": "test@example.com",
        "role": "user",
        "token_type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=10),
        "iat": datetime.utcnow(),
        "jti": str(uuid4())
    }
