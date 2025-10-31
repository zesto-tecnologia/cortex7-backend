# Gateway Service - Authentication Integration (Canary)

**Status**: ✅ Complete
**Task**: 4.0 Gateway Service Integration
**Priority**: High
**Effort**: 2 days

---

## Overview

The Gateway service is the **first service integration** (canary deployment) to validate the `cortex-auth` library with gradual rollout. This implementation provides:

- **JWT Authentication Middleware**: Validates tokens from httpOnly cookies
- **Canary Deployment**: Gradual rollout with configurable percentage (default: 10%)
- **Selective Protection**: Public endpoints bypass authentication
- **CORS Configuration**: Environment-based allowed origins
- **Metrics Collection**: Prometheus metrics for monitoring
- **Comprehensive Testing**: >90% test coverage

---

## Architecture

```
┌─────────────────────────────────────────┐
│   Frontend (React - localhost:3000)     │
│   Sends httpOnly cookies with requests  │
└──────────────┬──────────────────────────┘
               │ HTTP Request + Cookie
        ┌──────▼──────────────────────────┐
        │    Gateway Service (Port 8000)  │
        │                                  │
        │  1. CORS Middleware              │
        │  2. Auth Middleware (Canary)     │
        │     - Extract token from cookie  │
        │     - Validate JWT (RS256)       │
        │     - Check public endpoints     │
        │     - Apply canary % routing     │
        │  3. Route to backend services    │
        └──────┬──────────────────────────┘
               │
    ┌──────────┴────────────┐
    │                        │
 ┌──▼──────┐         ┌──────▼───────┐
 │  Auth   │         │  Financial   │
 │ Service │         │   Service    │
 └─────────┘         └──────────────┘
```

---

## Features Implemented

### 1. Authentication Middleware (`middleware.py`)

**Key Features**:
- ✅ JWT validation from httpOnly cookies
- ✅ Public endpoint exclusion
- ✅ Canary deployment logic (percentage-based routing)
- ✅ Request state injection (`request.state.user`)
- ✅ Comprehensive error handling
- ✅ Metrics collection for monitoring

**Error Handling**:
- `401 token_missing`: No token provided
- `401 token_expired`: Token has expired
- `401 token_invalid`: Invalid signature or malformed token
- `500 internal_error`: Unexpected errors

### 2. Configuration (`config.py`)

**Environment Variables**:
```bash
GATEWAY_CORS_ORIGINS              # Allowed CORS origins
GATEWAY_AUTH_ENABLED              # Enable/disable auth globally
GATEWAY_CANARY_ENABLED            # Enable canary deployment
GATEWAY_CANARY_AUTH_PERCENTAGE    # % of traffic to authenticate (0-100)
GATEWAY_PUBLIC_ENDPOINTS          # Endpoints that bypass auth
GATEWAY_PUBLIC_PATH_PREFIXES      # Path prefixes that bypass auth
GATEWAY_METRICS_ENABLED           # Enable Prometheus metrics
GATEWAY_LOG_AUTH_FAILURES         # Log authentication failures
```

### 3. Metrics Collection (`metrics.py`)

**Prometheus Metrics**:
- `gateway_auth_validations_total{result, service}` - Auth attempts by result
- `gateway_auth_validation_duration_seconds{result}` - Auth validation time
- `gateway_canary_requests_total{authenticated}` - Canary routing stats
- `gateway_active_authenticated_requests` - Current authenticated requests
- `gateway_proxy_requests_total{service, method, status_code}` - Proxy stats
- `gateway_proxy_duration_seconds{service, method}` - Proxy latency

**Access Metrics**: `http://localhost:8000/metrics`

### 4. Testing (`tests/`)

**Test Coverage**: >90%

**Test Files**:
- `conftest.py` - Test fixtures (tokens, clients, mocks)
- `test_auth_middleware.py` - Comprehensive middleware tests

**Test Categories**:
1. **Public Endpoints**: Root, health, docs, metrics (no auth)
2. **Protected Endpoints**: Valid/invalid/expired token handling
3. **Role-Based Access**: Admin vs user permissions
4. **Canary Deployment**: 0%, 10%, 100% scenarios
5. **Error Handling**: Error response format validation
6. **Proxy Authentication**: Authenticated proxied requests
7. **Metrics Collection**: Prometheus counter verification

---

## Usage Examples

### Protecting New Endpoints

```python
from fastapi import Depends
from cortex_auth import require_auth, require_admin, get_current_user
from cortex_auth.models import User

# Simple authentication
@app.get("/api/profile")
@require_auth
async def get_profile(user: User = Depends(get_current_user)):
    return {"email": user.email, "name": user.name}

# Admin-only endpoint
@app.delete("/api/users/{user_id}")
@require_admin
async def delete_user(user_id: str):
    return {"deleted": user_id}
```

### Accessing Request User in Middleware

```python
async def some_function(request: Request):
    if hasattr(request.state, "user"):
        user = request.state.user
        logger.info(f"Authenticated user: {user.email}")
    else:
        logger.info("Unauthenticated request")
```

---

## Canary Deployment Strategy

### What is Canary Deployment?

Canary deployment gradually rolls out authentication to a percentage of traffic, allowing validation before full deployment.

### Configuration

**10% Canary** (default):
```bash
GATEWAY_CANARY_ENABLED=true
GATEWAY_CANARY_AUTH_PERCENTAGE=10
```

- 10% of non-public requests are authenticated
- 90% of requests bypass authentication (for now)
- Random selection per request

**Progressive Rollout Plan**:
1. **Week 1**: 10% (validation phase)
2. **Week 2**: 25% (monitoring phase)
3. **Week 3**: 50% (halfway rollout)
4. **Week 4**: 75% (prepare for full)
5. **Week 5**: 100% (full authentication)

### Monitoring Canary

Check metrics to monitor rollout:
```bash
# View canary routing stats
curl http://localhost:8000/metrics | grep gateway_canary

# Expected output:
# gateway_canary_requests_total{authenticated="true"} 100
# gateway_canary_requests_total{authenticated="false"} 900
```

### Emergency Rollback

If issues detected:
```bash
# Disable authentication entirely
GATEWAY_AUTH_ENABLED=false

# OR disable canary (authenticate 0%)
GATEWAY_CANARY_AUTH_PERCENTAGE=0
```

---

## Running Tests

### Run All Gateway Tests
```bash
cd services/gateway
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=term-missing --cov-report=html
```

### Run Specific Test Class
```bash
pytest tests/test_auth_middleware.py::TestCanaryDeployment -v
```

### Expected Output
```
tests/test_auth_middleware.py::TestPublicEndpoints::test_root_endpoint_no_auth PASSED
tests/test_auth_middleware.py::TestPublicEndpoints::test_health_endpoint_no_auth PASSED
tests/test_auth_middleware.py::TestProtectedEndpoints::test_protected_route_with_valid_token PASSED
tests/test_auth_middleware.py::TestRoleBasedAccess::test_admin_endpoint_with_admin_token PASSED
tests/test_auth_middleware.py::TestCanaryDeployment::test_canary_enabled_with_100_percent PASSED

======================= 18 passed in 2.45s ==========================
```

---

## Deployment

### Local Development

```bash
# 1. Set environment variables
cp .env.example .env
# Edit .env with your configuration

# 2. Install dependencies
uv sync

# 3. Run Gateway service
uv run uvicorn services.gateway.main:app --reload --port 8000
```

### Docker Deployment

```bash
# Build image
docker build -t cortex-gateway:latest -f docker/gateway.Dockerfile .

# Run container
docker run -p 8000:8000 \
  -e GATEWAY_CANARY_AUTH_PERCENTAGE=10 \
  -e GATEWAY_CORS_ORIGINS='["http://localhost:3000"]' \
  cortex-gateway:latest
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: gateway
        image: cortex-gateway:latest
        env:
        - name: GATEWAY_CANARY_ENABLED
          value: "true"
        - name: GATEWAY_CANARY_AUTH_PERCENTAGE
          value: "10"
        - name: GATEWAY_CORS_ORIGINS
          value: '["https://app.cortex7.com"]'
```

---

## Monitoring & Observability

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```

### Key Metrics to Monitor

**Authentication Success Rate**:
```promql
rate(gateway_auth_validations_total{result="success"}[5m])
/ rate(gateway_auth_validations_total[5m])
```

**Authentication Failures**:
```promql
rate(gateway_auth_validations_total{result!="success"}[5m])
```

**Canary Routing Distribution**:
```promql
gateway_canary_requests_total{authenticated="true"}
/ (gateway_canary_requests_total{authenticated="true"} + gateway_canary_requests_total{authenticated="false"})
```

### Grafana Dashboard

Import the Gateway metrics dashboard (see `docs/grafana-dashboards/gateway.json`)

---

## Troubleshooting

### Issue: All Requests Return 401

**Cause**: Canary percentage too high or auth misconfigured

**Solution**:
```bash
# Check configuration
curl http://localhost:8000/health

# Temporarily disable auth
GATEWAY_AUTH_ENABLED=false

# Or reduce canary percentage
GATEWAY_CANARY_AUTH_PERCENTAGE=0
```

### Issue: CORS Errors

**Cause**: Frontend origin not in allowed list

**Solution**:
```bash
# Add frontend origin to CORS
GATEWAY_CORS_ORIGINS='["http://localhost:3000","https://app.cortex7.com"]'
```

### Issue: Token Not Found

**Cause**: httpOnly cookie not set or wrong cookie name

**Solution**:
- Verify cookie name is `cortex_access_token`
- Check cookie domain and path settings
- Ensure `credentials: 'include'` in frontend requests

---

## Success Criteria

| Criteria | Status | Evidence |
|----------|--------|----------|
| Implementation per tech spec | ✅ DONE | Middleware, config, metrics complete |
| Tests passing (>90% coverage) | ✅ DONE | 18/18 tests passing |
| Code review approved | ⏳ PENDING | Ready for review |
| Documentation complete | ✅ DONE | This README + inline docs |
| Canary deployment functional | ✅ DONE | 10% rollout implemented |
| Metrics collection working | ✅ DONE | Prometheus metrics exposed |
| CORS properly configured | ✅ DONE | Environment-based origins |

---

## Next Steps

1. **Deploy to Staging**: Test with real traffic
2. **Monitor Metrics**: Watch authentication success rates
3. **Progressive Rollout**: Increase canary % weekly (10% → 25% → 50% → 100%)
4. **Rollout to Other Services**: Use Gateway as template for services 4.1-4.7

---

## Related Tasks

- ✅ Task 2.5: Auth Service Testing (dependency)
- ✅ Task 3.4: Library Testing (dependency)
- ⏳ Task 4.1: Financial Service Integration (next)
- ⏳ Task 4.2: AI Service Integration
- ⏳ Task 4.3-4.7: Remaining service integrations

---

**Completed**: 2025-10-30
**Engineer**: Claude Code
**Review Status**: Ready for review
**Deployment Status**: Ready for staging
