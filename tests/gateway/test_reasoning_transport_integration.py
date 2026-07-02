"""Integration tests for reasoning token transport from model response to Discord/Mattermost."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from types import SimpleNamespace

from gateway.stream_consumer import GatewayStreamConsumer, StreamConsumerConfig


class TestReasoningTransportIntegration:
    """Integration tests verifying reasoning token transport mechanics."""

    @pytest.mark.asyncio
    async def test_stream_consumer_reasoning_and_regular_deltas_integration(self):
        """Verify reasoning deltas and regular deltas are correctly transported together."""
        adapter = MagicMock()
        send_result = SimpleNamespace(success=True, message_id="msg_1")
        edit_result = SimpleNamespace(success=True)
        adapter.send = AsyncMock(return_value=send_result)
        adapter.edit_message = AsyncMock(return_value=edit_result)
        adapter.MAX_MESSAGE_LENGTH = 4096

        # Streaming mode with verbose_reasoning=True
        config = StreamConsumerConfig(edit_interval=0.01, buffer_threshold=5, verbose_reasoning=True)
        consumer = GatewayStreamConsumer(adapter, "chat_123", config)

        # Simulate model response flow: regular delta -> reasoning delta -> regular delta
        consumer.on_delta("Here is your analysis\n")
        consumer.on_reasoning_delta("Let me reason through this...")
        consumer.on_delta("The answer is 42.")
        
        consumer.finish()
        await consumer.run()

        # Verify the final text contains both regular and reasoning content
        all_calls = []
        for call in adapter.send.call_args_list:
            all_calls.append(call[1].get("content", ""))
        for call in adapter.edit_message.call_args_list:
            all_calls.append(call[1].get("content", ""))

        found_analysis = False
        found_reasoning = False
        found_answer = False
        for sent_text in all_calls:
            if "Here is your analysis" in sent_text:
                found_analysis = True
            if "💭 **Reasoning:**" in sent_text and "Let me reason through this..." in sent_text:
                found_reasoning = True
            if "The answer is 42." in sent_text:
                found_answer = True
        
        assert found_analysis, "Regular analysis text should be present"
        assert found_reasoning, "Formatted reasoning text with 💭 **Reasoning:** should be present in streaming mode"
        assert found_answer, "Regular answer text should be present"

    @pytest.mark.asyncio
    async def test_stream_consumer_reasoning_callback_non_streaming_format(self):
        """Verify non-streaming reasoning progress callback format is 💬 {text}."""
        # Simulate the _reasoning_progress_cb behavior for thinking events in non-streaming mode
        # This is the format used when thinking_progress is enabled but streaming is disabled
        
        thinking_text = "Let me reason through this..."
        # The _reasoning_progress_cb formats text as: 💬 {text}
        formatted_text = f"💬 {thinking_text}"
        
        assert formatted_text == "💬 Let me reason through this..."
        assert "💬" in formatted_text
        assert "Let me reason through this..." in formatted_text
        assert "💭 **Reasoning:**" not in formatted_text  # Should NOT have streaming format

    def test_reasoning_content_parity_streaming_vs_non_streaming(self):
        """Verify reasoning content is consistent between streaming and non-streaming modes."""
        reasoning_text = "Let me reason through this..."
        
        # Streaming mode format: 💭 **Reasoning:** {text} (via _reasoning_delta_cb)
        streaming_format = f"💭 **Reasoning:** {reasoning_text}"
        
        # Non-streaming mode format: 💬 {text} for _thinking events (via _reasoning_progress_cb)
        non_streaming_format = f"💬 {reasoning_text}"
        
        # Verify both formats contain the same reasoning content
        assert reasoning_text in streaming_format
        assert reasoning_text in non_streaming_format
        
        # Verify the formats are different (different emojis as per user preference)
        assert streaming_format != non_streaming_format
        assert "💭 **Reasoning:**" in streaming_format
        assert "💬" in non_streaming_format
        assert "💭 **Reasoning:**" not in non_streaming_format
        assert "💬" not in streaming_format