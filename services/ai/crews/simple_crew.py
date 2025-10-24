"""
Simple crew with a single default agent for straightforward queries.
"""

from crewai import Crew, Task, Agent


def create_simple_crew(llm, company_id: str, query: str):
    """
    Create a simple crew with a single versatile agent.
    
    Perfect for quick queries and simple tasks that don't require
    multiple agents or complex workflows.
    
    Args:
        llm: Language model to use
        company_id: Company UUID
        query: User query or task description
    """
    # Create a single versatile agent
    default_agent = Agent(
        role="Business Assistant",
        goal="Understand and respond to business queries with accurate, helpful information",
        backstory=(
            "You are a knowledgeable business assistant with access to company data "
            "across multiple departments. You provide clear, concise, and accurate "
            "responses to business questions and tasks."
        ),
        tools=[],  # Can be extended with tools if needed
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=10,
    )
    
    # Create a single task
    task = Task(
        description=f"For company {company_id}: {query}. Provide a clear and helpful response.",
        agent=default_agent,
        expected_output="Clear, accurate response to the query"
    )
    
    # Create crew with single agent and task
    crew = Crew(
        agents=[default_agent],
        tasks=[task],
        verbose=True,
    )
    
    return crew

