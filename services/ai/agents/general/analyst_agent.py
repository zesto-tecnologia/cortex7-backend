"""
General purpose analyst agent.
"""

from crewai import Agent


def create_analyst_agent(llm):
    """Create a data analyst agent."""
    return Agent(
        role="Analista de Dados",
        goal="Analisar dados, identificar padrões e fornecer insights e recomendações acionáveis em português brasileiro",
        backstory=(
            "Você é um analista de dados qualificado com expertise em análise estatística, "
            "identificação de tendências e inteligência de negócios. Você transforma dados brutos "
            "em insights significativos que orientam a tomada de decisões. "
            "Você sempre responde em português brasileiro de forma clara e profissional."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )
