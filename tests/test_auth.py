import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.auth import auth_service, AuthService


def test_auth_service_init():
    service = AuthService()
    assert hasattr(service, 'valid_api_keys')
    assert isinstance(service.valid_api_keys, set)


def test_verify_api_key_valid():
    auth_service.valid_api_keys = {"test-key-123"}
    is_valid, api_key = auth_service.verify_api_key("Bearer test-key-123")
    assert is_valid is True
    assert api_key == "test-key-123"


def test_verify_api_key_invalid():
    auth_service.valid_api_keys = {"test-key-123"}
    is_valid, api_key = auth_service.verify_api_key("Bearer wrong-key")
    assert is_valid is False
    assert api_key is None


def test_verify_api_key_no_bearer():
    is_valid, api_key = auth_service.verify_api_key("test-key-123")
    assert is_valid is False
    assert api_key is None


def test_verify_api_key_none():
    is_valid, api_key = auth_service.verify_api_key(None)
    assert is_valid is False
    assert api_key is None


def test_add_api_key():
    service = AuthService()
    initial_count = len(service.valid_api_keys)
    service.add_api_key("new-key-456")
    assert "new-key-456" in service.valid_api_keys
    assert len(service.valid_api_keys) == initial_count + 1


def test_remove_api_key():
    service = AuthService()
    service.add_api_key("to-remove")
    result = service.remove_api_key("to-remove")
    assert result is True
    assert "to-remove" not in service.valid_api_keys


def test_remove_nonexistent_api_key():
    service = AuthService()
    result = service.remove_api_key("nonexistent")
    assert result is False
