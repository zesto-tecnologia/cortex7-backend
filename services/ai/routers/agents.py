"""
Agent and crew information endpoints.
"""

from fastapi import APIRouter

from ..schemas.agent import (
    AgentInfo,
    CrewInfo,
    AvailableAgentsResponse,
    AvailableCrewsResponse,
)

router = APIRouter()


@router.get("/", response_model=AvailableAgentsResponse)
async def list_available_agents():
    """List all available AI agents."""
    
    domain_agents = [
        AgentInfo(
            name="Financial Analyst",
            role="Financial Analyst",
            goal="Analyze financial data, accounts payable, suppliers, and cost centers",
            backstory="Experienced financial analyst with expertise in accounts payable and cost management",
            type="domain"
        ),
        AgentInfo(
            name="HR Manager",
            role="HR Manager",
            goal="Manage employee information, vacation requests, and employment contracts",
            backstory="Skilled HR professional with knowledge of employment law and benefits management",
            type="domain"
        ),
        AgentInfo(
            name="Legal Advisor",
            role="Legal Advisor",
            goal="Monitor legal contracts, deadlines, and processes to ensure compliance",
            backstory="Corporate legal expert specializing in contract management and compliance",
            type="domain"
        ),
        AgentInfo(
            name="Document Manager",
            role="Document Manager",
            goal="Search, retrieve, and organize company documents",
            backstory="Information specialist skilled in document management and retrieval",
            type="domain"
        ),
        AgentInfo(
            name="Procurement Specialist",
            role="Procurement Specialist",
            goal="Manage purchase orders and approval workflows",
            backstory="Procurement expert with experience in supply chain management",
            type="domain"
        ),
    ]
    
    general_agents = [
        AgentInfo(
            name="Research Specialist",
            role="Research Specialist",
            goal="Find and synthesize information from various sources",
            backstory="Expert researcher skilled at gathering and organizing information",
            type="general"
        ),
        AgentInfo(
            name="Data Analyst",
            role="Data Analyst",
            goal="Analyze data and provide actionable insights",
            backstory="Skilled analyst with expertise in pattern identification and business intelligence",
            type="general"
        ),
        AgentInfo(
            name="Content Writer",
            role="Content Writer",
            goal="Create clear, professional, and well-structured content",
            backstory="Professional writer with expertise in business communication",
            type="general"
        ),
    ]
    
    return AvailableAgentsResponse(
        domain_agents=domain_agents,
        general_agents=general_agents
    )


@router.get("/crews", response_model=AvailableCrewsResponse)
async def list_available_crews():
    """List all available agent crews (teams)."""
    
    crews = [
        CrewInfo(
            name="Financial Analysis Crew",
            description="Team specialized in comprehensive financial analysis",
            agents=["Financial Analyst", "Data Analyst"],
            use_case="Accounts payable analysis, supplier analysis, cost center review"
        ),
        CrewInfo(
            name="Document Review Crew",
            description="Team for document analysis and review",
            agents=["Document Manager", "Data Analyst", "Content Writer"],
            use_case="Document compliance review, content summarization, document analysis"
        ),
        CrewInfo(
            name="General Task Crew",
            description="Versatile team that adapts to various business tasks",
            agents=["Dynamic selection based on task", "Data Analyst", "Content Writer"],
            use_case="General business queries, multi-domain tasks, ad-hoc analysis"
        ),
    ]
    
    return AvailableCrewsResponse(crews=crews)

