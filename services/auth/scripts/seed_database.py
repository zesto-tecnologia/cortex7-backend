"""Seed database with initial roles, permissions, and admin user."""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import uuid as uuid_module

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert, select
import bcrypt

from services.auth.database import Base
from services.auth.models.user import User
from services.auth.models.role import Role, Permission, UserRole, role_permissions
from services.auth.config import settings


async def seed_database():
    """Seed database with initial data."""
    print("🌱 Starting database seed...")

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Check if roles already exist
            result = await session.execute(select(Role))
            existing_roles = result.scalars().all()

            if existing_roles:
                print("⚠️  Roles already exist. Skipping seed to avoid duplicates.")
                return

            print("📝 Creating roles...")
            # Create roles
            admin_role = Role(
                id=uuid_module.uuid4(),
                name="admin",
                description="System administrator with full access"
            )
            manager_role = Role(
                id=uuid_module.uuid4(),
                name="manager",
                description="Manager with elevated permissions"
            )
            user_role = Role(
                id=uuid_module.uuid4(),
                name="user",
                description="Regular user with basic permissions"
            )

            session.add_all([admin_role, manager_role, user_role])
            await session.flush()
            print(f"   ✅ Created roles: admin, manager, user")

            print("📝 Creating permissions...")
            # Create permissions
            permissions = [
                Permission(
                    id=uuid_module.uuid4(),
                    name="*:*",
                    resource="*",
                    action="*",
                    description="All permissions (super admin)"
                ),
                Permission(
                    id=uuid_module.uuid4(),
                    name="read:users",
                    resource="users",
                    action="read",
                    description="Read user data"
                ),
                Permission(
                    id=uuid_module.uuid4(),
                    name="write:users",
                    resource="users",
                    action="write",
                    description="Modify user data"
                ),
                Permission(
                    id=uuid_module.uuid4(),
                    name="delete:users",
                    resource="users",
                    action="delete",
                    description="Delete users"
                ),
                Permission(
                    id=uuid_module.uuid4(),
                    name="manage:invites",
                    resource="invites",
                    action="manage",
                    description="Manage invite codes"
                ),
                Permission(
                    id=uuid_module.uuid4(),
                    name="manage:roles",
                    resource="roles",
                    action="manage",
                    description="Manage user roles"
                ),
            ]

            session.add_all(permissions)
            await session.flush()
            print(f"   ✅ Created {len(permissions)} permissions")

            print("📝 Assigning permissions to roles...")
            # Assign permissions to roles using the association table
            # Admin gets all permissions
            for perm in permissions:
                await session.execute(
                    insert(role_permissions).values(
                        role_id=admin_role.id,
                        permission_id=perm.id
                    )
                )

            # Manager gets read/write permissions
            manager_perms = [p for p in permissions if p.name in ["read:users", "write:users", "manage:invites"]]
            for perm in manager_perms:
                await session.execute(
                    insert(role_permissions).values(
                        role_id=manager_role.id,
                        permission_id=perm.id
                    )
                )

            # User gets only read permissions
            user_perms = [p for p in permissions if p.name == "read:users"]
            for perm in user_perms:
                await session.execute(
                    insert(role_permissions).values(
                        role_id=user_role.id,
                        permission_id=perm.id
                    )
                )
            print(f"   ✅ Assigned permissions to roles")

            print("📝 Creating default admin user...")

            # Get admin password from environment variable
            admin_password = os.getenv("ADMIN_INITIAL_PASSWORD")
            if not admin_password:
                raise ValueError(
                    "❌ ADMIN_INITIAL_PASSWORD environment variable must be set.\n"
                    "   Generate a strong password: `openssl rand -base64 32`\n"
                    "   Then set: export ADMIN_INITIAL_PASSWORD='your-secure-password'"
                )

            # Truncate password to 72 bytes (bcrypt limit) and encode
            admin_password_bytes = admin_password.encode('utf-8')[:72]

            # Hash the password using bcrypt
            salt = bcrypt.gensalt()
            password_hash_bytes = bcrypt.hashpw(admin_password_bytes, salt)
            password_hash = password_hash_bytes.decode('utf-8')

            # Create default admin user with hashed password
            admin_user = User(
                id=uuid_module.uuid4(),
                email="admin@cortex7.com",
                name="Admin",
                password_hash=password_hash,
                email_verified=True,
                verified_at=datetime.now(timezone.utc),
                auth_provider=None
            )

            session.add(admin_user)
            await session.flush()
            print(f"   ✅ Created admin user: admin@cortex7.com")
            print(f"   ⚠️  Admin password has been securely hashed")

            print("📝 Assigning admin role to admin user...")
            # Assign admin role to admin user
            admin_user_role = UserRole(
                user_id=admin_user.id,
                role_id=admin_role.id,
                assigned_at=datetime.now(timezone.utc)
            )

            session.add(admin_user_role)

            # Commit transaction
            await session.commit()

            print("\n✅ Database seeded successfully!")
            print(f"   - Created 3 roles: admin, manager, user")
            print(f"   - Created {len(permissions)} permissions")
            print(f"   - Created admin user: admin@cortex7.com")
            print(f"   - Admin password securely hashed from ADMIN_INITIAL_PASSWORD")
            print(f"   ⚠️  Remember to change the admin password after first login")

        except Exception as e:
            print(f"\n❌ Error seeding database: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
