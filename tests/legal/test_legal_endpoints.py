"""Unit tests for Legal Service endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, date, timedelta
from uuid import uuid4


@pytest.mark.asyncio
class TestLegalEndpoints:
    """Test suite for Legal Service endpoints."""

    @pytest.fixture
    async def app(self):
        """Create FastAPI app instance."""
        from services.legal.main import app
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

    # Test Contracts endpoints
    @pytest.mark.unit
    async def test_list_contracts(self, client, valid_headers):
        """Test listing legal contracts."""
        with patch("services.legal.routers.contracts.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/legal/contracts",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_contract(self, client, valid_headers):
        """Test creating a new legal contract."""
        contract_data = {
            "contract_type": "supplier",
            "counterparty": "Tech Solutions Ltd",
            "counterparty_tax_id": "12345678901234",
            "subject": "Software development services",
            "amount": 50000.00,
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=365)).isoformat(),
            "auto_renewal": True,
            "status": "draft",
            "critical_clauses": {
                "sla": "99.9% uptime",
                "penalties": "1% per day of delay",
                "confidentiality": "5 years NDA"
            },
            "important_dates": [
                {
                    "description": "Quarterly review",
                    "date": (date.today() + timedelta(days=90)).isoformat(),
                    "notified": False
                }
            ],
            "responsible_id": str(uuid4())
        }

        with patch("services.legal.routers.contracts.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/legal/contracts",
                headers=valid_headers,
                json=contract_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_get_contract(self, client, valid_headers):
        """Test getting a specific contract."""
        contract_id = str(uuid4())

        with patch("services.legal.routers.contracts.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/legal/contracts/{contract_id}",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_update_contract(self, client, valid_headers):
        """Test updating a contract."""
        contract_id = str(uuid4())
        update_data = {
            "status": "active",
            "amount": 60000.00,
            "end_date": (date.today() + timedelta(days=730)).isoformat()
        }

        with patch("services.legal.routers.contracts.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.put(
                f"/legal/contracts/{contract_id}",
                headers=valid_headers,
                json=update_data
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_approve_contract(self, client, valid_headers):
        """Test approving a contract."""
        contract_id = str(uuid4())
        approval_data = {
            "approved_by": str(uuid4()),
            "approval_notes": "Reviewed and approved by legal department"
        }

        with patch("services.legal.routers.contracts.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/legal/contracts/{contract_id}/approve",
                headers=valid_headers,
                json=approval_data
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_terminate_contract(self, client, valid_headers):
        """Test terminating a contract."""
        contract_id = str(uuid4())
        termination_data = {
            "termination_date": date.today().isoformat(),
            "reason": "mutual_agreement",
            "notes": "Both parties agreed to terminate early"
        }

        with patch("services.legal.routers.contracts.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/legal/contracts/{contract_id}/terminate",
                headers=valid_headers,
                json=termination_data
            )

            assert response.status_code in [200, 404, 401]

    # Test Lawsuits endpoints (previously LegalProcess)
    @pytest.mark.unit
    async def test_list_lawsuits(self, client, valid_headers):
        """Test listing lawsuits."""
        with patch("services.legal.routers.lawsuits.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/legal/lawsuits",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_lawsuit(self, client, valid_headers):
        """Test creating a new lawsuit."""
        lawsuit_data = {
            "case_number": "0001234-56.2024.8.26.0100",
            "lawsuit_type": "labor",
            "counterparty": "Former Employee Inc.",
            "cause_amount": 100000.00,
            "status": "active",
            "risk": "medium",
            "court": "1st Labor Court of São Paulo",
            "responsible_attorney": "Dr. Legal Expert",
            "history": [
                {
                    "date": date.today().isoformat(),
                    "event": "Initial filing",
                    "description": "Lawsuit filed by counterparty"
                }
            ],
            "next_action": (date.today() + timedelta(days=30)).isoformat(),
            "next_action_description": "Submit initial defense",
            "document_ids": []
        }

        with patch("services.legal.routers.lawsuits.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/legal/lawsuits",
                headers=valid_headers,
                json=lawsuit_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_get_lawsuit(self, client, valid_headers):
        """Test getting a specific lawsuit."""
        lawsuit_id = str(uuid4())

        with patch("services.legal.routers.lawsuits.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/legal/lawsuits/{lawsuit_id}",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_update_lawsuit(self, client, valid_headers):
        """Test updating a lawsuit."""
        lawsuit_id = str(uuid4())
        update_data = {
            "status": "suspended",
            "risk": "high",
            "cause_amount": 150000.00,
            "next_action": (date.today() + timedelta(days=60)).isoformat(),
            "next_action_description": "Await court decision"
        }

        with patch("services.legal.routers.lawsuits.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.put(
                f"/legal/lawsuits/{lawsuit_id}",
                headers=valid_headers,
                json=update_data
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_add_lawsuit_history(self, client, valid_headers):
        """Test adding history to a lawsuit."""
        lawsuit_id = str(uuid4())
        history_data = {
            "event": "Hearing scheduled",
            "description": "Initial hearing scheduled for next month",
            "date": (date.today() + timedelta(days=30)).isoformat()
        }

        with patch("services.legal.routers.lawsuits.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/legal/lawsuits/{lawsuit_id}/history",
                headers=valid_headers,
                json=history_data
            )

            assert response.status_code in [200, 404, 401]

    # Test Deadlines endpoints
    @pytest.mark.unit
    async def test_list_deadlines(self, client, valid_headers):
        """Test listing legal deadlines."""
        with patch("services.legal.routers.deadlines.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/legal/deadlines",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_deadline(self, client, valid_headers):
        """Test creating a legal deadline."""
        deadline_data = {
            "title": "Submit defense documentation",
            "description": "Submit all defense documents for case 1234",
            "due_date": (date.today() + timedelta(days=15)).isoformat(),
            "related_entity_type": "lawsuit",
            "related_entity_id": str(uuid4()),
            "responsible_id": str(uuid4()),
            "priority": "high",
            "status": "pending",
            "reminder_days_before": [7, 3, 1]
        }

        with patch("services.legal.routers.deadlines.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/legal/deadlines",
                headers=valid_headers,
                json=deadline_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_complete_deadline(self, client, valid_headers):
        """Test marking a deadline as complete."""
        deadline_id = str(uuid4())
        completion_data = {
            "completed_by": str(uuid4()),
            "completion_notes": "All documents submitted on time"
        }

        with patch("services.legal.routers.deadlines.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/legal/deadlines/{deadline_id}/complete",
                headers=valid_headers,
                json=completion_data
            )

            assert response.status_code in [200, 404, 401]

    # Test Compliance endpoints
    @pytest.mark.unit
    async def test_get_compliance_status(self, client, valid_headers):
        """Test getting compliance status."""
        with patch("services.legal.routers.compliance.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/legal/compliance/status",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_check_contract_compliance(self, client, valid_headers):
        """Test checking contract compliance."""
        contract_id = str(uuid4())

        with patch("services.legal.routers.compliance.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/legal/compliance/contracts/{contract_id}",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    # Test Risk Assessment endpoints
    @pytest.mark.unit
    async def test_get_risk_assessment(self, client, valid_headers):
        """Test getting risk assessment."""
        with patch("services.legal.routers.risk.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/legal/risk/assessment",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_get_lawsuit_risk_analysis(self, client, valid_headers):
        """Test getting lawsuit risk analysis."""
        lawsuit_id = str(uuid4())

        with patch("services.legal.routers.risk.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/legal/risk/lawsuits/{lawsuit_id}",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    # Test Health endpoint
    @pytest.mark.unit
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200

        if response.status_code == 200:
            data = response.json()
            assert "status" in data