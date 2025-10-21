#!/bin/bash

# Script to run database migrations

echo "Running database migrations..."

# Navigate to backend directory
cd "$(dirname "$0")/.." || exit

# Check if we should upgrade or downgrade
if [ "$1" = "down" ]; then
    echo "Downgrading database..."
    alembic downgrade -1
elif [ "$1" = "head" ]; then
    echo "Upgrading to latest..."
    alembic upgrade head
elif [ -n "$1" ]; then
    echo "Migrating to revision: $1"
    alembic upgrade "$1"
else
    echo "Upgrading to latest..."
    alembic upgrade head
fi

echo "Migration complete!"

# Show current revision
echo ""
echo "Current database revision:"
alembic current