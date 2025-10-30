# Cortex Backend - Corporate Agent System

A microservices-based backend system for corporate agent management with PostgreSQL, pgvector for semantic search, and multiple specialized services.

## Architecture

The system follows a microservices architecture with:

- **API Gateway**: Central entry point routing requests to appropriate services
- **Auth Service**: Authentication and authorization
- **Financial Service**: Accounts payable, corporate cards, cost centers
- **HR Service**: Employee management, contracts
- **Legal Service**: Contract management, legal processes
- **Procurement Service**: Purchase orders, supplier management
- **Documents Service**: Document management with vector embeddings for semantic search

## Tech Stack

- **Python 3.11+** with FastAPI
- **PostgreSQL** with pgvector extension
- **SQLAlchemy 2.0** for ORM
- **Alembic** for database migrations
- **Redis** for caching and message queuing
- **Celery** for async task processing
- **Docker** for containerization
- **OpenAI API** for embeddings and AI features

## Project Structure

```
backend/
├── alembic.ini              # Alembic configuration
├── migrations/              # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── shared/                  # Shared code across services
│   ├── config/             # Configuration settings
│   ├── database/           # Database connection
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   └── utils/              # Utility functions
├── services/               # Microservices
│   ├── gateway/           # API Gateway
│   ├── auth/              # Authentication service
│   ├── financial/         # Financial service
│   ├── hr/                # HR service
│   ├── legal/             # Legal service
│   ├── procurement/       # Procurement service
│   └── documents/         # Documents service
├── docker/                 # Docker configurations
├── scripts/               # Helper scripts
├── tests/                 # Test files
├── docker-compose.yml     # Docker compose configuration
├── pyproject.toml         # Poetry dependencies
└── .env.example           # Environment variables example
```

## Setup Instructions

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 14+ with pgvector extension
- Redis
- Docker and Docker Compose
- Poetry (Python package manager)

### 2. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd cortex/backend

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration

# Install dependencies with Poetry
poetry install

# Or with pip
pip install -r requirements.txt
```

### 3. Database Setup

#### Option A: Using Docker Compose (Recommended)

```bash
# Start PostgreSQL with pgvector and Redis
docker-compose up -d postgres redis

# Wait for services to be ready
sleep 10

# Initialize database extensions
poetry run python scripts/init_db.py

# Run migrations
poetry run alembic upgrade head
```

#### Option B: Manual PostgreSQL Setup

```bash
# Install pgvector extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

# Create database
CREATE DATABASE cortex_db;

# Run migrations
poetry run alembic upgrade head
```

### 4. Running the Services

#### Using Docker Compose (All Services)

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build

# View logs
docker-compose logs -f
```

#### Running Individual Services (Development)

```bash
# Terminal 1: Start Gateway
poetry run uvicorn services.gateway.main:app --reload --port 8000

# Terminal 2: Start Financial Service
poetry run python -m services.financial.main

# Terminal 3: Start other services as needed...
```

## Database Migrations

### Creating a New Migration

```bash
# Auto-generate migration from model changes
./scripts/create_migration.sh "Description of changes"

# Or manually
poetry run alembic revision --autogenerate -m "Description"
```

### Running Migrations

```bash
# Upgrade to latest
./scripts/migrate.sh

# Or specific commands
poetry run alembic upgrade head  # Latest version
poetry run alembic upgrade +1    # Next version
poetry run alembic downgrade -1  # Previous version
poetry run alembic current       # Show current version
```

## API Documentation

Once the services are running, you can access the interactive API documentation:

- **API Gateway**: http://localhost:8000/docs
- **Financial Service**: http://localhost:8002/docs
- **HR Service**: http://localhost:8003/docs
- **Legal Service**: http://localhost:8004/docs
- **Procurement Service**: http://localhost:8005/docs
- **Documents Service**: http://localhost:8006/docs

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=.

# Run specific test file
poetry run pytest tests/test_financial.py

# Run tests in parallel
poetry run pytest -n auto
```

## Development Workflow

1. **Make Model Changes**: Edit models in `shared/models/`
2. **Create Migration**: `./scripts/create_migration.sh "Your changes"`
3. **Review Migration**: Check the generated file in `migrations/versions/`
4. **Apply Migration**: `./scripts/migrate.sh`
5. **Test Changes**: Write and run tests
6. **Commit**: Commit your changes with migrations

## Service Endpoints

### Gateway Routes

All services are accessed through the gateway at `http://localhost:8000`:

- `/auth/*` → Auth Service
- `/financial/*` → Financial Service
- `/hr/*` → HR Service
- `/legal/*` → Legal Service
- `/procurement/*` → Procurement Service
- `/documents/*` → Documents Service

### Example API Calls

```bash
# Health check
curl http://localhost:8000/health

# List contas a pagar (through gateway)
curl http://localhost:8000/financial/contas-pagar?empresa_id=<uuid>

# Create new conta a pagar
curl -X POST http://localhost:8000/financial/contas-pagar \
  -H "Content-Type: application/json" \
  -d '{
    "empresa_id": "<uuid>",
    "valor": 1500.00,
    "data_vencimento": "2025-01-30",
    "descricao": "Pagamento fornecedor"
  }'
```

## Monitoring and Logs

### View Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f gateway
docker-compose logs -f financial-service

# PostgreSQL logs
docker-compose logs -f postgres
```

### Database Inspection

```bash
# Connect to database
docker-compose exec postgres psql -U cortex_user -d cortex_db

# Or locally
psql -h localhost -U cortex_user -d cortex_db
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port
   lsof -i :8000
   # Kill process
   kill -9 <PID>
   ```

2. **Database connection errors**
   - Check PostgreSQL is running: `docker-compose ps postgres`
   - Verify credentials in `.env`
   - Check network connectivity

3. **Migration errors**
   - Ensure database exists
   - Check current migration: `alembic current`
   - Review migration history: `alembic history`

4. **Service discovery issues**
   - Verify service URLs in `.env`
   - Check service health: `curl http://localhost:8000/health`

## Production Deployment

For production deployment:

**Before deploying to production:**

1. **Generate production keys:**
   ```sh
   ./scripts/generate_keys.sh
   ```
2. **Upload keys to AWS Secrets Manager:**
   ```sh
   aws secretsmanager create-secret --name cortex/auth/private-key --secret-string file://keys/private.pem
   aws secretsmanager create-secret --name cortex/auth/public-key --secret-string file://keys/public.pem
   ```
3. **Configure IAM permissions:**  
   Ensure your deployment has `secretsmanager:GetSecretValue` permissions.
4. **Set environment to production:**  
   In your deployment, set:  
   ```
   ENVIRONMENT=production
   ```
5. **Distribute public key to all microservices:**  
   Use a Kubernetes `ConfigMap` to distribute the key.
6. **Schedule key rotation:**  
   Rotate keys approximately every 90 days.

---

**Additional Production Checklist:**

1. Update `.env` with production values
2. Use a production-grade PostgreSQL instance
3. Configure proper CORS origins
4. Set up SSL/TLS certificates
5. Use a reverse proxy (Nginx/Traefik)
6. Configure monitoring (Prometheus/Grafana)
7. Set up log aggregation (ELK Stack)
8. Implement rate limiting
9. Configure auto-scaling

## Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Create migrations if needed
5. Submit a pull request

## License

[Your License Here]