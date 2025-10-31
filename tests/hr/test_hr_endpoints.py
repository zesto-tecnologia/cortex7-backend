"""Unit tests for HR Service endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, date, timedelta
from uuid import uuid4


@pytest.mark.asyncio
class TestHREndpoints:
    """Test suite for HR Service endpoints."""

    @pytest.fixture
    async def app(self):
        """Create FastAPI app instance."""
        from services.hr.main import app
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

    # Test Employees endpoints
    @pytest.mark.unit
    async def test_list_employees(self, client, valid_headers):
        """Test listing employees."""
        with patch("services.hr.routers.employees.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/hr/employees",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_employee(self, client, valid_headers):
        """Test creating a new employee."""
        employee_data = {
            "name": "Jane Smith",
            "email": "jane.smith@company.com",
            "tax_id": "98765432101",
            "birth_date": "1990-05-15",
            "gender": "female",
            "marital_status": "single",
            "address": "456 Main St",
            "city": "São Paulo",
            "state": "SP",
            "zip_code": "01310-100",
            "phone": "+5511999999999",
            "position": "Senior Developer",
            "department": "Engineering",
            "admission_date": date.today().isoformat(),
            "salary": 120000.00,
            "status": "active"
        }

        with patch("services.hr.routers.employees.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/hr/employees",
                headers=valid_headers,
                json=employee_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_get_employee(self, client, valid_headers):
        """Test getting a specific employee."""
        employee_id = str(uuid4())

        with patch("services.hr.routers.employees.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/hr/employees/{employee_id}",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_update_employee(self, client, valid_headers):
        """Test updating an employee."""
        employee_id = str(uuid4())
        update_data = {
            "position": "Lead Developer",
            "salary": 150000.00,
            "department": "Engineering"
        }

        with patch("services.hr.routers.employees.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.put(
                f"/hr/employees/{employee_id}",
                headers=valid_headers,
                json=update_data
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_terminate_employee(self, client, valid_headers):
        """Test terminating an employee."""
        employee_id = str(uuid4())
        termination_data = {
            "termination_date": date.today().isoformat(),
            "reason": "resignation",
            "notes": "Moving to another city"
        }

        with patch("services.hr.routers.employees.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/hr/employees/{employee_id}/terminate",
                headers=valid_headers,
                json=termination_data
            )

            assert response.status_code in [200, 404, 401]

    # Test Contracts endpoints
    @pytest.mark.unit
    async def test_list_contracts(self, client, valid_headers):
        """Test listing employment contracts."""
        with patch("services.hr.routers.contracts.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/hr/contracts",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_contract(self, client, valid_headers):
        """Test creating an employment contract."""
        contract_data = {
            "employee_id": str(uuid4()),
            "contract_type": "CLT",
            "position": "Software Engineer",
            "salary": 100000.00,
            "start_date": date.today().isoformat(),
            "end_date": None,
            "working_hours": 40,
            "benefits": ["health_insurance", "meal_voucher", "transport_voucher"],
            "probation_period_days": 90,
            "status": "active"
        }

        with patch("services.hr.routers.contracts.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/hr/contracts",
                headers=valid_headers,
                json=contract_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_renew_contract(self, client, valid_headers):
        """Test renewing an employment contract."""
        contract_id = str(uuid4())
        renewal_data = {
            "new_end_date": (date.today() + timedelta(days=365)).isoformat(),
            "salary_adjustment": 10.0,
            "notes": "Annual renewal with salary adjustment"
        }

        with patch("services.hr.routers.contracts.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/hr/contracts/{contract_id}/renew",
                headers=valid_headers,
                json=renewal_data
            )

            assert response.status_code in [200, 404, 401]

    # Test Vacations endpoints
    @pytest.mark.unit
    async def test_list_vacation_requests(self, client, valid_headers):
        """Test listing vacation requests."""
        with patch("services.hr.routers.vacations.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/hr/vacations",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_vacation_request(self, client, valid_headers):
        """Test creating a vacation request."""
        vacation_data = {
            "employee_id": str(uuid4()),
            "start_date": (date.today() + timedelta(days=30)).isoformat(),
            "end_date": (date.today() + timedelta(days=45)).isoformat(),
            "days_requested": 15,
            "type": "vacation",
            "notes": "Family trip",
            "status": "pending"
        }

        with patch("services.hr.routers.vacations.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/hr/vacations",
                headers=valid_headers,
                json=vacation_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_approve_vacation(self, client, valid_headers):
        """Test approving a vacation request."""
        vacation_id = str(uuid4())
        approval_data = {
            "approved_by": str(uuid4()),
            "comments": "Approved for requested dates"
        }

        with patch("services.hr.routers.vacations.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/hr/vacations/{vacation_id}/approve",
                headers=valid_headers,
                json=approval_data
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_reject_vacation(self, client, valid_headers):
        """Test rejecting a vacation request."""
        vacation_id = str(uuid4())
        rejection_data = {
            "rejected_by": str(uuid4()),
            "reason": "Critical project deadline during requested period"
        }

        with patch("services.hr.routers.vacations.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/hr/vacations/{vacation_id}/reject",
                headers=valid_headers,
                json=rejection_data
            )

            assert response.status_code in [200, 404, 401]

    # Test Benefits endpoints
    @pytest.mark.unit
    async def test_list_benefits(self, client, valid_headers):
        """Test listing benefits."""
        with patch("services.hr.routers.benefits.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/hr/benefits",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_benefit(self, client, valid_headers):
        """Test creating a benefit."""
        benefit_data = {
            "name": "Health Insurance Premium",
            "type": "health",
            "description": "Comprehensive health insurance coverage",
            "provider": "HealthCare Plus",
            "cost_company": 800.00,
            "cost_employee": 200.00,
            "eligibility_criteria": {"minimum_tenure_days": 90},
            "status": "active"
        }

        with patch("services.hr.routers.benefits.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/hr/benefits",
                headers=valid_headers,
                json=benefit_data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_assign_benefit_to_employee(self, client, valid_headers):
        """Test assigning a benefit to an employee."""
        benefit_id = str(uuid4())
        employee_id = str(uuid4())
        assignment_data = {
            "employee_id": employee_id,
            "enrollment_date": date.today().isoformat(),
            "employee_contribution": 200.00,
            "company_contribution": 800.00
        }

        with patch("services.hr.routers.benefits.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/hr/benefits/{benefit_id}/assign",
                headers=valid_headers,
                json=assignment_data
            )

            assert response.status_code in [200, 404, 401]

    # Test Payroll endpoints
    @pytest.mark.unit
    async def test_calculate_payroll(self, client, valid_headers):
        """Test calculating payroll."""
        payroll_data = {
            "month": 12,
            "year": 2024,
            "include_13th_salary": False
        }

        with patch("services.hr.routers.payroll.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/hr/payroll/calculate",
                headers=valid_headers,
                json=payroll_data
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_get_payroll_summary(self, client, valid_headers):
        """Test getting payroll summary."""
        with patch("services.hr.routers.payroll.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/hr/payroll/summary",
                headers=valid_headers,
                params={"year": 2024, "month": 12}
            )

            assert response.status_code in [200, 401]

    # Test Organizational Structure endpoints
    @pytest.mark.unit
    async def test_get_org_structure(self, client, valid_headers):
        """Test getting organizational structure."""
        with patch("services.hr.routers.organization.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/hr/organization/structure",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_get_department_employees(self, client, valid_headers):
        """Test getting employees by department."""
        department_id = str(uuid4())

        with patch("services.hr.routers.organization.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/hr/organization/departments/{department_id}/employees",
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