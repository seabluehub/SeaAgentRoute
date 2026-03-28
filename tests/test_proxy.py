import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "available_models" in data


def test_chat_completions_unauthorized(client):
    response = client.post("/v1/chat/completions", json={})
    assert response.status_code == 401


def test_chat_completions_invalid_json(client):
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer test-key-123"},
        content="invalid json"
    )
    assert response.status_code == 400


def test_chat_completions_missing_model(client):
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer test-key-123"},
        json={"messages": [{"role": "user", "content": "hello"}]}
    )
    assert response.status_code == 400


def test_chat_completions_unknown_model(client):
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer test-key-123"},
        json={"model": "unknown-model", "messages": [{"role": "user", "content": "hello"}]}
    )
    assert response.status_code == 400
    assert "Unknown model" in response.json()["detail"]


@patch('services.proxy.forward_request')
def test_chat_completions_success(mock_forward, client):
    mock_response = {
        "id": "test-id",
        "object": "chat.completion",
        "model": "gpt-4o",
        "choices": [{"message": {"role": "assistant", "content": "Hello!"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    }
    mock_forward.return_value = mock_response
    
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer test-key-123"},
        json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "hello"}]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert "X-Request-ID" in response.headers


@patch('services.proxy.forward_request')
def test_chat_completions_stream(mock_forward, client):
    async def mock_stream():
        yield b"data: {\"choices\": [{\"delta\": {\"content\": \"Hello\"}}]}\n\n"
        yield b"data: [DONE]\n\n"
    
    mock_forward.return_value = mock_stream()
    
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer test-key-123"},
        json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True
        }
    )
    
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/event-stream"
    assert "X-Request-ID" in response.headers
