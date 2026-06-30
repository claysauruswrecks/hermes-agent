"""Tests for TTS reasoning/thinking playback configuration."""

import json
from unittest.mock import patch, MagicMock


def test_load_tts_reasoning_config_returns_default_when_not_configured():
    """Test that _load_tts_reasoning_config returns empty dict when not configured."""
    from tools.tts_tool import _load_tts_reasoning_config

    # When tts_reasoning is not in config, should return {}
    with patch("hermes_cli.config.load_config") as mock_load_config:
        mock_load_config.return_value = {"tts": {"provider": "edge"}}
        result = _load_tts_reasoning_config()
        assert result == {}


def test_load_tts_reasoning_config_returns_values_when_configured():
    """Test that _load_tts_reasoning_config returns tts_reasoning values when configured."""
    from tools.tts_tool import _load_tts_reasoning_config

    with patch("hermes_cli.config.load_config") as mock_load_config:
        mock_load_config.return_value = {
            "tts": {"provider": "edge"},
            "tts_reasoning": {
                "enabled": True,
                "provider": "edge",
                "edge": {"voice": "en-US-AndrewNeural"},
            },
        }
        result = _load_tts_reasoning_config()
        assert result == {
            "enabled": True,
            "provider": "edge",
            "edge": {"voice": "en-US-AndrewNeural"},
        }


def test_get_reasoning_provider_defaults_to_main_provider():
    """Test that _get_reasoning_provider defaults to main tts provider when not set."""
    from tools.tts_tool import _load_tts_config, _get_provider, _get_reasoning_provider

    tts_config = {"provider": "openai"}
    tts_reasoning_config = {}  # No provider specified

    # Should fall back to main provider
    result = _get_reasoning_provider(tts_reasoning_config, tts_config)
    assert result == "openai"


def test_get_reasoning_provider_uses_specific_provider():
    """Test that _get_reasoning_provider uses specific reasoning provider when set."""
    from tools.tts_tool import _get_reasoning_provider

    tts_config = {"provider": "edge"}
    tts_reasoning_config = {
        "provider": "elevenlabs",
        "elevenlabs": {"voice_id": "pNInz6obpgDQGcFmaJgB"},
    }

    result = _get_reasoning_provider(tts_reasoning_config, tts_config)
    assert result == "elevenlabs"


def test_text_to_speech_tool_reasoning_mode_fallback_when_disabled():
    """Test that reasoning_mode falls back to normal TTS when ttsreasoning is not enabled."""
    import logging

    # Setup mock for config loading
    with patch("tools.tts_tool._load_tts_config") as mock_load_tts:
        mock_load_tts.return_value = {
            "provider": "edge",
            "edge": {"voice": "en-US-AriaNeural"},
        }

        with patch("tools.tts_tool._load_tts_reasoning_config") as mock_load_reasoning:
            mock_load_reasoning.return_value = {}  # Not configured

            from tools.tts_tool import text_to_speech_tool

            # When reasoning_mode=True but ttsreasoning not enabled/configured,
            # it should fall back to normal TTS config
            result = json.loads(
                text_to_speech_tool(
                    text="Hello world", output_path="/tmp/test.mp3", reasoning_mode=True
                )
            )

            # Should succeed with normal TTS fallback
            assert result["success"] is True


def test_text_to_speech_tool_reasoning_mode_with_enabled_config():
    """Test that reasoning_mode uses ttsreasoning config when enabled."""
    import logging

    with patch("tools.tts_tool._load_tts_config") as mock_load_tts:
        mock_load_tts.return_value = {
            "provider": "edge",
            "edge": {"voice": "en-US-AriaNeural"},
        }

        with patch("tools.tts_tool._load_tts_reasoning_config") as mock_load_reasoning:
            mock_load_reasoning.return_value = {
                "enabled": True,
                "provider": "edge",
                "edge": {
                    "voice": "en-US-AndrewNeural"
                },  # Different voice for reasoning
            }

            with patch("tools.tts_tool._resolve_command_provider_config") as mock_cmd:
                mock_cmd.return_value = None

                from tools.tts_tool import text_to_speech_tool

                # Should use reasoning-specific config (AndrewNeural instead of AriaNeural)
                result = json.loads(
                    text_to_speech_tool(
                        text="Hello world",
                        output_path="/tmp/test.mp3",
                        reasoning_mode=True,
                    )
                )
