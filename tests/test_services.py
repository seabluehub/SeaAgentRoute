import pytest
import sys
import os
import httpx
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.proxy import forward_request
from config.models import ModelConfig


@pytest.fixture
def sample_model_config():
    return ModelConfig(
        base_url="https://api.example.com/v1",
        auth_header="Bearer test-key",
        target_model="test-model",
        max_tokens=4096,
        supports_stream=True,
        timeout=60
    )


@pytest.fixture
def sample_payload():
    return {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "hello"}]
    }


@patch('services.proxy.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_forward_request_non_stream(mock_client, sample_model_config, sample_payload):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "id": "test-id",
        "model": "test-model",
        "choices": [{"message": {"role": "assistant", "content": "Hello!"}}],
        "usage": {"total_tokens": 10}
    }
    
    mock_post = AsyncMock()
    mock_post.return_value = mock_response
    mock_client.return_value.__aenter__.return_value.post = mock_post
    
    result = await forward_request(sample_payload, sample_model_config, stream=False)
    
    assert isinstance(result, dict)
    assert result["model"] == "gpt-4o"
    assert "choices" in result
    mock_post.assert_called_once()


@patch('services.proxy.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_forward_request_stream(mock_client, sample_model_config, sample_payload):
    mock_stream = AsyncMock()
    mock_stream.raise_for_status = MagicMock()
    
    async def mock_aiter_bytes():
        yield b"data: test1\n\n"
        yield b"data: test2\n\n"
    
    mock_stream.aiter_bytes = mock_aiter_bytes
    
    mock_client_stream = AsyncMock()
    mock_client_stream.return_value.__aenter__.return_value = mock_stream
    mock_client.return_value.__aenter__.return_value.stream = mock_client_stream
    
    result = await forward_request(sample_payload, sample_model_config, stream=True)
    
    assert hasattr(result, '__aiter__')
