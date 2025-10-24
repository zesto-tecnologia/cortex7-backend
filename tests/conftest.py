"""Base pytest configuration and shared fixtures for all tests."""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock

# Set testing environment
os.environ["TESTING"] = "true"


# Pytest asyncio configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Database fixtures
@pytest.fixture(scope="function")
async def test_db_engine():
    """Create test database engine."""
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False
    )

    # Import all models to ensure they're registered
    from shared.models import (
        Company, Department, UserProfile, Document,
        CostCenter, Supplier, AccountPayable, CorporateCard, CardInvoice, CardTransaction,
        Employee, EmploymentContract, Contract, Lawsuit, PurchaseOrder,
        CorporateWorkflow, Task, AgentLog, AuditTrail, EmbeddingCache, AgentConfig
    )
    from shared.database.connection import Base

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# Company and User fixtures
@pytest.fixture
async def test_company(test_db_session: AsyncSession):
    """Create test company."""
    from shared.models.company import Company

    company = Company(
        company_name="Test Company",
        tax_id="12345678901234",
        settings={"timezone": "America/Sao_Paulo"}
    )
    test_db_session.add(company)
    await test_db_session.commit()
    await test_db_session.refresh(company)
    return company


@pytest.fixture
async def test_department(test_db_session: AsyncSession, test_company):
    """Create test department."""
    from shared.models.company import Department

    department = Department(
        company_id=test_company.id,
        name="Engineering",
        meta_data={"budget": 100000}
    )
    test_db_session.add(department)
    await test_db_session.commit()
    await test_db_session.refresh(department)
    return department


@pytest.fixture
async def test_user(test_db_session: AsyncSession, test_company, test_department):
    """Create test user."""
    from shared.models.user import UserProfile

    user = UserProfile(
        company_id=test_company.id,
        department_id=test_department.id,
        email="test@example.com",
        name="Test User",
        role="user",
        is_active=True,
        meta_data={"preferences": {}}
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(test_db_session: AsyncSession, test_company):
    """Create admin user."""
    from shared.models.user import UserProfile

    user = UserProfile(
        company_id=test_company.id,
        email="admin@example.com",
        name="Admin User",
        role="admin",
        is_active=True,
        meta_data={"admin": True}
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


# JWT and Authentication fixtures
@pytest.fixture
def mock_jwt_decode():
    """Mock JWT decode function."""
    def _mock_decode(token: str, **kwargs):
        if token == "valid_token":
            return {
                "sub": str(uuid4()),
                "email": "test@example.com",
                "role": "user",
                "company_id": str(uuid4()),
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow()
            }
        elif token == "admin_token":
            return {
                "sub": str(uuid4()),
                "email": "admin@example.com",
                "role": "admin",
                "company_id": str(uuid4()),
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow()
            }
        elif token == "expired_token":
            return {
                "sub": str(uuid4()),
                "email": "test@example.com",
                "role": "user",
                "company_id": str(uuid4()),
                "exp": datetime.utcnow() - timedelta(hours=1),
                "iat": datetime.utcnow() - timedelta(hours=2)
            }
        else:
            raise ValueError("Invalid token")

    return _mock_decode


@pytest.fixture
def auth_headers():
    """Generate authorization headers."""
    def _headers(token: str = "valid_token"):
        return {"Authorization": f"Bearer {token}"}
    return _headers


# API Client fixtures
@pytest.fixture
async def test_client(test_db_session):
    """Create test HTTP client for FastAPI app."""
    # This will be overridden in each service's test
    # Here we provide a base implementation
    from httpx import AsyncClient

    async with AsyncClient() as client:
        yield client


# Mock fixtures for external services
@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    mock.expire = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_celery():
    """Mock Celery task."""
    mock = MagicMock()
    mock.delay = MagicMock(return_value=MagicMock(id="test-task-id"))
    mock.apply_async = MagicMock(return_value=MagicMock(id="test-task-id"))
    return mock


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    mock = AsyncMock()
    mock.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="Test response from AI",
                        role="assistant"
                    )
                )
            ],
            usage=MagicMock(total_tokens=100)
        )
    )
    mock.embeddings.create = AsyncMock(
        return_value=MagicMock(
            data=[MagicMock(embedding=[0.1] * 1536)]
        )
    )
    return mock


# Utility fixtures
@pytest.fixture
def generate_uuid():
    """Generate UUID for testing."""
    def _generate():
        return str(uuid4())
    return _generate


@pytest.fixture
def sample_datetime():
    """Generate sample datetime for testing."""
    def _generate(days_delta: int = 0, hours_delta: int = 0):
        return datetime.utcnow() + timedelta(days=days_delta, hours=hours_delta)
    return _generate


# Test data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "newuser@example.com",
        "name": "New User",
        "role": "user",
        "password": "SecurePassword123!",
        "company_id": str(uuid4()),
        "department_id": str(uuid4())
    }


@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "title": "Test Document",
        "content": "This is a test document content",
        "document_type": "contract",
        "file_path": "/documents/test.pdf",
        "file_size": 1024,
        "mime_type": "application/pdf",
        "metadata": {"tags": ["test", "sample"]}
    }


@pytest.fixture
def sample_employee_data():
    """Sample employee data for testing."""
    return {
        "name": "John Doe",
        "email": "john.doe@company.com",
        "tax_id": "12345678901",
        "position": "Software Engineer",
        "admission_date": datetime.utcnow().date(),
        "department": "Engineering",
        "salary": 100000.00,
        "status": "active"
    }


@pytest.fixture
def sample_purchase_order_data():
    """Sample purchase order data for testing."""
    return {
        "supplier_id": str(uuid4()),
        "order_number": "PO-2024-001",
        "items": [
            {
                "description": "Laptop",
                "quantity": 2,
                "unit_price": 2500.00,
                "total": 5000.00
            }
        ],
        "total_amount": 5000.00,
        "status": "pending",
        "payment_term": "30 days",
        "delivery_date": datetime.utcnow().date() + timedelta(days=7)
    }


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()
            return self.end_time - self.start_time

        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()


# Test markers
pytest.mark.unit = pytest.mark.mark(name="unit")
pytest.mark.integration = pytest.mark.mark(name="integration")
pytest.mark.performance = pytest.mark.mark(name="performance")
pytest.mark.slow = pytest.mark.mark(name="slow")
pytest.mark.critical = pytest.mark.mark(name="critical")