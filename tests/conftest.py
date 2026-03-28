import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_auth_service():
    with patch('services.auth.auth_service') as mock:
        mock.verify_api_key.return_value = (True, "test-key-123")
        yield mock


@pytest.fixture
def mock_quota_service():
    with patch('services.quota.async_quota_service') as mock:
        mock.get_quota.return_value = 1000
        mock.set_quota.return_value = None
        mock.deduct_quota.return_value = True
        mock.add_quota.return_value = None
        yield mock


@pytest.fixture
def mock_logger_service():
    with patch('services.logger.async_logger_service') as mock:
        mock.log_request.return_value = None
        mock.log_response.return_value = None
        yield mock
