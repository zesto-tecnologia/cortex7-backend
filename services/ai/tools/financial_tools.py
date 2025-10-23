"""
CrewAI-compatible tools for Financial service integration.
"""

from crewai.tools import BaseTool
import httpx
import logging

logger = logging.getLogger(__name__)

FINANCIAL_SERVICE_URL = "http://financial-service:8002"


class GetContasPagarTool(BaseTool):
    name: str = "Get Contas Pagar"
    description: str = "Get accounts payable (contas a pagar) for a company. Use this when you need to check bills, payments due, or payables information. Input: empresa_id (required UUID string)"
    
    def _run(self, empresa_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{FINANCIAL_SERVICE_URL}/contas-pagar/",
                params={"empresa_id": empresa_id, "limit": 100},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No accounts payable found for company {empresa_id}"
            return f"Successfully retrieved {len(data)} accounts payable. Data: {data}"
        except Exception as e:
            logger.error(f"Error calling financial service: {e}")
            return f"Error retrieving accounts payable: {str(e)}"


class GetFornecedoresTool(BaseTool):
    name: str = "Get Fornecedores"
    description: str = "Get suppliers (fornecedores) for a company. Use this to get supplier information, contacts, and details. Input: empresa_id (required UUID string)"
    
    def _run(self, empresa_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{FINANCIAL_SERVICE_URL}/fornecedores/",
                params={"empresa_id": empresa_id, "limit": 100},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No suppliers found for company {empresa_id}"
            return f"Successfully retrieved {len(data)} supplier(s). Data: {data}"
        except Exception as e:
            logger.error(f"Error calling financial service: {e}")
            return f"Error retrieving suppliers: {str(e)}"


class GetCentrosCustoTool(BaseTool):
    name: str = "Get Centros Custo"
    description: str = "Get cost centers (centros de custo) for a company. Use this to check budgets, departmental spending, and cost allocation. Input: empresa_id (required UUID string)"
    
    def _run(self, empresa_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{FINANCIAL_SERVICE_URL}/centros-custo/",
                params={"empresa_id": empresa_id},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No cost centers found for company {empresa_id}"
            return f"Successfully retrieved cost centers. Data: {data}"
        except Exception as e:
            logger.error(f"Error calling financial service: {e}")
            return f"Error retrieving cost centers: {str(e)}"


def get_financial_tools():
    """Get all financial tools."""
    return [
        GetContasPagarTool(),
        GetFornecedoresTool(),
        GetCentrosCustoTool(),
    ]
