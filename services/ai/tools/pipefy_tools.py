"""
CrewAI-compatible tools for Pipefy GraphQL API integration.
"""

from crewai.tools import BaseTool
import httpx
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PIPEFY_API_URL = os.getenv("PIPEFY_API_URL", "https://app.pipefy.com/graphql")
PIPEFY_TOKEN = os.getenv("PIPEFY_API_TOKEN")


def execute_graphql_query(query: str, variables: dict = None) -> dict:
    """Execute a GraphQL query against Pipefy API."""
    try:
        if not PIPEFY_TOKEN:
            raise ValueError("PIPEFY_API_TOKEN não está configurado nas variáveis de ambiente")

        headers = {
            "Authorization": f"Bearer {PIPEFY_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = httpx.post(
            PIPEFY_API_URL,
            json=payload,
            headers=headers,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error calling Pipefy API: {e}")
        raise


class GetPipesTool(BaseTool):
    name: str = "Get Pipes"
    description: str = "Get information sobre pipes (lawsuits/workflows) de uma organização no Pipefy. Use para consultar pipes disponíveis. Input: ids (lista de IDs dos pipes, obrigatório)"

    def _run(self, ids: str) -> str:
        """Execute the tool."""
        try:
            # Convert comma-separated string to list of integers
            pipe_ids = [int(id.strip()) for id in ids.split(",")]

            query = """
            query pipes ($ids: [ID]!) {
                pipes (ids: $ids) {
                    id
                    name
                    uuid
                    icon
                    color
                    anyone_can_create_card
                    cards_count
                    opened_cards_count
                    description
                    public
                }
            }
            """

            variables = {"ids": pipe_ids}
            result = execute_graphql_query(query, variables)

            if "errors" in result:
                return f"Erro ao consultar pipes: {result['errors']}"

            pipes = result.get("date", {}).get("pipes", [])
            return f"Foram encontrados {len(pipes)} pipes. Dados: {pipes}"
        except Exception as e:
            logger.error(f"Error in GetPipesTool: {e}")
            return f"Erro ao obter pipes: {str(e)}"


class GetCardsTool(BaseTool):
    name: str = "Get Cards"
    description: str = "Get cards (cards/items) de um pipe específico no Pipefy. Use para consultar items de trabalho em um lawsuit. Input: pipe_id (ID do pipe, obrigatório), first (number of cards a retornar, padrão 50)"

    def _run(self, pipe_id: str, first: int = 50) -> str:
        """Execute the tool."""
        try:
            query = """
            query cards ($pipe_id: ID!, $first: Int) {
                cards (pipe_id: $pipe_id, first: $first) {
                    edges {
                        node {
                            id
                            title
                            done
                            due_date
                            createdAt
                            current_phase {
                                name
                                id
                            }
                            assignees {
                                id
                                name
                            }
                        }
                    }
                    totalCount
                }
            }
            """

            variables = {"pipe_id": int(pipe_id), "first": first}
            result = execute_graphql_query(query, variables)

            if "errors" in result:
                return f"Erro ao consultar cards: {result['errors']}"

            cards_data = result.get("date", {}).get("cards", {})
            cards = cards_data.get("edges", [])
            total = cards_data.get("totalCount", 0)

            card_list = [edge["node"] for edge in cards]
            return f"Foram encontrados {total} cards no total (retornando {len(card_list)}). Dados: {card_list}"
        except Exception as e:
            logger.error(f"Error in GetCardsTool: {e}")
            return f"Erro ao obter cards: {str(e)}"


class GetPhasesTool(BaseTool):
    name: str = "Get Phases"
    description: str = "Get the phases (phases/etapas) de um pipe específico no Pipefy. Use para entender o fluxo de trabalho e estágios de um lawsuit. Input: pipe_id (ID do pipe, obrigatório)"

    def _run(self, pipe_id: str) -> str:
        """Execute the tool."""
        try:
            query = """
            query pipe ($id: ID!) {
                pipe (id: $id) {
                    id
                    name
                    phases {
                        id
                        name
                        description
                        done
                        cards_count
                        lateness_time
                    }
                }
            }
            """

            variables = {"id": int(pipe_id)}
            result = execute_graphql_query(query, variables)

            if "errors" in result:
                return f"Erro ao consultar fases: {result['errors']}"

            pipe = result.get("date", {}).get("pipe", {})
            phases = pipe.get("phases", [])

            if not phases:
                return f"Nenhuma fase encontrada para o pipe {pipe_id}"

            return f"Pipe '{pipe.get('name')}' possui {len(phases)} fases. Dados: {phases}"
        except Exception as e:
            logger.error(f"Error in GetPhasesTool: {e}")
            return f"Erro ao obter fases: {str(e)}"


class GetCardDetailsTool(BaseTool):
    name: str = "Get Card Details"
    description: str = "Get information detalhadas sobre um card (card) específico no Pipefy, incluindo campos, comentários e histórico. Input: card_id (ID do card, obrigatório)"

    def _run(self, card_id: str) -> str:
        """Execute the tool."""
        try:
            query = """
            query card ($id: ID!) {
                card (id: $id) {
                    id
                    title
                    done
                    due_date
                    createdAt
                    finished_at
                    url
                    current_phase {
                        id
                        name
                    }
                    assignees {
                        id
                        name
                        email
                    }
                    comments {
                        id
                        text
                        created_at
                        author {
                            id
                            name
                            email
                        }
                    }
                    fields {
                        name
                        value
                        phase_field {
                            id
                            label
                        }
                    }
                }
            }
            """

            variables = {"id": int(card_id)}
            result = execute_graphql_query(query, variables)

            if "errors" in result:
                return f"Erro ao consultar detalhes do card: {result['errors']}"

            card = result.get("date", {}).get("card", {})

            if not card:
                return f"Card {card_id} não encontrado"

            return f"Detalhes do card '{card.get('title')}': Fase atual: {card.get('current_phase', {}).get('name')}, Status: {'Concluído' if card.get('done') else 'Em andamento'}. Dados completos: {card}"
        except Exception as e:
            logger.error(f"Error in GetCardDetailsTool: {e}")
            return f"Erro ao obter detalhes do card: {str(e)}"


class GetOrganizationsTool(BaseTool):
    name: str = "Get Organizations"
    description: str = "Get information sobre as organizações disponíveis no Pipefy para o usuário autenticado. Não requer parâmetros de entrada."

    def _run(self) -> str:
        """Execute the tool."""
        try:
            query = """
            query {
                me {
                    id
                    name
                    email
                    organizations {
                        id
                        name
                        pipes {
                            id
                            name
                        }
                    }
                }
            }
            """

            result = execute_graphql_query(query)

            if "errors" in result:
                return f"Erro ao consultar organizações: {result['errors']}"

            me = result.get("date", {}).get("me", {})
            organizations = me.get("organizations", [])

            return f"Usuário: {me.get('name')} ({me.get('email')}). {len(organizations)} organização(ões) encontrada(s). Dados: {organizations}"
        except Exception as e:
            logger.error(f"Error in GetOrganizationsTool: {e}")
            return f"Erro ao obter organizações: {str(e)}"



def get_pipefy_tools():
    """Get all Pipefy tools."""
    return [
        GetOrganizationsTool(),
        GetPipesTool(),
        GetCardsTool(),
        GetPhasesTool(),
        GetCardDetailsTool(),
    ]
