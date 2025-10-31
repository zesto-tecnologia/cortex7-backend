# Makefile Commands Reference

Quick reference for all essential Makefile commands.

## 🚀 Service Management

Start individual services with all their dependencies automatically included.

### Start Services (with postgres + redis + gateway)

| Command | Services Started | URL |
|---------|-----------------|-----|
| `make up-auth` | postgres, redis, gateway, auth | http://localhost:8001 |
| `make up-financial` | postgres, redis, gateway, financial | http://localhost:8002 |
| `make up-hr` | postgres, redis, gateway, hr | http://localhost:8003 |
| `make up-legal` | postgres, redis, gateway, legal | http://localhost:8004 |
| `make up-procurement` | postgres, redis, gateway, procurement | http://localhost:8005 |
| `make up-documents` | postgres, redis, gateway, documents | http://localhost:8006 |
| `make up-ai` | postgres, redis, gateway, ai | http://localhost:8007 |

**Example:**
```bash
# Only want to work on auth service today?
make up-auth

# This starts: postgres + redis + gateway + auth
# Everything else stays off
```

### Stop Services (service only)

| Command | What it stops |
|---------|--------------|
| `make stop-auth` | Auth service only |
| `make stop-financial` | Financial service only |
| `make stop-hr` | HR service only |
| `make stop-legal` | Legal service only |
| `make stop-procurement` | Procurement service only |
| `make stop-documents` | Documents service only |
| `make stop-ai` | AI service only |

**Example:**
```bash
# Done with auth for now
make stop-auth

# Dependencies (postgres, redis, gateway) keep running
# So you can quickly start another service
make up-financial
```

### Why This is Useful

**Before:**
```bash
# Had to start everything
docker-compose up -d  # All 12+ services!
```

**Now:**
```bash
# Start only what you need
make up-auth  # Just 4 services: postgres, redis, gateway, auth
```

**Benefits:**
- ⚡ Faster startup
- 💾 Less memory usage
- 🎯 Focus on what you're working on
- 🔄 Dependencies managed automatically

## 🐛 Debugging (Essential Commands)

Only 3 commands you need to know:

| Command | Description |
|---------|-------------|
| `make debug-auth` | Start auth in debug mode (foreground with logs) |
| `make debug-stop` | Stop debug and restart normal auth |
| `make attach` | Show VSCode debugger instructions |

### Debug Workflow

```bash
# 1. Start debug mode
make debug-auth
# Wait for: "Debugger will listen on 0.0.0.0:5678"

# 2. In VSCode: Press Cmd+Shift+D → Select "Docker: Attach to Auth Service" → F5

# 3. Set breakpoints and test your code

# 4. When done: Press Ctrl+C

# 5. Return to normal mode
make debug-stop
```

**What `make debug-auth` does:**
1. Stops regular auth service
2. Starts postgres, redis, gateway
3. Starts auth in debug mode
4. Exposes debugger on port 5678
5. Shows logs in foreground

**What `make debug-stop` does:**
1. Stops debug auth container
2. Removes debug container
3. Starts regular auth service
4. You're back to normal mode

## 🐳 Docker Container Management

| Command | Description |
|---------|-------------|
| `make up` | Start ALL services |
| `make down` | Stop ALL services |
| `make restart` | Restart ALL services |
| `make ps` | Show container status |
| `make logs` | Follow logs for all services |
| `make logs-auth` | Follow logs for auth only |

## 🗄️ Database

| Command | Description |
|---------|-------------|
| `make migrate` | Apply migrations |
| `make migration-new m="description"` | Create new migration |
| `make db-shell` | Connect to PostgreSQL |
| `make db-backup` | Backup database |

## ⚡ Quick Actions

| Command | Description |
|---------|-------------|
| `make status` | Show system status |
| `make health` | Check all service health |

## 📋 Common Workflows

### Workflow 1: Daily Development (Auth Service)

```bash
# Morning: Start only what you need
make up-auth

# Develop...

# Need to debug?
make stop-auth
make debug-auth
# Attach VSCode debugger (Cmd+Shift+D → F5)

# Done debugging
# Ctrl+C
make debug-stop

# End of day: Stop everything
make down
```

### Workflow 2: Working on Multiple Services

```bash
# Start auth for testing
make up-auth

# Start financial to test integration
make up-financial

# Both services now running with shared postgres/redis/gateway

# Done with financial
make stop-financial

# Continue with auth...
```

### Workflow 3: Full System Test

```bash
# Start everything
make up

# Check health
make health

# View logs
make logs

# Stop everything
make down
```

### Workflow 4: Quick Debug Session

```bash
# Currently have services running
make up-auth

# Need to debug quickly
make stop-auth && make debug-auth

# VSCode: Cmd+Shift+D → F5
# Test, debug, fix...
# Ctrl+C when done

# Back to normal
make debug-stop
```

## 🎯 When to Use Each Command

### Use `make up-SERVICE`
- Daily development on specific service
- Testing one service
- Saving resources
- Faster startup times

### Use `make up`
- Full system integration testing
- Demo or presentation
- CI/CD pipeline
- Need everything running

### Use `make debug-auth`
- Setting breakpoints
- Stepping through code
- Inspecting variables
- Understanding complex logic

### Use `make stop-SERVICE`
- Done with that service
- Need to free resources
- Switching to different service
- Service misbehaving

## 💡 Pro Tips

### Tip 1: Chain Commands
```bash
# Stop and start quickly
make stop-auth && make up-auth

# Debug cycle
make stop-auth && make debug-auth
```

### Tip 2: Multiple Terminals
```bash
# Terminal 1: Run service
make up-auth

# Terminal 2: Watch logs
make logs-auth

# Terminal 3: Run tests/requests
curl http://localhost:8001/health
```

### Tip 3: Check Status First
```bash
# Before starting, see what's running
make ps

# Then decide what to start/stop
```

### Tip 4: Quick Health Check
```bash
# Started services, want to verify all OK
make health
# ✅ or ❌ for each service
```

## 🔄 Service Dependencies

All services automatically get:
- **postgres**: Database (port 5432)
- **redis**: Cache (port 6379)
- **gateway**: API Gateway (port 8000)

Plus the service itself on its port.

**Example:**
```bash
make up-auth
```

Actually starts 4 containers:
1. `cortex-postgres` (5432)
2. `cortex-redis` (6379)
3. `cortex-gateway` (8000)
4. `cortex-auth` (8001)

## 🆘 Quick Troubleshooting

### Service won't start
```bash
# Check what's running
make ps

# Check logs
make logs-auth

# Rebuild if needed
make rebuild
make up-auth
```

### Port already in use
```bash
# Stop everything
make down

# Start what you need
make up-auth
```

### Database issues
```bash
# Connect to database
make db-shell

# Check migrations
make migrate
```

### Debug won't connect
```bash
# Restart debug session
# Ctrl+C current session
make debug-auth

# Check service is running
docker-compose ps auth-service
```

## 📚 More Help

```bash
# See all commands
make help

# Debug instructions
make attach

# Full documentation
cat DEBUGGING.md
cat DEBUG_QUICK_START.md
```

---

**Quick Reference Card:**
```bash
# Daily work
make up-auth          # Start auth + dependencies
make stop-auth        # Stop auth only

# Debug
make debug-auth       # Debug mode
make debug-stop       # Back to normal

# All services
make up               # Start everything
make down             # Stop everything

# Status
make ps               # What's running?
make health           # All healthy?
```
