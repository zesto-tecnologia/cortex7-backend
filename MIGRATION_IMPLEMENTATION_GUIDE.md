# Migration Implementation Guide

## ✅ Completed

1. **MIGRATION_CONSOLIDATION_PLAN.md** - Full analysis and strategy
2. **migrations_unified/env.py** - Alembic environment configuration
3. **migrations_unified/script.py.mako** - Migration template
4. **001_unified_foundation.py** - Extensions, auth tables, corporate core (empresas, departamentos, usuarios)
5. **002_corporate_modules.py** - Financial, HR, legal, procurement modules (documentos, centros_custo, fornecedores, contas_pagar, cartoes_corporativos, faturas_cartao, lancamentos_cartao, ordens_compra, funcionarios, contratos_trabalho, contratos, processos_juridicos)
6. **003_workflows_and_tasks.py** - Unified workflow system (workflows_corporate, workflows_ai, tarefas with workflow_type enum)
7. **004_cache_and_utilities.py** - Cache, agent logging, audit, views (logs_agentes, auditoria, cache_embeddings, agentes_config, 4 business views)
8. **005_seed_data.py** - Optional development seed data (demo company, users, suppliers, financial data)


## 🎯 Migration Files Created

All migration files have been successfully created! Here's the complete structure:

### ✅ migrations_unified/versions/

1. **001_20251023_1520_unified_foundation.py** (~290 lines)
   - Extensions (uuid-ossp, vector/pgvector)
   - Auth system (users, jwt_keys, refresh_tokens, audit_logs)
   - Corporate core (empresas, departamentos, usuarios)
   - User-company relationships (user_companies)
   - Updated_at triggers

2. **002_20251023_1530_corporate_modules.py** (~543 lines)
   - Documents with vector embeddings (documentos)
   - Financial module (centros_custo, fornecedores, contas_pagar)
   - Corporate cards (cartoes_corporativos, faturas_cartao, lancamentos_cartao)
   - Procurement (ordens_compra)
   - HR module (funcionarios, contratos_trabalho)
   - Legal module (contratos, processos_juridicos)
   - All indexes, constraints, and triggers

3. **003_20251023_1540_workflows_and_tasks.py** (~246 lines)
   - Workflow type ENUM (corporate, ai)
   - Corporate workflows (workflows_corporate)
   - AI workflows (workflows_ai)
   - Unified tasks (tarefas) supporting both types
   - Auto-calculation function for dias_vencimento
   - All necessary triggers

4. **004_20251023_1550_cache_and_utilities.py** (~264 lines)
   - Agent logging (logs_agentes)
   - Corporate audit trail (auditoria)
   - Embedding cache (cache_embeddings)
   - Agent configuration (agentes_config)
   - Business views (contratos_com_status_real, dashboard_cartoes, dashboard_metricas, contas_pagar_vencendo)

5. **005_20251023_1600_seed_data.py** (~235 lines)
   - Environment-aware (skips in production)
   - Demo company (TechCorp Brasil)
   - Sample departments and users
   - Sample suppliers and financial data
   - Sample workflows and tasks
   - Clean downgrade function

## 🔧 Implementation Steps

### 1. Create Remaining Migrations

```bash
cd /Users/zeduino/pd7/cortex7-backend

# Create each migration file as shown above
# You can use the original SQL as reference
# migrations/versions/001_initial_schema.sql
# migrations/versions/002_seed_data.sql
```

### 2. Update alembic.ini

```bash
cp alembic.ini alembic_unified.ini
```

Edit `alembic_unified.ini`:
```ini
[alembic]
script_location = migrations_unified
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s
sqlalchemy.url = postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}
```

### 3. Update docker-compose.yml

Change the PostgreSQL init script mount:

```yaml
postgres:
  volumes:
    # OLD: - ./migrations/versions/001_initial_schema.sql:/docker-entrypoint-initdb.d/001_initial_schema.sql
    # NEW: Let Alembic handle migrations, remove init script
    - postgres_data:/var/lib/postgresql/data
```

Add migration initialization to gateway or a dedicated init container:

```yaml
migration-init:
  build:
    context: .
    dockerfile: ./docker/Dockerfile.gateway
  container_name: cortex-migration-init
  environment:
    - DATABASE_URL=postgresql+asyncpg://${DATABASE_USER}:${DATABASE_PASSWORD}@postgres:5432/${DATABASE_NAME}
  depends_on:
    postgres:
      condition: service_healthy
  networks:
    - cortex-network
  command: alembic -c alembic_unified.ini upgrade head
  volumes:
    - ./:/app
  restart: "no"
```

### 4. Test Migrations

```bash
# Create test database
psql -U postgres -c "DROP DATABASE IF EXISTS cortex_db_test;"
psql -U postgres -c "CREATE DATABASE cortex_db_test;"

# Run migrations
export DATABASE_URL="postgresql://cortex_user:cortex_password@localhost:5432/cortex_db_test"
alembic -c alembic_unified.ini upgrade head

# Verify
psql -U cortex_user -d cortex_db_test -c "\dt"
psql -U cortex_user -d cortex_db_test -c "\d+ users"
psql -U cortex_user -d cortex_db_test -c "\d+ usuarios"
psql -U cortex_user -d cortex_db_test -c "\d+ empresas"

# Check alembic version
alembic -c alembic_unified.ini current
```

### 5. Create Migration Script

Create `migrate_old_to_unified.sh`:

```bash
#!/bin/bash
set -e

echo "========================================="
echo "Cortex-7 Migration to Unified Schema"
echo "========================================="

# Check if old schema exists
if psql -U cortex_user -d cortex_db -c "\dt usuarios" 2>/dev/null | grep -q "usuarios"; then
    echo "✓ Old schema detected"

    # Backup
    echo "Creating backup..."
    pg_dump -U cortex_user -d cortex_db -F c -f "backup_$(date +%Y%m%d_%H%M%S).dump"

    # Data migration strategy needed here
    echo "⚠️  Data migration required - not yet implemented"
    echo "Please review MIGRATION_CONSOLIDATION_PLAN.md"
    exit 1
else
    echo "✓ Clean database - applying fresh migrations"
    alembic -c alembic_unified.ini upgrade head
    echo "✓ Migrations applied successfully"
fi
```

### 6. Backup Old Migrations

```bash
mkdir -p migrations_backup_$(date +%Y%m%d)
cp -r migrations/* migrations_backup_$(date +%Y%m%d)/
```

### 7. Switch to Unified Migrations

```bash
# Remove old migration directories
mv migrations migrations_old
mv migrations/auth migrations/auth_old

# Activate unified
mv migrations_unified migrations

# Update alembic.ini
mv alembic_unified.ini alembic.ini
```

## ⚠️ Important Notes

1. **Data Migration**: If you have existing data, you'll need a data migration strategy:
   - Export existing usuarios → create auth users + link to usuarios
   - Map existing workflows to appropriate workflow type
   - Preserve all relationships

2. **Testing**: Test thoroughly before production:
   - Clean database installation
   - Migration from old schema (if applicable)
   - All application endpoints
   - Data integrity

3. **Rollback Plan**: Always have a backup:
   ```bash
   pg_dump -U cortex_user -d cortex_db -F c -f backup_pre_migration.dump
   ```

4. **Application Code Updates**: Update models to match new schema:
   - `usuarios` now has `user_id` FK to `users`
   - Workflow references split into `workflow_corporate_id` and `workflow_ai_id`
   - Import path changes for models

## 📝 Validation Checklist

After migration:

- [ ] All tables created successfully
- [ ] All indexes present
- [ ] All foreign keys working
- [ ] Triggers functioning (updated_at columns)
- [ ] Views returning correct data
- [ ] Auth endpoints working
- [ ] Corporate endpoints working
- [ ] Multi-tenancy (user_companies) working
- [ ] Alembic version table correct
- [ ] No orphaned tables from old schema

## 🚀 Next Steps

1. Create remaining migration files (002-005)
2. Test on clean database
3. Update application models
4. Update docker-compose.yml
5. Document API changes (if any)
6. Deploy to staging
7. Validate all functionality
8. Create data migration scripts (if needed)
9. Deploy to production

## 📚 References

- Original SQL migrations: `migrations/versions/`
- Auth migrations: `migrations/auth/versions/`
- Consolidation plan: `MIGRATION_CONSOLIDATION_PLAN.md`
- Alembic docs: https://alembic.sqlalchemy.org/
