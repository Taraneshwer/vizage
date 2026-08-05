"""
Integration tests for the health endpoint.
"""
import pytest
from app.core.constants import API_V1_STR

@pytest.mark.asyncio
async def test_health_check(async_client):
    response = await async_client.get(f"{API_V1_STR}/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data
    assert "database" in data
