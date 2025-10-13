
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_main():
    """Test głównego endpointu"""
    response = client.get("/")
    assert response.status_code == 200


def test_health_check():
    """Test endpointu health check"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


