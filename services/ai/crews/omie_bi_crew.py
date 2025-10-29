"""
OMIE Business Intelligence Crew - Multi-agent system for comprehensive financial analysis.

This crew coordinates multiple specialized agents to provide deep financial insights
from the OMIE Data Warehouse, including transaction analysis, BI insights, forecasting,
and collections strategy.

"Quais são os 20 maiores clientes por receita?"
"Qual é a tendência de crescimento dos últimos 12 meses?"
"Quais clientes estão inadimplentes há mais de 60 dias?"
"Qual é a projeção de receita para os próximos 3 meses?"
"Como está a carga tributária por categoria?"
"Qual é o fluxo de caixa projetado?"


"""

from crewai import Crew, Task, Process
from ..agents.domain.transaction_analist import (
    create_transaction_analyst,
    create_bi_analyst,
    create_forecast_analyst,
    create_collections_specialist,
)
from typing import List, Dict, Optional


def create_omie_bi_crew(
    llm,
    company_id: str,
    query: str,
    analysis_type: str = "forecast",
    periodo: Optional[str] = None,
):
    """
    Create a Business Intelligence crew for OMIE financial analysis.

    Args:
        llm: Language model to use for all agents
        company_id: Company ID for context (currently unused but kept for API consistency)
        query: User's query/request (currently unused but kept for API consistency)
        analysis_type: Type of analysis to perform:
            - "comprehensive": Full financial analysis with all agents
            - "revenue_analysis": Focus on revenue and client performance
            - "collections": Focus on overdue analysis and recovery
            - "forecast": Focus on predictions and trends
            - "pl_analysis": Focus on P&L and categories
            - "cash_flow": Focus on cash flow and liquidity
        periodo: Optional period filter (e.g., "2023", "2023-Q1", "2023-01")

    Returns:
        Crew: Configured crew ready to execute financial analysis
    """

    # Create specialized agents
    transaction_analyst = create_transaction_analyst(llm)
    bi_analyst = create_bi_analyst(llm)
    forecast_analyst = create_forecast_analyst(llm)
    collections_specialist = create_collections_specialist(llm)

    # Configure tasks based on analysis type
    tasks = []

    if analysis_type == "revenue_analysis":
        # Full comprehensive analysis with all agents
        tasks = _create_comprehensive_analysis_tasks(
            transaction_analyst,
            bi_analyst,
            forecast_analyst,
            collections_specialist,
            periodo,
        )

    elif analysis_type == "revenue_analysis":
        tasks = _create_revenue_analysis_tasks(
            transaction_analyst, bi_analyst, forecast_analyst, periodo
        )

    elif analysis_type == "collections":
        tasks = _create_collections_analysis_tasks(
            transaction_analyst, collections_specialist, periodo
        )

    elif analysis_type == "forecast":
        tasks = _create_forecast_analysis_tasks(
            transaction_analyst, forecast_analyst, bi_analyst, periodo
        )

    elif analysis_type == "pl_analysis":
        tasks = _create_pl_analysis_tasks(
            transaction_analyst, bi_analyst, periodo
        )

    elif analysis_type == "cash_flow":
        tasks = _create_cash_flow_analysis_tasks(
            transaction_analyst, bi_analyst, forecast_analyst, periodo
        )

    else:
        raise ValueError(f"Unknown analysis_type: {analysis_type}")

    # Create crew with hierarchical process
    crew = Crew(
        agents=[transaction_analyst, bi_analyst, forecast_analyst, collections_specialist],
        tasks=tasks,
        process=Process.sequential,  # Tasks run in sequence
        verbose=True,
    )

    return crew


def _create_comprehensive_analysis_tasks(
    transaction_analyst, bi_analyst, forecast_analyst, collections_specialist, periodo
) -> List[Task]:
    """Create tasks for comprehensive financial analysis."""

    period_str = f" para o período {periodo}" if periodo else ""

    # Task 1: Data Collection and Initial Analysis
    data_collection_task = Task(
        description=(
            f"Colete e analise dados financeiros completos do Data Warehouse OMIE{period_str}. "
            "Inclua:\n"
            "1. Receitas por cliente (top 20)\n"
            "2. Análise P&L por categoria\n"
            "3. Fluxo de caixa dos últimos 6 meses\n"
            "4. Títulos atrasados e inadimplência\n"
            "5. Análise tributária\n\n"
            "Organize os dados de forma estruturada para análise posterior."
        ),
        agent=transaction_analyst,
        expected_output=(
            "Relatório estruturado com dados financeiros organizados por área "
            "(receita, despesas, fluxo de caixa, inadimplência, impostos) em português brasileiro"
        ),
    )

    # Task 2: Business Intelligence Insights
    bi_insights_task = Task(
        description=(
            "Com base nos dados coletados, gere insights estratégicos de Business Intelligence:\n"
            "1. Identifique os 5 principais insights positivos e negativos\n"
            "2. Compare performance entre períodos e identifique tendências\n"
            "3. Analise KPIs chave: ticket médio, DSO, taxa de inadimplência\n"
            "4. Identifique outliers e anomalias importantes\n"
            "5. Crie recomendações estratégicas baseadas em dados\n\n"
            "Apresente em formato executivo com visualizações sugeridas."
        ),
        agent=bi_analyst,
        expected_output=(
            "Dashboard executivo em formato markdown com insights estratégicos, "
            "KPIs principais e recomendações acionáveis em português brasileiro"
        ),
        context=[data_collection_task],
    )

    # Task 3: Forecasting and Trends
    forecast_task = Task(
        description=(
            "Analise séries temporais e crie previsões financeiras:\n"
            "1. Identifique tendências de receita nos últimos 12 meses\n"
            "2. Projete receitas para os próximos 3 meses (cenários otimista/realista/pessimista)\n"
            "3. Identifique sazonalidades e padrões cíclicos\n"
            "4. Avalie riscos emergentes baseados em dados históricos\n"
            "5. Analise cohorts de clientes e preveja churn\n\n"
            "Inclua intervalos de confiança e premissas utilizadas."
        ),
        agent=forecast_analyst,
        expected_output=(
            "Relatório de previsões com projeções quantitativas, análise de tendências, "
            "identificação de riscos e premissas utilizadas em português brasileiro"
        ),
        context=[data_collection_task, bi_insights_task],
    )

    # Task 4: Collections Strategy
    collections_task = Task(
        description=(
            "Desenvolva estratégia de cobrança baseada em análise de inadimplência:\n"
            "1. Liste top 10 clientes inadimplentes por valor e dias de atraso\n"
            "2. Segmente clientes por risco (alto/médio/baixo)\n"
            "3. Priorize ações de cobrança por ROI esperado\n"
            "4. Recomende estratégias específicas por perfil de cliente\n"
            "5. Estime potencial de recuperação e timeline\n\n"
            "Foque em ações práticas e mensuráveis."
        ),
        agent=collections_specialist,
        expected_output=(
            "Plano de ação de cobrança com clientes priorizados, estratégias específicas, "
            "estimativas de recuperação e timeline em português brasileiro"
        ),
        context=[data_collection_task],
    )

    # Task 5: Executive Summary
    executive_summary_task = Task(
        description=(
            "Consolide todas as análises anteriores em um sumário executivo:\n"
            "1. Situação financeira atual (resumo em 3 pontos)\n"
            "2. Top 5 insights mais importantes\n"
            "3. Top 3 oportunidades de melhoria\n"
            "4. Top 3 riscos que requerem atenção imediata\n"
            "5. Recomendações estratégicas priorizadas (curto, médio, longo prazo)\n\n"
            "Linguagem clara para executivos C-level."
        ),
        agent=bi_analyst,
        expected_output=(
            "Sumário executivo de 1-2 páginas com situação atual, insights principais, "
            "oportunidades, riscos e recomendações estratégicas priorizadas em português brasileiro"
        ),
        context=[data_collection_task, bi_insights_task, forecast_task, collections_task],
    )

    return [
        data_collection_task,
        bi_insights_task,
        forecast_task,
        collections_task,
        executive_summary_task,
    ]


def _create_revenue_analysis_tasks(
    transaction_analyst, bi_analyst, forecast_analyst, periodo
) -> List[Task]:
    """Create tasks focused on revenue analysis."""

    period_str = f" para o período {periodo}" if periodo else ""

    revenue_data_task = Task(
        description=(
            f"Analise receitas detalhadamente{period_str}:\n"
            "1. Receita por cliente (top 30)\n"
            "2. Receita por vertical e key account\n"
            "3. Receita por categoria P&L\n"
            "4. Evolução mensal de receitas\n"
            "5. Análise de ticket médio por segmento"
        ),
        agent=transaction_analyst,
        expected_output="Análise detalhada de receitas com segmentação múltipla",
    )

    revenue_insights_task = Task(
        description=(
            "Gere insights estratégicos sobre receitas:\n"
            "1. Concentração de receita (% dos top 10 clientes)\n"
            "2. Clientes com crescimento/declínio acelerado\n"
            "3. Oportunidades de cross-sell/upsell\n"
            "4. Comparação com períodos anteriores\n"
            "5. Recomendações para otimizar receita"
        ),
        agent=bi_analyst,
        expected_output="Dashboard de insights de receita com recomendações",
        context=[revenue_data_task],
    )

    revenue_forecast_task = Task(
        description=(
            "Projete receitas futuras:\n"
            "1. Previsão para próximos 3 meses\n"
            "2. Identificar sazonalidades\n"
            "3. Avaliar impacto de churn previsto\n"
            "4. Cenários de crescimento"
        ),
        agent=forecast_analyst,
        expected_output="Projeção de receitas com cenários e premissas",
        context=[revenue_data_task, revenue_insights_task],
    )

    return [revenue_data_task, revenue_insights_task, revenue_forecast_task]


def _create_collections_analysis_tasks(
    transaction_analyst, collections_specialist, periodo
) -> List[Task]:
    """Create tasks focused on collections and overdue analysis."""

    overdue_data_task = Task(
        description=(
            "Analise todos os títulos atrasados:\n"
            "1. Lista completa de clientes inadimplentes\n"
            "2. Valores totais por faixa de atraso (30, 60, 90+ dias)\n"
            "3. Histórico de pagamento dos inadimplentes\n"
            "4. Análise de concentração de risco"
        ),
        agent=transaction_analyst,
        expected_output="Relatório completo de inadimplência com dados estruturados",
    )

    collections_strategy_task = Task(
        description=(
            "Desenvolva plano de ação de cobrança:\n"
            "1. Priorização de clientes por valor x risco\n"
            "2. Estratégias customizadas por perfil\n"
            "3. Sequência de ações (contato, negociação, jurídico)\n"
            "4. Metas de recuperação por período\n"
            "5. KPIs para monitoramento"
        ),
        agent=collections_specialist,
        expected_output="Plano de ação de cobrança detalhado com estratégias e metas",
        context=[overdue_data_task],
    )

    return [overdue_data_task, collections_strategy_task]


def _create_forecast_analysis_tasks(
    transaction_analyst, forecast_analyst, bi_analyst, periodo
) -> List[Task]:
    """Create tasks focused on forecasting and predictive analytics."""

    historical_data_task = Task(
        description=(
            "Colete dados históricos para análise preditiva:\n"
            "1. Série temporal de receitas (últimos 24 meses)\n"
            "2. Série temporal de despesas\n"
            "3. Fluxo de caixa histórico\n"
            "4. Análise de cohorts de clientes"
        ),
        agent=transaction_analyst,
        expected_output="Dataset estruturado com séries temporais financeiras",
    )

    forecast_modeling_task = Task(
        description=(
            "Crie modelos preditivos:\n"
            "1. Previsão de receita (6 meses)\n"
            "2. Previsão de despesas\n"
            "3. Previsão de fluxo de caixa\n"
            "4. Análise de tendências e sazonalidade\n"
            "5. Identificação de riscos emergentes"
        ),
        agent=forecast_analyst,
        expected_output="Projeções financeiras com intervalos de confiança e análise de riscos",
        context=[historical_data_task],
    )

    forecast_insights_task = Task(
        description=(
            "Traduza previsões em insights acionáveis:\n"
            "1. Impacto das tendências nos objetivos\n"
            "2. Recomendações preventivas para riscos\n"
            "3. Oportunidades identificadas nas projeções\n"
            "4. Ajustes recomendados na estratégia"
        ),
        agent=bi_analyst,
        expected_output="Sumário executivo com insights e recomendações baseadas em previsões",
        context=[forecast_modeling_task],
    )

    return [historical_data_task, forecast_modeling_task, forecast_insights_task]


def _create_pl_analysis_tasks(transaction_analyst, bi_analyst, periodo) -> List[Task]:
    """Create tasks focused on P&L analysis."""

    period_str = f" para o período {periodo}" if periodo else ""

    pl_data_task = Task(
        description=(
            f"Analise P&L completo{period_str}:\n"
            "1. Receitas por categoria hierárquica\n"
            "2. Despesas por categoria\n"
            "3. Margem bruta e líquida\n"
            "4. Análise de custos fixos vs variáveis\n"
            "5. Evolução temporal do P&L"
        ),
        agent=transaction_analyst,
        expected_output="Análise P&L detalhada com categorias hierárquicas",
    )

    pl_insights_task = Task(
        description=(
            "Gere insights sobre P&L:\n"
            "1. Categorias com melhor/pior performance\n"
            "2. Oportunidades de otimização de custos\n"
            "3. Análise de margem por produto/serviço\n"
            "4. Comparação com períodos anteriores\n"
            "5. Recomendações para melhorar rentabilidade"
        ),
        agent=bi_analyst,
        expected_output="Dashboard P&L com insights e recomendações",
        context=[pl_data_task],
    )

    return [pl_data_task, pl_insights_task]


def _create_cash_flow_analysis_tasks(
    transaction_analyst, bi_analyst, forecast_analyst, periodo
) -> List[Task]:
    """Create tasks focused on cash flow analysis."""

    cash_flow_data_task = Task(
        description=(
            "Analise fluxo de caixa:\n"
            "1. Entradas e saídas dos últimos 12 meses\n"
            "2. Saldo líquido mensal\n"
            "3. Títulos a vencer nos próximos 90 dias\n"
            "4. Análise de liquidez\n"
            "5. Ciclo de conversão de caixa"
        ),
        agent=transaction_analyst,
        expected_output="Análise detalhada de fluxo de caixa histórico e projetado",
    )

    cash_flow_forecast_task = Task(
        description=(
            "Projete fluxo de caixa futuro:\n"
            "1. Projeção de entradas (próximos 6 meses)\n"
            "2. Projeção de saídas\n"
            "3. Saldo projetado\n"
            "4. Identificar períodos de aperto de caixa\n"
            "5. Recomendações de gestão de liquidez"
        ),
        agent=forecast_analyst,
        expected_output="Projeção de fluxo de caixa com análise de liquidez",
        context=[cash_flow_data_task],
    )

    cash_flow_strategy_task = Task(
        description=(
            "Desenvolva estratégia de gestão de caixa:\n"
            "1. Ações para otimizar recebimentos\n"
            "2. Estratégias de pagamento inteligente\n"
            "3. Gestão de capital de giro\n"
            "4. Política de crédito recomendada\n"
            "5. Plano de contingência para períodos críticos"
        ),
        agent=bi_analyst,
        expected_output="Estratégia de gestão de caixa com ações concretas",
        context=[cash_flow_data_task, cash_flow_forecast_task],
    )

    return [cash_flow_data_task, cash_flow_forecast_task, cash_flow_strategy_task]
