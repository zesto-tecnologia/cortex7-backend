# Cortex Backend - FastAPI Microservices Project

**Project Type**: Python FastAPI Microservices Architecture
**Python Version**: 3.11+
**Package Manager**: uv
**Architecture**: Event-driven microservices with shared core

---

## 🚫 CRITICAL RULE: NO AUTOMATIC MARKDOWN DOCUMENTATION

### **ABSOLUTE PROHIBITION**
**NEVER create `.md` documentation files automatically after implementations.**

### **REQUIRED BEHAVIOR**
After ANY implementation, code change, or feature completion:
1. ✅ **Print concise terminal summary** with:
   - What was implemented/changed
   - Files modified with line references
   - Testing instructions (commands to run)
   - Next steps (if applicable)
2. ❌ **DO NOT create** analysis.md, summary.md, guide.md, or ANY .md files
3. ❌ **DO NOT write** to claudedocs/ directory automatically

### **EXCEPTION: ASK FIRST**
If documentation would be valuable:
```
"Implementation complete. Would you like me to create documentation for this feature?"
```
Only create .md files after explicit user confirmation: "yes", "create docs", "document this"

### **TERMINAL OUTPUT FORMAT**
```
✅ Implementation Complete

Modified Files:
- services/auth/api/v1/users.py:45-67 (added validation)
- services/auth/schemas/user.py:12-18 (new schema)

Testing:
make test-auth
# or
pytest tests/auth/test_users.py -v

Next Steps:
- Review validation logic
- Test edge cases
```

---

## 🏗️ Project Architecture

### **Directory Structure**
```
cortex7-backend/
├── services/           # Microservices (domain-driven)
│   ├── auth/          # Authentication & authorization
│   ├── financial/     # Financial operations
│   ├── procurement/   # Procurement management
│   ├── hr/            # Human resources
│   ├── legal/         # Legal documents
│   ├── ai/            # AI/ML agents
│   ├── presentation/  # Presentation generation
│   ├── documents/     # Document processing
│   └── gateway/       # API Gateway
├── shared/            # Shared utilities & models
├── migrations/        # Alembic database migrations
├── tests/             # Test suites per service
├── scripts/           # Utility scripts
└── docker/            # Docker configurations
```

### **Service Structure Pattern**
Each microservice follows this structure:
```
services/{service_name}/
├── __init__.py
├── main.py                    # FastAPI app entry point
├── config.py                  # Service-specific configuration
├── dependencies.py            # FastAPI dependency injection
├── api/
│   └── v1/                    # Versioned API endpoints
│       ├── __init__.py
│       └── {resource}.py      # Resource endpoints
├── models/                    # SQLAlchemy ORM models
│   ├── __init__.py
│   └── {entity}.py
├── schemas/                   # Pydantic schemas (DTOs)
│   ├── __init__.py
│   └── {entity}.py
├── services/                  # Business logic layer
│   ├── __init__.py
│   └── {service}_service.py
├── repositories/              # Data access layer
│   ├── __init__.py
│   └── {entity}_repository.py
└── tests/                     # Service-specific tests
    ├── unit/
    └── integration/
```

---

## 🔧 Development Standards

### **Code Quality Tools**
- **Formatter**: `black` (line-length: 100)
- **Linter**: `ruff` (with auto-fix enabled)
- **Type Checker**: `mypy` (optional, not strict)
- **Import Sorter**: `isort` (black-compatible profile)

### **Pre-Implementation Checklist**
Before writing code:
1. ✅ Read existing patterns in the service
2. ✅ Check `shared/` for reusable utilities
3. ✅ Review similar implementations in other services
4. ✅ Understand the service's `dependencies.py` injection patterns
5. ✅ Check if migrations are needed (database changes)

### **Code Style Guidelines**

#### **FastAPI Patterns**
```python
# ✅ CORRECT: Use dependency injection
@router.post("/users")
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    return await service.create_user(user_data)

# ❌ WRONG: Direct instantiation
@router.post("/users")
async def create_user(user_data: UserCreate):
    service = UserService()  # Don't do this
    return await service.create_user(user_data)
```

#### **Async/Await Pattern**
```python
# ✅ CORRECT: Async all the way
async def get_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

# ❌ WRONG: Mixing sync/async
def get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()
```

#### **Repository Pattern**
```python
# ✅ CORRECT: Repository encapsulates data access
class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalars().first()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
```

#### **Service Layer Pattern**
```python
# ✅ CORRECT: Business logic in service layer
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, user_data: UserCreate) -> User:
        # Validation
        existing = await self.repository.get_by_email(user_data.email)
        if existing:
            raise ValueError("Email already exists")

        # Business logic
        hashed_password = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password
        )

        # Persistence
        return await self.repository.create(user)
```

#### **Pydantic Schemas**
```python
# ✅ CORRECT: Separate request/response schemas
class UserCreate(BaseModel):
    """Request schema for user creation"""
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str

class UserResponse(BaseModel):
    """Response schema - no sensitive data"""
    id: int
    email: EmailStr
    full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ❌ WRONG: Exposing sensitive data
class UserResponse(BaseModel):
    password: str  # Never expose passwords!
    hashed_password: str  # Never expose hashes!
```

---

## 🗄️ Database Patterns

### **SQLAlchemy 2.0 Style**
```python
# ✅ CORRECT: Modern SQLAlchemy 2.0 syntax
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

# ❌ WRONG: Old SQLAlchemy 1.x style
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
```

### **Migrations with Alembic**
```bash
# Create new migration
alembic revision --autogenerate -m "add_user_roles"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check current version
alembic current
```

**Migration Best Practices**:
- Always review autogenerated migrations
- Add indexes for foreign keys
- Use batch operations for large tables
- Test rollback before committing
- Never edit applied migrations

---

## 🔐 Authentication & Security

### **JWT Authentication Pattern**
Project uses JWT tokens with:
- **Access Token**: Short-lived (15 minutes typical)
- **Refresh Token**: Long-lived, stored in database
- **RSA Keys**: Asymmetric encryption (see `keys/` directory)

### **Security Best Practices**
```python
# ✅ CORRECT: Dependency injection for auth
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> User:
    payload = jwt_service.verify_token(token)
    return await get_user_by_id(payload["sub"])

# ✅ CORRECT: Role-based access control
async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Use in routes
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin)  # Only admins can delete
):
    ...
```

### **Password Security**
- Use `passlib` with bcrypt
- Never log passwords
- Never return passwords in responses
- Use strong password validation

---

## 🧪 TESTING & PERFORMANCE POLICY

### **ASK BEFORE IMPLEMENTING**
**NEVER automatically implement tests or performance optimizations without asking first.**

### **REQUIRED BEHAVIOR**
After implementing core functionality:
1. ✅ **Assess criticality**: Determine what is vital vs optional
2. ✅ **Offer summary**: Present what tests/optimizations would be added
3. ✅ **Ask for decision**: Let user decide to implement now or later
4. ✅ **Prioritize context**: Consider project stage, urgency, and resources

### **DECISION FRAMEWORK**

#### **VITAL (Implement Automatically)**
These should be implemented as part of the core work without asking:

**Security & Authentication:**
- ✅ Password hashing validation
- ✅ JWT token verification tests
- ✅ Authorization/permission checks
- ✅ SQL injection prevention (parameterized queries)
- ✅ Input sanitization for user data
- ✅ Rate limiting for auth endpoints

**Data Integrity:**
- ✅ Unique constraint tests (emails, usernames, IDs)
- ✅ Foreign key relationship validation
- ✅ Transaction rollback on errors
- ✅ Required field validation
- ✅ Data type/format validation

**Core Business Logic:**
- ✅ Payment processing validation
- ✅ Order state machine transitions
- ✅ Financial calculations accuracy
- ✅ Inventory/stock management
- ✅ Critical workflow validation

**Error Handling (Must Have):**
- ✅ 404 for resource not found
- ✅ 401/403 for auth failures
- ✅ 400 for validation errors
- ✅ 409 for conflicts (duplicates)
- ✅ 500 error logging

**Database Operations (Critical):**
- ✅ Async session management (proper commit/rollback)
- ✅ Index on foreign keys
- ✅ Index on frequently queried fields (emails, status)
- ✅ Unique indexes where needed

#### **OPTIONAL (Ask First)**
These should be proposed with summary and time estimate:

**Performance Optimizations:**
- 🤔 Redis caching strategies
- 🤔 Query optimization (N+1 prevention)
- 🤔 Eager loading relationships
- 🤔 Pagination implementation
- 🤔 Background job processing (Celery)
- 🤔 Connection pooling tuning

**Extended Testing:**
- 🤔 Unit tests for simple CRUD operations
- 🤔 Integration tests for internal endpoints
- 🤔 Edge case scenario tests
- 🤔 Load/stress/performance tests
- 🤔 E2E workflow tests
- 🤔 Mock/fixture creation for testing

**Advanced Features:**
- 🤔 Comprehensive logging/monitoring
- 🤔 Metrics/observability
- 🤔 Advanced audit trails
- 🤔 Soft delete implementation
- 🤔 Versioning strategies

### **IMPLEMENTATION EXAMPLES**

#### **VITAL - Included Automatically**
```python
# ✅ Security: Password validation (ALWAYS INCLUDED)
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator('password')
    def validate_password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain digit')
        return v

# ✅ Data Integrity: Unique constraint (ALWAYS INCLUDED)
email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

# ✅ Error Handling: Proper HTTP exceptions (ALWAYS INCLUDED)
@router.get("/users/{user_id}")
async def get_user(user_id: int, service: UserService = Depends()):
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ✅ Database: Transaction management (ALWAYS INCLUDED)
async def create_user(self, user: User) -> User:
    try:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    except IntegrityError:
        await self.db.rollback()
        raise ValueError("Email already exists")
```

### **CONSULTATION FORMAT** (For Optional Items)
```
✅ Implementation Complete

Core functionality includes vital security/data integrity measures.

Would you like me to add optional optimizations?

[OPTIONAL - Your Decision]
- Performance: Redis caching for user profiles (~10 min)
- Performance: N+1 query prevention with eager loading (~15 min)
- Tests: Edge case unit tests (duplicate emails, invalid tokens) (~20 min)
- Tests: Integration test for full registration flow (~25 min)

Total estimated time: ~70 minutes

Add any/all of these? (yes/no/select specific)
```

### **TESTING REFERENCE** (When Implementing)

#### **Test Organization**
```
tests/{service}/
├── unit/           # Fast, isolated, no external dependencies
└── integration/    # Database, API, external services
```

#### **Basic Test Pattern**
```python
@pytest.mark.asyncio
async def test_create_user(user_service):
    user_data = UserCreate(email="test@example.com", password="strong123")
    user = await user_service.create_user(user_data)
    assert user.email == "test@example.com"
```

#### **Running Tests**
```bash
make test              # All tests
make test-auth         # Service-specific
pytest -m unit         # Only unit tests
pytest -m integration  # Only integration tests
```

### **PERFORMANCE REFERENCE** (When Implementing)

#### **Common Optimizations**
```python
# Database: Eager loading (prevent N+1)
result = await db.execute(
    select(User).options(selectinload(User.roles))
)

# Caching: Redis for expensive operations
cached = await redis.get(f"user:{user_id}")

# Background: Celery for heavy tasks
send_email.delay(user.id)  # Async task

# Indexes: Add in migrations for frequent queries
op.create_index('ix_users_email', 'users', ['email'])
```

---

## 📦 Dependency Management with UV

### **Common Commands**
```bash
# Add dependency
uv add fastapi

# Add dev dependency
uv add --dev pytest

# Install all dependencies
uv sync

# Update dependencies
uv lock --upgrade

# Run with UV
uv run python -m services.auth.main
uv run pytest
```

### **Import Organization**
```python
# ✅ CORRECT: Import order (enforced by isort)
# 1. Standard library
import json
from datetime import datetime
from typing import Optional

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from pydantic import BaseModel

# 3. Local (absolute imports preferred)
from services.auth.models.user import User
from services.auth.schemas.user import UserCreate
from shared.database import get_db
```

---

## 🔄 Git Workflow

### **Branch Naming**
```
feature/user-authentication
bugfix/token-expiration
hotfix/security-vulnerability
refactor/database-queries
```

### **Commit Messages**
```bash
# ✅ CORRECT: Clear, descriptive
git commit -m "Add JWT refresh token rotation logic"
git commit -m "Fix N+1 query in user profile endpoint"
git commit -m "Refactor: Extract email service to shared module"

# ❌ WRONG: Vague
git commit -m "fix stuff"
git commit -m "update"
git commit -m "changes"
```

### **Before Committing**
```bash
# Format code
ruff check --fix .
black .

# Run tests
make test

# Check types (if needed)
mypy services/auth/
```

---

## 🚀 Makefile Commands

The project uses `make` for common tasks. Key commands:

```bash
# Development
make setup              # Initial project setup
make run-auth           # Run auth service
make run-all            # Run all services

# Database
make db-migrate         # Create migration
make db-upgrade         # Apply migrations
make db-downgrade       # Rollback migration

# Testing
make test               # Run all tests
make test-auth          # Test auth service
make test-coverage      # Run with coverage

# Code Quality
make format             # Format code (black + ruff)
make lint               # Check code quality
make type-check         # Run mypy

# Docker
make docker-build       # Build containers
make docker-up          # Start containers
make docker-down        # Stop containers
make docker-logs        # View logs
```

---

## 🐛 Common Patterns & Solutions

### **Error Handling**
```python
# ✅ CORRECT: Specific exceptions with context
from fastapi import HTTPException, status

@router.get("/users/{user_id}")
async def get_user(user_id: int, service: UserService = Depends()):
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return user

# ✅ CORRECT: Service-level exceptions
class UserNotFoundError(Exception):
    pass

class UserService:
    async def get_user(self, user_id: int) -> User:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        return user
```

### **Configuration Management**
```python
# ✅ CORRECT: Use Pydantic Settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    jwt_secret_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()
```

### **Database Sessions**
```python
# ✅ CORRECT: Use dependency injection
from shared.database import get_db

@router.post("/users")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Session automatically committed/rolled back
    ...
```

---

## 📚 AI/ML Integration

Project uses multiple AI frameworks:
- **OpenAI**: GPT models for text generation
- **CrewAI**: Multi-agent orchestration
- **LangChain**: LLM application framework
- **ChromaDB**: Vector database for embeddings

### **AI Service Pattern**
```python
# ✅ CORRECT: Encapsulate AI logic
class AIService:
    def __init__(self, openai_client):
        self.client = openai_client

    async def generate_summary(self, text: str) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize concisely."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
```

---

## 🔍 Debugging

### **Development Server**
```bash
# Run with hot reload
uvicorn services.auth.main:app --reload --port 8001

# Run with debugger (VSCode configuration available)
# See .vscode/launch.json
```

### **Logging**
```python
# ✅ CORRECT: Structured logging
import structlog

logger = structlog.get_logger()

async def process_order(order_id: int):
    logger.info("processing_order", order_id=order_id)
    try:
        result = await process(order_id)
        logger.info("order_processed", order_id=order_id, result=result)
        return result
    except Exception as e:
        logger.error("order_processing_failed", order_id=order_id, error=str(e))
        raise
```

---

## 📝 API Documentation

FastAPI auto-generates documentation:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI JSON**: http://localhost:8001/openapi.json

### **Enhance Documentation**
```python
# ✅ CORRECT: Add descriptions
@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Creates a new user with email and password. Email must be unique.",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Invalid request data"},
        409: {"description": "Email already exists"}
    }
)
async def create_user(user_data: UserCreate):
    ...
```

---

## 🎯 Best Practices Summary

### **DO (Always Implement)**
✅ Use async/await consistently
✅ Follow repository pattern for data access
✅ Use dependency injection
✅ **Include vital security measures** (password validation, auth checks, input sanitization)
✅ **Include vital data integrity** (unique constraints, foreign keys, transaction rollback)
✅ **Include vital error handling** (404, 401, 403, 400, 409, 500 with logging)
✅ **Include vital database patterns** (indexes on FKs, async sessions, proper commits)
✅ Use type hints
✅ Use Pydantic for validation
✅ Check existing code patterns first
✅ Run formatters before committing
✅ Use migrations for schema changes

### **DON'T (Never Do)**
❌ Mix sync/async code
❌ Put business logic in endpoints
❌ Expose sensitive data in responses
❌ Create migrations manually
❌ Use global state
❌ Ignore type hints
❌ Return ORM models directly from endpoints
❌ **Create .md files automatically**
❌ Skip vital error handling
❌ Skip vital security measures

### **ASK FIRST (Optional Items)**
🤔 Performance optimizations (caching, query optimization, pagination)
🤔 Extended testing (edge cases, integration tests, E2E tests)
🤔 Advanced features (comprehensive logging, metrics, soft deletes)
🤔 Documentation files (.md creation)
🤔 When context matters: MVP vs Production, urgent vs planned

### **VITAL vs OPTIONAL Quick Reference**
| Category | VITAL (Auto-include) | OPTIONAL (Ask first) |
|----------|---------------------|---------------------|
| **Security** | Password validation, auth checks, input sanitization | Rate limiting, advanced audit logs |
| **Data** | Unique constraints, FK validation, transaction safety | Soft deletes, versioning |
| **Errors** | 404, 401, 403, 400, 409 handling | Comprehensive error logging |
| **Database** | Indexes on FKs/emails, async sessions | Query optimization, caching |
| **Testing** | None (ask for all) | All test types |
| **Performance** | None (ask for all) | All optimizations |

---

## 🆘 Getting Help

### **Documentation**
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Pydantic: https://docs.pydantic.dev/
- Alembic: https://alembic.sqlalchemy.org/

### **Project-Specific**
- Check `README.md` for setup instructions
- See `MAKEFILE_COMMANDS.md` for available commands
- Review existing services for implementation patterns
- Check `shared/` for reusable utilities

### **Troubleshooting**
```bash
# Database issues
make db-reset           # Reset database
alembic current         # Check migration status

# Dependency issues
uv sync                 # Resync dependencies
uv clean                # Clean cache

# Container issues
make docker-restart     # Restart containers
make docker-logs        # Check logs
```

---

**Remember**:
- **ALWAYS AUTO-INCLUDE**: Security measures, data integrity, error handling, critical DB patterns
- **NEVER AUTO-INCLUDE**: Tests, performance optimizations, advanced features (ask first)
- **NEVER CREATE**: .md files automatically - always ask first
- **ALWAYS PROVIDE**: Clear terminal summaries instead of documentation
- **ALWAYS CONSULT**: On optional items with summary + time estimate

**Implementation Checklist for Every Feature**:
1. ✅ Core functionality (main requirement)
2. ✅ Vital security (if auth/data involved)
3. ✅ Vital data integrity (constraints, validation)
4. ✅ Vital error handling (proper HTTP exceptions)
5. ✅ Vital database (indexes, transactions)
6. 🤔 **THEN ASK**: "Would you like me to add [optional items with estimates]?"
