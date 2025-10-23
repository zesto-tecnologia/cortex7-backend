"""
Financial domain-specific agent.
"""

from crewai import Agent
from ...tools.financial_tools import get_financial_tools


def create_financial_agent(llm):
    """Create a financial analysis agent."""
    return Agent(
        role="Analista Financeiro",
        goal="Analisar dados financeiros, contas a pagar, fornecedores e centros de custo para fornecer insights e recomendações em português brasileiro",
        backstory=(
            "Você é um analista financeiro experiente com expertise em contas a pagar, "
            "gestão de fornecedores e análise de centros de custo. Você se destaca em identificar tendências, "
            "riscos e oportunidades em dados financeiros. Você sempre responde em português brasileiro de forma clara e profissional."
        ),
        tools=get_financial_tools(),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

