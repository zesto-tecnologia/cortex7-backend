"""
General purpose writer agent.
"""

from crewai import Agent


def create_writer_agent(llm):
    """Create a content writer agent."""
    return Agent(
        role="Content Writer",
        goal="Create clear, professional, and well-structured written content",
        backstory=(
            "You are a professional writer with expertise in business communication, "
            "technical writing, and content creation. You excel at transforming complex "
            "information into clear, accessible content."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

