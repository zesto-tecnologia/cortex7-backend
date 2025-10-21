"""
General purpose analyst agent.
"""

from crewai import Agent


def create_analyst_agent(llm):
    """Create a data analyst agent."""
    return Agent(
        role="Data Analyst",
        goal="Analyze data, identify patterns, and provide actionable insights and recommendations",
        backstory=(
            "You are a skilled data analyst with expertise in statistical analysis, "
            "trend identification, and business intelligence. You transform raw data "
            "into meaningful insights that drive decision-making."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )
