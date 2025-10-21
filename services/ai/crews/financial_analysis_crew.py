"""
Financial analysis crew for complex financial workflows.
"""

from crewai import Crew, Task
from ..agents.domain.financial_agent import create_financial_agent
from ..agents.general.analyst_agent import create_analyst_agent


def create_financial_analysis_crew(llm, empresa_id: str, analysis_type: str):
    """
    Create a crew for financial analysis workflows.
    
    Args:
        llm: Language model to use
        empresa_id: Company UUID
        analysis_type: Type of analysis (e.g., 'accounts_payable', 'supplier_analysis', 'cost_centers')
    """
    financial_agent = create_financial_agent(llm)
    analyst_agent = create_analyst_agent(llm)
    
    # Define tasks based on analysis type
    tasks = []
    
    if analysis_type == "accounts_payable":
        data_task = Task(
            description=f"Retrieve and summarize accounts payable data for company {empresa_id}. Focus on overdue payments, upcoming due dates, and payment priorities.",
            agent=financial_agent,
            expected_output="Summary of accounts payable with key insights about payment status and priorities"
        )
        
        analysis_task = Task(
            description="Analyze the accounts payable data to identify trends, risks, and recommendations for cash flow optimization.",
            agent=analyst_agent,
            expected_output="Detailed analysis with actionable recommendations for accounts payable management",
            context=[data_task]
        )
        
        tasks = [data_task, analysis_task]
    
    elif analysis_type == "supplier_analysis":
        data_task = Task(
            description=f"Retrieve supplier information and payment history for company {empresa_id}.",
            agent=financial_agent,
            expected_output="Summary of suppliers with payment patterns and relationships"
        )
        
        analysis_task = Task(
            description="Analyze supplier data to identify key partners, payment reliability, and opportunities for better terms.",
            agent=analyst_agent,
            expected_output="Supplier analysis report with recommendations",
            context=[data_task]
        )
        
        tasks = [data_task, analysis_task]
    
    else:  # general financial analysis
        data_task = Task(
            description=f"Retrieve comprehensive financial data including accounts payable, suppliers, and cost centers for company {empresa_id}.",
            agent=financial_agent,
            expected_output="Comprehensive financial data summary"
        )
        
        analysis_task = Task(
            description="Perform comprehensive financial analysis identifying strengths, weaknesses, and opportunities.",
            agent=analyst_agent,
            expected_output="Complete financial analysis report with strategic recommendations",
            context=[data_task]
        )
        
        tasks = [data_task, analysis_task]
    
    crew = Crew(
        agents=[financial_agent, analyst_agent],
        tasks=tasks,
        verbose=True,
    )
    
    return crew

