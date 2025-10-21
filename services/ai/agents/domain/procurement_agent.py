"""
Procurement domain-specific agent.
"""

from crewai import Agent
from ...tools.procurement_tools import get_procurement_tools


def create_procurement_agent(llm):
    """Create a procurement management agent."""
    return Agent(
        role="Procurement Specialist",
        goal="Manage purchase orders and approval workflows to ensure efficient procurement operations",
        backstory=(
            "You are a procurement expert with experience in supply chain management, "
            "vendor relations, and approval workflows. You optimize purchasing processes "
            "and ensure timely approvals."
        ),
        tools=get_procurement_tools(),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

