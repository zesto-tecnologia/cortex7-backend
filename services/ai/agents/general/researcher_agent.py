"""
General purpose researcher agent.
"""

from crewai import Agent


def create_researcher_agent(llm):
    """Create a research specialist agent."""
    return Agent(
        role="Especialista em Pesquisa",
        goal="Encontrar e sintetizar informações de várias fontes para responder perguntas e fornecer pesquisa abrangente em português brasileiro",
        backstory=(
            "Você é um pesquisador especialista habilidoso em encontrar informações precisas "
            "de múltiplas fontes, avaliar credibilidade e sintetizar descobertas "
            "em insights claros e acionáveis. Você se destaca em coletar dados e "
            "apresentá-los de forma organizada. Você sempre responde em português brasileiro de forma clara e profissional."
        ),
        tools=[],  # No external tools for now to avoid compatibility issues
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

