#!/usr/bin/env python3
"""
Test script for OMIE BI Agents system.
Demonstrates how to use the multi-agent system for financial analysis.

Usage:
    python scripts/test_omie_bi_agents.py [analysis_type] [periodo]

Examples:
    python scripts/test_omie_bi_agents.py revenue_analysis 2023-Q4
    python scripts/test_omie_bi_agents.py collections
    python scripts/test_omie_bi_agents.py comprehensive 2023
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


def test_individual_tools():
    """Test individual tools directly."""
    print("=" * 80)
    print("TESTE 1: Ferramentas Individuais")
    print("=" * 80)
    print()

    from services.ai.tools.datawarehouse_tools import (
        QueryRevenueByClientTool,
        QueryCashFlowTool,
        QueryOverdueAnalysisTool,
    )

    # Test 1: Revenue by Client
    print("📊 Teste: Receita por Cliente (Top 10)")
    print("-" * 80)
    tool = QueryRevenueByClientTool()
    result = tool._run(periodo="")
    print(result[:500] + "..." if len(result) > 500 else result)
    print()

    # Test 2: Cash Flow
    print("💰 Teste: Fluxo de Caixa (últimos 6 meses)")
    print("-" * 80)
    tool = QueryCashFlowTool()
    result = tool._run(numero_meses="6")
    print(result[:500] + "..." if len(result) > 500 else result)
    print()

    # Test 3: Overdue Analysis
    print("⚠️  Teste: Títulos Atrasados (acima de 30 dias)")
    print("-" * 80)
    tool = QueryOverdueAnalysisTool()
    result = tool._run(dias_minimos="30")
    print(result[:500] + "..." if len(result) > 500 else result)
    print()


def test_single_agent():
    """Test a single agent with a simple task."""
    print("=" * 80)
    print("TESTE 2: Agente Individual (Transaction Analyst)")
    print("=" * 80)
    print()

    from services.ai.agents.domain.transaction_analist import create_transaction_analyst
    from crewai import Task
    from langchain_openai import ChatOpenAI

    # Configure LLM (use gpt-3.5-turbo for faster testing)
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Create agent
    agent = create_transaction_analyst(llm)

    # Create simple task
    task = Task(
        description=(
            "Analise rapidamente a receita total e identifique os 3 principais clientes. "
            "Use a ferramenta Query Revenue by Client sem filtro de período. "
            "Apresente um resumo de 3 linhas."
        ),
        agent=agent,
        expected_output="Resumo de 3 linhas com receita total e top 3 clientes"
    )

    print("🤖 Executando agente...")
    print()

    try:
        result = agent.execute_task(task)
        print("✅ Resultado:")
        print(result)
    except Exception as e:
        print(f"❌ Erro: {e}")

    print()


def test_simple_crew():
    """Test a simple 2-agent crew."""
    print("=" * 80)
    print("TESTE 3: Crew Simples (Revenue Analysis)")
    print("=" * 80)
    print()

    from services.ai.crews.omie_bi_crew import create_omie_bi_crew
    from langchain_openai import ChatOpenAI

    # Configure LLM
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    print("🚀 Criando crew de análise de receita...")
    crew = create_omie_bi_crew(
        llm=llm,
        analysis_type="revenue_analysis",
        periodo="2023"
    )

    print("🤖 Executando crew (pode levar alguns minutos)...")
    print()

    try:
        result = crew.kickoff()
        print("=" * 80)
        print("✅ RESULTADO DA ANÁLISE:")
        print("=" * 80)
        print()
        print(result)
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    print()


def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Test OMIE BI Agents")
    parser.add_argument(
        "--test",
        choices=["tools", "agent", "crew", "all"],
        default="tools",
        help="Which test to run"
    )
    parser.add_argument(
        "--analysis-type",
        default="revenue_analysis",
        help="Analysis type for crew test"
    )
    parser.add_argument(
        "--periodo",
        default="",
        help="Period filter (e.g., 2023, 2023-Q1)"
    )

    args = parser.parse_args()

    print()
    print("=" * 80)
    print("OMIE BI AGENTS - SISTEMA DE TESTES")
    print("=" * 80)
    print()

    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Erro: OPENAI_API_KEY não configurada no .env")
        print("   Configure a API key antes de executar os testes com agentes.")
        print()
        print("   Executando apenas teste de tools...")
        test_individual_tools()
        return

    if args.test == "tools" or args.test == "all":
        test_individual_tools()

    if args.test == "agent" or args.test == "all":
        test_single_agent()

    if args.test == "crew" or args.test == "all":
        test_simple_crew()

    print("=" * 80)
    print("✅ TESTES CONCLUÍDOS")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
