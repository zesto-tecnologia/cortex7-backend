"""
Financial domain-specific agent.
"""

from crewai import Agent
from ...tools.financial_tools import get_financial_tools


def create_financial_agent(llm):
    """Create a financial analysis agent."""
    return Agent(
        role="Financial Analyst",
        goal="Analyze financial data, accounts payable, suppliers, and cost centers to provide insights and recommendations",
        backstory=(
            "You are an experienced financial analyst with expertise in accounts payable, "
            "supplier management, and cost center analysis. You excel at identifying trends, "
            "risks, and opportunities in financial data."
        ),
        tools=get_financial_tools(),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

