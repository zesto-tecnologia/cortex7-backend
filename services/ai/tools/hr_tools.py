"""
CrewAI-compatible tools for HR service integration.
"""

from crewai.tools import BaseTool
import httpx
import logging

logger = logging.getLogger(__name__)

HR_SERVICE_URL = "http://hr-service:8003"


class GetFuncionariosTool(BaseTool):
    name: str = "Get Funcionarios"
    description: str = "Get employees (funcionários) for a company. Use this to check employee information, department assignments, and staff details. Input: empresa_id (required), departamento (optional)"
    
    def _run(self, empresa_id: str, departamento: str = "") -> str:
        """Execute the tool."""
        try:
            params = {"empresa_id": empresa_id, "limit": 100}
            if departamento:
                params["departamento"] = departamento
                
            response = httpx.get(
                f"{HR_SERVICE_URL}/funcionarios/",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return f"Successfully retrieved {len(data)} employees. Data: {data}"
        except Exception as e:
            logger.error(f"Error calling HR service: {e}")
            return f"Error retrieving employees: {str(e)}"


class GetFeriasTool(BaseTool):
    name: str = "Get Ferias"
    description: str = "Get vacation information (férias) for a specific employee. Use this to check vacation balance, used days, and vacation history. Input: funcionario_id (required UUID)"
    
    def _run(self, funcionario_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{HR_SERVICE_URL}/ferias/funcionario/{funcionario_id}",
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return f"Successfully retrieved vacation data for employee. Available days: {data.get('dias_disponiveis', 'N/A')}, Used days: {data.get('dias_utilizados', 'N/A')}. Full data: {data}"
        except Exception as e:
            logger.error(f"Error calling HR service: {e}")
            return f"Error retrieving vacation data: {str(e)}"


class GetContratosTool(BaseTool):
    name: str = "Get Contratos Trabalhistas"
    description: str = "Get employment contracts (contratos de trabalho) for a specific employee. Use this to check contract details, terms, and employment agreements. Input: funcionario_id (required UUID)"
    
    def _run(self, funcionario_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{HR_SERVICE_URL}/contratos/funcionario/{funcionario_id}",
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No contracts found for employee {funcionario_id}"
            return f"Successfully retrieved {len(data)} employment contract(s) for employee. Data: {data}"
        except Exception as e:
            logger.error(f"Error calling HR service: {e}")
            return f"Error retrieving contracts: {str(e)}"


def get_hr_tools():
    """Get all HR tools."""
    return [
        GetFuncionariosTool(),
        GetFeriasTool(),
        GetContratosTool(),
    ]
