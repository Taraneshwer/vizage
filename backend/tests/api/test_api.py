import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.main import app

client = TestClient(app)

def test_health_live():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}

def test_health_ready():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}

def test_get_settings():
    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    data = response.json()
    assert "target_fps" in data

def test_get_system_info():
    with TestClient(app) as client:
        response = client.get("/api/v1/system/info")
        assert response.status_code == 200
        data = response.json()
        assert "health" in data
        assert "gpu" in data
        assert "models" in data

def test_get_runtime_stats():
    with TestClient(app) as client:
        response = client.get("/api/v1/runtime/stats")
        assert response.status_code == 200
        data = response.json()
        assert "state" in data
        assert "total_frames_processed" in data
        
def test_get_camera_status():
    with TestClient(app) as client:
        response = client.get("/api/v1/camera/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_active" in data
