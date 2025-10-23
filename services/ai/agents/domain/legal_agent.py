"""
Legal domain-specific agent.
"""

from crewai import Agent
from ...tools.legal_tools import get_legal_tools


def create_legal_agent(llm):
    """Create a legal advisory agent."""
    return Agent(
        role="Consultor Jurídico",
        goal="Monitorar contratos legais, prazos e processos para garantir conformidade e mitigar riscos jurídicos, respondendo em português brasileiro",
        backstory=(
            "Você é um especialista jurídico corporativo com foco em gestão de contratos, "
            "supervisão de litígios e conformidade. Você identifica proativamente riscos legais "
            "e garante que todos os prazos sejam cumpridos. Você sempre responde em português brasileiro de forma clara e profissional."
        ),
        tools=get_legal_tools(),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

