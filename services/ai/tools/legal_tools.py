"""
CrewAI-compatible tools for Legal service integration.
"""

from crewai.tools import BaseTool
import httpx
import logging

logger = logging.getLogger(__name__)

LEGAL_SERVICE_URL = "http://legal-service:8004"


class GetLegalContractsTool(BaseTool):
    name: str = "Get Legal Contracts"
    description: str = "Get legal contracts for a company. Use this to check contract details, terms, obligations, and legal agreements. Input: company_id (required UUID string)"
    
    def _run(self, company_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{LEGAL_SERVICE_URL}/legal-contracts/",
                params={"company_id": company_id, "limit": 100},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No legal contracts found for company {company_id}"
            return f"Successfully retrieved {len(data)} legal contract(s). Data: {data}"
        except Exception as e:
            logger.error(f"Error calling legal service: {e}")
            return f"Error retrieving legal contracts: {str(e)}"


class GetLegalDeadlinesTool(BaseTool):
    name: str = "Get Legal Deadlines"
    description: str = "Get legal deadlines (deadlines) for a company. Use this to check upcoming deadlines, critical dates, and legal obligations. Input: company_id (required UUID string)"
    
    def _run(self, company_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{LEGAL_SERVICE_URL}/legal-deadlines/{company_id}",
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            total_deadlines = data.get('total_deadlines', 0)
            return f"Successfully retrieved {total_deadlines} legal deadline(s). Data: {data}"
        except Exception as e:
            logger.error(f"Error calling legal service: {e}")
            return f"Error retrieving deadlines: {str(e)}"


class GetLegalLawsuitsTool(BaseTool):
    name: str = "Get Legal Lawsuits"
    description: str = "Get legal lawsuits (lawsuits) for a company. Use this to check ongoing legal cases, their status, and details. Input: company_id (required UUID string)"
    
    def _run(self, company_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{LEGAL_SERVICE_URL}/legal-lawsuits/",
                params={"company_id": company_id, "limit": 100},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No legal lawsuits found for company {company_id}"
            return f"Successfully retrieved {len(data)} legal lawsuit(s). Data: {data}"
        except Exception as e:
            logger.error(f"Error calling legal service: {e}")
            return f"Error retrieving legal lawsuits: {str(e)}"


def get_legal_tools():
    """Get all legal tools."""
    return [
        GetLegalContractsTool(),
        GetLegalDeadlinesTool(),
        GetLegalLawsuitsTool(),
    ]

