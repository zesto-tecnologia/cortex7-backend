"""
CrewAI-compatible tools for HR service integration.
"""

from crewai.tools import BaseTool
import httpx
import logging

logger = logging.getLogger(__name__)

HR_SERVICE_URL = "http://hr-service:8003"


class GetEmployeesTool(BaseTool):
    name: str = "Get Employees"
    description: str = "Get employees (employees) for a company. Use this to check employee information, department assignments, and staff details. Input: company_id (required), department (optional)"
    
    def _run(self, company_id: str, department: str = "") -> str:
        """Execute the tool."""
        try:
            params = {"company_id": company_id, "limit": 100}
            if department:
                params["department"] = department
                
            response = httpx.get(
                f"{HR_SERVICE_URL}/employees/",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return f"Successfully retrieved {len(data)} employees. Data: {data}"
        except Exception as e:
            logger.error(f"Error calling HR service: {e}")
            return f"Error retrieving employees: {str(e)}"


class GetVacationTool(BaseTool):
    name: str = "Get Vacation"
    description: str = "Get vacation information (vacation) for a specific employee. Use this to check vacation balance, used days, and vacation history. Input: employee_id (required UUID)"
    
    def _run(self, employee_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{HR_SERVICE_URL}/vacation/employee/{employee_id}",
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return f"Successfully retrieved vacation date for employee. Available days: {data.get('available_days', 'N/A')}, Used days: {data.get('used_days', 'N/A')}. Full date: {data}"
        except Exception as e:
            logger.error(f"Error calling HR service: {e}")
            return f"Error retrieving vacation date: {str(e)}"


class GetEmploymentContractsTool(BaseTool):
    name: str = "Get Employment Contracts"
    description: str = "Get employment contracts (employment contracts) for a specific employee. Use this to check contract details, terms, and employment agreements. Input: employee_id (required UUID)"
    
    def _run(self, employee_id: str) -> str:
        """Execute the tool."""
        try:
            response = httpx.get(
                f"{HR_SERVICE_URL}/employment-contracts/employee/{employee_id}",
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No contracts found for employee {employee_id}"
            return f"Successfully retrieved {len(data)} employment contract(s) for employee. Data: {data}"
        except Exception as e:
            logger.error(f"Error calling HR service: {e}")
            return f"Error retrieving contracts: {str(e)}"


def get_hr_tools():
    """Get all HR tools."""
    return [
        GetEmployeesTool(),
        GetVacationTool(),
        GetEmploymentContractsTool(),
    ]
