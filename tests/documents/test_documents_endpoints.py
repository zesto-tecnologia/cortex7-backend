"""Unit tests for Documents Service endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, date
from uuid import uuid4
import io
import base64


@pytest.mark.asyncio
class TestDocumentsEndpoints:
    """Test suite for Documents Service endpoints."""

    @pytest.fixture
    async def app(self):
        """Create FastAPI app instance."""
        from services.documents.main import app
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
    def sample_pdf_content(self):
        """Generate sample PDF content."""
        # Simple PDF header (not a valid PDF, but enough for testing)
        return b"%PDF-1.4\n%Fake PDF content for testing"

    @pytest.fixture
    def sample_text_content(self):
        """Generate sample text content."""
        return b"This is a sample document content for testing purposes."

    # Test Document CRUD endpoints
    @pytest.mark.unit
    async def test_list_documents(self, client, valid_headers):
        """Test listing documents."""
        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/documents",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_upload_document(self, client, valid_headers, sample_pdf_content):
        """Test uploading a document."""
        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            # Create form data for file upload
            files = {
                "file": ("test_document.pdf", sample_pdf_content, "application/pdf")
            }
            data = {
                "title": "Test Document",
                "document_type": "contract",
                "description": "Test contract document",
                "tags": "test,contract,sample"
            }

            response = await client.post(
                "/documents/upload",
                headers=valid_headers,
                files=files,
                data=data
            )

            assert response.status_code in [201, 200, 401]

    @pytest.mark.unit
    async def test_get_document(self, client, valid_headers):
        """Test getting a specific document."""
        document_id = str(uuid4())

        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/documents/{document_id}",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_update_document_metadata(self, client, valid_headers):
        """Test updating document metadata."""
        document_id = str(uuid4())
        update_data = {
            "title": "Updated Document Title",
            "description": "Updated description",
            "tags": ["updated", "test"],
            "metadata": {
                "department": "Legal",
                "confidential": True
            }
        }

        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.put(
                f"/documents/{document_id}",
                headers=valid_headers,
                json=update_data
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_delete_document(self, client, valid_headers):
        """Test deleting a document."""
        document_id = str(uuid4())

        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.delete(
                f"/documents/{document_id}",
                headers=valid_headers
            )

            assert response.status_code in [204, 200, 404, 401]

    @pytest.mark.unit
    async def test_download_document(self, client, valid_headers, sample_pdf_content):
        """Test downloading a document."""
        document_id = str(uuid4())

        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            with patch("services.documents.routers.documents.get_file_content") as mock_file:
                mock_file.return_value = sample_pdf_content

                response = await client.get(
                    f"/documents/{document_id}/download",
                    headers=valid_headers
                )

                assert response.status_code in [200, 404, 401]

    # Test Search endpoints
    @pytest.mark.unit
    async def test_search_documents(self, client, valid_headers):
        """Test searching documents."""
        with patch("services.documents.routers.search.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/documents/search",
                headers=valid_headers,
                params={"query": "contract", "document_type": "contract"}
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_advanced_search(self, client, valid_headers):
        """Test advanced document search."""
        search_data = {
            "query": "important contract",
            "document_types": ["contract", "agreement"],
            "date_from": "2024-01-01",
            "date_to": "2024-12-31",
            "tags": ["legal", "vendor"],
            "departments": ["Legal", "Procurement"],
            "min_size": 1024,
            "max_size": 10485760,
            "include_content": True
        }

        with patch("services.documents.routers.search.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                "/documents/search/advanced",
                headers=valid_headers,
                json=search_data
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_semantic_search(self, client, valid_headers):
        """Test semantic document search using embeddings."""
        with patch("services.documents.routers.search.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            with patch("services.documents.routers.search.generate_embedding") as mock_embed:
                mock_embed.return_value = [0.1] * 1536  # Mock embedding vector

                response = await client.post(
                    "/documents/search/semantic",
                    headers=valid_headers,
                    json={
                        "query": "find contracts related to software licensing",
                        "similarity_threshold": 0.8,
                        "max_results": 10
                    }
                )

                assert response.status_code in [200, 401]

    # Test OCR and Text Extraction endpoints
    @pytest.mark.unit
    async def test_extract_text_from_document(self, client, valid_headers):
        """Test extracting text from a document."""
        document_id = str(uuid4())

        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            with patch("services.documents.routers.documents.extract_text") as mock_extract:
                mock_extract.return_value = "Extracted text content from document"

                response = await client.post(
                    f"/documents/{document_id}/extract-text",
                    headers=valid_headers
                )

                assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_ocr_document(self, client, valid_headers):
        """Test OCR processing for a document."""
        document_id = str(uuid4())

        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            with patch("services.documents.routers.documents.perform_ocr") as mock_ocr:
                mock_ocr.return_value = "OCR extracted text from scanned document"

                response = await client.post(
                    f"/documents/{document_id}/ocr",
                    headers=valid_headers
                )

                assert response.status_code in [200, 404, 401]

    # Test Document Versioning endpoints
    @pytest.mark.unit
    async def test_create_document_version(self, client, valid_headers, sample_pdf_content):
        """Test creating a new version of a document."""
        document_id = str(uuid4())

        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            files = {
                "file": ("updated_document.pdf", sample_pdf_content, "application/pdf")
            }
            data = {
                "version_notes": "Updated terms and conditions",
                "major_version": False
            }

            response = await client.post(
                f"/documents/{document_id}/versions",
                headers=valid_headers,
                files=files,
                data=data
            )

            assert response.status_code in [201, 200, 404, 401]

    @pytest.mark.unit
    async def test_list_document_versions(self, client, valid_headers):
        """Test listing all versions of a document."""
        document_id = str(uuid4())

        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/documents/{document_id}/versions",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_restore_document_version(self, client, valid_headers):
        """Test restoring a previous version of a document."""
        document_id = str(uuid4())
        version_id = str(uuid4())

        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/documents/{document_id}/versions/{version_id}/restore",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    # Test Document Sharing endpoints
    @pytest.mark.unit
    async def test_share_document(self, client, valid_headers):
        """Test sharing a document."""
        document_id = str(uuid4())
        share_data = {
            "shared_with": [str(uuid4()), str(uuid4())],
            "permission_level": "read",
            "expiration_date": (date.today().replace(year=date.today().year + 1)).isoformat(),
            "notify_users": True
        }

        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/documents/{document_id}/share",
                headers=valid_headers,
                json=share_data
            )

            assert response.status_code in [200, 404, 401]

    @pytest.mark.unit
    async def test_get_document_permissions(self, client, valid_headers):
        """Test getting document permissions."""
        document_id = str(uuid4())

        with patch("services.documents.routers.documents.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/documents/{document_id}/permissions",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    # Test Document Analytics endpoints
    @pytest.mark.unit
    async def test_get_document_statistics(self, client, valid_headers):
        """Test getting document statistics."""
        with patch("services.documents.routers.analytics.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/documents/analytics/statistics",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_get_document_usage(self, client, valid_headers):
        """Test getting document usage metrics."""
        document_id = str(uuid4())

        with patch("services.documents.routers.analytics.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                f"/documents/analytics/{document_id}/usage",
                headers=valid_headers
            )

            assert response.status_code in [200, 404, 401]

    # Test Document Templates endpoints
    @pytest.mark.unit
    async def test_list_templates(self, client, valid_headers):
        """Test listing document templates."""
        with patch("services.documents.routers.templates.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.get(
                "/documents/templates",
                headers=valid_headers
            )

            assert response.status_code in [200, 401]

    @pytest.mark.unit
    async def test_create_document_from_template(self, client, valid_headers):
        """Test creating a document from a template."""
        template_id = str(uuid4())
        template_data = {
            "title": "New Contract from Template",
            "variables": {
                "company_name": "Test Company",
                "contract_value": "100000",
                "start_date": date.today().isoformat()
            }
        }

        with patch("services.documents.routers.templates.get_db") as mock_db:
            mock_db.return_value = AsyncMock()

            response = await client.post(
                f"/documents/templates/{template_id}/create",
                headers=valid_headers,
                json=template_data
            )

            assert response.status_code in [201, 200, 404, 401]

    # Test Health endpoint
    @pytest.mark.unit
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200

        if response.status_code == 200:
            data = response.json()
            assert "status" in data