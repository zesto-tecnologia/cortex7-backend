#!/bin/bash
set -e

echo "Running Alembic migrations..."
alembic -c alembic_unified.ini upgrade head

echo "Migrations completed successfully!"

# Start the application
exec "$@"