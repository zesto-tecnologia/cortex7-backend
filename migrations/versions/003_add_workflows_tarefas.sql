-- Migration: Add workflows and tarefas tables for AI service
-- Created: 2025-10-21

-- Create workflows table
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    workflow_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    input_data JSONB,
    result JSONB,
    error_message TEXT,
    celery_task_id VARCHAR(100) UNIQUE,
    priority VARCHAR(10) DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_workflows_empresa_id FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
);

-- Create indexes for workflows
CREATE INDEX IF NOT EXISTS ix_workflows_empresa_id ON workflows (empresa_id);
CREATE INDEX IF NOT EXISTS ix_workflows_workflow_type ON workflows (workflow_type);
CREATE INDEX IF NOT EXISTS ix_workflows_status ON workflows (status);
CREATE INDEX IF NOT EXISTS ix_workflows_celery_task_id ON workflows (celery_task_id);

-- Create tarefas table
CREATE TABLE IF NOT EXISTS tarefas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    tipo VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    atribuido_a UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    resultado JSONB,
    prioridade VARCHAR(10) DEFAULT 'normal',
    data_vencimento VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_tarefas_empresa_id FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    CONSTRAINT fk_tarefas_atribuido_a FOREIGN KEY (atribuido_a) REFERENCES usuarios(id) ON DELETE SET NULL,
    CONSTRAINT fk_tarefas_workflow_id FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);

-- Create indexes for tarefas
CREATE INDEX IF NOT EXISTS ix_tarefas_empresa_id ON tarefas (empresa_id);
CREATE INDEX IF NOT EXISTS ix_tarefas_status ON tarefas (status);

