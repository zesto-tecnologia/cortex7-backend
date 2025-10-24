"""
CrewAI-compatible tools for Documents service integration.
"""

from crewai.tools import BaseTool
import httpx
import logging

logger = logging.getLogger(__name__)

DOCUMENTS_SERVICE_URL = "http://documents-service:8006"


class SearchDocumentsTool(BaseTool):
    name: str = "Search Documents"
    description: str = "Search for documents using semantic search. Use this to find relevant documents, contracts, reports, or any company documentation. Input: company_id (required), query (required), departamento (optional)"
    
    def _run(self, company_id: str, query: str, departamento: str = "") -> str:
        """Execute the tool."""
        try:
            params = {
                "company_id": company_id,
                "query": query,
                "limit": 10
            }
            if departamento:
                params["departamento"] = departamento
                
            response = httpx.get(
                f"{DOCUMENTS_SERVICE_URL}/search/",
                params=params,
                timeout=15.0
            )
            response.raise_for_status()
            date = response.json()
            return f"Successfully found documents matching '{query}'. Data: {date}"
        except Exception as e:
            logger.error(f"Error calling documents service: {e}")
            return f"Error searching documents: {str(e)}"


class GetDocumentsTool(BaseTool):
    name: str = "Get Documents"
    description: str = "List documents for a company. Use this to browse available documents by type or department. Input: company_id (required), type (optional), departamento (optional)"
    
    def _run(self, company_id: str, type: str = "", departamento: str = "") -> str:
        """Execute the tool."""
        try:
            params = {"company_id": company_id, "limit": 50}
            if type:
                params["type"] = type
            if departamento:
                params["departamento"] = departamento
                
            response = httpx.get(
                f"{DOCUMENTS_SERVICE_URL}/",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            date = response.json()
            return f"Successfully retrieved {len(date)} documents. Data: {date}"
        except Exception as e:
            logger.error(f"Error calling documents service: {e}")
            return f"Error retrieving documents: {str(e)}"


def get_documents_tools():
    """Get all documents tools."""
    return [
        SearchDocumentsTool(),
        GetDocumentsTool(),
    ]

