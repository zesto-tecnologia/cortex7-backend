"""
CrewAI-compatible tools for Financial service integration.
"""

from crewai.tools import BaseTool
import httpx
import logging

logger = logging.getLogger(__name__)

FINANCIAL_SERVICE_URL = "http://financial-service:8002"


class GetAccountsPayableTool(BaseTool):
    name: str = "Get Accounts Payable"
    description: str = "Get accounts payable (accounts payable) for a company. Use this when you need to check bills, payments due, or payables information. Input: company_id (required UUID string)"
    
    def _run(self, company_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{FINANCIAL_SERVICE_URL}/accounts-payable/",
                params={"company_id": company_id, "limit": 100},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No accounts payable found for company {company_id}"
            return f"Successfully retrieved {len(data)} accounts payable. Data: {data}"
        except Exception as e:
            logger.error(f"Error calling financial service: {e}")
            return f"Error retrieving accounts payable: {str(e)}"


class GetSuppliersTool(BaseTool):
    name: str = "Get Suppliers"
    description: str = "Get suppliers (suppliers) for a company. Use this to get supplier information, contacts, and details. Input: company_id (required UUID string)"
    
    def _run(self, company_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{FINANCIAL_SERVICE_URL}/suppliers/",
                params={"company_id": company_id, "limit": 100},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No suppliers found for company {company_id}"
            return f"Successfully retrieved {len(data)} supplier(s). Data: {data}"
        except Exception as e:
            logger.error(f"Error calling financial service: {e}")
            return f"Error retrieving suppliers: {str(e)}"


class GetCostCentersTool(BaseTool):
    name: str = "Get Cost Centers"
    description: str = "Get cost centers (centros de custo) for a company. Use this to check budgets, departmental spending, and cost allocation. Input: company_id (required UUID string)"
    
    def _run(self, company_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{FINANCIAL_SERVICE_URL}/cost-centers/",
                params={"company_id": company_id},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No cost centers found for company {company_id}"
            return f"Successfully retrieved cost centers. Data: {data}"
        except Exception as e:
            logger.error(f"Error calling financial service: {e}")
            return f"Error retrieving cost centers: {str(e)}"


def get_financial_tools():
    """Get all financial tools."""
    return [
        GetAccountsPayableTool(),
        GetSuppliersTool(),
        GetCostCentersTool(),
    ]
