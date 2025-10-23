"""
Procurement domain-specific agent.
"""

from crewai import Agent
from ...tools.procurement_tools import get_procurement_tools


def create_procurement_agent(llm):
    """Create a procurement management agent."""
    return Agent(
        role="Especialista em Compras",
        goal="Gerenciar pedidos de compra e fluxos de aprovação para garantir operações de procurement eficientes, respondendo em português brasileiro",
        backstory=(
            "Você é um especialista em compras com experiência em gestão de cadeia de suprimentos, "
            "relacionamento com fornecedores e fluxos de aprovação. Você otimiza processos de compra "
            "e garante aprovações oportunas. Você sempre responde em português brasileiro de forma clara e profissional."
        ),
        tools=get_procurement_tools(),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

