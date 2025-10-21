#!/usr/bin/env python3
"""
Initialize the database with extensions and run migrations.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from shared.database.connection import engine
from shared.config.settings import settings


async def init_extensions():
    """Install required PostgreSQL extensions."""
    async with engine.begin() as conn:
        print("Installing PostgreSQL extensions...")
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "vector"'))
        print("Extensions installed successfully!")


async def main():
    """Main initialization function."""
    try:
        await init_extensions()
        print("\nDatabase initialization complete!")
        print("\nNext steps:")
        print("1. Run migrations: alembic upgrade head")
        print("2. Start services: docker-compose up")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())