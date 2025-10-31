#!/bin/bash
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Migrations completed successfully!"

# Start the application
exec "$@"