# Migration Consolidation Plan

## Overview
Consolidating migrations from two merged projects:
1. **Old Project**: Corporate agent system (SQL migrations)
2. **Auth Project**: Authentication system (Alembic migrations)
3. **Final Result**: Erase all migrations and start from zero ground considering all the plan below. Authentication system (Alembic migrations)
## Current State

### Old Project Migrations (SQL-based)
Located in: `migrations/versions/`

1. **001_initial_schema.sql** (793 lines)
   - Extensions: uuid-ossp, vector (pgvector)
   - Tables: empresas, departamentos, usuarios, documentos, centros_custo, fornecedores, contas_pagar, cartoes_corporativos, faturas_cartao, lancamentos_cartao, ordens_compra, funcionarios, contratos_trabalho, contratos, processos_juridicos, workflows, tarefas, logs_agentes, auditoria, cache_embeddings, agentes_config
   - Views: contratos_com_status_real, dashboard_cartoes, dashboard_metricas, contas_pagar_vencendo
   - Triggers and functions

2. **002_seed_data.sql** (597 lines)
   - Demo data for all tables
   - Test company, users, suppliers, invoices, etc.

3. **003_add_workflows_tarefas.sql** (50 lines)
   - **CONFLICT**: Attempts to create workflows/tarefas tables that already exist in 001
   - Different schema than 001 (simpler, AI-focused)

### Auth Project Migrations (Alembic-based)
Located in: `migrations/auth/versions/`

1. **967855e4987d_initial_schema.py**
   - Tables: jwt_keys, users, audit_logs, refresh_tokens, user_companies
   - User roles enum: user, admin, super_admin

2. **f0f81bf68110_add_supabase_fields_to_users.py**
   - Adds: verified_at, last_login, auth_provider

3. **f5e7752c5eca_add_token_family_id_and_device_id_to_.py**
   - Adds: token_family_id, device_id to refresh_tokens

## Conflicts and Issues

### 1. Table Naming Conflicts
- **usuarios** (old) vs **users** (auth) - Different schemas, both represent users
- **workflows** (old) vs **workflows** (003) - Same name, different schemas
- **tarefas** (old) vs **tarefas** (003) - Same name, different schemas
- **audit_logs** (auth) vs **auditoria** (old) - Similar purpose, different names

### 2. Schema Inconsistencies
**usuarios** (old - corporate users):
```sql
id UUID, empresa_id UUID, departamento_id UUID, nome VARCHAR, email VARCHAR,
cargo VARCHAR, alcadas JSONB, status VARCHAR
```

**users** (auth - authentication):
```sql
id UUID, email VARCHAR, name VARCHAR, role ENUM, email_verified BOOLEAN,
verified_at TIMESTAMP, last_login TIMESTAMP, auth_provider VARCHAR
```

**workflows** (old - corporate workflows):
```sql
id UUID, empresa_id UUID, tipo VARCHAR, nome VARCHAR, fases JSONB, ativo BOOLEAN
```

**workflows** (003 - AI workflows):
```sql
id UUID, empresa_id UUID, workflow_type VARCHAR, status VARCHAR, input_data JSONB,
result JSONB, error_message TEXT, celery_task_id VARCHAR, priority VARCHAR
```

### 3. Missing Relationships
- Auth `user_companies.company_id` references non-existent `companies` table
- No link between auth `users` and corporate `usuarios`
- Corporate tables reference `usuarios` which doesn't align with auth `users`

### 4. Foreign Key Dependencies
- Auth migrations create `users` table first
- Old migrations create `empresas` → `usuarios` → other tables
- Need to establish: `users` (auth) → `usuarios` (corporate) → `empresas` relationship

## Unified Migration Strategy

### Phase 1: Foundation (Migration 001)
Create base tables in this order:

1. **Extensions and Enums**
   ```sql
   CREATE EXTENSION uuid-ossp;
   CREATE EXTENSION vector;
   CREATE TYPE user_role AS ENUM ('user', 'admin', 'super_admin');
   ```

2. **Auth Core Tables** (from auth migrations)
   - jwt_keys
   - users (auth table - email, password, role)
   - refresh_tokens
   - audit_logs (auth audit)

3. **Corporate Core Tables** (from old 001)
   - empresas (companies)
   - user_companies (link users to companies)
   - departamentos (departments)
   - usuarios (corporate user profiles - links to auth.users)

### Phase 2: Corporate Modules (Migration 002)
Financial, HR, Legal, Procurement modules:
- centros_custo, fornecedores, contas_pagar
- cartoes_corporativos, faturas_cartao, lancamentos_cartao
- ordens_compra
- funcionarios, contratos_trabalho
- contratos, processos_juridicos
- documentos (with vector embeddings)

### Phase 3: Workflow & Tasks (Migration 003)
Unified workflow system:
- workflows_corporate (renamed from old workflows)
- workflows_ai (from 003, for AI agent tasks)
- tarefas (unified tasks table supporting both types)
- logs_agentes, agentes_config

### Phase 4: Cache & Utilities (Migration 004)
- cache_embeddings
- Views (contratos_com_status_real, dashboard_cartoes, etc.)
- Triggers and functions

### Phase 5: Seed Data (Migration 005)
- Demo company and users
- Test data for all modules

## Unified Table Relationships

```
users (auth)
  └─> user_companies
       └─> empresas (companies)
            ├─> departamentos
            ├─> usuarios (corporate profiles)
            │    ├─> funcionarios
            │    └─> [all other corporate tables]
            ├─> documentos
            ├─> fornecedores
            └─> [all corporate tables]
```

## Implementation Plan

### Step 1: Backup Current State
```bash
# Backup existing migrations
cp -r migrations migrations_backup_$(date +%Y%m%d)
```

### Step 2: Create Unified Alembic Structure
```bash
# Create new unified migrations directory
mkdir -p migrations_unified/versions
```

### Step 3: Generate Unified Migrations
1. `001_unified_foundation.py` - Extensions, auth tables, empresas, usuarios
2. `002_corporate_modules.py` - Financial, HR, Legal, Procurement
3. `003_workflows_and_tasks.py` - Unified workflow system
4. `004_cache_and_utilities.py` - Cache, views, triggers
5. `005_seed_data.py` - Test data

### Step 4: Migration Script
Create `migrate_to_unified.sh` to:
1. Detect current database state
2. Apply appropriate migration path
3. Migrate data if needed

### Step 5: Validation
- Test migrations on clean database
- Test migrations on existing data
- Verify all relationships
- Run application tests

## Breaking Changes

### For Applications Using Old Schema
1. **usuarios → users + usuarios split**
   - Auth operations use `users` table
   - Corporate profile data in `usuarios` table
   - `usuarios.usuario_id` references `users.id`

2. **workflows renamed**
   - Corporate workflows: `workflows_corporate`
   - AI workflows: `workflows_ai`
   - Update application code accordingly

3. **New required fields**
   - `usuarios.user_id` (FK to users.id) - REQUIRED
   - `empresas` now linked via `user_companies`

### For Applications Using Auth Schema
1. **companies table added**
   - User-company relationships via `user_companies`
   - Multi-tenancy support

2. **Additional user fields**
   - Corporate profile in `usuarios` table
   - Department and role assignments

## Migration Commands

### Generate New Migration
```bash
alembic -c alembic.ini revision --autogenerate -m "description"
```

### Apply Migrations
```bash
# Check current version
alembic -c alembic.ini current

# Upgrade to latest
alembic -c alembic.ini upgrade head

# Downgrade
alembic -c alembic.ini downgrade -1
```

### Stamp Database (if manually applied)
```bash
alembic -c alembic.ini stamp head
```

## Testing Strategy

### 1. Clean Database Test
```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE IF EXISTS cortex_db_test;"
psql -U postgres -c "CREATE DATABASE cortex_db_test;"

# Run migrations
DATABASE_URL="postgresql://user:pass@localhost/cortex_db_test" alembic upgrade head

# Verify schema
psql -U user -d cortex_db_test -c "\dt"
psql -U user -d cortex_db_test -c "\d+ users"
psql -U user -d cortex_db_test -c "\d+ usuarios"
```

### 2. Data Migration Test
```bash
# Load old data
psql -U user -d cortex_db_test -f migrations_backup/versions/001_initial_schema.sql
psql -U user -d cortex_db_test -f migrations_backup/versions/002_seed_data.sql

# Run migration script
./migrate_to_unified.sh

# Verify data integrity
psql -U user -d cortex_db_test -c "SELECT COUNT(*) FROM users;"
psql -U user -d cortex_db_test -c "SELECT COUNT(*) FROM usuarios;"
```

### 3. Application Integration Test
```bash
# Start services with test database
DATABASE_URL="postgresql://user:pass@localhost/cortex_db_test" docker-compose up

# Run test suite
pytest tests/integration/

# Verify all endpoints work
curl http://localhost:8000/health
curl http://localhost:8001/api/v1/auth/login
```

## Rollback Plan

If issues arise:

1. **Restore from backup**
   ```bash
   psql -U postgres -c "DROP DATABASE cortex_db;"
   psql -U postgres -c "CREATE DATABASE cortex_db;"
   pg_restore -U user -d cortex_db backup_file.dump
   ```

2. **Revert to old migrations**
   ```bash
   cp -r migrations_backup_YYYYMMDD/* migrations/
   ```

3. **Downgrade Alembic**
   ```bash
   alembic downgrade base
   ```

## Next Steps

1. ✅ Document consolidation plan (this file)
2. ⏳ Create unified Alembic migrations
3. ⏳ Write data migration scripts
4. ⏳ Update application models to match new schema
5. ⏳ Update docker-compose.yml to use unified migrations
6. ⏳ Test on clean database
7. ⏳ Test with existing data
8. ⏳ Deploy to staging environment

## Notes

- **Prioritize data safety**: All migrations should be reversible
- **Test thoroughly**: Both clean install and migration paths
- **Update documentation**: All schema changes documented
- **Monitor performance**: Verify indexes and query performance
- **Backup before production**: Full database backup before applying

## Questions to Resolve

1. Should we keep Portuguese table names (empresas, usuarios) or standardize to English?
2. How to handle existing production data during migration?
3. Should workflows_corporate and workflows_ai remain separate or unified?
4. Timezone handling: Use `TIMESTAMP WITH TIME ZONE` everywhere?
5. Soft delete strategy: Add `deleted_at` to all tables?
