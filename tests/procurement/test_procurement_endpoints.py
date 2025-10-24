"""Unit tests for Procurement Service endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, date, timedelta
from uuid import uuid4
from decimal import Decimal


@pytest.mark.asyncio
class TestProcurementEndpoints:
    """Test suite for Procurement Service endpoints."""

    @pytest.fixture
    async def app(self):
        """Create FastAPI app instance."""
        from services.procurement.main import app
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

    # Test Purchase Orders endpoints
    @pytest.mark.unit
    async def test_list_purchase_orders(self, client, valid_headers):
        """Test listing purchase orders."""
        with patch("services.procurement.routers.purchase_orders.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/procurement/purchase-orders",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_purchase_order(self, client, valid_headers):
        """Test creating a new purchase order."""
        purchase_order_data = {
            "supplier_id": str(uuid4()),
            "cost_center_id": str(uuid4()),
            "order_number": "PO-2024-001",
            "order_date": date.today().isoformat(),
            "delivery_date": (date.today() + timedelta(days=14)).isoformat(),
            "payment_term": "30 days",
            "items": [
                {
                    "description": "Office Laptops",
                    "quantity": 5,
                    "unit_price": 3000.00,
                    "total": 15000.00,
                    "category": "IT Equipment"
                },
                {
                    "description": "Wireless Mice",
                    "quantity": 10,
                    "unit_price": 50.00,
                    "total": 500.00,
                    "category": "IT Accessories"
                }
            ],
            "subtotal": 15500.00,
            "tax_amount": 2790.00,
            "shipping_cost": 200.00,
            "discount": 0.00,
            "total_amount": 18490.00,
            "currency": "BRL",
            "notes": "Urgent delivery required for new hires",
            "status": "draft",
            "requester_id": str(uuid4()),
            "approval_status": "pending",
            "approval_levels": ["manager", "finance", "director"]
        }

        with patch("services.procurement.routers.purchase_orders.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/procurement/purchase-orders",
                headers=valid_headers,
                json=purchase_order_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_get_purchase_order(self, client, valid_headers):
        """Test getting a specific purchase order."""
        po_id = str(uuid4())

        with patch("services.procurement.routers.purchase_orders.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/procurement/purchase-orders/{po_id}",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_update_purchase_order(self, client, valid_headers):
        """Test updating a purchase order."""
        po_id = str(uuid4())
        update_data = {
            "delivery_date": (date.today() + timedelta(days=21)).isoformat(),
            "notes": "Updated delivery date due to supplier delay",
            "status": "pending_approval"
        }

        with patch("services.procurement.routers.purchase_orders.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.put(
                f"/procurement/purchase-orders/{po_id}",
                headers=valid_headers,
                json=update_data
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_submit_purchase_order(self, client, valid_headers):
        """Test submitting a purchase order for approval."""
        po_id = str(uuid4())
        submission_data = {
            "submitted_by": str(uuid4()),
            "urgency": "high",
            "justification": "Required for critical project"
        }

        with patch("services.procurement.routers.purchase_orders.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/procurement/purchase-orders/{po_id}/submit",
                headers=valid_headers,
                json=submission_data
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_cancel_purchase_order(self, client, valid_headers):
        """Test canceling a purchase order."""
        po_id = str(uuid4())
        cancellation_data = {
            "reason": "Duplicate order",
            "cancelled_by": str(uuid4())
        }

        with patch("services.procurement.routers.purchase_orders.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/procurement/purchase-orders/{po_id}/cancel",
                headers=valid_headers,
                json=cancellation_data
            )

            assert response.status_code in [200, 404, 401]

    # Test Approvals endpoints
    @pytest.mark.unit
    async def test_list_pending_approvals(self, client, valid_headers):
        """Test listing pending approvals."""
        with patch("services.procurement.routers.approvals.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/procurement/approvals/pending",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_approve_purchase_order(self, client, valid_headers):
        """Test approving a purchase order."""
        po_id = str(uuid4())
        approval_data = {
            "approver_id": str(uuid4()),
            "approval_level": "manager",
            "comments": "Approved for immediate procurement",
            "conditions": []
        }

        with patch("services.procurement.routers.approvals.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/procurement/approvals/{po_id}/approve",
                headers=valid_headers,
                json=approval_data
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_reject_purchase_order(self, client, valid_headers):
        """Test rejecting a purchase order."""
        po_id = str(uuid4())
        rejection_data = {
            "rejector_id": str(uuid4()),
            "rejection_level": "finance",
            "reason": "Budget constraints",
            "suggestions": "Reduce quantity or find alternative supplier"
        }

        with patch("services.procurement.routers.approvals.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/procurement/approvals/{po_id}/reject",
                headers=valid_headers,
                json=rejection_data
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_get_approval_history(self, client, valid_headers):
        """Test getting approval history for a purchase order."""
        po_id = str(uuid4())

        with patch("services.procurement.routers.approvals.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/procurement/approvals/{po_id}/history",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    # Test Analytics endpoints
    @pytest.mark.unit
    async def test_get_procurement_analytics(self, client, valid_headers):
        """Test getting procurement analytics."""
        with patch("services.procurement.routers.analytics.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/procurement/analytics/overview",
                headers=valid_headers,
                params={"year": 2024, "quarter": 4}
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_get_supplier_performance(self, client, valid_headers):
        """Test getting supplier performance metrics."""
        supplier_id = str(uuid4())

        with patch("services.procurement.routers.analytics.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/procurement/analytics/suppliers/{supplier_id}/performance",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_get_spending_by_category(self, client, valid_headers):
        """Test getting spending by category."""
        with patch("services.procurement.routers.analytics.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/procurement/analytics/spending-by-category",
                headers=valid_headers,
                params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_get_cost_center_spending(self, client, valid_headers):
        """Test getting cost center spending."""
        cost_center_id = str(uuid4())

        with patch("services.procurement.routers.analytics.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/procurement/analytics/cost-centers/{cost_center_id}/spending",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    # Test Requisitions endpoints
    @pytest.mark.unit
    async def test_create_requisition(self, client, valid_headers):
        """Test creating a purchase requisition."""
        requisition_data = {
            "requester_id": str(uuid4()),
            "department_id": str(uuid4()),
            "items": [
                {
                    "description": "Office chairs",
                    "quantity": 10,
                    "estimated_cost": 5000.00,
                    "justification": "Replace broken chairs"
                }
            ],
            "total_estimated_cost": 5000.00,
            "urgency": "medium",
            "business_justification": "Employee comfort and productivity"
        }

        with patch("services.procurement.routers.requisitions.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/procurement/requisitions",
                headers=valid_headers,
                json=requisition_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_convert_requisition_to_po(self, client, valid_headers):
        """Test converting requisition to purchase order."""
        requisition_id = str(uuid4())
        conversion_data = {
            "supplier_id": str(uuid4()),
            "payment_term": "30 days",
            "delivery_date": (date.today() + timedelta(days=14)).isoformat()
        }

        with patch("services.procurement.routers.requisitions.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/procurement/requisitions/{requisition_id}/convert-to-po",
                headers=valid_headers,
                json=conversion_data
            )

            assert response.status_code in [200, 404, 401]

    # Test Vendor Management endpoints
    @pytest.mark.unit
    async def test_register_vendor(self, client, valid_headers):
        """Test registering a new vendor."""
        vendor_data = {
            "name": "New Vendor Corp",
            "tax_id": "98765432109876",
            "contact_info": {
                "name": "Vendor Contact",
                "email": "contact@newvendor.com",
                "phone": "+5511988887777"
            },
            "address": {
                "street": "456 Vendor St",
                "city": "São Paulo",
                "state": "SP",
                "zip_code": "01310-200"
            },
            "categories": ["IT Equipment", "Office Supplies"],
            "payment_terms": ["30 days", "60 days"],
            "certifications": ["ISO 9001", "ISO 14001"]
        }

        with patch("services.procurement.routers.vendors.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/procurement/vendors",
                headers=valid_headers,
                json=vendor_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_evaluate_vendor(self, client, valid_headers):
        """Test evaluating a vendor."""
        vendor_id = str(uuid4())
        evaluation_data = {
            "evaluator_id": str(uuid4()),
            "quality_score": 4.5,
            "delivery_score": 4.0,
            "price_score": 4.2,
            "service_score": 4.8,
            "overall_score": 4.4,
            "comments": "Reliable vendor with good quality products",
            "evaluation_period": "Q4 2024"
        }

        with patch("services.procurement.routers.vendors.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/procurement/vendors/{vendor_id}/evaluate",
                headers=valid_headers,
                json=evaluation_data
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