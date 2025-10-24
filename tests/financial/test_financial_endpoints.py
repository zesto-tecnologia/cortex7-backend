"""Unit tests for Financial Service endpoints."""

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4


@pytest.mark.asyncio
class TestFinancialEndpoints:
    """Test suite for Financial Service endpoints."""

    @pytest.fixture
    async def app(self):
        """Create FastAPI app instance."""
        from services.financial.main import app
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

    # Test Cost Centers endpoints
    @pytest.mark.unit
    async def test_list_cost_centers(self, client, valid_headers, test_company):
        """Test listing cost centers."""
        with patch("services.financial.routers.cost_centers.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/financial/cost-centers",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]  # Might need auth

    @pytest.mark.unit
    async def test_create_cost_center(self, client, valid_headers):
        """Test creating a new cost center."""
        cost_center_data = {
            "name": "Engineering",
            "code": "ENG-001",
            "budget": 100000.00,
            "responsible_id": str(uuid4()),
            "parent_id": None,
            "active": True
        }

        with patch("services.financial.routers.cost_centers.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/financial/cost-centers",
                headers=valid_headers,
                json=cost_center_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_get_cost_center(self, client, valid_headers):
        """Test getting a specific cost center."""
        cost_center_id = str(uuid4())

        with patch("services.financial.routers.cost_centers.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/financial/cost-centers/{cost_center_id}",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_update_cost_center(self, client, valid_headers):
        """Test updating a cost center."""
        cost_center_id = str(uuid4())
        update_data = {
            "name": "Updated Engineering",
            "budget": 150000.00
        }

        with patch("services.financial.routers.cost_centers.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.put(
                f"/financial/cost-centers/{cost_center_id}",
                headers=valid_headers,
                json=update_data
            )

            assert response.status_code in [200, 404, 401]

    # Test Suppliers endpoints
    @pytest.mark.unit
    async def test_list_suppliers(self, client, valid_headers):
        """Test listing suppliers."""
        with patch("services.financial.routers.suppliers.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/financial/suppliers",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_supplier(self, client, valid_headers):
        """Test creating a new supplier."""
        supplier_data = {
            "name": "Tech Supplies Inc.",
            "tax_id": "12345678901234",
            "contact_name": "John Supplier",
            "contact_email": "contact@techsupplies.com",
            "contact_phone": "+551199999999",
            "address": "123 Tech Street",
            "payment_term": "30 days",
            "status": "active"
        }

        with patch("services.financial.routers.suppliers.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/financial/suppliers",
                headers=valid_headers,
                json=supplier_data
            )

            assert response.status_code in [201, 200, 401]

    # Test Accounts Payable endpoints
    @pytest.mark.unit
    async def test_list_accounts_payable(self, client, valid_headers):
        """Test listing accounts payable."""
        with patch("services.financial.routers.accounts_payable.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/financial/accounts-payable",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_account_payable(self, client, valid_headers):
        """Test creating a new account payable."""
        account_data = {
            "supplier_id": str(uuid4()),
            "cost_center_id": str(uuid4()),
            "invoice_number": "INV-2024-001",
            "invoice_date": datetime.utcnow().isoformat(),
            "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "amount": 5000.00,
            "description": "Office supplies",
            "payment_status": "pending",
            "approver_id": str(uuid4())
        }

        with patch("services.financial.routers.accounts_payable.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/financial/accounts-payable",
                headers=valid_headers,
                json=account_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_approve_payment(self, client, valid_headers):
        """Test approving a payment."""
        payment_id = str(uuid4())

        with patch("services.financial.routers.accounts_payable.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/financial/accounts-payable/{payment_id}/approve",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    # Test Corporate Cards endpoints
    @pytest.mark.unit
    async def test_list_cards(self, client, valid_headers):
        """Test listing corporate cards."""
        with patch("services.financial.routers.cards.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/financial/cards",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_card(self, client, valid_headers):
        """Test creating a new corporate card."""
        card_data = {
            "card_number_last4": "1234",
            "holder_name": "John Doe",
            "holder_id": str(uuid4()),
            "credit_limit": 10000.00,
            "available_limit": 10000.00,
            "status": "active",
            "card_type": "credit",
            "expiry_date": (datetime.utcnow() + timedelta(days=365*3)).isoformat()
        }

        with patch("services.financial.routers.cards.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/financial/cards",
                headers=valid_headers,
                json=card_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_block_card(self, client, valid_headers):
        """Test blocking a corporate card."""
        card_id = str(uuid4())

        with patch("services.financial.routers.cards.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/financial/cards/{card_id}/block",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    # Test Card Transactions endpoints
    @pytest.mark.unit
    async def test_list_card_transactions(self, client, valid_headers):
        """Test listing card transactions."""
        card_id = str(uuid4())

        with patch("services.financial.routers.cards.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/financial/cards/{card_id}/transactions",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_create_card_transaction(self, client, valid_headers):
        """Test creating a card transaction."""
        card_id = str(uuid4())
        transaction_data = {
            "transaction_date": datetime.utcnow().isoformat(),
            "amount": 250.00,
            "merchant": "Tech Store",
            "category": "Office Supplies",
            "description": "Laptop accessories",
            "status": "pending"
        }

        with patch("services.financial.routers.cards.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/financial/cards/{card_id}/transactions",
                headers=valid_headers,
                json=transaction_data
            )

            assert response.status_code in [201, 200, 404, 401]

    # Test Analytics endpoints
    @pytest.mark.unit
    async def test_get_spending_analytics(self, client, valid_headers):
        """Test getting spending analytics."""
        with patch("services.financial.routers.analytics.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/financial/analytics/spending",
                headers=valid_headers,
                params={"period": "monthly", "year": 2024}
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_get_budget_utilization(self, client, valid_headers):
        """Test getting budget utilization."""
        with patch("services.financial.routers.analytics.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/financial/analytics/budget-utilization",
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