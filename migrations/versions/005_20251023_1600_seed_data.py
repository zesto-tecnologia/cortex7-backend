"""Seed data for development and testing

Revision ID: 005_seed_data
Revises: 004_cache_and_utilities
Create Date: 2025-10-23 16:00:00.000000

OPTIONAL: This migration inserts demo data for development and testing.
Should NOT be run in production environments.

Demo data includes:
- Demo company (TechCorp Brasil)
- Test users and departments
- Sample suppliers
- Sample financial data
"""
from alembic import op
import sqlalchemy as sa
import os

# revision identifiers, used by Alembic.
revision = '005_seed_data'
down_revision = '004_cache_and_utilities'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if we should skip (production environment)
    env = os.getenv('ENVIRONMENT', 'development')
    if env == 'production':
        print("⚠️  Skipping seed data in production environment")
        return

    print("📦 Inserting seed data for development...")

    # ============================================
    # 1. EMPRESA E ESTRUTURA ORGANIZACIONAL
    # ============================================

    # Insert Demo Company
    op.execute("""
        INSERT INTO companies (id, company_name, tax_id, settings) VALUES
        ('11111111-1111-1111-1111-111111111111', 'TechCorp Brasil Ltda', '12345678000100',
         '{
           "approval_limits": {
             "financeiro": {
               "analista": 5000,
               "gerente": 25000,
               "diretor": 100000
             },
             "suprimentos": {
               "analista": 3000,
               "gerente": 15000,
               "diretor": 50000
             }
           },
           "politicas": {
             "aprovacao_automatica": false,
             "limite_parcelamento": 12
           }
         }'::jsonb)
    """)

    # Insert Departments
    op.execute("""
        INSERT INTO departments (id, company_id, name, metadata) VALUES
        ('22222222-2222-2222-2222-222222222221', '11111111-1111-1111-1111-111111111111', 'Financeiro', '{"code": "FIN", "responsavel": "João Silva"}'::jsonb),
        ('22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'Recursos Humanos', '{"code": "RH", "responsavel": "Maria Santos"}'::jsonb),
        ('22222222-2222-2222-2222-222222222223', '11111111-1111-1111-1111-111111111111', 'Jurídico', '{"code": "JUR", "responsavel": "Carlos Oliveira"}'::jsonb),
        ('22222222-2222-2222-2222-222222222224', '11111111-1111-1111-1111-111111111111', 'Suprimentos', '{"code": "SUP", "responsavel": "Ana Costa"}'::jsonb),
        ('22222222-2222-2222-2222-222222222225', '11111111-1111-1111-1111-111111111111', 'TI', '{"code": "TI", "responsavel": "Pedro Alves"}'::jsonb)
    """)

    # Insert test auth users first
    op.execute("""
        INSERT INTO users (id, email, name, role, email_verified) VALUES
        ('44444444-4444-4444-4444-444444444441', 'joao.silva@techcorp.com.br', 'João Silva', 'admin', true)
        ON CONFLICT (id) DO NOTHING
    """)

    # Insert Corporate User Profiles (now with valid user_id references)
    op.execute("""
        INSERT INTO user_profiles (id, user_id, company_id, department_id, name, email, position, approval_limits, status) VALUES
        -- Financial
        ('33333333-3333-3333-3333-333333333331', '44444444-4444-4444-4444-444444444441', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222221',
         'João Silva', 'joao.silva@techcorp.com.br', 'Diretor Financeiro',
         '{"financeiro": 100000, "suprimentos": 50000}'::jsonb, 'active')
        ON CONFLICT (id) DO NOTHING
    """)

    # Note: In a real setup, you would:
    # 1. Create auth users first (via auth service)
    # 2. Then update user_profiles.user_id to link them
    # For development, we'll create placeholder user_profiles without user_id linkage

    # ============================================
    # 2. MÓDULO FINANCEIRO
    # ============================================

    # Cost Centers
    op.execute("""
        INSERT INTO cost_centers (id, company_id, code, name, department, monthly_budget, current_spending) VALUES
        ('44444444-4444-4444-4444-444444444441', '11111111-1111-1111-1111-111111111111', 'CC-TI-001', 'IT Infrastructure', 'IT', 50000.00, 12500.50),
        ('44444444-4444-4444-4444-444444444442', '11111111-1111-1111-1111-111111111111', 'CC-RH-001', 'Personnel', 'HR', 200000.00, 180000.00),
        ('44444444-4444-4444-4444-444444444443', '11111111-1111-1111-1111-111111111111', 'CC-ADM-001', 'Administrative', 'Administrative', 30000.00, 15000.00)
    """)

    # Suppliers
    op.execute("""
        INSERT INTO suppliers (id, company_id, company_name, tax_id, category, status, bank_details, contacts, ratings) VALUES
        ('55555555-5555-5555-5555-555555555551', '11111111-1111-1111-1111-111111111111',
         'AWS Brasil Serviços de Internet Ltda', '09346601000118', 'TI', 'active',
         '{"banco": "341", "agencia": "0001", "conta": "12345-6", "type": "corrente"}'::jsonb,
         '[{"name": "Suporte AWS", "email": "suporte@aws.com.br", "telefone": "11-3000-0000"}]'::jsonb,
         '{"ultima_avaliacao": "2025-01", "nota": 9.5, "entregas_no_prazo": 98}'::jsonb),

        ('55555555-5555-5555-5555-555555555552', '11111111-1111-1111-1111-111111111111',
         'Microsoft Brasil Ltda', '04712500000157', 'TI', 'active',
         '{"banco": "001", "agencia": "1234", "conta": "98765-0"}'::jsonb,
         '[{"name": "Comercial", "email": "comercial@microsoft.com.br", "telefone": "11-4000-0000"}]'::jsonb,
         '{"ultima_avaliacao": "2025-01", "nota": 9.0, "entregas_no_prazo": 95}'::jsonb)
    """)

    # Sample Documents
    op.execute("""
        INSERT INTO documents (id, company_id, department, type, title, original_content, metadata, file_url, status) VALUES
        ('66666666-6666-6666-6666-666666666661', '11111111-1111-1111-1111-111111111111',
         'financial', 'invoice', 'Invoice 12345 - AWS Cloud Services',
         'Service Invoice #12345. Provider: AWS Brasil. Value: R$ 8,500.00. Related to cloud computing services.',
         '{"invoice_number": "12345", "amount": 8500.00, "issue_date": "2025-01-15", "issuer_tax_id": "09346601000118"}'::jsonb,
         's3://cortex-docs/demo/invoice-12345-aws.pdf', 'active')
    """)

    # Sample Accounts Payable
    op.execute("""
        INSERT INTO accounts_payable (id, company_id, supplier_id, document_id, document_number, description, amount, due_date, status, cost_center, category, priority) VALUES
        ('77777777-7777-7777-7777-777777777771', '11111111-1111-1111-1111-111111111111',
         '55555555-5555-5555-5555-555555555551', '66666666-6666-6666-6666-666666666661',
         'NF-12345', 'AWS Cloud Services - Janeiro/2025', 8500.00, CURRENT_DATE + 30, 'pendente', 'CC-TI-001', 'Serviços', 3)
    """)

    # ============================================
    # 3. WORKFLOWS DEMO
    # ============================================

    # Corporate Workflow Example
    op.execute("""
        INSERT INTO corporate_workflows (id, company_id, type, name, phases, active) VALUES
        ('88888888-8888-8888-8888-888888888881', '11111111-1111-1111-1111-111111111111',
         'compra', 'Aprovação de Compras',
         '[
           {"name": "Solicitação", "ordem": 1, "responsavel": "solicitante", "acoes": ["criar_ordem"]},
           {"name": "Aprovação Gerente", "ordem": 2, "responsavel": "gerente", "acoes": ["aprovar", "rejeitar"]},
           {"name": "Aprovação Diretor", "ordem": 3, "responsavel": "diretor", "acoes": ["aprovar", "rejeitar"]},
           {"name": "Emissão Pedido", "ordem": 4, "responsavel": "suprimentos", "acoes": ["emitir_pedido"]}
         ]'::jsonb,
         true)
    """)

    # Sample Task
    op.execute("""
        INSERT INTO tasks (id, company_id, workflow_corporate_id, workflow_type, title, description, department, status, priority, deadline) VALUES
        ('99999999-9999-9999-9999-999999999991', '11111111-1111-1111-1111-111111111111',
         '88888888-8888-8888-8888-888888888881', 'corporate',
         'Aprovar Compra AWS Cloud Services', 'Aprovar ordem de compra no amount de R$ 8.500,00',
         'Financeiro', 'pendente', 2, CURRENT_DATE + 7)
    """)

    print("✅ Seed data inserted successfully!")


def downgrade() -> None:
    """Remove seed data by known IDs"""

    # Check if we should skip
    env = os.getenv('ENVIRONMENT', 'development')
    if env == 'production':
        print("⚠️  Skipping seed data removal in production")
        return

    print("🗑️  Removing seed data...")

    # Remove in reverse order of dependencies
    op.execute("DELETE FROM tasks WHERE company_id = '11111111-1111-1111-1111-111111111111'")
    op.execute("DELETE FROM corporate_workflows WHERE company_id = '11111111-1111-1111-1111-111111111111'")
    op.execute("DELETE FROM accounts_payable WHERE company_id = '11111111-1111-1111-1111-111111111111'")
    op.execute("DELETE FROM documents WHERE company_id = '11111111-1111-1111-1111-111111111111'")
    op.execute("DELETE FROM suppliers WHERE company_id = '11111111-1111-1111-1111-111111111111'")
    op.execute("DELETE FROM cost_centers WHERE company_id = '11111111-1111-1111-1111-111111111111'")
    op.execute("DELETE FROM user_profiles WHERE company_id = '11111111-1111-1111-1111-111111111111'")
    op.execute("DELETE FROM departments WHERE company_id = '11111111-1111-1111-1111-111111111111'")
    op.execute("DELETE FROM companies WHERE id = '11111111-1111-1111-1111-111111111111'")

    print("✅ Seed data removed successfully!")
