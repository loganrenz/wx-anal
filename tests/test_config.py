"""Tests for configuration module."""

import os
import pytest
from pathlib import Path

from wx_anal.config import Config


def test_config_defaults():
    """Test default configuration values."""
    config = Config()
    
    assert config.data_dir == Path(Config.DEFAULT_DATA_DIR)
    assert config.cache_size == Config.DEFAULT_CACHE_SIZE
    assert config.timeout == Config.DEFAULT_TIMEOUT
    assert config.api_keys == {}


def test_config_custom_values():
    """Test configuration with custom values."""
    config = Config(
        data_dir="/tmp/test_data",
        cache_size=500,
        timeout=60,
        api_keys={"service1": "key1"},
    )
    
    assert config.data_dir == Path("/tmp/test_data")
    assert config.cache_size == 500
    assert config.timeout == 60
    assert config.get_api_key("service1") == "key1"


def test_config_from_env(monkeypatch):
    """Test configuration from environment variables."""
    monkeypatch.setenv("WX_ANAL_DATA_DIR", "/tmp/env_data")
    monkeypatch.setenv("WX_ANAL_CACHE_SIZE", "2000")
    monkeypatch.setenv("WX_ANAL_TIMEOUT", "45")
    monkeypatch.setenv("WX_ANAL_API_KEY_TEST", "test_key")
    
    config = Config.from_env()
    
    assert config.data_dir == Path("/tmp/env_data")
    assert config.cache_size == 2000
    assert config.timeout == 45
    assert config.get_api_key("test") == "test_key"


def test_config_api_key_operations():
    """Test API key get/set operations."""
    config = Config()
    
    # Initially no key
    assert config.get_api_key("myservice") is None
    
    # Set key
    config.set_api_key("myservice", "mykey123")
    assert config.get_api_key("myservice") == "mykey123"
    
    # Case insensitive
    assert config.get_api_key("MYSERVICE") == "mykey123"


def test_config_to_dict():
    """Test configuration serialization."""
    config = Config(
        data_dir="/tmp/test",
        cache_size=1500,
        api_keys={"svc1": "key1", "svc2": "key2"},
    )
    
    config_dict = config.to_dict()
    
    assert config_dict["data_dir"] == "/tmp/test"
    assert config_dict["cache_size"] == 1500
    assert config_dict["timeout"] == Config.DEFAULT_TIMEOUT
    
    # API keys should be masked
    assert config_dict["api_keys"]["svc1"] == "***"
    assert config_dict["api_keys"]["svc2"] == "***"


def test_config_creates_data_dir(tmp_path):
    """Test that data directory is created if it doesn't exist."""
    data_dir = tmp_path / "new_data_dir"
    assert not data_dir.exists()
    
    config = Config(data_dir=str(data_dir))
    
    assert data_dir.exists()
    assert data_dir.is_dir()
