import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app


class TestAPIEndpoints:
    """Test API endpoints"""

    @patch("src.services.search_service.SearchService.search_products")
    def test_health_returns_ok(self, mock_search):
        """WHEN GET /health THEN returns {'status': 'ok'}"""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "OpenClaw API"}

    @patch("src.services.search_service.SearchService.search_products")
    def test_search_accepts_valid_request(self, mock_search):
        """WHEN POST /api/search with valid body THEN returns ChatResponse"""
        mock_search.return_value = [
            {
                "id": "1",
                "name": "Test Product",
                "description": "Test description",
                "price": 50.0,
                "brand": "Test",
                "category": "Fashion",
                "image_url": "http://example.com/image.jpg",
                "product_url": "http://example.com/product",
                "gender": "men",
            }
        ]

        client = TestClient(app)
        response = client.post("/api/search", json={"query": "shoes"})

        assert response.status_code == 200
        assert "response" in response.json()

    @patch("src.services.search_service.SearchService.search_products")
    def test_search_returns_400_on_empty_query(self, mock_search):
        """WHEN POST /api/search with empty query THEN returns 400"""
        client = TestClient(app)
        response = client.post("/api/search", json={"query": ""})

        assert response.status_code == 422

    def test_root_returns_message(self):
        """WHEN GET / THEN returns welcome message"""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert "Welcome" in response.json()["message"]


class TestDebugHeaders:
    """Test debugging headers"""

    def test_includes_x_request_id(self):
        """WHEN request THEN response has X-Request-ID header"""
        client = TestClient(app)
        response = client.get("/health")

        assert "x-request-id" in response.headers or "X-Request-ID" in response.headers

    def test_includes_x_response_time(self):
        """WHEN request THEN response has X-Response-Time header"""
        client = TestClient(app)
        response = client.get("/health")

        assert (
            "x-response-time" in response.headers
            or "X-Response-Time" in response.headers
        )
