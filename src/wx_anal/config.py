"""
Configuration management for wx-anal.

This module handles configuration settings for weather data downloading
and analysis.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for wx-anal."""

    DEFAULT_DATA_DIR = "data"
    DEFAULT_CACHE_SIZE = 1000  # MB
    DEFAULT_TIMEOUT = 30  # seconds

    def __init__(
        self,
        data_dir: Optional[str] = None,
        cache_size: Optional[int] = None,
        timeout: Optional[int] = None,
        api_keys: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize configuration.

        Args:
            data_dir: Directory for storing downloaded weather data
            cache_size: Maximum cache size in MB
            timeout: Request timeout in seconds
            api_keys: Dictionary of API keys for various weather services
        """
        self.data_dir = Path(data_dir or self.DEFAULT_DATA_DIR)
        self.cache_size = cache_size or self.DEFAULT_CACHE_SIZE
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.api_keys = api_keys or {}

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Config":
        """
        Create configuration from environment variables.

        Environment variables:
            WX_ANAL_DATA_DIR: Data directory path
            WX_ANAL_CACHE_SIZE: Cache size in MB
            WX_ANAL_TIMEOUT: Request timeout in seconds
            WX_ANAL_API_KEY_*: API keys for various services

        Returns:
            Config instance populated from environment
        """
        data_dir = os.getenv("WX_ANAL_DATA_DIR")
        cache_size = os.getenv("WX_ANAL_CACHE_SIZE")
        timeout = os.getenv("WX_ANAL_TIMEOUT")

        # Parse numeric values
        cache_size_int = int(cache_size) if cache_size else None
        timeout_int = int(timeout) if timeout else None

        # Extract API keys
        api_keys = {}
        for key, value in os.environ.items():
            if key.startswith("WX_ANAL_API_KEY_"):
                service_name = key.replace("WX_ANAL_API_KEY_", "").lower()
                api_keys[service_name] = value

        return cls(
            data_dir=data_dir,
            cache_size=cache_size_int,
            timeout=timeout_int,
            api_keys=api_keys,
        )

    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get API key for a specific service.

        Args:
            service: Service name

        Returns:
            API key if available, None otherwise
        """
        return self.api_keys.get(service.lower())

    def set_api_key(self, service: str, key: str) -> None:
        """
        Set API key for a specific service.

        Args:
            service: Service name
            key: API key
        """
        self.api_keys[service.lower()] = key

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "data_dir": str(self.data_dir),
            "cache_size": self.cache_size,
            "timeout": self.timeout,
            "api_keys": {k: "***" for k in self.api_keys.keys()},  # Hide actual keys
        }
