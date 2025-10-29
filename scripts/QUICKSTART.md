# Quick Start: Seeding Employees

## TL;DR

```bash
# 0. Install dependencies (if not done yet)
cd backend
uv sync

# 1. Make sure database is running
docker-compose up -d postgres

# 2. Run migrations (if not already done)
alembic upgrade head

# 3. Seed employees
uv run python scripts/seed_employees.py
# OR activate venv first:
# source .venv/bin/activate
# python scripts/seed_employees.py
```

## What Gets Created?

8 employees across all departments:
- 2 in TI (1 developer, 1 intern)
- 2 in Financeiro (1 analyst, 1 manager)
- 2 in Jurídico (1 employee lawyer, 1 PJ consultant)
- 1 in RH (coordinator)
- 1 in Suprimentos (analyst)

Each with complete:
- ✅ Personal data (address, phone, emergency contact)
- ✅ Benefits (health insurance, meal vouchers, etc.)
- ✅ Documents (RG, work card, professional licenses)
- ✅ Vacation tracking
- ✅ Different contract types (CLT, PJ, Estagio)
- ✅ Different work modes (Remote, Hybrid, On-site)

## Verification

After running the script, verify with:

```bash
# Using psql
psql -U postgres -d cortex -c "SELECT position, personal_data->>'full_name' as name, contract_type FROM employees;"

# Or via API (if server is running)
curl http://localhost:8000/hr/employees?company_id=11111111-1111-1111-1111-111111111111
```

## Tax IDs (CPF) Used

- `12345678901` - Carlos Eduardo Silva (Dev Senior)
- `98765432109` - Ana Paula Souza (Analyst)
- `45678912345` - Roberto Carlos Mendes (Lawyer)
- `32165498701` - Fernanda Lima Santos (HR Coordinator)
- `78945612301` - Lucas Martins Oliveira (Supply Analyst)
- `65432109876` - Julia Almeida Costa (IT Intern)
- `14725836901` - Marcos Antônio Ferreira (Finance Manager)
- `95175385201` - Beatriz Rodrigues Lima (Legal Consultant PJ)

## Troubleshooting

| Error | Solution |
|-------|----------|
| Company not found | Run `alembic upgrade head` first |
| Connection refused | Start PostgreSQL: `docker-compose up -d postgres` |
| Module 'pgvector' not found | Install deps: `uv sync` |
| Module 'shared' not found | Run from backend dir: `cd backend && uv run python scripts/seed_employees.py` |
| Already exists | Safe to ignore - script is idempotent |

## Clean Up

To remove seeded employees:

```sql
-- Remove only seeded employees (by tax_id)
DELETE FROM employees WHERE tax_id IN (
    '12345678901', '98765432109', '45678912345', '32165498701',
    '78945612301', '65432109876', '14725836901', '95175385201'
);
```

Or remove all demo data:

```bash
# Downgrade to before seed data
alembic downgrade 004_cache_and_utilities

# Then upgrade back
alembic upgrade head
```
