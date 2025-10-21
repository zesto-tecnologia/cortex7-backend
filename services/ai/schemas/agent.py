"""
Pydantic schemas for AI agents and crews.
"""

from pydantic import BaseModel
from typing import List, Optional


class AgentInfo(BaseModel):
    """Information about an available agent."""
    name: str
    role: str
    goal: str
    backstory: str
    type: str  # domain or general


class CrewInfo(BaseModel):
    """Information about an available crew."""
    name: str
    description: str
    agents: List[str]
    use_case: str


class AvailableAgentsResponse(BaseModel):
    """Response with all available agents."""
    domain_agents: List[AgentInfo]
    general_agents: List[AgentInfo]


class AvailableCrewsResponse(BaseModel):
    """Response with all available crews."""
    crews: List[CrewInfo]

