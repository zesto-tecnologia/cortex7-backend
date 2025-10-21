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
    description: str = "Get legal contracts for a company. Use this to check contract details, terms, obligations, and legal agreements. Input: empresa_id (required UUID string)"
    
    def _run(self, empresa_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{LEGAL_SERVICE_URL}/contratos/",
                params={"empresa_id": empresa_id, "limit": 100},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No legal contracts found for company {empresa_id}"
            return f"Successfully retrieved {len(data)} legal contract(s). Data: {data}"
        except Exception as e:
            logger.error(f"Error calling legal service: {e}")
            return f"Error retrieving legal contracts: {str(e)}"


class GetPrazosLegaisTool(BaseTool):
    name: str = "Get Prazos Legais"
    description: str = "Get legal deadlines (prazos) for a company. Use this to check upcoming deadlines, critical dates, and legal obligations. Input: empresa_id (required UUID string)"
    
    def _run(self, empresa_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{LEGAL_SERVICE_URL}/prazos/todos/{empresa_id}",
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            total_prazos = data.get('total_prazos', 0)
            return f"Successfully retrieved {total_prazos} legal deadline(s). Data: {data}"
        except Exception as e:
            logger.error(f"Error calling legal service: {e}")
            return f"Error retrieving deadlines: {str(e)}"


class GetProcessosLegaisTool(BaseTool):
    name: str = "Get Processos Legais"
    description: str = "Get legal processes (lawsuits, litigation) for a company. Use this to check ongoing legal cases, their status, and details. Input: empresa_id (required UUID string)"
    
    def _run(self, empresa_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{LEGAL_SERVICE_URL}/processos/",
                params={"empresa_id": empresa_id, "limit": 100},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No legal processes found for company {empresa_id}"
            return f"Successfully retrieved {len(data)} legal process(es). Data: {data}"
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

