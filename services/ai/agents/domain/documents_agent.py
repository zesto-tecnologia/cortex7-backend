"""
Documents domain-specific agent.
"""

from crewai import Agent
from ...tools.documents_tools import get_documents_tools


def create_documents_agent(llm):
    """Create a document management agent."""
    return Agent(
        role="Document Manager",
        goal="Search, retrieve, and organize company documents to provide quick access to information",
        backstory=(
            "You are an information specialist skilled in document management and retrieval. "
            "You excel at finding relevant information quickly and organizing it effectively."
        ),
        tools=get_documents_tools(),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

