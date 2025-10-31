"""
CrewAI-compatible tools for Procurement service integration.
"""

from crewai.tools import BaseTool
import httpx
import logging

logger = logging.getLogger(__name__)

PROCUREMENT_SERVICE_URL = "http://procurement-service:8005"


class GetPurchaseOrdersTool(BaseTool):
    name: str = "Get Purchase Orders"
    description: str = "Get purchase orders (purchase orders) for a company. Use this to check purchase orders, their status, and procurement details. Input: company_id (required), status (optional)"
    
    def _run(self, company_id: str, status: str = "") -> str:
        """Execute the tool."""
        try:
            params = {"company_id": company_id}
            if status:
                params["status"] = status
                
            response = httpx.get(
                f"{PROCUREMENT_SERVICE_URL}/purchase-orders/",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return f"Successfully retrieved purchase orders. Data: {data}"
        except Exception as e:
            logger.error(f"Error calling procurement service: {e}")
            return f"Error retrieving purchase orders: {str(e)}"


class GetPendingApprovalsTool(BaseTool):
    name: str = "Get Pending Approvals"
    description: str = "Get pending approvals for purchase orders. Use this to check what orders need approval and their approval status. Input: company_id (required)"
    
    def _run(self, company_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{PROCUREMENT_SERVICE_URL}/pending-approvals/",
                params={"company_id": company_id, "status": "pendente"},
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
        GetPurchaseOrdersTool(),
        GetPendingApprovalsTool(),
    ]

