-- ============================================
-- CORTEX - SEED DATA
-- Dados sintéticos para teste da aplicação
-- ============================================

-- Limpar dados existentes (cuidado em produção!)
-- TRUNCATE empresas CASCADE;

-- ============================================
-- 1. EMPRESA E ESTRUTURA ORGANIZACIONAL
-- ============================================

-- Inserir Empresa Demo
INSERT INTO empresas (id, razao_social, cnpj, configuracoes) VALUES
('11111111-1111-1111-1111-111111111111', 'TechCorp Brasil Ltda', '12345678000100',
 '{
   "alcadas": {
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
 }'::jsonb);

-- Inserir Departamentos
INSERT INTO departamentos (id, empresa_id, nome, meta_data) VALUES
('22222222-2222-2222-2222-222222222221', '11111111-1111-1111-1111-111111111111', 'Financeiro', '{"codigo": "FIN", "responsavel": "João Silva"}'::jsonb),
('22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'Recursos Humanos', '{"codigo": "RH", "responsavel": "Maria Santos"}'::jsonb),
('22222222-2222-2222-2222-222222222223', '11111111-1111-1111-1111-111111111111', 'Jurídico', '{"codigo": "JUR", "responsavel": "Carlos Oliveira"}'::jsonb),
('22222222-2222-2222-2222-222222222224', '11111111-1111-1111-1111-111111111111', 'Suprimentos', '{"codigo": "SUP", "responsavel": "Ana Costa"}'::jsonb),
('22222222-2222-2222-2222-222222222225', '11111111-1111-1111-1111-111111111111', 'TI', '{"codigo": "TI", "responsavel": "Pedro Alves"}'::jsonb);

-- Inserir Usuários
INSERT INTO usuarios (id, empresa_id, departamento_id, nome, email, cargo, alcadas, status) VALUES
-- Financeiro
('33333333-3333-3333-3333-333333333331', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222221',
 'João Silva', 'joao.silva@techcorp.com.br', 'Diretor Financeiro',
 '{"financeiro": 100000, "suprimentos": 50000}'::jsonb, 'ativo'),
('33333333-3333-3333-3333-333333333332', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222221',
 'Ana Paula Ferreira', 'ana.ferreira@techcorp.com.br', 'Analista Financeiro',
 '{"financeiro": 5000}'::jsonb, 'ativo'),

-- RH
('33333333-3333-3333-3333-333333333333', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
 'Maria Santos', 'maria.santos@techcorp.com.br', 'Gerente de RH',
 '{"financeiro": 25000}'::jsonb, 'ativo'),

-- Jurídico
('33333333-3333-3333-3333-333333333334', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222223',
 'Carlos Oliveira', 'carlos.oliveira@techcorp.com.br', 'Advogado Senior',
 '{}'::jsonb, 'ativo'),

-- Suprimentos
('33333333-3333-3333-3333-333333333335', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222224',
 'Ana Costa', 'ana.costa@techcorp.com.br', 'Gerente de Suprimentos',
 '{"suprimentos": 15000}'::jsonb, 'ativo'),
('33333333-3333-3333-3333-333333333336', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222224',
 'Roberto Lima', 'roberto.lima@techcorp.com.br', 'Analista de Compras',
 '{"suprimentos": 3000}'::jsonb, 'ativo'),

-- TI
('33333333-3333-3333-3333-333333333337', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222225',
 'Pedro Alves', 'pedro.alves@techcorp.com.br', 'Gerente de TI',
 '{"suprimentos": 15000}'::jsonb, 'ativo');

-- ============================================
-- 2. MÓDULO FINANCEIRO
-- ============================================

-- Centros de Custo
INSERT INTO centros_custo (id, empresa_id, codigo, nome, departamento, orcamento_mensal, gasto_atual) VALUES
('44444444-4444-4444-4444-444444444441', '11111111-1111-1111-1111-111111111111', 'CC-TI-001', 'Infraestrutura TI', 'TI', 50000.00, 12500.50),
('44444444-4444-4444-4444-444444444442', '11111111-1111-1111-1111-111111111111', 'CC-RH-001', 'Pessoal', 'RH', 200000.00, 180000.00),
('44444444-4444-4444-4444-444444444443', '11111111-1111-1111-1111-111111111111', 'CC-ADM-001', 'Administrativo', 'Administrativo', 30000.00, 15000.00),
('44444444-4444-4444-4444-444444444444', '11111111-1111-1111-1111-111111111111', 'CC-MKT-001', 'Marketing', 'Marketing', 40000.00, 8500.00);

-- Fornecedores
INSERT INTO fornecedores (id, empresa_id, razao_social, cnpj, categoria, status, dados_bancarios, contatos, avaliacoes) VALUES
('55555555-5555-5555-5555-555555555551', '11111111-1111-1111-1111-111111111111',
 'AWS Brasil Serviços de Internet Ltda', '09346601000118', 'TI', 'ativo',
 '{"banco": "341", "agencia": "0001", "conta": "12345-6", "tipo": "corrente"}'::jsonb,
 '[{"nome": "Suporte AWS", "email": "suporte@aws.com.br", "telefone": "11-3000-0000"}]'::jsonb,
 '{"ultima_avaliacao": "2025-01", "nota": 9.5, "entregas_no_prazo": 98}'::jsonb),

('55555555-5555-5555-5555-555555555552', '11111111-1111-1111-1111-111111111111',
 'Microsoft Brasil Ltda', '04712500000157', 'TI', 'ativo',
 '{"banco": "001", "agencia": "1234", "conta": "98765-0"}'::jsonb,
 '[{"nome": "Comercial", "email": "comercial@microsoft.com.br", "telefone": "11-4000-0000"}]'::jsonb,
 '{"ultima_avaliacao": "2025-01", "nota": 9.0, "entregas_no_prazo": 95}'::jsonb),

('55555555-5555-5555-5555-555555555553', '11111111-1111-1111-1111-111111111111',
 'Limpeza Total Serviços Ltda', '12345678000199', 'Limpeza', 'ativo',
 '{"banco": "033", "agencia": "5678", "conta": "11111-1"}'::jsonb,
 '[{"nome": "João Limpeza", "email": "contato@limpezatotal.com.br", "telefone": "11-5555-5555"}]'::jsonb,
 '{"ultima_avaliacao": "2025-01", "nota": 8.0, "entregas_no_prazo": 90}'::jsonb),

('55555555-5555-5555-5555-555555555554', '11111111-1111-1111-1111-111111111111',
 'Dell Computadores do Brasil Ltda', '72381189000106', 'TI', 'ativo',
 '{"banco": "237", "agencia": "9999", "conta": "22222-2"}'::jsonb,
 '[{"nome": "Vendas Corporativas", "email": "vendas@dell.com.br", "telefone": "11-6000-0000"}]'::jsonb,
 '{"ultima_avaliacao": "2024-12", "nota": 8.5, "entregas_no_prazo": 92}'::jsonb);

-- Documentos (alguns exemplos)
INSERT INTO documentos (id, empresa_id, departamento, tipo, titulo, conteudo_original, meta_data, arquivo_url, status) VALUES
('66666666-6666-6666-6666-666666666661', '11111111-1111-1111-1111-111111111111',
 'financeiro', 'nota_fiscal', 'NF 12345 - AWS Cloud Services',
 'Nota Fiscal de Serviço nº 12345. Prestador: AWS Brasil. Valor: R$ 8.500,00. Referente a serviços de cloud computing mês 01/2025.',
 '{"numero_nf": "12345", "valor": 8500.00, "data_emissao": "2025-01-15", "cnpj_emissor": "09346601000118"}'::jsonb,
 's3://cortex-docs/nf-12345-aws.pdf', 'ativo'),

('66666666-6666-6666-6666-666666666662', '11111111-1111-1111-1111-111111111111',
 'juridico', 'contrato', 'Contrato de Licenciamento Microsoft 2025',
 'Contrato de licenciamento de software Microsoft 365 Enterprise. Vigência: 12 meses. Valor anual: R$ 120.000,00.',
 '{"tipo_contrato": "licenciamento", "vigencia_meses": 12, "valor_anual": 120000.00}'::jsonb,
 's3://cortex-docs/contrato-microsoft-2025.pdf', 'ativo'),

('66666666-6666-6666-6666-666666666663', '11111111-1111-1111-1111-111111111111',
 'rh', 'curriculo', 'Currículo - Fernanda Rodrigues',
 'Fernanda Rodrigues. Desenvolvedora Full Stack. 5 anos de experiência em Python, React e AWS.',
 '{"nome": "Fernanda Rodrigues", "cargo_pretendido": "Desenvolvedora Senior", "experiencia_anos": 5}'::jsonb,
 's3://cortex-docs/cv-fernanda-rodrigues.pdf', 'ativo');

-- Contas a Pagar
INSERT INTO contas_pagar (id, empresa_id, fornecedor_id, documento_id, numero_documento, descricao, valor, data_vencimento, data_pagamento, status, centro_custo, categoria, meta_data, prioridade) VALUES
-- Vencidas
('77777777-7777-7777-7777-777777777771', '11111111-1111-1111-1111-111111111111',
 '55555555-5555-5555-5555-555555555551', '66666666-6666-6666-6666-666666666661',
 'NF-12345', 'AWS Cloud Services - Janeiro/2025', 8500.00, '2025-01-10', NULL, 'pendente', 'CC-TI-001', 'Serviços',
 '{"forma_pagamento": "boleto", "parcela": "1/1"}'::jsonb, 1),

-- Vence hoje
('77777777-7777-7777-7777-777777777772', '11111111-1111-1111-1111-111111111111',
 '55555555-5555-5555-5555-555555555553', NULL,
 'NF-67890', 'Serviços de Limpeza - Janeiro/2025', 3200.00, CURRENT_DATE, NULL, 'aprovado', 'CC-ADM-001', 'Serviços',
 '{"forma_pagamento": "transferencia"}'::jsonb, 2),

-- Vence em 7 dias
('77777777-7777-7777-7777-777777777773', '11111111-1111-1111-1111-111111111111',
 '55555555-5555-5555-5555-555555555552', '66666666-6666-6666-6666-666666666662',
 'NF-11111', 'Microsoft 365 - Parcela 1/12', 10000.00, CURRENT_DATE + 7, NULL, 'pendente', 'CC-TI-001', 'Software',
 '{"forma_pagamento": "boleto", "parcela": "1/12", "contrato_id": "CONT-MS-2025"}'::jsonb, 5),

-- Vence em 15 dias
('77777777-7777-7777-7777-777777777774', '11111111-1111-1111-1111-111111111111',
 '55555555-5555-5555-5555-555555555554', NULL,
 'NF-22222', 'Notebooks Dell Latitude - 5 unidades', 22500.00, CURRENT_DATE + 15, NULL, 'pendente', 'CC-TI-001', 'Materiais',
 '{"forma_pagamento": "boleto", "parcela": "1/3", "quantidade": 5}'::jsonb, 5),

-- Já pago
('77777777-7777-7777-7777-777777777775', '11111111-1111-1111-1111-111111111111',
 '55555555-5555-5555-5555-555555555553', NULL,
 'NF-55555', 'Serviços de Limpeza - Dezembro/2024', 3200.00, '2024-12-28', '2024-12-27', 'pago', 'CC-ADM-001', 'Serviços',
 '{"forma_pagamento": "transferencia"}'::jsonb, 5);

-- ============================================
-- 3. MÓDULO CARTÕES CORPORATIVOS
-- ============================================

-- Cartões Corporativos
INSERT INTO cartoes_corporativos (id, empresa_id, portador_id, numero_mascarado, bandeira, tipo, limite, limite_disponivel, data_vencimento_fatura, status, centro_custo_padrao, departamento, meta_data) VALUES
('88888888-8888-8888-8888-888888888881', '11111111-1111-1111-1111-111111111111',
 '33333333-3333-3333-3333-333333333331', '**** **** **** 1234', 'Visa', 'corporativo',
 50000.00, 38500.00, 10, 'ativo', 'CC-ADM-001', 'Financeiro',
 '{"banco": "Itaú", "programa_milhas": "Multiplus", "cashback": 1.5}'::jsonb),

('88888888-8888-8888-8888-888888888882', '11111111-1111-1111-1111-111111111111',
 '33333333-3333-3333-3333-333333333337', '**** **** **** 5678', 'Mastercard', 'corporativo',
 30000.00, 22000.00, 15, 'ativo', 'CC-TI-001', 'TI',
 '{"banco": "Bradesco", "programa_milhas": "Smiles"}'::jsonb),

('88888888-8888-8888-8888-888888888883', '11111111-1111-1111-1111-111111111111',
 '33333333-3333-3333-3333-333333333335', '**** **** **** 9012', 'American Express', 'corporativo',
 20000.00, 15000.00, 20, 'ativo', 'CC-ADM-001', 'Suprimentos',
 '{"banco": "Amex", "programa_pontos": "Membership Rewards"}'::jsonb);

-- Faturas de Cartão
INSERT INTO faturas_cartao (id, empresa_id, cartao_id, documento_id, referencia, data_fechamento, data_vencimento, valor_total, valor_pago, status, observacoes, meta_data) VALUES
-- Fatura aberta - Cartão João
('99999999-9999-9999-9999-999999999991', '11111111-1111-1111-1111-111111111111',
 '88888888-8888-8888-8888-888888888881', NULL, '01/2025', '2025-01-05', '2025-01-10',
 11500.00, 0, 'aberta', 'Fatura em aberto - vence dia 10/01',
 '{"iof": 120.50, "juros": 0, "multa": 0}'::jsonb),

-- Fatura paga - Cartão Pedro
('99999999-9999-9999-9999-999999999992', '11111111-1111-1111-1111-111111111111',
 '88888888-8888-8888-8888-888888888882', NULL, '12/2024', '2024-12-10', '2024-12-15',
 8000.00, 8000.00, 'paga', 'Fatura paga em 14/12/2024',
 '{"iof": 85.00, "juros": 0, "multa": 0}'::jsonb),

-- Fatura aberta - Cartão Ana
('99999999-9999-9999-9999-999999999993', '11111111-1111-1111-1111-111111111111',
 '88888888-8888-8888-8888-888888888883', NULL, '01/2025', '2025-01-15', '2025-01-20',
 5000.00, 0, 'aberta', NULL,
 '{"iof": 52.50}'::jsonb);

-- Lançamentos de Cartão
INSERT INTO lancamentos_cartao (id, empresa_id, fatura_id, cartao_id, data_transacao, data_lancamento, estabelecimento, categoria, descricao, valor, moeda, centro_custo, aprovado, aprovador_id, justificativa) VALUES
-- Lançamentos Cartão João - Fatura 01/2025
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa01', '11111111-1111-1111-1111-111111111111',
 '99999999-9999-9999-9999-999999999991', '88888888-8888-8888-8888-888888888881',
 '2024-12-18', '2024-12-20', 'Amazon Web Services', 'Software', 'Créditos AWS - Produção',
 6500.00, 'BRL', 'CC-TI-001', true, '33333333-3333-3333-3333-333333333331', 'Infraestrutura cloud ambiente produção'),

('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa02', '11111111-1111-1111-1111-111111111111',
 '99999999-9999-9999-9999-999999999991', '88888888-8888-8888-8888-888888888881',
 '2024-12-22', '2024-12-23', 'Uber', 'Transporte', 'Corridas corporativas',
 450.00, 'BRL', 'CC-ADM-001', true, '33333333-3333-3333-3333-333333333331', 'Deslocamento reuniões clientes'),

('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa03', '11111111-1111-1111-1111-111111111111',
 '99999999-9999-9999-9999-999999999991', '88888888-8888-8888-8888-888888888881',
 '2024-12-28', '2024-12-30', 'Hotel Ibis', 'Hospedagem', 'Hospedagem viagem São Paulo',
 3200.00, 'BRL', 'CC-ADM-001', false, NULL, 'Reunião com cliente - 2 diárias'),

('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa04', '11111111-1111-1111-1111-111111111111',
 '99999999-9999-9999-9999-999999999991', '88888888-8888-8888-8888-888888888881',
 '2025-01-02', '2025-01-03', 'iFood', 'Alimentacao', 'Almoço reunião equipe',
 850.00, 'BRL', 'CC-ADM-001', false, NULL, 'Reunião planejamento anual'),

('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa05', '11111111-1111-1111-1111-111111111111',
 '99999999-9999-9999-9999-999999999991', '88888888-8888-8888-8888-888888888881',
 '2025-01-03', '2025-01-04', 'Posto Shell', 'Combustivel', 'Abastecimento veículo empresa',
 500.00, 'BRL', 'CC-ADM-001', false, NULL, 'Abastecimento carro corporativo'),

-- Lançamentos Cartão Ana - Fatura 01/2025
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa06', '11111111-1111-1111-1111-111111111111',
 '99999999-9999-9999-9999-999999999993', '88888888-8888-8888-8888-888888888883',
 '2024-12-20', '2024-12-22', 'Office Depot', 'Material Escritorio', 'Material de escritório',
 2500.00, 'BRL', 'CC-ADM-001', true, '33333333-3333-3333-3333-333333333335', 'Renovação estoque escritório'),

('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa07', '11111111-1111-1111-1111-111111111111',
 '99999999-9999-9999-9999-999999999993', '88888888-8888-8888-8888-888888888883',
 '2025-01-05', '2025-01-06', 'Correios', 'Logistica', 'Envio documentos',
 250.00, 'BRL', 'CC-ADM-001', false, NULL, 'Envio contratos para filial'),

('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa08', '11111111-1111-1111-1111-111111111111',
 '99999999-9999-9999-9999-999999999993', '88888888-8888-8888-8888-888888888883',
 '2025-01-08', '2025-01-09', 'Udemy Business', 'Treinamento', 'Curso Gestão de Compras',
 2250.00, 'BRL', 'CC-RH-001', false, NULL, 'Capacitação equipe suprimentos');

-- ============================================
-- 4. MÓDULO SUPRIMENTOS
-- ============================================

-- Ordens de Compra
INSERT INTO ordens_compra (id, empresa_id, numero, solicitante_id, fornecedor_id, valor_total, status, itens, aprovadores, centro_custo, data_entrega_prevista, meta_data) VALUES
-- Ordem aguardando aprovação
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01', '11111111-1111-1111-1111-111111111111',
 'OC-2025-0001', '33333333-3333-3333-3333-333333333337', '55555555-5555-5555-5555-555555555554',
 22500.00, 'aguardando_aprovacao',
 '[
   {"descricao": "Notebook Dell Latitude 5430", "quantidade": 5, "valor_unitario": 4500.00}
 ]'::jsonb,
 NULL, 'CC-TI-001', CURRENT_DATE + 20,
 '{"urgencia": "normal", "projeto": "Expansao Equipe TI"}'::jsonb),

-- Ordem aprovada
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb02', '11111111-1111-1111-1111-111111111111',
 'OC-2025-0002', '33333333-3333-3333-3333-333333333336', '55555555-5555-5555-5555-555555555552',
 36000.00, 'aprovada',
 '[
   {"descricao": "Licença Microsoft 365 E5", "quantidade": 100, "valor_unitario": 120.00},
   {"descricao": "Licença Power BI Pro", "quantidade": 50, "valor_unitario": 80.00},
   {"descricao": "Azure Credits", "quantidade": 1, "valor_unitario": 20000.00}
 ]'::jsonb,
 '[
   {"usuario_id": "33333333-3333-3333-3333-333333333335", "nome": "Ana Costa", "nivel": 1, "aprovado_em": "2025-01-15", "valor_aprovado": 36000.00}
 ]'::jsonb,
 'CC-TI-001', CURRENT_DATE + 10,
 '{"contrato_base": "CONT-MS-2025"}'::jsonb),

-- Ordem em rascunho
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb03', '11111111-1111-1111-1111-111111111111',
 'OC-2025-0003', '33333333-3333-3333-3333-333333333336', '55555555-5555-5555-5555-555555555553',
 1920.00, 'rascunho',
 '[
   {"descricao": "Serviço de Limpeza - 6 meses", "quantidade": 6, "valor_unitario": 320.00}
 ]'::jsonb,
 NULL, 'CC-ADM-001', CURRENT_DATE + 30,
 '{"periodicidade": "mensal"}'::jsonb),

-- Ordem pedido emitido
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb04', '11111111-1111-1111-1111-111111111111',
 'OC-2024-0099', '33333333-3333-3333-3333-333333333337', '55555555-5555-5555-5555-555555555551',
 12000.00, 'pedido_emitido',
 '[
   {"descricao": "AWS EC2 Instances - Reserved", "quantidade": 10, "valor_unitario": 1200.00}
 ]'::jsonb,
 '[
   {"usuario_id": "33333333-3333-3333-3333-333333333337", "nome": "Pedro Alves", "nivel": 1, "aprovado_em": "2024-12-15"}
 ]'::jsonb,
 'CC-TI-001', '2024-12-30',
 '{"emissao": {"emitido_em": "2024-12-16"}}'::jsonb);

-- ============================================
-- 5. MÓDULO RH
-- ============================================

-- Funcionários
INSERT INTO funcionarios (id, empresa_id, usuario_id, cpf, data_nascimento, data_admissao, data_demissao, cargo, departamento_id, salario, tipo_contrato, regime_trabalho, dados_pessoais, beneficios, ferias, status) VALUES
-- Funcionário 1 - João Silva (também é usuário)
('cccccccc-cccc-cccc-cccc-cccccccccc01', '11111111-1111-1111-1111-111111111111',
 '33333333-3333-3333-3333-333333333331', '12345678901', '1985-03-15', '2020-01-10', NULL,
 'Diretor Financeiro', '22222222-2222-2222-2222-222222222221', 18000.00, 'CLT', 'Hibrido',
 '{"endereco": "Rua das Flores, 123, São Paulo - SP", "telefone": "11-99999-0001", "contato_emergencia": {"nome": "Maria Silva", "telefone": "11-98888-0001"}}'::jsonb,
 '{"vale_transporte": false, "vale_refeicao": 1200.00, "plano_saude": "Unimed Nacional", "plano_dental": true}'::jsonb,
 '{"saldo_dias": 30, "historico": [{"periodo": "2023-2024", "dias_usados": 30, "data_inicio": "2024-01-15", "data_fim": "2024-02-14"}]}'::jsonb,
 'ativo'),

-- Funcionário 2 - Maria Santos (também é usuária)
('cccccccc-cccc-cccc-cccc-cccccccccc02', '11111111-1111-1111-1111-111111111111',
 '33333333-3333-3333-3333-333333333333', '23456789012', '1990-07-22', '2021-05-01', NULL,
 'Gerente de RH', '22222222-2222-2222-2222-222222222222', 12000.00, 'CLT', 'Presencial',
 '{"endereco": "Av. Paulista, 1000, São Paulo - SP", "telefone": "11-99999-0002"}'::jsonb,
 '{"vale_transporte": true, "vale_refeicao": 1000.00, "plano_saude": "Bradesco Saúde"}'::jsonb,
 '{"saldo_dias": 15, "historico": []}'::jsonb,
 'ativo'),

-- Funcionário 3 - Desenvolvedor
('cccccccc-cccc-cccc-cccc-cccccccccc03', '11111111-1111-1111-1111-111111111111',
 NULL, '34567890123', '1995-11-08', '2023-03-15', NULL,
 'Desenvolvedor Full Stack', '22222222-2222-2222-2222-222222222225', 9000.00, 'CLT', 'Remoto',
 '{"endereco": "Rua das Acácias, 456, Campinas - SP", "telefone": "19-99999-0003"}'::jsonb,
 '{"vale_transporte": false, "vale_refeicao": 800.00, "auxilio_home_office": 300.00}'::jsonb,
 '{"saldo_dias": 22, "historico": []}'::jsonb,
 'ativo'),

-- Funcionário 4 - Demitido
('cccccccc-cccc-cccc-cccc-cccccccccc04', '11111111-1111-1111-1111-111111111111',
 NULL, '45678901234', '1988-02-14', '2019-08-01', '2024-12-31',
 'Analista Administrativo', '22222222-2222-2222-2222-222222222221', 5000.00, 'CLT', 'Presencial',
 '{"endereco": "Rua Teste, 789, São Paulo - SP", "telefone": "11-99999-0004"}'::jsonb,
 '{"vale_transporte": true, "vale_refeicao": 600.00}'::jsonb,
 '{"saldo_dias": 0}'::jsonb,
 'inativo');

-- Contratos de Trabalho
INSERT INTO contratos_trabalho (id, funcionario_id, documento_id, tipo, data_inicio, data_fim, conteudo, assinado, assinatura_funcionario_data, assinatura_empresa_data) VALUES
-- Contrato admissão João
('dddddddd-dddd-dddd-dddd-dddddddddd01', 'cccccccc-cccc-cccc-cccc-cccccccccc01', NULL,
 'admissao', '2020-01-10', NULL,
 'Contrato de trabalho por prazo indeterminado. Cargo: Diretor Financeiro. Salário: R$ 18.000,00.',
 true, '2020-01-09', '2020-01-09'),

-- Contrato admissão Maria
('dddddddd-dddd-dddd-dddd-dddddddddd02', 'cccccccc-cccc-cccc-cccc-cccccccccc02', NULL,
 'admissao', '2021-05-01', NULL,
 'Contrato de trabalho por prazo indeterminado. Cargo: Gerente de RH. Salário: R$ 12.000,00.',
 true, '2021-04-30', '2021-04-30'),

-- Contrato rescisão
('dddddddd-dddd-dddd-dddd-dddddddddd03', 'cccccccc-cccc-cccc-cccc-cccccccccc04', NULL,
 'rescisao', '2019-08-01', '2024-12-31',
 'Termo de rescisão contratual. Motivo: Pedido de demissão.',
 true, '2024-12-15', '2024-12-16');

-- ============================================
-- 6. MÓDULO JURÍDICO
-- ============================================

-- Contratos Jurídicos
INSERT INTO contratos (id, empresa_id, documento_id, tipo, parte_contraria, cnpj_cpf_contraparte, objeto, valor, data_inicio, data_fim, renovacao_automatica, status, clausulas_criticas, prazos_importantes, responsavel_id, meta_data) VALUES
-- Contrato vigente
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeee01', '11111111-1111-1111-1111-111111111111',
 '66666666-6666-6666-6666-666666666662', 'fornecedor', 'Microsoft Brasil Ltda', '04712500000157',
 'Licenciamento de software Microsoft 365 e Azure para 100 usuários', 120000.00,
 '2025-01-01', '2025-12-31', true, 'vigente',
 '{"multa_rescisao": "30% do valor restante", "sla_suporte": "99.9% uptime", "confidencialidade": "NDA incluído"}'::jsonb,
 '[
   {"descricao": "Renovação contrato", "data": "2025-11-01", "notificado": false},
   {"descricao": "Revisão de valores", "data": "2025-06-01", "notificado": false}
 ]'::jsonb,
 '33333333-3333-3333-3333-333333333334',
 '{"gestor_microsoft": "João Silva Vendas", "email": "joao.silva@microsoft.com"}'::jsonb),

-- Contrato vencendo em breve
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeee02', '11111111-1111-1111-1111-111111111111',
 NULL, 'fornecedor', 'AWS Brasil Serviços de Internet Ltda', '09346601000118',
 'Serviços de infraestrutura cloud AWS', 102000.00,
 '2024-02-01', CURRENT_DATE + 45, false, 'vigente',
 '{"multa_rescisao": "não aplicável", "sla_disponibilidade": "99.99%"}'::jsonb,
 jsonb_build_array(
   jsonb_build_object('descricao', 'Término contrato', 'data', (CURRENT_DATE + 45)::text, 'notificado', false)
 ),
 '33333333-3333-3333-3333-333333333334',
 NULL),

-- Contrato cliente
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeee03', '11111111-1111-1111-1111-111111111111',
 NULL, 'cliente', 'Empresa XYZ Tecnologia Ltda', '98765432000111',
 'Desenvolvimento de sistema customizado de gestão', 250000.00,
 '2024-06-01', '2025-12-31', false, 'vigente',
 '{"multa_atraso": "1% ao mês sobre valor em aberto", "garantia": "12 meses após entrega"}'::jsonb,
 '[
   {"descricao": "Entrega Fase 1", "data": "2025-03-01", "notificado": true},
   {"descricao": "Entrega Fase 2", "data": "2025-08-01", "notificado": false},
   {"descricao": "Entrega Final", "data": "2025-12-01", "notificado": false}
 ]'::jsonb,
 '33333333-3333-3333-3333-333333333334',
 '{"forma_pagamento": "30% entrada + 70% parcelado em 7x"}'::jsonb);

-- Processos Jurídicos
INSERT INTO processos_juridicos (id, empresa_id, numero_processo, tipo, parte_contraria, valor_causa, status, risco, tribunal, advogado_responsavel, historico, proxima_acao, proxima_acao_descricao) VALUES
-- Processo trabalhista em andamento
('ffffffff-ffff-ffff-ffff-ffffffffff01', '11111111-1111-1111-1111-111111111111',
 '0001234-56.2024.5.02.0001', 'trabalhista', 'João Antônio da Silva', 85000.00,
 'andamento', 'medio', 'TRT 2ª Região - São Paulo', 'Dr. Carlos Oliveira',
 '[
   {"data": "2024-06-15", "evento": "Distribuição", "descricao": "Processo distribuído"},
   {"data": "2024-07-20", "evento": "Defesa", "descricao": "Apresentada defesa contestando todos os pontos"},
   {"data": "2024-09-10", "evento": "Audiência Inicial", "descricao": "Tentativa de conciliação sem êxito"},
   {"data": "2024-12-05", "evento": "Perícia", "descricao": "Realizada perícia contábil"}
 ]'::jsonb,
 CURRENT_DATE + 30, 'Audiência de instrução e julgamento'),

-- Processo cível de baixo risco
('ffffffff-ffff-ffff-ffff-ffffffffff02', '11111111-1111-1111-1111-111111111111',
 '1234567-89.2024.8.26.0100', 'civel', 'Fornecedor ABC Ltda', 15000.00,
 'andamento', 'baixo', 'Foro Central - SP', 'Dra. Fernanda Costa',
 '[
   {"data": "2024-10-01", "evento": "Distribuição", "descricao": "Cobrança de valores em duplicidade"},
   {"data": "2024-11-15", "evento": "Contestação", "descricao": "Apresentada reconvenção"}
 ]'::jsonb,
 CURRENT_DATE + 15, 'Manifestação sobre documentos apresentados');

-- ============================================
-- 7. WORKFLOWS E TAREFAS
-- ============================================

-- Workflows
INSERT INTO workflows (id, empresa_id, tipo, nome, fases, ativo) VALUES
('11111111-aaaa-bbbb-cccc-111111111111', '11111111-1111-1111-1111-111111111111',
 'aprovacao_compra', 'Aprovação de Ordem de Compra',
 '[
   {"nome": "Solicitação", "ordem": 1, "responsavel": "solicitante", "acoes": ["criar", "editar"]},
   {"nome": "Aprovação Gerente", "ordem": 2, "responsavel": "gerente", "acoes": ["aprovar", "rejeitar", "solicitar_ajustes"]},
   {"nome": "Aprovação Diretor", "ordem": 3, "responsavel": "diretor", "acoes": ["aprovar", "rejeitar"], "condicao": "valor > 15000"},
   {"nome": "Emissão Pedido", "ordem": 4, "responsavel": "compras", "acoes": ["emitir"]},
   {"nome": "Recebimento", "ordem": 5, "responsavel": "solicitante", "acoes": ["confirmar_recebimento"]}
 ]'::jsonb,
 true),

('11111111-aaaa-bbbb-cccc-111111111112', '11111111-1111-1111-1111-111111111111',
 'aprovacao_despesa', 'Aprovação de Despesa Cartão Corporativo',
 '[
   {"nome": "Lançamento", "ordem": 1, "responsavel": "portador", "acoes": ["justificar", "anexar_recibo"]},
   {"nome": "Aprovação", "ordem": 2, "responsavel": "gestor", "acoes": ["aprovar", "rejeitar", "contestar"]}
 ]'::jsonb,
 true);

-- Tarefas
INSERT INTO tarefas (id, empresa_id, workflow_id, entidade_tipo, entidade_id, titulo, descricao, responsavel_id, departamento, status, prioridade, prazo, prazo_legal, dias_para_vencimento, meta_data) VALUES
-- Tarefa urgente - prazo vencido
('22222222-aaaa-bbbb-cccc-222222222221', '11111111-1111-1111-1111-111111111111',
 NULL, 'conta_pagar', '77777777-7777-7777-7777-777777777771',
 'Pagar AWS Cloud Services - VENCIDO',
 'Conta vencida desde 10/01. Efetuar pagamento urgente para evitar suspensão dos serviços.',
 '33333333-3333-3333-3333-333333333331', 'financeiro', 'pendente', 1,
 '2025-01-10', false, (('2025-01-10'::date) - CURRENT_DATE),
 '{"tipo": "pagamento", "valor": 8500.00, "urgencia": "critica"}'::jsonb),

-- Tarefa importante - vence hoje
('22222222-aaaa-bbbb-cccc-222222222222', '11111111-1111-1111-1111-111111111111',
 NULL, 'conta_pagar', '77777777-7777-7777-7777-777777777772',
 'Pagar Serviços de Limpeza - VENCE HOJE',
 'Conta aprovada. Processar pagamento via transferência bancária.',
 '33333333-3333-3333-3333-333333333332', 'financeiro', 'em_andamento', 2,
 CURRENT_DATE, false, 0,
 '{"tipo": "pagamento", "valor": 3200.00, "forma": "transferencia"}'::jsonb),

-- Tarefa - aprovar ordem de compra
('22222222-aaaa-bbbb-cccc-222222222223', '11111111-1111-1111-1111-111111111111',
 '11111111-aaaa-bbbb-cccc-111111111111', 'ordem_compra', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb01',
 'Aprovar Ordem de Compra - Notebooks Dell',
 'Ordem de compra de 5 notebooks Dell Latitude no valor de R$ 22.500,00. Verificar especificações e autorizar.',
 '33333333-3333-3333-3333-333333333335', 'suprimentos', 'pendente', 5,
 CURRENT_DATE + 3, false, 3,
 '{"tipo": "aprovacao", "valor": 22500.00, "workflow_fase": "Aprovação Gerente"}'::jsonb),

-- Tarefa - revisar contrato
('22222222-aaaa-bbbb-cccc-222222222224', '11111111-1111-1111-1111-111111111111',
 NULL, 'contrato', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee02',
 'Revisar renovação contrato AWS',
 'Contrato AWS vence em 45 dias. Negociar condições de renovação ou buscar alternativas.',
 '33333333-3333-3333-3333-333333333334', 'juridico', 'pendente', 3,
 CURRENT_DATE + 30, false, 30,
 '{"tipo": "revisao_contrato", "contrato_id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeee02", "acao": "renovacao"}'::jsonb),

-- Tarefa - prazo legal
('22222222-aaaa-bbbb-cccc-222222222225', '11111111-1111-1111-1111-111111111111',
 NULL, 'processo_juridico', 'ffffffff-ffff-ffff-ffff-ffffffffff02',
 'Manifestação Processo Cível - PRAZO LEGAL',
 'Apresentar manifestação sobre documentos no processo contra Fornecedor ABC. Prazo legal de 15 dias.',
 '33333333-3333-3333-3333-333333333334', 'juridico', 'pendente', 1,
 CURRENT_DATE + 15, true, 15,
 '{"tipo": "manifestacao_processual", "processo": "1234567-89.2024.8.26.0100", "prazo_fatal": true}'::jsonb),

-- Tarefa - aprovar despesas cartão
('22222222-aaaa-bbbb-cccc-222222222226', '11111111-1111-1111-1111-111111111111',
 '11111111-aaaa-bbbb-cccc-111111111112', 'lancamento_cartao', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa03',
 'Aprovar despesa - Hotel Ibis',
 'Aprovar lançamento de R$ 3.200,00 referente a hospedagem em São Paulo.',
 '33333333-3333-3333-3333-333333333331', 'financeiro', 'pendente', 5,
 CURRENT_DATE + 7, false, 7,
 '{"tipo": "aprovacao_despesa", "valor": 3200.00, "portador": "João Silva"}'::jsonb),

-- Tarefa concluída
('22222222-aaaa-bbbb-cccc-222222222227', '11111111-1111-1111-1111-111111111111',
 NULL, 'conta_pagar', '77777777-7777-7777-7777-777777777775',
 'Pagar Serviços de Limpeza - Dezembro',
 'Pagamento realizado com sucesso em 27/12/2024.',
 '33333333-3333-3333-3333-333333333332', 'financeiro', 'concluida', 5,
 '2024-12-28', false, NULL,
 '{"tipo": "pagamento", "valor": 3200.00, "data_pagamento": "2024-12-27"}'::jsonb);

-- ============================================
-- 8. CONFIGURAÇÕES E CACHE
-- ============================================

-- Configurações de Agentes
INSERT INTO agentes_config (id, empresa_id, agente_tipo, configuracao, ativo) VALUES
('33333333-aaaa-bbbb-cccc-333333333331', '11111111-1111-1111-1111-111111111111',
 'ranqueador',
 '{
   "modelo": "gpt-4",
   "temperatura": 0.3,
   "criterios_priorizacao": ["prazo_legal", "valor_financeiro", "urgencia", "dependencias"],
   "peso_prazo_legal": 10,
   "peso_valor": 5
 }'::jsonb,
 true),

('33333333-aaaa-bbbb-cccc-333333333332', '11111111-1111-1111-1111-111111111111',
 'extrator',
 '{
   "modelo": "gpt-4-vision",
   "tipos_documento": ["nota_fiscal", "contrato", "recibo"],
   "campos_extracao": {
     "nota_fiscal": ["numero", "data_emissao", "valor", "cnpj_emissor", "descricao"],
     "contrato": ["partes", "objeto", "valor", "vigencia", "clausulas_especiais"]
   }
 }'::jsonb,
 true),

('33333333-aaaa-bbbb-cccc-333333333333', '11111111-1111-1111-1111-111111111111',
 'conversacional',
 '{
   "modelo": "gpt-4-turbo",
   "temperatura": 0.7,
   "max_tokens": 2000,
   "contexto_empresa": true,
   "acesso_dados": ["tarefas", "contas_pagar", "contratos"]
 }'::jsonb,
 true);

-- ============================================
-- VERIFICAÇÃO DOS DADOS INSERIDOS
-- ============================================

-- Contar registros por tabela
DO $$
DECLARE
  empresas_count INTEGER;
  usuarios_count INTEGER;
  fornecedores_count INTEGER;
  contas_count INTEGER;
  funcionarios_count INTEGER;
  tarefas_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO empresas_count FROM empresas;
  SELECT COUNT(*) INTO usuarios_count FROM usuarios;
  SELECT COUNT(*) INTO fornecedores_count FROM fornecedores;
  SELECT COUNT(*) INTO contas_count FROM contas_pagar;
  SELECT COUNT(*) INTO funcionarios_count FROM funcionarios;
  SELECT COUNT(*) INTO tarefas_count FROM tarefas;

  RAISE NOTICE '========================================';
  RAISE NOTICE 'SEED DATA - RESUMO';
  RAISE NOTICE '========================================';
  RAISE NOTICE 'Empresas: %', empresas_count;
  RAISE NOTICE 'Usuários: %', usuarios_count;
  RAISE NOTICE 'Fornecedores: %', fornecedores_count;
  RAISE NOTICE 'Contas a Pagar: %', contas_count;
  RAISE NOTICE 'Funcionários: %', funcionarios_count;
  RAISE NOTICE 'Tarefas: %', tarefas_count;
  RAISE NOTICE '========================================';
END $$;
