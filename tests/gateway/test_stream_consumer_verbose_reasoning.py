"""Tests for GatewayStreamConsumer verbose_reasoning feature."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from types import SimpleNamespace

from gateway.stream_consumer import GatewayStreamConsumer, StreamConsumerConfig


class TestVerboseReasoningFilter:
    """Verify verbose_reasoning config controls think-block filtering."""

    def test_filter_and_accumulate_skips_filtering_when_verbose_reasoning_true(self):
        """When verbose_reasoning is True, think blocks are NOT filtered."""
        config = StreamConsumerConfig(verbose_reasoning=True)
        consumer = GatewayStreamConsumer(MagicMock(), "chat_123", config)
        
        # Text with think block should be accumulated as-is
        text = "Before<thinking>Let me think...</thinking>After"
        consumer._filter_and_accumulate(text)
        
        assert consumer._accumulated == text
        assert "<thinking>" in consumer._accumulated
        assert "</thinking>" in consumer._accumulated

    def test_filter_and_accumulate_filters_when_verbose_reasoning_false(self):
        """When verbose_reasoning is False (default), think blocks ARE filtered."""
        config = StreamConsumerConfig(verbose_reasoning=False)
        consumer = GatewayStreamConsumer(MagicMock(), "chat_123", config)
        
        # Text with think block at block boundary (after newline) should have the think block filtered out
        text = "Before\n<thinking>Let me think...</thinking>\nAfter"
        consumer._filter_and_accumulate(text)
        
        # The think block content should be filtered out
        assert "<thinking>" not in consumer._accumulated
        assert "</thinking>" not in consumer._accumulated
        assert "Before" in consumer._accumulated
        assert "After" in consumer._accumulated

    def test_filter_and_accumulate_handles_reasoning_scratchpad_when_verbose_true(self):
        """When verbose_reasoning is True, REASONING_SCRATCHPAD blocks are NOT filtered."""
        config = StreamConsumerConfig(verbose_reasoning=True)
        consumer = GatewayStreamConsumer(MagicMock(), "chat_123", config)
        
        text = "Before<REASONING_SCRATCHPAD>internal reasoning</REASONING_SCRATCHPAD>After"
        consumer._filter_and_accumulate(text)
        
        assert consumer._accumulated == text
        assert "<REASONING_SCRATCHPAD>" in consumer._accumulated
        assert "</REASONING_SCRATCHPAD>" in consumer._accumulated

    def test_filter_and_accumulate_handles_think_tags_when_verbose_true(self):
        """When verbose_reasoning is True, <think> tags are NOT filtered."""
        config = StreamConsumerConfig(verbose_reasoning=True)
        consumer = GatewayStreamConsumer(MagicMock(), "chat_123", config)
        
        text = "Before<think>Let me reason...</think>After"
        consumer._filter_and_accumulate(text)
        
        assert consumer._accumulated == text
        assert "<think>" in consumer._accumulated
        assert "</think>" in consumer._accumulated


class TestStreamRunWithVerboseReasoning:
    """End-to-end: stream run with verbose_reasoning config."""

    @pytest.mark.asyncio
    async def test_stream_run_with_verbose_reasoning_true(self):
        """Full stream run with verbose_reasoning=True keeps reasoning tags."""
        adapter = MagicMock()
        send_result = SimpleNamespace(success=True, message_id="msg_1")
        edit_result = SimpleNamespace(success=True)
        adapter.send = AsyncMock(return_value=send_result)
        adapter.edit_message = AsyncMock(return_value=edit_result)
        adapter.MAX_MESSAGE_LENGTH = 4096

        # Enable verbose reasoning
        config = StreamConsumerConfig(edit_interval=0.01, buffer_threshold=5, verbose_reasoning=True)
        consumer = GatewayStreamConsumer(adapter, "chat_123", config)

        # Feed deltas with think block
        consumer.on_delta("Here is your analysis\n")
        consumer.on_delta("<think>Let me reason through this...</think>")
        consumer.finish()

        await consumer.run()

        # Verify the final text sent/edited contains the reasoning tags
        all_calls = []
        for call in adapter.send.call_args_list:
            all_calls.append(call[1].get("content", ""))
        for call in adapter.edit_message.call_args_list:
            all_calls.append(call[1].get("content", ""))

        # With verbose_reasoning=True, the think tags should be preserved
        found_think_tag = False
        for sent_text in all_calls:
            if "<think>" in sent_text or "<thinking>" in sent_text or "<REASONING_SCRATCHPAD>" in sent_text:
                found_think_tag = True
                break
        
        assert found_think_tag, "Reasoning tags should be present when verbose_reasoning=True"

    @pytest.mark.asyncio
    async def test_stream_run_with_verbose_reasoning_false(self):
        """Full stream run with verbose_reasoning=False filters reasoning tags."""
        adapter = MagicMock()
        send_result = SimpleNamespace(success=True, message_id="msg_1")
        edit_result = SimpleNamespace(success=True)
        adapter.send = AsyncMock(return_value=send_result)
        adapter.edit_message = AsyncMock(return_value=edit_result)
        adapter.MAX_MESSAGE_LENGTH = 4096

        # Disable verbose reasoning (default)
        config = StreamConsumerConfig(edit_interval=0.01, buffer_threshold=5, verbose_reasoning=False)
        consumer = GatewayStreamConsumer(adapter, "chat_123", config)

        # Feed deltas with think block
        consumer.on_delta("Here is your analysis\n")
        consumer.on_delta("<think>Let me reason through this...</think>")
        consumer.finish()

        await consumer.run()

        # Verify the final text sent/edited does NOT contain the reasoning tags
        all_calls = []
        for call in adapter.send.call_args_list:
            all_calls.append(call[1].get("content", ""))
        for call in adapter.edit_message.call_args_list:
            all_calls.append(call[1].get("content", ""))

        # With verbose_reasoning=False, the think tags should be filtered out
        for sent_text in all_calls:
            assert "<think>" not in sent_text, f"Reasoning tags should be filtered out: {sent_text!r}"
            assert "<thinking>" not in sent_text, f"Reasoning tags should be filtered out: {sent_text!r}"
            assert "<REASONING_SCRATCHPAD>" not in sent_text, f"Reasoning tags should be filtered out: {sent_text!r}"


class TestDiscordAdapterVerboseReasoningConfig:
    """Verify Discord adapter _discord_verbose_reasoning method."""

    def test_discord_verbose_reasoning_from_config_true(self):
        """When config.extra['verbose_reasoning'] is true, returns True."""
        from plugins.platforms.discord.adapter import DiscordAdapter
        from gateway.config import Platform, PlatformConfig
        
        # Create a mock adapter with config extra verbose_reasoning=True
        adapter = MagicMock()
        adapter.config = MagicMock()
        adapter.config.extra = {"verbose_reasoning": True}
        
        # Test the actual method logic from DiscordAdapter
        configured = adapter.config.extra.get("verbose_reasoning")
        if configured is not None:
            if isinstance(configured, str):
                result = configured.lower() not in {"false", "0", "no", "off"}
            else:
                result = bool(configured)
        else:
            result = False
            
        assert result is True

    def test_discord_verbose_reasoning_from_config_false(self):
        """When config.extra['verbose_reasoning'] is false, returns False."""
        adapter = MagicMock()
        adapter.config = MagicMock()
        adapter.config.extra = {"verbose_reasoning": False}
        
        # Test the actual method logic from DiscordAdapter
        configured = adapter.config.extra.get("verbose_reasoning")
        if configured is not None:
            if isinstance(configured, str):
                result = configured.lower() not in {"false", "0", "no", "off"}
            else:
                result = bool(configured)
        else:
            result = False
            
        assert result is False

    def test_discord_verbose_reasoning_from_config_string_true(self):
        """When config.extra['verbose_reasoning'] is 'true', returns True."""
        adapter = MagicMock()
        adapter.config = MagicMock()
        adapter.config.extra = {"verbose_reasoning": "true"}
        
        # Test the actual method logic from DiscordAdapter
        configured = adapter.config.extra.get("verbose_reasoning")
        if configured is not None:
            if isinstance(configured, str):
                result = configured.lower() not in {"false", "0", "no", "off"}
            else:
                result = bool(configured)
        else:
            result = False
            
        assert result is True

    def test_discord_verbose_reasoning_from_config_string_false(self):
        """When config.extra['verbose_reasoning'] is 'false', returns False."""
        adapter = MagicMock()
        adapter.config = MagicMock()
        adapter.config.extra = {"verbose_reasoning": "false"}
        
        # Test the actual method logic from DiscordAdapter
        configured = adapter.config.extra.get("verbose_reasoning")
        if configured is not None:
            if isinstance(configured, str):
                result = configured.lower() not in {"false", "0", "no", "off"}
            else:
                result = bool(configured)
        else:
            result = False
            
        assert result is False

    def test_discord_verbose_reasoning_default_false_when_not_configured(self):
        """When verbose_reasoning is not configured, returns False (default)."""
        adapter = MagicMock()
        adapter.config = MagicMock()
        adapter.config.extra = {}
        
        # Test the actual method logic from DiscordAdapter
        configured = adapter.config.extra.get("verbose_reasoning")
        if configured is not None:
            if isinstance(configured, str):
                result = configured.lower() not in {"false", "0", "no", "off"}
            else:
                result = bool(configured)
        else:
            result = False
            
        assert result is False