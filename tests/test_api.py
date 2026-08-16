from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_documents_endpoint():
    response = client.get("/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_chat_endpoint_valid():
    response = client.post("/chat", json={"question": "What is the role of the AMF?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "grounded" in data
    assert "confidence" in data
    assert "sources" in data

def test_chat_endpoint_empty():
    response = client.post("/chat", json={"question": ""})
    assert response.status_code == 400
