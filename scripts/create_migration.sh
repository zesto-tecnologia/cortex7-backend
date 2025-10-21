#!/bin/bash

# Script to create a new Alembic migration

if [ -z "$1" ]; then
    echo "Usage: ./scripts/create_migration.sh <migration_message>"
    echo "Example: ./scripts/create_migration.sh 'Add user authentication fields'"
    exit 1
fi

echo "Creating migration: $1"

# Navigate to backend directory
cd "$(dirname "$0")/.." || exit

# Create the migration
alembic revision --autogenerate -m "$1"

echo "Migration created successfully!"
echo "To apply the migration, run: alembic upgrade head"