"""
HR domain-specific agent.
"""

from crewai import Agent
from ...tools.hr_tools import get_hr_tools


def create_hr_agent(llm):
    """Create an HR management agent."""
    return Agent(
        role="HR Manager",
        goal="Manage employee information, vacation requests, and employment contracts to ensure smooth HR operations",
        backstory=(
            "You are a skilled HR professional with deep knowledge of employment law, "
            "benefits management, and employee relations. You help ensure compliance "
            "and employee satisfaction."
        ),
        tools=get_hr_tools(),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

