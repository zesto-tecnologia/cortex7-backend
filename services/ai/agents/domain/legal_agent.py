"""
Legal domain-specific agent.
"""

from crewai import Agent
from ...tools.legal_tools import get_legal_tools


def create_legal_agent(llm):
    """Create a legal advisory agent."""
    return Agent(
        role="Legal Advisor",
        goal="Monitor legal contracts, deadlines, and processes to ensure compliance and mitigate legal risks",
        backstory=(
            "You are a corporate legal expert specializing in contract management, "
            "litigation oversight, and compliance. You proactively identify legal risks "
            "and ensure all deadlines are met."
        ),
        tools=get_legal_tools(),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

