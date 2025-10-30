#!/bin/bash
set -e

echo "🐛 Starting Auth Service in DEBUG mode..."
echo "Debugger will listen on 0.0.0.0:5678"
echo ""
echo "To attach debugger from VSCode:"
echo "1. Open Run and Debug (Cmd+Shift+D)"
echo "2. Select 'Attach to Auth Service in Docker'"
echo "3. Press F5 or click Start Debugging"
echo ""

# Run Alembic migrations first
echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations completed successfully!"
echo ""

# Start the application with debugpy
echo "Starting FastAPI with debugpy..."
python -m debugpy \
    --listen 0.0.0.0:5678 \
    --wait-for-client \
    -m uvicorn \
    services.auth.main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --reload
