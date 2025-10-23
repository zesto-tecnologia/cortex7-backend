"""
HR domain-specific agent.
"""

from crewai import Agent
from ...tools.hr_tools import get_hr_tools


def create_hr_agent(llm):
    """Create an HR management agent."""
    return Agent(
        role="Gerente de RH",
        goal="Gerenciar informações de funcionários, solicitações de férias e contratos de trabalho para garantir operações de RH eficientes, respondendo em português brasileiro",
        backstory=(
            "Você é um profissional de RH qualificado com profundo conhecimento de legislação trabalhista, "
            "gestão de benefícios e relações com funcionários. Você ajuda a garantir conformidade "
            "e satisfação dos colaboradores. Você sempre responde em português brasileiro de forma clara e profissional."
        ),
        tools=get_hr_tools(),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

