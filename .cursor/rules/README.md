# Python Microservices Development Rules

This directory contains comprehensive rules and standards for developing Python FastAPI microservices with gRPC communication in a distributed architecture.

## 📚 Rule Categories

### 1. [Critical Validation](./critical-validation.mdc) ⚠️
- **MANDATORY** requirements for Python/FastAPI projects
- Core validation rules and quality gates
- Testing and code quality requirements
- Service implementation order
- Task completion checklist

### 2. [Architecture Rules](./architecture.mdc)
- Microservices design principles
- Service boundaries and domain contexts
- Communication patterns (gRPC, REST, Events)
- Database strategies (per-service databases)
- Resilience patterns (circuit breakers, retries)
- Anti-patterns to avoid

### 3. [Python Standards](./python-standards.mdc)
- Python 3.11+ requirements
- Coding standards and PEP 8
- Async/await patterns
- Type hints and Pydantic models
- Error handling
- Documentation standards

### 4. [API Standards](./api-standards.mdc)
- REST API design with FastAPI
- gRPC service implementation
- Request/response validation with Pydantic
- Error handling and status codes
- Pagination and filtering
- Rate limiting and caching

### 5. [gRPC Patterns](./grpc-patterns.mdc)
- Protocol Buffer design
- Service implementation
- Client patterns
- Streaming (unary, server, client, bidirectional)
- Error handling and status codes
- Interceptors and middleware

### 6. [Testing Standards](./testing-standards.mdc)
- Test structure and organization
- Unit testing with pytest
- Integration testing
- End-to-end testing
- Performance testing
- Coverage requirements (>80%)

### 7. [Deployment Rules](./deployment.mdc)
- Docker containerization
- Kubernetes deployment
- CI/CD pipelines
- Health checks and probes
- Monitoring and observability
- Environment configuration

### 8. [Security Rules](./security.mdc)
- Authentication (JWT)
- Authorization (RBAC)
- Input validation
- SQL injection prevention
- Rate limiting
- Secrets management
- Security headers

### 9. [Zen MCP Tools - Python](./zen-mcp-tools-python.md)
- Service architecture analysis with Zen MCP
- Python async debugging patterns
- gRPC contract validation
- Microservices code review requirements

### 10. [Magic Numbers - Python](./magic-numbers-python.md)
- Python constant conventions
- Pydantic Settings configuration
- Service-specific constants
- gRPC and database constants

## 🎯 Core Principles

### Service Design
1. **Single Responsibility**: One service, one business capability
2. **Loose Coupling**: Services communicate through contracts
3. **High Cohesion**: Related functionality stays together
4. **Database per Service**: No shared databases
5. **Async First**: All I/O operations use async/await

### Communication
1. **gRPC Internal**: Service-to-service communication
2. **REST External**: Client-facing APIs
3. **Events Async**: Kafka/RabbitMQ for async messaging
4. **Circuit Breakers**: Resilience for all external calls
5. **Timeouts**: Appropriate timeout configuration

### Development
1. **Type Safety**: Complete type hints with mypy
2. **Testing**: Minimum 80% coverage
3. **Documentation**: Clear docstrings and OpenAPI
4. **Security First**: Input validation, authentication, authorization
5. **Observability**: Logging, metrics, tracing

## 🏗️ Standard Project Structure

```
service-name/
├── src/
│   ├── api/              # FastAPI routes
│   ├── grpc/             # gRPC services
│   ├── services/         # Business logic
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── repositories/     # Data access layer
│   └── core/             # Config, security, database
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/            # End-to-end tests
├── proto/               # Protocol buffer definitions
├── migrations/          # Database migrations
├── docker/             # Docker configurations
├── k8s/                # Kubernetes manifests
├── .github/            # CI/CD workflows
├── pyproject.toml      # UV dependency management
├── Dockerfile          # Container definition
└── README.md          # Service documentation
```

## 🛠️ Technology Stack

### Core
- **Python 3.11+** - Runtime
- **FastAPI** - Web framework
- **gRPC** - Inter-service communication
- **UV** - Package management

### Data
- **PostgreSQL** - Primary database
- **Redis** - Caching and sessions
- **SQLAlchemy 2.0** - ORM
- **Alembic** - Migrations

### Messaging
- **Kafka** - Event streaming
- **Celery** - Task queue

### Testing
- **pytest** - Test framework
- **pytest-asyncio** - Async testing
- **coverage** - Code coverage

### Development
- **mypy** - Type checking
- **ruff** - Linting
- **black** - Formatting

### Observability
- **OpenTelemetry** - Tracing
- **Prometheus** - Metrics
- **Grafana** - Visualization
- **Sentry** - Error tracking

## 📋 Checklists

### New Service Checklist
- [ ] Service structure follows standard layout
- [ ] Proto definitions created
- [ ] Database schema designed
- [ ] API endpoints documented
- [ ] Authentication/authorization implemented
- [ ] Health checks added
- [ ] Metrics exposed
- [ ] Logging configured
- [ ] Tests written (>80% coverage)
- [ ] Dockerfile created
- [ ] K8s manifests prepared
- [ ] CI/CD pipeline configured

### Code Review Checklist
- [ ] Async patterns used correctly
- [ ] Type hints complete
- [ ] Error handling appropriate
- [ ] Input validation present
- [ ] Security considerations addressed
- [ ] Tests comprehensive
- [ ] Documentation clear
- [ ] Performance optimized

### Deployment Checklist
- [ ] Environment variables configured
- [ ] Secrets stored securely
- [ ] Resource limits set
- [ ] Autoscaling configured
- [ ] Monitoring dashboards created
- [ ] Alerts configured
- [ ] Rollback strategy defined
- [ ] Documentation updated

## 🚀 Quick Commands

```bash
# Development
uv sync                              # Install dependencies
uv run pytest                        # Run tests
uv run mypy src/                     # Type check
uv run ruff check src/               # Lint code
uv run black src/                    # Format code

# Docker
docker build -t service-name .       # Build image
docker-compose up                    # Run locally

# Kubernetes
kubectl apply -k k8s/                # Deploy to K8s
kubectl rollout status deployment/service-name
kubectl logs -f deployment/service-name

# Database
alembic revision --autogenerate      # Create migration
alembic upgrade head                 # Apply migrations
alembic downgrade -1                 # Rollback migration

# gRPC
python -m grpc_tools.protoc          # Generate gRPC code
grpcurl -plaintext localhost:50051 list  # List services
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [gRPC Python Guide](https://grpc.io/docs/languages/python/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Python Async/Await Guide](https://docs.python.org/3/library/asyncio.html)

## 🔒 Security Considerations

Always remember:
1. Never commit secrets to version control
2. Always validate and sanitize input
3. Use parameterized queries for database operations
4. Implement proper authentication and authorization
5. Keep dependencies updated
6. Regular security audits
7. Follow OWASP guidelines

## 📈 Performance Guidelines

1. Use connection pooling for databases
2. Implement caching strategies
3. Optimize database queries
4. Use async operations throughout
5. Implement pagination for large datasets
6. Monitor and profile regularly
7. Set appropriate resource limits

---

**Note**: These rules are living documents. Update them as the project evolves and new patterns emerge.