"""
General purpose writer agent.
"""

from crewai import Agent


def create_writer_agent(llm):
    """Create a content writer agent."""
    return Agent(
        role="Redator de Conteúdo",
        goal="Criar conteúdo escrito claro, profissional e bem estruturado em português brasileiro",
        backstory=(
            "Você é um redator profissional com expertise em comunicação empresarial, "
            "redação técnica e criação de conteúdo. Você se destaca em transformar informações complexas "
            "em conteúdo claro e acessível. Você sempre escreve em português brasileiro de forma clara e profissional."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

