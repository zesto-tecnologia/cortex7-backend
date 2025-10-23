You are an AI assistant managing a Python FastAPI microservices project. Your task is to identify the next available service task, perform setup, and prepare for implementation in a distributed system context.

<critical>Python microservices critical validation rules</critical>

**YOU MUST USE** --think for distributed system analysis

<arguments>$ARGUMENTS</arguments>
<arguments_table>
| Argument | Description | Example |
|----------|-------------|---------|
| --prd | PRD identifier | --prd=ai-chat |
| --service | Service name | --service=auth |
| --task | Task identifier | --task=4.2 |
</arguments_table>

<task_locations>
Service Task: ./tasks/prd-[$prd]/[$service]/[$task]_task.md
PRD: ./tasks/prd-[$prd]/_prd.md
Tech Spec: ./tasks/prd-[$prd]/_techspec.md
Proto Definitions: ./tasks/prd-[$prd]/proto/
Service Design: ./tasks/prd-[$prd]/services/[$service]/design.md
</task_locations>

<project_standards>
Python Standards: ./standards/python-fastapi.md
gRPC Patterns: ./standards/grpc-patterns.md
Microservices: ./standards/microservices.md
</project_standards>

Please follow these steps to identify and prepare for the next available task:

## 1. Scan Service Tasks

Scan the task directories in tasks/prd-[$prd]/[$service]/ for task files:
- Identify uncompleted service tasks
- Check shared component tasks
- Review infrastructure tasks

## 2. Pre-Task Setup

Once you've identified the next task, perform the following setup:

a. **Read task definition** from service task file
b. **Review PRD context** for business requirements
c. **Check Tech Spec** for:
   - Service boundaries and responsibilities
   - gRPC service definitions
   - REST API specifications
   - Database schemas
   - Communication patterns
d. **Review Proto definitions** for service contracts
e. **Check service design** documents
f. **Understand dependencies** from:
   - Other services (gRPC clients needed)
   - Shared libraries
   - Infrastructure components

## 3. Task Analysis

<task_analysis>
Analyze the gathered information considering:

**Service Architecture:**
- Service boundaries and data ownership
- Inter-service communication patterns
- Dependency on other microservices
- Database strategy (shared vs service-specific)

**Python Implementation:**
- FastAPI routes and dependency injection
- Async/await patterns required
- Pydantic models for validation
- SQLAlchemy models if database involved

**gRPC Integration:**
- Protocol buffer definitions needed
- Service stubs and implementations
- Client connections to other services
- Streaming vs unary calls

**Infrastructure:**
- Docker configuration
- Kubernetes manifests
- Environment variables
- Secrets management

**Testing Strategy:**
- Unit tests with pytest
- gRPC service tests
- Integration tests
- Load testing requirements
</task_analysis>

## 4. Task Summary

<task_summary>
Task ID: [Service.Task e.g., auth.4.2]
Service: [Service name]
Task Name: [Brief description]

Business Context:
- PRD requirements addressed
- User stories impacted

Technical Requirements:
- gRPC endpoints to implement
- REST APIs to expose
- Database operations
- Cache strategies

Service Dependencies:
- Upstream services (depends on)
- Downstream services (provides to)
- Shared libraries needed

Infrastructure:
- Deployment configuration
- Scaling requirements
- Monitoring setup

Main Objectives:
1. [Primary implementation goal]
2. [Secondary goal]
3. [Testing goal]

Risks/Challenges:
- [Distributed system challenges]
- [Performance considerations]
- [Consistency requirements]
</task_summary>

## 5. Implementation Approach

<task_approach>
### Phase 1: Service Setup
1. Verify UV package manager and pyproject.toml
2. Install required dependencies
3. Set up project structure

### Phase 2: Proto Definition (if needed)
1. Define/update protocol buffer messages
2. Generate Python gRPC code
3. Update service contracts

### Phase 3: Core Implementation
1. Implement gRPC service methods
2. Create FastAPI endpoints
3. Add business logic layer
4. Implement data access layer

### Phase 4: Integration
1. Connect to dependent services
2. Set up gRPC clients
3. Configure circuit breakers
4. Add retry logic

### Phase 5: Testing
1. Write unit tests with pytest
2. Add gRPC service tests
3. Create integration tests
4. Verify against success criteria

### Phase 6: Deployment Prep
1. Update Dockerfile
2. Configure Kubernetes manifests
3. Set up health checks
4. Add monitoring endpoints
</task_approach>

## 6. Python Implementation Details

<python_specifics>
### FastAPI Setup
```python
from fastapi import FastAPI, Depends
from src.core.config import settings
from src.api.routes import router

app = FastAPI(title=settings.SERVICE_NAME)
app.include_router(router)
```

### gRPC Service Implementation
```python
import grpc
from concurrent import futures
from src.grpc import service_pb2_grpc

server = grpc.aio.server()
service_pb2_grpc.add_ServiceServicer_to_server(
    ServiceImpl(), server
)
```

### Dependency Injection Pattern
```python
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

async def get_service(
    db: AsyncSession = Depends(get_db)
) -> ServiceClass:
    return ServiceClass(db)
```

### Testing Setup
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_endpoint():
    async with AsyncClient(app=app) as client:
        response = await client.post("/api/v1/resource")
        assert response.status_code == 201
```
</python_specifics>

## 7. Begin Implementation

<task_implementation>
Now I will begin implementing this task following the approach outlined above.

Starting with:
1. Environment setup and dependency verification
2. Proto definition updates (if needed)
3. Core service implementation
4. Testing and validation
5. Deployment configuration
</task_implementation>

[Continue with actual implementation...]

## Important Notes

- **Service Isolation**: Ensure services remain loosely coupled
- **Async Patterns**: Use async/await throughout for performance
- **Error Handling**: Implement proper error propagation across services
- **Observability**: Add structured logging and tracing
- **Testing**: Include both unit and integration tests
- **Documentation**: Update OpenAPI specs and gRPC documentation

<requirements>
- **YOU MUST** start implementation immediately after analysis
- **YOU MUST** follow Python async patterns
- **YOU MUST** ensure gRPC contracts are respected
- **YOU MUST** validate against microservices best practices
</requirements>