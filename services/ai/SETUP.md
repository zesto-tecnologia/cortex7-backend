# AI Service Setup Guide

This guide walks through setting up the AI service from scratch.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Poetry (for dependency management)
- OpenAI API key

## Installation Steps

### 1. Install Dependencies

```bash
cd backend
poetry install
```

This installs all required packages including:
- CrewAI 0.80.0
- LangChain 0.3.0
- Celery 5.3.4
- FastAPI and other dependencies

### 2. Set Environment Variables

Create or update `.env` file in `/backend`:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=cortex_db
DATABASE_USER=cortex_user
DATABASE_PASSWORD=cortex_password

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_BACKEND_URL=redis://redis:6379/0

# Service Configuration
AI_SERVICE_PORT=8007
```

### 3. Run Database Migrations

Apply the workflow tables migration:

```bash
# From the backend directory
make migrate

# Or manually:
psql -h localhost -U cortex_user -d cortex_db -f migrations/versions/003_add_workflows_tarefas.sql
```

This creates:
- `workflows` table: For tracking AI workflow execution
- `tarefas` table: For task management

### 4. Start Services

Start all services including the AI service:

```bash
docker-compose up -d
```

This starts:
- `ai-service`: Main AI service (port 8007)
- `celery-worker`: Async task executor
- `flower`: Celery monitoring UI (port 5555)

### 5. Verify Installation

Check that all services are healthy:

```bash
# Check service status
docker-compose ps

# Check AI service health
curl http://localhost:8007/health

# Check Celery workers
curl http://localhost:5555
```

Expected health response:
```json
{
  "status": "healthy",
  "service": "ai",
  "openai_configured": true,
  "celery_broker": "redis://redis:6379/0"
}
```

## Configuration Details

### Docker Compose Configuration

The AI service is defined in `docker-compose.yml`:

```yaml
ai-service:
  build:
    context: .
    dockerfile: ./docker/Dockerfile.service
  container_name: cortex-ai
  environment:
    - SERVICE_NAME=ai
    - DATABASE_HOST=postgres
    - DATABASE_PORT=5432
    - DATABASE_NAME=cortex_db
    - DATABASE_USER=cortex_user
    - DATABASE_PASSWORD=cortex_password
    - REDIS_HOST=redis
    - REDIS_PORT=6379
    - SERVICE_PORT=8007
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - CELERY_BROKER_URL=redis://redis:6379/0
  ports:
    - "8007:8007"
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  networks:
    - cortex-network
```

### Celery Worker Configuration

```yaml
celery-worker:
  build:
    context: .
    dockerfile: ./docker/Dockerfile.celery
  container_name: cortex-celery-worker
  environment:
    - DATABASE_HOST=postgres
    - DATABASE_PORT=5432
    - DATABASE_NAME=cortex_db
    - DATABASE_USER=cortex_user
    - DATABASE_PASSWORD=cortex_password
    - REDIS_HOST=redis
    - REDIS_PORT=6379
    - OPENAI_API_KEY=${OPENAI_API_KEY}
  command: celery -A services.ai.tasks.workflow_tasks:celery_app worker --loglevel=info --concurrency=4
  networks:
    - cortex-network
```

## Database Schema

### Workflows Table

Tracks AI workflow execution:

```sql
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    workflow_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    input_data JSONB,
    result JSONB,
    error_message TEXT,
    celery_task_id VARCHAR(100) UNIQUE,
    priority VARCHAR(10) DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Tarefas Table

Tracks tasks and assignments:

```sql
CREATE TABLE tarefas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    tipo VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    atribuido_a UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    resultado JSONB,
    prioridade VARCHAR(10) DEFAULT 'normal',
    data_vencimento VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## Testing the Installation

### 1. Test Basic Chat

```bash
curl -X POST http://localhost:8007/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, what can you help me with?",
    "empresa_id": "11111111-1111-1111-1111-111111111111"
  }'
```

### 2. Test Async Workflow

```bash
curl -X POST http://localhost:8007/workflows/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "general",
    "empresa_id": "11111111-1111-1111-1111-111111111111",
    "input_data": {
      "task_description": "Analyze our company data"
    },
    "priority": "normal"
  }'
```

### 3. List Available Agents

```bash
curl http://localhost:8007/agents/
```

### 4. Check Celery Tasks in Flower

Open browser: http://localhost:5555

## Troubleshooting

### Issue: AI service won't start

**Check:**
1. OpenAI API key is set: `echo $OPENAI_API_KEY`
2. All dependencies installed: `poetry install`
3. Redis is running: `docker-compose ps redis`
4. Check logs: `docker-compose logs ai-service`

### Issue: Tools returning 404/405 errors

**Solution:**
- Ensure all backend services are running:
  ```bash
  docker-compose up -d hr-service legal-service procurement-service documents-service financial-service
  ```
- Verify service health:
  ```bash
  curl http://localhost:8003/health  # HR
  curl http://localhost:8004/health  # Legal
  curl http://localhost:8005/health  # Procurement
  ```

### Issue: Celery tasks failing

**Check:**
1. Celery worker is running: `docker-compose ps celery-worker`
2. Worker logs: `docker-compose logs celery-worker -f`
3. Redis connection: `docker-compose ps redis`
4. Flower UI for task status: http://localhost:5555

### Issue: Database migration fails

**Solution:**
```bash
# Check if tables already exist
psql -h localhost -U cortex_user -d cortex_db -c "\dt"

# If workflows/tarefas exist, migration already ran
# If not, run migration manually:
psql -h localhost -U cortex_user -d cortex_db -f migrations/versions/003_add_workflows_tarefas.sql
```

## Development Workflow

### Making Changes

1. **Modify code** in `services/ai/`
2. **Rebuild service**: `docker-compose up -d --build ai-service`
3. **Check logs**: `docker-compose logs ai-service -f`
4. **Test changes**: Use curl or Postman

### Adding New Dependencies

1. Add to `pyproject.toml`:
   ```toml
   [tool.poetry.dependencies]
   new-package = "^1.0.0"
   ```

2. Update lock file:
   ```bash
   poetry lock
   ```

3. Rebuild containers:
   ```bash
   docker-compose up -d --build ai-service celery-worker
   ```

## Next Steps

- Review [README.md](./README.md) for architecture overview
- Check [TOOLS_DOCUMENTATION.md](./TOOLS_DOCUMENTATION.md) for tool details
- Test the API using the Postman collection at `/backend/Cortex_API.postman_collection.json`

## Support

For issues or questions:
1. Check service logs
2. Verify all services are healthy
3. Review Flower UI for Celery task status
4. Consult the README and TOOLS_DOCUMENTATION

