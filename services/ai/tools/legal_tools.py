"""
CrewAI-compatible tools for Legal service integration.
"""

from crewai.tools import BaseTool
import httpx
import logging

logger = logging.getLogger(__name__)

LEGAL_SERVICE_URL = "http://legal-service:8004"


class GetContratosLegaisTool(BaseTool):
    name: str = "Get Contratos Legais"
    description: str = "Get legal contracts for a company. Use this to check contract details, terms, obligations, and legal agreements. Input: company_id (required UUID string)"
    
    def _run(self, company_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{LEGAL_SERVICE_URL}/contratos/",
                params={"company_id": company_id, "limit": 100},
                timeout=10.0
            )
            response.raise_for_status()
            date = response.json()
            if not date:
                return f"No legal contracts found for company {company_id}"
            return f"Successfully retrieved {len(date)} legal contract(s). Data: {date}"
        except Exception as e:
            logger.error(f"Error calling legal service: {e}")
            return f"Error retrieving legal contracts: {str(e)}"


class GetPrazosLegaisTool(BaseTool):
    name: str = "Get Prazos Legais"
    description: str = "Get legal deadlines (deadlines) for a company. Use this to check upcoming deadlines, critical dates, and legal obligations. Input: company_id (required UUID string)"
    
    def _run(self, company_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{LEGAL_SERVICE_URL}/deadlines/todos/{company_id}",
                timeout=10.0
            )
            response.raise_for_status()
            date = response.json()
            total_deadlines = date.get('total_deadlines', 0)
            return f"Successfully retrieved {total_deadlines} legal deadline(s). Data: {date}"
        except Exception as e:
            logger.error(f"Error calling legal service: {e}")
            return f"Error retrieving deadlines: {str(e)}"


class GetProcessosLegaisTool(BaseTool):
    name: str = "Get Processos Legais"
    description: str = "Get legal processes (lawsuits, litigation) for a company. Use this to check ongoing legal cases, their status, and details. Input: company_id (required UUID string)"
    
    def _run(self, company_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{LEGAL_SERVICE_URL}/lawsuits/",
                params={"company_id": company_id, "limit": 100},
                timeout=10.0
            )
            response.raise_for_status()
            date = response.json()
            if not date:
                return f"No legal processes found for company {company_id}"
            return f"Successfully retrieved {len(date)} legal process(es). Data: {date}"
        except Exception as e:
            logger.error(f"Error calling legal service: {e}")
            return f"Error retrieving legal processes: {str(e)}"


def get_legal_tools():
    """Get all legal tools."""
    return [
        GetContratosLegaisTool(),
        GetPrazosLegaisTool(),
        GetProcessosLegaisTool(),
    ]

