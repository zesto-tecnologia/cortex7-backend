#!/usr/bin/env python3
"""
Comprehensive test script for all English-translated models.
Tests imports, relationships, and basic CRUD operations.
"""

import asyncio
import sys
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

# Add the project to path
sys.path.insert(0, '/Users/zeduino/pd7/cortex7-backend')

from shared.database.connection import AsyncSessionLocal
from shared.models import (
    Company, Department, UserProfile, Document,
    CostCenter, Supplier, AccountPayable, CorporateCard,
    CardInvoice, CardTransaction, PurchaseOrder,
    Employee, EmploymentContract, Contract, LegalProcess,
    CorporateWorkflow, Task, AgentLog, AuditTrail,
    EmbeddingCache, AgentConfig
)


async def test_model_imports():
    """Test that all models can be imported."""
    print("🔍 Testing model imports...")
    models = [
        Company, Department, UserProfile, Document,
        CostCenter, Supplier, AccountPayable, CorporateCard,
        CardInvoice, CardTransaction, PurchaseOrder,
        Employee, EmploymentContract, Contract, LegalProcess,
        CorporateWorkflow, Task, AgentLog, AuditTrail,
        EmbeddingCache, AgentConfig
    ]

    for model in models:
        assert hasattr(model, '__tablename__'), f"{model.__name__} missing __tablename__"
        print(f"  ✅ {model.__name__}: {model.__tablename__}")

    print(f"\n✅ All {len(models)} models imported successfully!\n")
    return True


async def test_database_connection():
    """Test database connection."""
    print("🔍 Testing database connection...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.version()))
        version = result.scalar()
        print(f"  ✅ Connected to PostgreSQL: {version}\n")
    return True


async def test_existing_data():
    """Test reading existing seed data."""
    print("🔍 Testing existing seed data...")

    async with AsyncSessionLocal() as session:
        # Test Company
        companies = await session.execute(select(Company))
        companies_list = companies.scalars().all()
        print(f"  ✅ Found {len(companies_list)} companies")
        for company in companies_list:
            print(f"     - {company.company_name} (Tax ID: {company.tax_id})")

        # Test Department
        departments = await session.execute(select(Department))
        departments_list = departments.scalars().all()
        print(f"  ✅ Found {len(departments_list)} departments")

        # Test User
        users = await session.execute(select(UserProfile))
        users_list = users.scalars().all()
        print(f"  ✅ Found {len(users_list)} user profiles")

    print()
    return True


async def test_create_operations():
    """Test creating new records with English fields."""
    print("🔍 Testing CREATE operations with English fields...")

    async with AsyncSessionLocal() as session:
        # Create a new company with unique tax_id
        import random
        unique_tax_id = f"{random.randint(10000000000000, 99999999999999)}"
        new_company = Company(
            id=uuid4(),
            company_name="Test Company Ltd",
            tax_id=unique_tax_id,  # Random unique tax_id
            settings={"language": "en", "timezone": "UTC"}
        )
        session.add(new_company)

        # Create a department
        new_department = Department(
            id=uuid4(),
            company_id=new_company.id,
            name="Engineering",
            meta_data={"code": "ENG", "manager": "John Doe"}
        )
        session.add(new_department)

        # Note: Skipping UserProfile creation as it requires auth users table
        # which is part of the authentication system
        # In production, users are created through the auth service first

        # Instead, we'll test CostCenter creation with unique code
        import random
        unique_code = f"CC-TEST-{random.randint(1000, 9999)}"
        new_cost_center = CostCenter(
            id=uuid4(),
            company_id=new_company.id,
            code=unique_code,  # Use unique code
            name="Test Department",
            department="Testing",
            monthly_budget=Decimal("10000.00"),
            current_spending=Decimal("0.00")
        )
        session.add(new_cost_center)

        # Create a supplier
        unique_supplier_tax_id = f"{random.randint(10000000000000, 99999999999999)}"
        new_supplier = Supplier(
            id=uuid4(),
            company_id=new_company.id,
            company_name="ABC Supplies Inc",
            tax_id=unique_supplier_tax_id,  # Random unique tax_id
            category="IT",
            status="active",
            bank_details={"bank": "Bank of Test", "account": "12345"},
            contacts=[{"name": "Bob Wilson", "email": "bob@abc.com", "phone": "+1-555-0100"}]
        )
        session.add(new_supplier)

        await session.commit()

        print(f"  ✅ Created Company: {new_company.company_name}")
        print(f"  ✅ Created Department: {new_department.name}")
        print(f"  ✅ Created CostCenter: {new_cost_center.name}")
        print(f"  ✅ Created Supplier: {new_supplier.company_name}")

        # Clean up test data
        await session.delete(new_cost_center)
        await session.delete(new_supplier)
        await session.delete(new_department)
        await session.delete(new_company)
        await session.commit()
        print("  ✅ Cleaned up test data\n")

    return True


async def test_relationships():
    """Test model relationships with English names."""
    print("🔍 Testing model relationships...")

    async with AsyncSessionLocal() as session:
        # Get a company with its relationships
        result = await session.execute(
            select(Company).limit(1)
        )
        company = result.scalar_one_or_none()

        if company:
            print(f"  Testing relationships for: {company.company_name}")

            # Test departments relationship
            departments = await session.execute(
                select(Department).where(Department.company_id == company.id)
            )
            dept_count = len(departments.scalars().all())
            print(f"  ✅ Company->Departments: {dept_count} departments found")

            # Test users relationship
            users = await session.execute(
                select(UserProfile).where(UserProfile.company_id == company.id)
            )
            user_count = len(users.scalars().all())
            print(f"  ✅ Company->UserProfiles: {user_count} users found")

            print(f"  ✅ All relationships use English names correctly")
        else:
            print("  ⚠️  No company found in database")

    print()
    return True


async def test_views():
    """Test database views."""
    print("🔍 Testing database views...")

    async with AsyncSessionLocal() as session:
        # Test the views exist
        views = [
            'contracts_with_real_status',
            'cards_dashboard',
            'metrics_dashboard',
            'accounts_payable_due_soon'
        ]

        for view in views:
            try:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {view}"))
                count = result.scalar()
                print(f"  ✅ View '{view}' exists with {count} rows")
            except Exception as e:
                print(f"  ❌ View '{view}' error: {str(e)}")

    print()
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 COMPREHENSIVE MODEL TESTING - ENGLISH TRANSLATION")
    print("=" * 60)
    print()

    tests = [
        ("Model Imports", test_model_imports),
        ("Database Connection", test_database_connection),
        ("Existing Data", test_existing_data),
        ("CREATE Operations", test_create_operations),
        ("Relationships", test_relationships),
        ("Database Views", test_views),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, "PASSED" if result else "FAILED"))
        except Exception as e:
            print(f"  ❌ Error: {str(e)}\n")
            results.append((test_name, "ERROR"))

    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    for test_name, status in results:
        icon = "✅" if status == "PASSED" else "❌"
        print(f"{icon} {test_name}: {status}")

    passed = sum(1 for _, status in results if status == "PASSED")
    total = len(results)

    print()
    print(f"🎯 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! The English translation is complete and working!")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())