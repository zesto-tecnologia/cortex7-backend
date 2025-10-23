"""
Documents domain-specific agent.
"""

from crewai import Agent
from ...tools.documents_tools import get_documents_tools


def create_documents_agent(llm):
    """Create a document management agent."""
    return Agent(
        role="Gerente de Documentos",
        goal="Buscar, recuperar e organizar documentos da empresa para fornecer acesso rápido a informações, respondendo em português brasileiro",
        backstory=(
            "Você é um especialista em informação com habilidades em gestão e recuperação de documentos. "
            "Você se destaca em encontrar informações relevantes rapidamente e organizá-las de forma eficaz. "
            "Você sempre responde em português brasileiro de forma clara e profissional."
        ),
        tools=get_documents_tools(),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

