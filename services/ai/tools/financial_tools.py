"""
LangChain tools for Financial service integration.
"""

from langchain_core.tools import BaseTool
from typing import Optional, Type, Any
from pydantic import BaseModel, Field
import httpx
import logging

logger = logging.getLogger(__name__)

FINANCIAL_SERVICE_URL = "http://financial-service:8002"


class GetContasPagarInput(BaseModel):
    """Input for GetContasPagarTool."""
    empresa_id: str = Field(..., description="Company UUID")
    status: Optional[str] = Field(None, description="Filter by status: pendente, aprovado, pago, cancelado")


class GetContasPagarTool(BaseTool):
    name: str = "get_contas_pagar"
    description: str = "Get accounts payable (contas a pagar) for a company. Use this when you need to check bills, payments due, or payables information."
    args_schema: Type[BaseModel] = GetContasPagarInput
    
    def _run(self, empresa_id: str, status: Optional[str] = None) -> dict:
        """Execute the tool."""
        try:
            params = {"empresa_id": empresa_id, "limit": 100}
            if status:
                params["status"] = status
                
            response = httpx.get(
                f"{FINANCIAL_SERVICE_URL}/contas-pagar/",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Error calling financial service: {e}")
            return {"success": False, "error": str(e)}


class GetFornecedoresInput(BaseModel):
    """Input for GetFornecedoresTool."""
    empresa_id: str = Field(..., description="Company UUID")


class GetFornecedoresTool(BaseTool):
    name: str = "get_fornecedores"
    description: str = "Get suppliers (fornecedores) for a company. Use this to get supplier information, contacts, and details."
    args_schema: Type[BaseModel] = GetFornecedoresInput
    
    def _run(self, empresa_id: str) -> dict:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{FINANCIAL_SERVICE_URL}/fornecedores/",
                params={"empresa_id": empresa_id, "limit": 100},
                timeout=10.0
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Error calling financial service: {e}")
            return {"success": False, "error": str(e)}


class GetCentrosCustoInput(BaseModel):
    """Input for GetCentrosCustoTool."""
    empresa_id: str = Field(..., description="Company UUID")


class GetCentrosCustoTool(BaseTool):
    name: str = "get_centros_custo"
    description: str = "Get cost centers (centros de custo) for a company. Use this to check budgets, departmental spending, and cost allocation."
    args_schema: Type[BaseModel] = GetCentrosCustoInput
    
    def _run(self, empresa_id: str) -> dict:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{FINANCIAL_SERVICE_URL}/centros-custo/",
                params={"empresa_id": empresa_id},
                timeout=10.0
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Error calling financial service: {e}")
            return {"success": False, "error": str(e)}


def get_financial_tools():
    """Get all financial tools."""
    return [
        GetContasPagarTool(),
        GetFornecedoresTool(),
        GetCentrosCustoTool(),
    ]

