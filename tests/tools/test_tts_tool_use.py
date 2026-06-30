"""Tests for TTS tool-use/tool-generation playback configuration."""

import json
from unittest.mock import patch, MagicMock


def test_load_tts_tool_use_config_returns_default_when_not_configured():
    """Test that _load_tts_tool_use_config returns empty dict when not configured."""
    from tools.tts_tool import _load_tts_tool_use_config

    # When tts_tool_use is not in config, should return {}
    with patch("hermes_cli.config.load_config") as mock_load_config:
        mock_load_config.return_value = {"tts": {"provider": "edge"}}
        result = _load_tts_tool_use_config()
        assert result == {}


def test_load_tts_tool_use_config_returns_values_when_configured():
    """Test that _load_tts_tool_use_config returns tts_tool_use values when configured."""
    from tools.tts_tool import _load_tts_tool_use_config

    with patch("hermes_cli.config.load_config") as mock_load_config:
        mock_load_config.return_value = {
            "tts": {"provider": "edge"},
            "tts_tool_use": {
                "enabled": True,
                "provider": "edge",
                "edge": {"voice": "en-US-BrianNeural"},
            },
        }
        result = _load_tts_tool_use_config()
        assert result == {
            "enabled": True,
            "provider": "edge",
            "edge": {"voice": "en-US-BrianNeural"},
        }


def test_get_tool_use_provider_defaults_to_main_provider():
    """Test that _get_tool_use_provider defaults to main tts provider when not set."""
    from tools.tts_tool import _get_provider, _get_tool_use_provider

    tts_config = {"provider": "openai"}
    tts_tool_use_config = {}  # No provider specified

    # Should fall back to main provider
    result = _get_tool_use_provider(tts_tool_use_config, tts_config)
    assert result == "openai"


def test_get_tool_use_provider_uses_specific_provider():
    """Test that _get_tool_use_provider uses specific tool-use provider when set."""
    from tools.tts_tool import _get_tool_use_provider

    tts_config = {"provider": "edge"}
    tts_tool_use_config = {
        "provider": "elevenlabs",
        "elevenlabs": {"voice_id": "pNInz6obpgDQGcFmaJgB"},
    }

    result = _get_tool_use_provider(tts_tool_use_config, tts_config)
    assert result == "elevenlabs"


def test_text_to_speech_tool_tool_use_mode_fallback_when_disabled():
    """Test that tool_use_mode falls back to normal TTS when tts_tool_use is not enabled."""
    with patch("tools.tts_tool._load_tts_config") as mock_load_tts:
        mock_load_tts.return_value = {
            "provider": "edge",
            "edge": {"voice": "en-US-AriaNeural"},
        }

        with patch("tools.tts_tool._load_tts_tool_use_config") as mock_load_tool_use:
            mock_load_tool_use.return_value = {}  # Not configured

            from tools.tts_tool import text_to_speech_tool

            # When tool_use_mode=True but tts_tool_use not enabled/configured,
            # it should fall back to normal TTS config
            result = json.loads(
                text_to_speech_tool(
                    text="Hello world", output_path="/tmp/test.mp3", tool_use_mode=True
                )
            )

            # Should succeed with normal TTS fallback
            assert result["success"] is True


def test_text_to_speech_tool_tool_use_mode_with_enabled_config():
    """Test that tool_use_mode uses tts_tool_use config when enabled."""
    with patch("tools.tts_tool._load_tts_config") as mock_load_tts:
        mock_load_tts.return_value = {
            "provider": "edge",
            "edge": {"voice": "en-US-AriaNeural"},
        }

        with patch("tools.tts_tool._load_tts_tool_use_config") as mock_load_tool_use:
            mock_load_tool_use.return_value = {
                "enabled": True,
                "provider": "edge",
                "edge": {"voice": "en-US-BrianNeural"},  # Different voice for tool-use
            }

            with patch("tools.tts_tool._resolve_command_provider_config") as mock_cmd:
                mock_cmd.return_value = None

                from tools.tts_tool import text_to_speech_tool

                # Should use tool-use-specific config (BrianNeural instead of AriaNeural)
                result = json.loads(
                    text_to_speech_tool(
                        text="Hello world",
                        output_path="/tmp/test.mp3",
                        tool_use_mode=True,
                    )
                )
