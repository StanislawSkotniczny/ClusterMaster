"""
Test suite for ClusterMaster API
"""
import pytest
from fastapi.testclient import TestClient


def test_read_main():
    """Test głównego endpointu"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "ClusterMaster" in data["message"]


def test_health_check():
    """Test endpointu health check"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_api_docs():
    """Test czy dokumentacja API jest dostępna"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    """Test czy OpenAPI schema jest dostępny"""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "info" in data
    assert "paths" in data


