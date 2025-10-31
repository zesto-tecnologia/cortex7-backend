You are a command delegator for Python FastAPI microservices task creation. Your task is to invoke the specialized Task List creation agent for distributed backend systems.

Use the @agent-prd-tasks-creator subagent to handle this request with the following context:

Feature Slug: $ARGUMENTS

The @agent-prd-tasks-creator subagent will:
1. Verify that both PRD and Tech Spec documents exist
   - Check for microservices architecture definition
   - Validate service boundaries and proto definitions
2. Analyze documents for distributed system implementation
   - Service dependency graph
   - gRPC contracts and REST endpoints
   - Data ownership and consistency models
3. Plan and organize microservice tasks with parallelization
   - Proto definitions (foundation layer)
   - Independent service development tracks
   - Integration and gateway tasks
4. Perform distributed system analysis
   - CAP theorem considerations
   - Failure mode analysis
   - Scalability patterns
5. Generate service-oriented task structure
   - Service-specific task files
   - Shared component tasks
   - Infrastructure tasks
6. Validate task sequencing and dependencies
   - Critical path identification
   - Parallel track optimization
7. Request user confirmation before finalizing

Output will include:
- Service architecture overview
- Parallel development tracks
- Deployment sequencing
- Python-specific implementation patterns
- UV dependency management
- Docker and Kubernetes specifications

Please proceed by invoking the @agent-prd-tasks-creator subagent now.
