"""Unit tests for AI Service endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from uuid import uuid4


@pytest.mark.asyncio
class TestAIEndpoints:
    """Test suite for AI Service endpoints."""

    @pytest.fixture
    async def app(self):
        """Create FastAPI app instance."""
        from services.ai.main import app
        return app

    @pytest.fixture
    async def client(self, app, test_db_session):
        """Create test client with mocked dependencies."""
        app.dependency_overrides = {}

        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

        app.dependency_overrides = {}

    @pytest.fixture
    def valid_headers(self):
        """Valid auth headers for testing."""
        return {"Authorization": "Bearer valid_token"}

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        return MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="AI generated response for testing",
                        role="assistant"
                    )
                )
            ],
            usage=MagicMock(
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150
            )
        )

    # Test Chat endpoints
    @pytest.mark.unit
    async def test_chat_completion(self, client, valid_headers, mock_openai_response):
        """Test chat completion endpoint."""
        chat_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "Help me understand the company's procurement process"
                }
            ],
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 500
        }

        with patch("services.ai.routers.chat.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            with patch("services.ai.routers.chat.openai_client.chat.completions.create") as mock_chat:
                mock_chat.return_value = mock_openai_response

                response = await client.post(
                    "/ai/chat",
                    headers=valid_headers,
                    json=chat_data
                )

                assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_chat_with_context(self, client, valid_headers, mock_openai_response):
        """Test chat with document context."""
        chat_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "Summarize the contract terms"
                }
            ],
            "context": {
                "document_ids": [str(uuid4()), str(uuid4())],
                "include_embeddings": True
            },
            "model": "gpt-4"
        }

        with patch("services.ai.routers.chat.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            with patch("services.ai.routers.chat.openai_client.chat.completions.create") as mock_chat:
                mock_chat.return_value = mock_openai_response

                response = await client.post(
                    "/ai/chat/with-context",
                    headers=valid_headers,
                    json=chat_data
                )

                assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_streaming_chat(self, client, valid_headers):
        """Test streaming chat response."""
        chat_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "Explain the financial reports"
                }
            ],
            "stream": True,
            "model": "gpt-4"
        }

        with patch("services.ai.routers.chat.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            with patch("services.ai.routers.chat.openai_client.chat.completions.create") as mock_chat:
                # Mock streaming response
                mock_chat.return_value = AsyncMock()

                response = await client.post(
                    "/ai/chat/stream",
                    headers=valid_headers,
                    json=chat_data
                )

                assert response.status_code in [200, 401]

    # Test Workflows endpoints
    @pytest.mark.unit
    async def test_list_workflows(self, client, valid_headers):
        """Test listing workflows."""
        with patch("services.ai.routers.workflows.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/ai/workflows",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_workflow(self, client, valid_headers):
        """Test creating a new workflow."""
        workflow_data = {
            "name": "Invoice Processing Workflow",
            "description": "Automated workflow for processing invoices",
            "trigger_type": "document_upload",
            "trigger_conditions": {
                "document_type": "invoice",
                "min_amount": 1000
            },
            "steps": [
                {
                    "name": "Extract Invoice Data",
                    "type": "ai_extraction",
                    "config": {
                        "model": "gpt-4",
                        "fields": ["invoice_number", "amount", "due_date"]
                    }
                },
                {
                    "name": "Validate Data",
                    "type": "validation",
                    "config": {
                        "rules": ["amount > 0", "due_date > today"]
                    }
                },
                {
                    "name": "Create Approval Request",
                    "type": "approval",
                    "config": {
                        "approvers": ["finance_manager"],
                        "threshold": 5000
                    }
                }
            ],
            "status": "active"
        }

        with patch("services.ai.routers.workflows.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/ai/workflows",
                headers=valid_headers,
                json=workflow_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_execute_workflow(self, client, valid_headers):
        """Test executing a workflow."""
        workflow_id = str(uuid4())
        execution_data = {
            "input_data": {
                "document_id": str(uuid4()),
                "user_id": str(uuid4())
            },
            "execution_mode": "async"
        }

        with patch("services.ai.routers.workflows.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/ai/workflows/{workflow_id}/execute",
                headers=valid_headers,
                json=execution_data
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_get_workflow_execution_status(self, client, valid_headers):
        """Test getting workflow execution status."""
        workflow_id = str(uuid4())
        execution_id = str(uuid4())

        with patch("services.ai.routers.workflows.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/ai/workflows/{workflow_id}/executions/{execution_id}",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    # Test Agents endpoints
    @pytest.mark.unit
    async def test_list_agents(self, client, valid_headers):
        """Test listing AI agents."""
        with patch("services.ai.routers.agents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/ai/agents",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_agent(self, client, valid_headers):
        """Test creating a new AI agent."""
        agent_data = {
            "name": "Financial Analyst Agent",
            "role": "financial_analyst",
            "goal": "Analyze financial data and provide insights",
            "backstory": "Expert financial analyst with 10 years of experience",
            "tools": ["calculator", "data_analyzer", "report_generator"],
            "llm_config": {
                "model": "gpt-4",
                "temperature": 0.5,
                "max_tokens": 1000
            },
            "capabilities": ["financial_analysis", "report_generation", "forecasting"],
            "status": "active"
        }

        with patch("services.ai.routers.agents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/ai/agents",
                headers=valid_headers,
                json=agent_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_execute_agent_task(self, client, valid_headers, mock_openai_response):
        """Test executing an agent task."""
        agent_id = str(uuid4())
        task_data = {
            "task_description": "Analyze Q4 financial performance",
            "context": {
                "documents": [str(uuid4())],
                "data_sources": ["financial_db"],
                "time_period": "Q4 2024"
            },
            "output_format": "report"
        }

        with patch("services.ai.routers.agents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            with patch("services.ai.routers.agents.execute_agent") as mock_execute:
                mock_execute.return_value = {
                    "result": "Financial analysis completed",
                    "insights": ["Revenue increased by 15%", "Costs reduced by 5%"]
                }

                response = await client.post(
                    f"/ai/agents/{agent_id}/execute",
                    headers=valid_headers,
                    json=task_data
                )

                assert response.status_code in [200, 404, 401]

    # Test Crew endpoints
    @pytest.mark.unit
    async def test_create_crew(self, client, valid_headers):
        """Test creating an agent crew."""
        crew_data = {
            "name": "Financial Analysis Crew",
            "description": "Crew for comprehensive financial analysis",
            "agents": [
                str(uuid4()),  # Financial Analyst Agent
                str(uuid4()),  # Data Collector Agent
                str(uuid4())   # Report Writer Agent
            ],
            "process": "sequential",
            "manager_llm": {
                "model": "gpt-4",
                "temperature": 0.7
            }
        }

        with patch("services.ai.routers.crews.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/ai/crews",
                headers=valid_headers,
                json=crew_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_execute_crew_task(self, client, valid_headers):
        """Test executing a crew task."""
        crew_id = str(uuid4())
        task_data = {
            "objective": "Complete financial audit for Q4",
            "tasks": [
                {
                    "description": "Collect financial data",
                    "agent_role": "data_collector"
                },
                {
                    "description": "Analyze financial metrics",
                    "agent_role": "financial_analyst"
                },
                {
                    "description": "Generate audit report",
                    "agent_role": "report_writer"
                }
            ]
        }

        with patch("services.ai.routers.crews.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/ai/crews/{crew_id}/execute",
                headers=valid_headers,
                json=task_data
            )

            assert response.status_code in [200, 404, 401]

    # Test Embeddings endpoints
    @pytest.mark.unit
    async def test_generate_embeddings(self, client, valid_headers):
        """Test generating embeddings."""
        embedding_data = {
            "texts": [
                "This is a sample text for embedding",
                "Another text to generate embeddings"
            ],
            "model": "text-embedding-ada-002"
        }

        with patch("services.ai.routers.embeddings.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            with patch("services.ai.routers.embeddings.openai_client.embeddings.create") as mock_embed:
                mock_embed.return_value = MagicMock(
                    data=[
                        MagicMock(embedding=[0.1] * 1536),
                        MagicMock(embedding=[0.2] * 1536)
                    ]
                )

                response = await client.post(
                    "/ai/embeddings",
                    headers=valid_headers,
                    json=embedding_data
                )

                assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_similarity_search(self, client, valid_headers):
        """Test similarity search using embeddings."""
        search_data = {
            "query": "Find documents about financial planning",
            "collection": "documents",
            "top_k": 5,
            "threshold": 0.7
        }

        with patch("services.ai.routers.embeddings.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/ai/embeddings/search",
                headers=valid_headers,
                json=search_data
            )

            assert response.status_code in [200, 401]

    # Test Prompts Management endpoints
    @pytest.mark.unit
    async def test_list_prompts(self, client, valid_headers):
        """Test listing prompt templates."""
        with patch("services.ai.routers.prompts.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/ai/prompts",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_prompt_template(self, client, valid_headers):
        """Test creating a prompt template."""
        prompt_data = {
            "name": "Financial Report Summary",
            "description": "Template for summarizing financial reports",
            "template": "Summarize the following financial report:\n\n{report_content}\n\nFocus on: {focus_areas}",
            "variables": ["report_content", "focus_areas"],
            "category": "financial",
            "model_config": {
                "model": "gpt-4",
                "temperature": 0.3,
                "max_tokens": 500
            }
        }

        with patch("services.ai.routers.prompts.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/ai/prompts",
                headers=valid_headers,
                json=prompt_data
            )

            assert response.status_code in [201, 200, 401]

    # Test Analytics endpoints
    @pytest.mark.unit
    async def test_get_ai_usage_statistics(self, client, valid_headers):
        """Test getting AI usage statistics."""
        with patch("services.ai.routers.analytics.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/ai/analytics/usage",
                headers=valid_headers,
                params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_get_model_performance(self, client, valid_headers):
        """Test getting model performance metrics."""
        with patch("services.ai.routers.analytics.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/ai/analytics/performance",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    # Test Health endpoint
    @pytest.mark.unit
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200

        if response.status_code == 200:
            data = response.json()
            assert "status" in data