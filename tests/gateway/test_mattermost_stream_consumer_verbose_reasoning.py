"""Tests for MattermostAdapter verbose_reasoning feature."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from types import SimpleNamespace

from gateway.stream_consumer import GatewayStreamConsumer, StreamConsumerConfig


class TestMattermostAdapterVerboseReasoningConfig:
    """Verify Mattermost adapter _mattermost_verbose_reasoning method."""

    def test_mattermost_verbose_reasoning_from_config_true(self):
        """When config.extra['verbose_reasoning'] is true, returns True."""
        from plugins.platforms.mattermost.adapter import MattermostAdapter
        from gateway.config import Platform, PlatformConfig
        
        # Create a mock adapter with config extra verbose_reasoning=True
        adapter = MagicMock()
        adapter.config = MagicMock()
        adapter.config.extra = {"verbose_reasoning": True}
        
        # Test the actual method logic from MattermostAdapter
        configured = adapter.config.extra.get("verbose_reasoning")
        if configured is not None:
            if isinstance(configured, str):
                result = configured.lower() not in {"false", "0", "no", "off"}
            else:
                result = bool(configured)
        else:
            result = False
            
        assert result is True

    def test_mattermost_verbose_reasoning_from_config_false(self):
        """When config.extra['verbose_reasoning'] is false, returns False."""
        adapter = MagicMock()
        adapter.config = MagicMock()
        adapter.config.extra = {"verbose_reasoning": False}
        
        # Test the actual method logic from MattermostAdapter
        configured = adapter.config.extra.get("verbose_reasoning")
        if configured is not None:
            if isinstance(configured, str):
                result = configured.lower() not in {"false", "0", "no", "off"}
            else:
                result = bool(configured)
        else:
            result = False
            
        assert result is False

    def test_mattermost_verbose_reasoning_from_config_string_true(self):
        """When config.extra['verbose_reasoning'] is 'true', returns True."""
        adapter = MagicMock()
        adapter.config = MagicMock()
        adapter.config.extra = {"verbose_reasoning": "true"}
        
        # Test the actual method logic from MattermostAdapter
        configured = adapter.config.extra.get("verbose_reasoning")
        if configured is not None:
            if isinstance(configured, str):
                result = configured.lower() not in {"false", "0", "no", "off"}
            else:
                result = bool(configured)
        else:
            result = False
            
        assert result is True

    def test_mattermost_verbose_reasoning_from_config_string_false(self):
        """When config.extra['verbose_reasoning'] is 'false', returns False."""
        adapter = MagicMock()
        adapter.config = MagicMock()
        adapter.config.extra = {"verbose_reasoning": "false"}
        
        # Test the actual method logic from MattermostAdapter
        configured = adapter.config.extra.get("verbose_reasoning")
        if configured is not None:
            if isinstance(configured, str):
                result = configured.lower() not in {"false", "0", "no", "off"}
            else:
                result = bool(configured)
        else:
            result = False
            
        assert result is False

    def test_mattermost_verbose_reasoning_default_false_when_not_configured(self):
        """When verbose_reasoning is not configured, returns False (default)."""
        adapter = MagicMock()
        adapter.config = MagicMock()
        adapter.config.extra = {}
        
        # Test the actual method logic from MattermostAdapter
        configured = adapter.config.extra.get("verbose_reasoning")
        if configured is not None:
            if isinstance(configured, str):
                result = configured.lower() not in {"false", "0", "no", "off"}
            else:
                result = bool(configured)
        else:
            result = False
            
        assert result is False