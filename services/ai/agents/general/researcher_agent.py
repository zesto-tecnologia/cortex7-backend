"""
General purpose researcher agent.
"""

from crewai import Agent


def create_researcher_agent(llm):
    """Create a research specialist agent."""
    return Agent(
        role="Research Specialist",
        goal="Find and synthesize information from various sources to answer questions and provide comprehensive research",
        backstory=(
            "You are an expert researcher skilled at finding accurate information "
            "from multiple sources, evaluating credibility, and synthesizing findings "
            "into clear, actionable insights. You excel at gathering data and "
            "presenting it in an organized manner."
        ),
        tools=[],  # No external tools for now to avoid compatibility issues
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

