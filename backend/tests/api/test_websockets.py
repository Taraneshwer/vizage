import pytest
from fastapi.testclient import TestClient
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.main import app

def test_websocket_recognition_connect():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/recognition") as websocket:
                            
            websocket.send_text("ping")
            pass

def test_websocket_system_connect():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/system") as websocket:
                                                                                        
            websocket.send_text("ping")
            pass

def test_websocket_logs_connect():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/logs") as websocket:
            websocket.send_text("ping")
            pass
