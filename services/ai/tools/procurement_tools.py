"""
CrewAI-compatible tools for Procurement service integration.
"""

from crewai.tools import BaseTool
import httpx
import logging

logger = logging.getLogger(__name__)

PROCUREMENT_SERVICE_URL = "http://procurement-service:8005"


class GetOrdensCompraTool(BaseTool):
    name: str = "Get Ordens Compra"
    description: str = "Get purchase orders (ordens de compra) for a company. Use this to check purchase orders, their status, and procurement details. Input: empresa_id (required), status (optional)"
    
    def _run(self, empresa_id: str, status: str = "") -> str:
        """Execute the tool."""
        try:
            params = {"empresa_id": empresa_id}
            if status:
                params["status"] = status
                
            response = httpx.get(
                f"{PROCUREMENT_SERVICE_URL}/ordens-compra/",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return f"Successfully retrieved purchase orders. Data: {data}"
        except Exception as e:
            logger.error(f"Error calling procurement service: {e}")
            return f"Error retrieving purchase orders: {str(e)}"


class GetAprovacoesPendentesTool(BaseTool):
    name: str = "Get Aprovacoes Pendentes"
    description: str = "Get pending approvals for purchase orders. Use this to check what orders need approval and their approval status. Input: empresa_id (required)"
    
    def _run(self, empresa_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{PROCUREMENT_SERVICE_URL}/aprovacoes/",
                params={"empresa_id": empresa_id, "status": "pendente"},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return f"Successfully retrieved pending approvals. Data: {data}"
        except Exception as e:
            logger.error(f"Error calling procurement service: {e}")
            return f"Error retrieving pending approvals: {str(e)}"


def get_procurement_tools():
    """Get all procurement tools."""
    return [
        GetOrdensCompraTool(),
        GetAprovacoesPendentesTool(),
    ]

