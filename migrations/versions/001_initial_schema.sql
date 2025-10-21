-- ============================================
-- SISTEMA DE AGENTES CORPORATIVO
-- Schema Completo PostgreSQL
-- ============================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================
-- CORE: ORGANIZAÇÃO
-- ============================================

CREATE TABLE empresas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  razao_social VARCHAR(255) NOT NULL,
  cnpj VARCHAR(14) UNIQUE NOT NULL,
  configuracoes JSONB, -- Políticas, alçadas, regras de negócio
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_empresas_cnpj ON empresas(cnpj);

COMMENT ON TABLE empresas IS 'Empresas clientes do sistema';
COMMENT ON COLUMN empresas.configuracoes IS 'Políticas, alçadas e regras de negócio da empresa';

CREATE TABLE departamentos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  nome VARCHAR(100) NOT NULL, -- RH, Financeiro, Jurídico, Suprimentos
  meta_data JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dept_empresa ON departamentos(empresa_id);

COMMENT ON TABLE departamentos IS 'Departamentos dentro de cada empresa';

CREATE TABLE usuarios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  departamento_id UUID REFERENCES departamentos(id) ON DELETE SET NULL,
  nome VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  cargo VARCHAR(100),
  alcadas JSONB, -- {financeiro: 50000, suprimentos: 30000}
  status VARCHAR(20) DEFAULT 'ativo',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_empresa ON usuarios(empresa_id);
CREATE INDEX idx_usuarios_status ON usuarios(status);

COMMENT ON TABLE usuarios IS 'Usuários com acesso ao sistema';
COMMENT ON COLUMN usuarios.alcadas IS 'Limites de aprovação por módulo em JSON';

-- ============================================
-- DOCUMENTOS E VETORES
-- ============================================

CREATE TABLE documentos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  departamento VARCHAR(50) NOT NULL, -- juridico, financeiro, rh, suprimentos
  tipo VARCHAR(50) NOT NULL, -- contrato, nota_fiscal, curriculo, politica
  titulo VARCHAR(255),
  conteudo_original TEXT, -- Texto extraído pelo Extrator
  meta_data JSONB NOT NULL, -- Dados estruturados extraídos
  arquivo_url VARCHAR(500), -- Link S3/Storage
  embedding vector(1536), -- OpenAI ada-002 ou similar
  status VARCHAR(20) DEFAULT 'ativo',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Índice para busca vetorial
CREATE INDEX idx_docs_embedding ON documentos
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_docs_empresa_dept ON documentos(empresa_id, departamento);
CREATE INDEX idx_docs_tipo ON documentos(tipo);
CREATE INDEX idx_docs_metadata ON documentos USING gin(meta_data);
CREATE INDEX idx_docs_status ON documentos(status);

COMMENT ON TABLE documentos IS 'Documentos com embeddings para busca semântica';
COMMENT ON COLUMN documentos.embedding IS 'Vetor de embedding (1536 dimensões) para busca semântica';
COMMENT ON COLUMN documentos.meta_data IS 'Dados estruturados extraídos do documento';

-- ============================================
-- MÓDULO: FINANCEIRO
-- ============================================

CREATE TABLE centros_custo (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  codigo VARCHAR(20) UNIQUE NOT NULL,
  nome VARCHAR(100) NOT NULL,
  departamento VARCHAR(50),
  orcamento_mensal DECIMAL(15,2),
  gasto_atual DECIMAL(15,2) DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cc_codigo ON centros_custo(codigo);
CREATE INDEX idx_cc_empresa ON centros_custo(empresa_id);

COMMENT ON TABLE centros_custo IS 'Centros de custo para controle orçamentário';

CREATE TABLE fornecedores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  razao_social VARCHAR(255) NOT NULL,
  cnpj VARCHAR(14) UNIQUE NOT NULL,
  categoria VARCHAR(50), -- TI, Limpeza, Materiais
  status VARCHAR(20) DEFAULT 'ativo',
  dados_bancarios JSONB,
  contatos JSONB, -- [{nome, email, telefone}]
  avaliacoes JSONB, -- Histórico de performance
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_forn_cnpj ON fornecedores(cnpj);
CREATE INDEX idx_forn_empresa ON fornecedores(empresa_id);
CREATE INDEX idx_forn_status ON fornecedores(status);

COMMENT ON TABLE fornecedores IS 'Fornecedores cadastrados no sistema';
COMMENT ON COLUMN fornecedores.avaliacoes IS 'Histórico de performance e avaliações do fornecedor';

CREATE TABLE contas_pagar (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  fornecedor_id UUID REFERENCES fornecedores(id) ON DELETE SET NULL,
  documento_id UUID REFERENCES documentos(id) ON DELETE SET NULL,
  numero_documento VARCHAR(50),
  descricao TEXT,
  valor DECIMAL(15,2) NOT NULL,
  data_vencimento DATE NOT NULL,
  data_pagamento DATE,
  status VARCHAR(20) DEFAULT 'pendente', -- pendente, aprovado, pago, cancelado
  centro_custo VARCHAR(50),
  categoria VARCHAR(50), -- Materiais, Serviços, Pessoal
  meta_data JSONB, -- parcela, forma_pagamento, etc
  prioridade INTEGER DEFAULT 5, -- 1=crítico, 5=normal, 10=baixo
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cp_vencimento ON contas_pagar(data_vencimento);
CREATE INDEX idx_cp_status ON contas_pagar(status);
CREATE INDEX idx_cp_empresa ON contas_pagar(empresa_id);
CREATE INDEX idx_cp_fornecedor ON contas_pagar(fornecedor_id);

COMMENT ON TABLE contas_pagar IS 'Contas a pagar do módulo financeiro';
COMMENT ON COLUMN contas_pagar.prioridade IS '1=crítico, 5=normal, 10=baixo';

-- ============================================
-- MÓDULO: CARTÕES CORPORATIVOS
-- ============================================

CREATE TABLE cartoes_corporativos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  portador_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
  numero_mascarado VARCHAR(20) NOT NULL, -- **** **** **** 1234
  bandeira VARCHAR(20) NOT NULL, -- Visa, Master, Amex
  tipo VARCHAR(20) DEFAULT 'corporativo', -- corporativo, empresarial
  limite DECIMAL(15,2),
  limite_disponivel DECIMAL(15,2),
  data_vencimento_fatura INTEGER, -- Dia do mês (ex: 10)
  status VARCHAR(20) DEFAULT 'ativo', -- ativo, bloqueado, cancelado
  centro_custo_padrao VARCHAR(50),
  departamento VARCHAR(50),
  meta_data JSONB, -- Dados do banco, taxas, etc
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cartoes_portador ON cartoes_corporativos(portador_id);
CREATE INDEX idx_cartoes_empresa ON cartoes_corporativos(empresa_id);
CREATE INDEX idx_cartoes_status ON cartoes_corporativos(status);

COMMENT ON TABLE cartoes_corporativos IS 'Cartões de crédito corporativos';
COMMENT ON COLUMN cartoes_corporativos.data_vencimento_fatura IS 'Dia do mês do vencimento da fatura (1-31)';

CREATE TABLE faturas_cartao (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  cartao_id UUID NOT NULL REFERENCES cartoes_corporativos(id) ON DELETE CASCADE,
  documento_id UUID REFERENCES documentos(id) ON DELETE SET NULL,
  referencia VARCHAR(7) NOT NULL, -- MM/YYYY (ex: 10/2025)
  data_fechamento DATE NOT NULL,
  data_vencimento DATE NOT NULL,
  valor_total DECIMAL(15,2) NOT NULL,
  valor_pago DECIMAL(15,2) DEFAULT 0,
  status VARCHAR(20) DEFAULT 'aberta', -- aberta, parcialmente_paga, paga, atrasada, contestada
  conta_pagar_id UUID REFERENCES contas_pagar(id) ON DELETE SET NULL,
  observacoes TEXT,
  meta_data JSONB, -- IOF, juros, multas
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(cartao_id, referencia)
);

CREATE INDEX idx_faturas_cartao ON faturas_cartao(cartao_id);
CREATE INDEX idx_faturas_vencimento ON faturas_cartao(data_vencimento);
CREATE INDEX idx_faturas_status ON faturas_cartao(status);
CREATE INDEX idx_faturas_empresa ON faturas_cartao(empresa_id);

COMMENT ON TABLE faturas_cartao IS 'Faturas mensais dos cartões corporativos';
COMMENT ON COLUMN faturas_cartao.referencia IS 'Referência no formato MM/YYYY';

CREATE TABLE lancamentos_cartao (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  fatura_id UUID NOT NULL REFERENCES faturas_cartao(id) ON DELETE CASCADE,
  cartao_id UUID NOT NULL REFERENCES cartoes_corporativos(id) ON DELETE CASCADE,
  data_transacao DATE NOT NULL,
  data_lancamento DATE NOT NULL, -- Data que aparece na fatura
  estabelecimento VARCHAR(255) NOT NULL,
  categoria VARCHAR(50), -- Alimentacao, Transporte, Software, Hospedagem
  descricao TEXT,
  valor DECIMAL(15,2) NOT NULL,
  valor_dolar DECIMAL(15,2), -- Se transação internacional
  cotacao_dolar DECIMAL(10,4), -- Taxa de conversão
  moeda VARCHAR(3) DEFAULT 'BRL',
  parcela VARCHAR(10), -- "1/3", "2/3" se parcelado
  centro_custo VARCHAR(50),
  projeto VARCHAR(100), -- Se vinculado a projeto específico
  aprovado BOOLEAN DEFAULT false,
  aprovador_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
  aprovado_em DATE,
  justificativa TEXT, -- Justificativa da despesa
  recibo_url VARCHAR(500), -- Link para recibo/nota fiscal
  contestado BOOLEAN DEFAULT false,
  motivo_contestacao TEXT,
  meta_data JSONB, -- milhas, cashback, etc
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lanc_fatura ON lancamentos_cartao(fatura_id);
CREATE INDEX idx_lanc_cartao ON lancamentos_cartao(cartao_id);
CREATE INDEX idx_lanc_data ON lancamentos_cartao(data_transacao);
CREATE INDEX idx_lanc_categoria ON lancamentos_cartao(categoria);
CREATE INDEX idx_lanc_aprovacao ON lancamentos_cartao(aprovado) WHERE NOT aprovado;
CREATE INDEX idx_lanc_empresa ON lancamentos_cartao(empresa_id);

COMMENT ON TABLE lancamentos_cartao IS 'Lançamentos individuais em cada fatura';
COMMENT ON COLUMN lancamentos_cartao.aprovado IS 'Indica se o lançamento foi aprovado pelo gestor';

-- ============================================
-- MÓDULO: SUPRIMENTOS
-- ============================================

CREATE TABLE ordens_compra (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  numero VARCHAR(20) UNIQUE NOT NULL,
  solicitante_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  fornecedor_id UUID NOT NULL REFERENCES fornecedores(id) ON DELETE RESTRICT,
  valor_total DECIMAL(15,2) NOT NULL,
  status VARCHAR(30) DEFAULT 'rascunho', -- rascunho, aguardando_aprovacao, aprovada, pedido_emitido, recebido, cancelada
  itens JSONB NOT NULL, -- [{descricao, qtd, valor_unit}]
  aprovadores JSONB, -- [{usuario_id, nivel, aprovado_em}]
  centro_custo VARCHAR(50),
  data_entrega_prevista DATE,
  meta_data JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_oc_numero ON ordens_compra(numero);
CREATE INDEX idx_oc_status ON ordens_compra(status);
CREATE INDEX idx_oc_empresa ON ordens_compra(empresa_id);
CREATE INDEX idx_oc_solicitante ON ordens_compra(solicitante_id);
CREATE INDEX idx_oc_fornecedor ON ordens_compra(fornecedor_id);

COMMENT ON TABLE ordens_compra IS 'Ordens de compra do módulo de suprimentos';
COMMENT ON COLUMN ordens_compra.itens IS 'Array JSON com itens da ordem: [{descricao, quantidade, valor_unitario}]';
COMMENT ON COLUMN ordens_compra.aprovadores IS 'Histórico de aprovações: [{usuario_id, nivel, aprovado_em}]';

-- ============================================
-- MÓDULO: RH
-- ============================================

CREATE TABLE funcionarios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  usuario_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
  cpf VARCHAR(11) UNIQUE NOT NULL,
  data_nascimento DATE,
  data_admissao DATE NOT NULL,
  data_demissao DATE,
  cargo VARCHAR(100) NOT NULL,
  departamento_id UUID REFERENCES departamentos(id) ON DELETE SET NULL,
  salario DECIMAL(10,2),
  tipo_contrato VARCHAR(20), -- CLT, PJ, Estagio
  regime_trabalho VARCHAR(20), -- Presencial, Remoto, Hibrido
  dados_pessoais JSONB, -- Endereço, contatos emergência
  beneficios JSONB, -- VT, VA, plano saúde
  documentos JSONB, -- Links docs: RG, CPF, carteira trabalho
  ferias JSONB, -- [{periodo_aquisitivo, dias_disponiveis, historico}]
  status VARCHAR(20) DEFAULT 'ativo',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_func_cpf ON funcionarios(cpf);
CREATE INDEX idx_func_empresa ON funcionarios(empresa_id);
CREATE INDEX idx_func_status ON funcionarios(status);
CREATE INDEX idx_func_departamento ON funcionarios(departamento_id);
CREATE INDEX idx_func_usuario ON funcionarios(usuario_id);

COMMENT ON TABLE funcionarios IS 'Funcionários cadastrados no sistema de RH';
COMMENT ON COLUMN funcionarios.ferias IS 'Controle de férias: [{periodo_aquisitivo, dias_disponiveis, historico}]';

CREATE TABLE contratos_trabalho (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  funcionario_id UUID NOT NULL REFERENCES funcionarios(id) ON DELETE CASCADE,
  documento_id UUID REFERENCES documentos(id) ON DELETE SET NULL,
  tipo VARCHAR(20) NOT NULL, -- admissao, alteracao, rescisao
  data_inicio DATE NOT NULL,
  data_fim DATE,
  conteudo TEXT, -- Texto completo do contrato
  clausulas_especiais JSONB,
  assinado BOOLEAN DEFAULT false,
  assinatura_funcionario_data DATE,
  assinatura_empresa_data DATE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ct_funcionario ON contratos_trabalho(funcionario_id);
CREATE INDEX idx_ct_tipo ON contratos_trabalho(tipo);
CREATE INDEX idx_ct_documento ON contratos_trabalho(documento_id);

COMMENT ON TABLE contratos_trabalho IS 'Contratos de trabalho de funcionários';
COMMENT ON COLUMN contratos_trabalho.tipo IS 'Tipo do contrato: admissao, alteracao, rescisao';

-- ============================================
-- MÓDULO: JURÍDICO
-- ============================================

CREATE TABLE contratos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  documento_id UUID REFERENCES documentos(id) ON DELETE SET NULL,
  tipo VARCHAR(50) NOT NULL, -- fornecedor, cliente, parceria, trabalhista
  parte_contraria VARCHAR(255) NOT NULL,
  cnpj_cpf_contraparte VARCHAR(14),
  objeto TEXT NOT NULL, -- Descrição do contrato
  valor DECIMAL(15,2),
  data_inicio DATE NOT NULL,
  data_fim DATE,
  renovacao_automatica BOOLEAN DEFAULT false,
  status VARCHAR(20) DEFAULT 'vigente', -- rascunho, aprovacao, vigente, rescindido, encerrado, vencido
  clausulas_criticas JSONB, -- Multas, SLAs, confidencialidade
  prazos_importantes JSONB, -- [{descricao, data, notificado}]
  responsavel_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
  meta_data JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_contr_empresa ON contratos(empresa_id);
CREATE INDEX idx_contr_status ON contratos(status);
CREATE INDEX idx_contr_datas ON contratos(data_inicio, data_fim);
CREATE INDEX idx_contr_tipo ON contratos(tipo);
CREATE INDEX idx_contr_responsavel ON contratos(responsavel_id);

COMMENT ON TABLE contratos IS 'Contratos jurídicos gerais';
COMMENT ON COLUMN contratos.clausulas_criticas IS 'Cláusulas importantes: multas, SLAs, confidencialidade';
COMMENT ON COLUMN contratos.prazos_importantes IS 'Prazos relevantes: [{descricao, data, notificado}]';

CREATE TABLE processos_juridicos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  numero_processo VARCHAR(50) UNIQUE,
  tipo VARCHAR(50), -- trabalhista, civel, tributario
  parte_contraria VARCHAR(255),
  valor_causa DECIMAL(15,2),
  status VARCHAR(30), -- andamento, suspenso, concluido
  risco VARCHAR(20), -- baixo, medio, alto
  tribunal VARCHAR(100),
  advogado_responsavel VARCHAR(255),
  historico JSONB, -- [{data, evento, descricao}]
  proxima_acao DATE,
  proxima_acao_descricao TEXT,
  documentos_ids UUID[], -- Array de IDs de documentos
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pj_numero ON processos_juridicos(numero_processo);
CREATE INDEX idx_pj_empresa ON processos_juridicos(empresa_id);
CREATE INDEX idx_pj_proxima_acao ON processos_juridicos(proxima_acao);
CREATE INDEX idx_pj_status ON processos_juridicos(status);
CREATE INDEX idx_pj_risco ON processos_juridicos(risco);

COMMENT ON TABLE processos_juridicos IS 'Processos jurídicos em andamento';
COMMENT ON COLUMN processos_juridicos.historico IS 'Timeline de eventos: [{data, evento, descricao}]';

-- ============================================
-- WORKFLOWS E TAREFAS
-- ============================================

CREATE TABLE workflows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  tipo VARCHAR(50) NOT NULL, -- contratacao, compra, aprovacao_contrato
  nome VARCHAR(255) NOT NULL,
  fases JSONB NOT NULL, -- [{nome, ordem, responsavel, acoes}]
  ativo BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_wf_empresa ON workflows(empresa_id);
CREATE INDEX idx_wf_tipo ON workflows(tipo);
CREATE INDEX idx_wf_ativo ON workflows(ativo);

COMMENT ON TABLE workflows IS 'Workflows configuráveis do sistema';
COMMENT ON COLUMN workflows.fases IS 'Fases do workflow: [{nome, ordem, responsavel, acoes}]';

CREATE TABLE tarefas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
  workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
  entidade_tipo VARCHAR(50), -- ordem_compra, contrato, funcionario
  entidade_id UUID NOT NULL,
  titulo VARCHAR(255) NOT NULL,
  descricao TEXT,
  responsavel_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
  departamento VARCHAR(50) NOT NULL,
  status VARCHAR(20) DEFAULT 'pendente', -- pendente, em_andamento, bloqueada, concluida, cancelada
  prioridade INTEGER DEFAULT 5, -- 1=crítico até 10=baixo
  prazo DATE,
  prazo_legal BOOLEAN DEFAULT false, -- True se tem implicação legal
  dias_para_vencimento INTEGER, -- Calculado automaticamente
  dependencias UUID[], -- IDs de outras tarefas que bloqueiam esta
  meta_data JSONB,
  concluida_em DATE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tarefas_ranking ON tarefas(status, prioridade, prazo, departamento)
  WHERE status != 'concluida';
CREATE INDEX idx_tar_empresa ON tarefas(empresa_id);
CREATE INDEX idx_tar_responsavel ON tarefas(responsavel_id);
CREATE INDEX idx_tar_workflow ON tarefas(workflow_id);
CREATE INDEX idx_tar_status ON tarefas(status);
CREATE INDEX idx_tar_prazo ON tarefas(prazo) WHERE prazo IS NOT NULL;

COMMENT ON TABLE tarefas IS 'Tarefas do sistema de workflow';
COMMENT ON COLUMN tarefas.prioridade IS '1=crítico, 5=normal, 10=baixo';
COMMENT ON COLUMN tarefas.prazo_legal IS 'Indica se o prazo tem implicação legal';
COMMENT ON COLUMN tarefas.dependencias IS 'Array de UUIDs de tarefas que bloqueiam esta';

-- ============================================
-- LOGS E AUDITORIA
-- ============================================

CREATE TABLE logs_agentes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
  agente_tipo VARCHAR(50) NOT NULL, -- ranqueador, gerador, atuador, validador, extrator, conversacional, orquestrador
  acao VARCHAR(100) NOT NULL,
  entidade_tipo VARCHAR(50), -- tarefa, documento, ordem_compra
  entidade_id UUID,
  input JSONB, -- O que foi enviado ao agente
  output JSONB, -- O que o agente retornou
  sucesso BOOLEAN DEFAULT true,
  tempo_execucao_ms INTEGER,
  erro TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_logs_agente_tipo ON logs_agentes(agente_tipo);
CREATE INDEX idx_logs_empresa ON logs_agentes(empresa_id);
CREATE INDEX idx_logs_created ON logs_agentes(created_at);
CREATE INDEX idx_logs_sucesso ON logs_agentes(sucesso) WHERE NOT sucesso;

COMMENT ON TABLE logs_agentes IS 'Log de execução dos agentes de IA';
COMMENT ON COLUMN logs_agentes.agente_tipo IS 'Tipo do agente: ranqueador, gerador, atuador, validador, extrator, conversacional, orquestrador';

CREATE TABLE auditoria (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
  usuario_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
  tabela VARCHAR(50) NOT NULL,
  registro_id UUID NOT NULL,
  acao VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
  dados_anteriores JSONB,
  dados_novos JSONB,
  ip_address INET,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_tabela ON auditoria(tabela);
CREATE INDEX idx_audit_registro ON auditoria(registro_id);
CREATE INDEX idx_audit_created ON auditoria(created_at);
CREATE INDEX idx_audit_empresa ON auditoria(empresa_id);
CREATE INDEX idx_audit_usuario ON auditoria(usuario_id);

COMMENT ON TABLE auditoria IS 'Auditoria completa de mudanças no sistema';
COMMENT ON COLUMN auditoria.acao IS 'Tipo de ação: INSERT, UPDATE, DELETE';

-- ============================================
-- CACHE E CONFIGURAÇÕES
-- ============================================

CREATE TABLE cache_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  texto TEXT NOT NULL,
  hash VARCHAR(64) UNIQUE NOT NULL, -- Hash do texto
  embedding vector(1536) NOT NULL,
  modelo VARCHAR(50) DEFAULT 'text-embedding-ada-002',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cache_hash ON cache_embeddings(hash);
CREATE INDEX idx_cache_created ON cache_embeddings(created_at);

COMMENT ON TABLE cache_embeddings IS 'Cache de embeddings para evitar reprocessamento';
COMMENT ON COLUMN cache_embeddings.hash IS 'Hash SHA-256 do texto para identificação única';

CREATE TABLE agentes_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id UUID REFERENCES empresas(id) ON DELETE CASCADE,
  agente_tipo VARCHAR(50) NOT NULL,
  configuracao JSONB NOT NULL,
  ativo BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agconfig_empresa ON agentes_config(empresa_id);
CREATE INDEX idx_agconfig_tipo ON agentes_config(agente_tipo);
CREATE INDEX idx_agconfig_ativo ON agentes_config(ativo);

COMMENT ON TABLE agentes_config IS 'Configurações dos agentes de IA por empresa';
COMMENT ON COLUMN agentes_config.configuracao IS 'Configuração JSON específica para cada tipo de agente';

-- ============================================
-- VIEWS ÚTEIS
-- ============================================

-- View para calcular status real dos contratos
CREATE VIEW contratos_com_status_real AS
SELECT
  c.*,

  -- Status calculado dinamicamente
  CASE
    WHEN c.status IN ('rascunho', 'aprovacao') THEN 'nao_vigente'
    WHEN c.status IN ('rescindido', 'encerrado') THEN 'nao_vigente'
    WHEN c.data_inicio > CURRENT_DATE THEN 'nao_vigente'
    WHEN c.data_fim IS NULL THEN 'vigente'
    WHEN c.data_fim >= CURRENT_DATE THEN 'vigente'
    WHEN c.data_fim < CURRENT_DATE AND c.renovacao_automatica THEN 'vigente_renovado'
    ELSE 'vencido'
  END as status_calculado,

  -- Alertas
  CASE
    WHEN c.data_fim IS NOT NULL AND c.data_fim - CURRENT_DATE <= 30 THEN true
    ELSE false
  END as vence_em_30_dias,

  CASE
    WHEN c.data_fim IS NOT NULL AND c.data_fim - CURRENT_DATE <= 90 THEN true
    ELSE false
  END as vence_em_90_dias,

  -- Dias para vencer
  CASE
    WHEN c.data_fim IS NOT NULL THEN c.data_fim - CURRENT_DATE
  END as dias_ate_vencimento

FROM contratos c;

COMMENT ON VIEW contratos_com_status_real IS 'View de contratos com status calculado dinamicamente e alertas de vencimento';

-- View para dashboard de cartões
CREATE VIEW dashboard_cartoes AS
SELECT
  c.id,
  c.numero_mascarado,
  c.empresa_id,
  u.nome as portador,
  c.limite,
  c.limite_disponivel,
  COALESCE(f_aberta.valor_total, 0) as fatura_atual,
  COUNT(l.id) FILTER (WHERE NOT l.aprovado) as lancamentos_pendentes,
  SUM(l.valor) FILTER (WHERE NOT l.aprovado) as valor_pendente_aprovacao
FROM cartoes_corporativos c
LEFT JOIN usuarios u ON c.portador_id = u.id
LEFT JOIN faturas_cartao f_aberta ON f_aberta.cartao_id = c.id
  AND f_aberta.status = 'aberta'
LEFT JOIN lancamentos_cartao l ON l.cartao_id = c.id
  AND l.fatura_id = f_aberta.id
WHERE c.status = 'ativo'
GROUP BY c.id, c.numero_mascarado, c.empresa_id, u.nome, c.limite, c.limite_disponivel, f_aberta.valor_total;

COMMENT ON VIEW dashboard_cartoes IS 'Dashboard consolidado de cartões corporativos com métricas';

-- View para dashboard de métricas gerais
CREATE VIEW dashboard_metricas AS
SELECT
  COUNT(*) FILTER (WHERE status = 'pendente') as tarefas_pendentes,
  COUNT(*) FILTER (WHERE status = 'pendente' AND prazo < CURRENT_DATE) as tarefas_atrasadas,
  COUNT(*) FILTER (WHERE prazo_legal AND prazo <= CURRENT_DATE + 3) as prazos_legais_proximos,
  COUNT(*) FILTER (WHERE status = 'em_andamento') as tarefas_em_andamento
FROM tarefas
WHERE status != 'concluida';

COMMENT ON VIEW dashboard_metricas IS 'Métricas consolidadas para dashboard principal';

-- View para contas a pagar vencendo
CREATE VIEW contas_pagar_vencendo AS
SELECT
  cp.*,
  f.razao_social as fornecedor_nome,
  cp.data_vencimento - CURRENT_DATE as dias_ate_vencimento,
  CASE
    WHEN cp.data_vencimento < CURRENT_DATE THEN 'vencido'
    WHEN cp.data_vencimento = CURRENT_DATE THEN 'vence_hoje'
    WHEN cp.data_vencimento <= CURRENT_DATE + 7 THEN 'vence_semana'
    WHEN cp.data_vencimento <= CURRENT_DATE + 30 THEN 'vence_mes'
    ELSE 'normal'
  END as urgencia
FROM contas_pagar cp
LEFT JOIN fornecedores f ON cp.fornecedor_id = f.id
WHERE cp.status IN ('pendente', 'aprovado')
  AND cp.data_vencimento <= CURRENT_DATE + 30
ORDER BY cp.data_vencimento ASC, cp.prioridade ASC;

COMMENT ON VIEW contas_pagar_vencendo IS 'Contas a pagar com vencimento nos próximos 30 dias com nível de urgência';

-- ============================================
-- TRIGGERS E FUNÇÕES
-- ============================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION atualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION atualizar_updated_at() IS 'Atualiza automaticamente o campo updated_at antes de cada UPDATE';

-- Triggers para updated_at
CREATE TRIGGER trigger_empresas_updated_at
  BEFORE UPDATE ON empresas
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_usuarios_updated_at
  BEFORE UPDATE ON usuarios
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_documentos_updated_at
  BEFORE UPDATE ON documentos
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_fornecedores_updated_at
  BEFORE UPDATE ON fornecedores
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_contas_pagar_updated_at
  BEFORE UPDATE ON contas_pagar
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_cartoes_updated_at
  BEFORE UPDATE ON cartoes_corporativos
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_faturas_updated_at
  BEFORE UPDATE ON faturas_cartao
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_lancamentos_updated_at
  BEFORE UPDATE ON lancamentos_cartao
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_ordens_compra_updated_at
  BEFORE UPDATE ON ordens_compra
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_funcionarios_updated_at
  BEFORE UPDATE ON funcionarios
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_contratos_trabalho_updated_at
  BEFORE UPDATE ON contratos_trabalho
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_contratos_updated_at
  BEFORE UPDATE ON contratos
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_processos_updated_at
  BEFORE UPDATE ON processos_juridicos
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_workflows_updated_at
  BEFORE UPDATE ON workflows
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_tarefas_updated_at
  BEFORE UPDATE ON tarefas
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_agentes_config_updated_at
  BEFORE UPDATE ON agentes_config
  FOR EACH ROW
  EXECUTE FUNCTION atualizar_updated_at();

-- Função para calcular dias_para_vencimento em tarefas
CREATE OR REPLACE FUNCTION calcular_dias_vencimento()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.prazo IS NOT NULL THEN
    NEW.dias_para_vencimento := NEW.prazo - CURRENT_DATE;
  ELSE
    NEW.dias_para_vencimento := NULL;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calcular_dias_vencimento() IS 'Calcula automaticamente os dias até o vencimento da tarefa';

-- Trigger para tarefas
CREATE TRIGGER trigger_tarefas_dias_vencimento
  BEFORE INSERT OR UPDATE ON tarefas
  FOR EACH ROW
  EXECUTE FUNCTION calcular_dias_vencimento();

-- ============================================
-- DADOS INICIAIS (SEED DATA)
-- ============================================

-- Inserir empresa demo (comentado - descomentar para ambiente de desenvolvimento)
/*
INSERT INTO empresas (razao_social, cnpj, configuracoes) VALUES
('Empresa Demo Ltda', '12345678000100',
 '{"alcadas": {"financeiro": {"gerente": 10000, "diretor": 50000}, "suprimentos": {"gerente": 5000, "diretor": 30000}}}'::jsonb);
*/

-- ============================================
-- INSTRUÇÕES DE USO
-- ============================================

-- Para executar este script:
-- psql -U cortex_user -d cortex_db -f 001_initial_schema.sql

-- Para verificar as tabelas criadas:
-- \dt

-- Para verificar as views:
-- \dv

-- Para verificar os índices:
-- \di

-- Para verificar as foreign keys:
-- SELECT conname, conrelid::regclass AS table_name, confrelid::regclass AS referenced_table
-- FROM pg_constraint
-- WHERE contype = 'f';
