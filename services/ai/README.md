# AI Service - CrewAI & LangChain Integration

This service provides AI agent capabilities using CrewAI and LangChain, integrated with existing backend microservices.

## Overview

The AI service orchestrates intelligent agents that can:
- Query and analyze data from other microservices (Financial, HR, Legal, Documents, Procurement)
- Execute complex multi-step workflows
- Provide conversational AI through chat interface
- Run asynchronous background tasks for complex operations

## Architecture

```
┌─────────────────────┐
│   Chat Interface    │  ← Synchronous queries
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   AI Service        │
│  (FastAPI + CrewAI) │
└──────────┬──────────┘
           │
     ┌─────┴──────┐
     │            │
┌────▼────┐  ┌───▼────┐
│  Crews  │  │ Agents │
│         │  │        │
│ General │  │ Domain │
│Financial│  │   HR   │
│Document │  │ Legal  │
└────┬────┘  └────┬───┘
     │            │
     └─────┬──────┘
           │
     ┌─────▼─────┐
     │   Tools   │ ← Call other services
     └───────────┘
```

## Components

### 1. Agents (`agents/`)

**Domain Agents:**
- `financial_agent`: Financial data analysis
- `hr_agent`: Employee and HR management
- `legal_agent`: Legal compliance and contracts
- `documents_agent`: Document search and retrieval
- `procurement_agent`: Purchase orders and approvals

**General Agents:**
- `researcher_agent`: Information gathering
- `analyst_agent`: Data analysis and insights
- `writer_agent`: Content generation

### 2. Tools (`tools/`)

Tools are integrations with backend services:
- `financial_tools`: Accounts payable, suppliers, cost centers
- `hr_tools`: Employees, vacation, contracts
- `legal_tools`: Contracts, deadlines, legal processes
- `documents_tools`: Document search and listing
- `procurement_tools`: Purchase orders, approvals

All tools use **CrewAI's native BaseTool** format for compatibility.

### 3. Crews (`crews/`)

Crews are teams of agents working together:
- `general_task_crew`: Versatile crew for any business task
- `financial_analysis_crew`: Specialized financial analysis
- `document_review_crew`: Document review and compliance

### 4. Routers (`routers/`)

API endpoints:
- `/chat`: Synchronous chat interface
- `/chat/stream`: Streaming chat responses
- `/workflows`: Async workflow management
- `/agents`: List available agents and crews

### 5. Tasks (`tasks/`)

Celery tasks for async execution:
- `execute_general_workflow`: General task execution
- `execute_financial_analysis`: Financial analysis workflow
- `execute_document_review`: Document review workflow

## API Endpoints

### Health Check
```
GET /health
```

### Chat (Synchronous)
```
POST /chat/
{
  "message": "How many employees do we have?",
  "empresa_id": "uuid",
  "is_async": false
}
```

### Chat (Streaming)
```
POST /chat/stream
{
  "message": "Analyze our financial situation",
  "empresa_id": "uuid"
}
```

### Trigger Workflow (Asynchronous)
```
POST /workflows/trigger
{
  "workflow_type": "general|financial_analysis|document_review",
  "empresa_id": "uuid",
  "input_data": {...},
  "priority": "normal|high|low"
}
```

### Get Workflow Status
```
GET /workflows/{workflow_id}
```

### List Workflows
```
GET /workflows/?empresa_id={uuid}&status=pending&limit=50
```

### Cancel Workflow
```
DELETE /workflows/{workflow_id}
```

### List Available Agents
```
GET /agents/
```

### List Available Crews
```
GET /agents/crews
```

## Configuration

Environment variables (set in docker-compose.yml):
- `OPENAI_API_KEY`: OpenAI API key for LLM
- `CELERY_BROKER_URL`: Redis URL for Celery
- `SERVICE_PORT`: Port for the service (default: 8007)

## Dependencies

Key dependencies:
- `crewai ^0.80.0`: Agent orchestration framework
- `langchain ^0.3.0`: LLM framework
- `langchain-openai ^0.3.0`: OpenAI integration
- `celery ^5.3.4`: Async task queue
- `httpx`: HTTP client for service calls

## Tool Endpoint Mapping

### HR Service (port 8003)
- `GET /funcionarios/` - List employees
- `GET /ferias/funcionario/{id}` - Employee vacation info
- `GET /contratos/funcionario/{id}` - Employee contracts

### Financial Service (port 8002)
- `GET /contas-pagar/` - Accounts payable
- `GET /fornecedores/` - Suppliers
- `GET /centros-custo/` - Cost centers

### Legal Service (port 8004)
- `GET /contratos/` - Legal contracts
- `GET /prazos/todos/{empresa_id}` - Legal deadlines
- `GET /processos/` - Legal processes

### Documents Service (port 8006)
- `GET /search/` - Semantic document search
- `GET /` - List documents

### Procurement Service (port 8005)
- `GET /ordens-compra/` - Purchase orders
- `GET /aprovacoes/` - Pending approvals

## Monitoring

- **Flower UI**: http://localhost:5555 (Celery task monitoring)
- **Service Logs**: `docker-compose logs ai-service -f`
- **Celery Worker Logs**: `docker-compose logs celery-worker -f`

## Development

### Testing Locally

```bash
# Test health endpoint
curl http://localhost:8007/health

# Test chat endpoint
curl -X POST http://localhost:8007/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"List employees","empresa_id":"11111111-1111-1111-1111-111111111111"}'

# List available agents
curl http://localhost:8007/agents/
```

### Adding New Tools

1. Create tool in `tools/` directory using CrewAI's `BaseTool`
2. Define `name`, `description`, and `_run()` method
3. Add to appropriate agent's tools list
4. Update documentation

### Adding New Agents

1. Create agent in `agents/` directory
2. Import tools the agent needs
3. Define role, goal, and backstory
4. Add to crew composition if needed

## Troubleshooting

### Tool Validation Errors

If you see "Input should be a valid dictionary or instance of BaseTool":
- Ensure tools inherit from `crewai.tools.BaseTool` (not LangChain's)
- Define `name` and `description` as class attributes
- Implement `_run()` method (not `_arun()`)

### Service Connection Errors

If tools can't reach services:
- Check service is running: `docker-compose ps`
- Verify service URLs use docker service names (e.g., `http://hr-service:8003`)
- Check network: all services should be on `cortex-network`

### Celery Task Failures

If async workflows fail:
- Check Celery worker logs: `docker-compose logs celery-worker`
- Verify Redis is running: `docker-compose ps redis`
- Check Flower UI for task status: http://localhost:5555

## See Also

- [TOOLS_DOCUMENTATION.md](./TOOLS_DOCUMENTATION.md) - Detailed tool reference
- [SETUP.md](./SETUP.md) - Setup and installation guide

