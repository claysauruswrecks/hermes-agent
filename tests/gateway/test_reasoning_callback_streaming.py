"""Tests for GatewayStreamConsumer reasoning_callback functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from types import SimpleNamespace

from gateway.stream_consumer import GatewayStreamConsumer, StreamConsumerConfig


class TestReasoningDeltaCallback:
    """Verify reasoning_delta callback functionality."""

    def test_on_reasoning_delta_queues_formatted_text_when_verbose_reasoning_true(self):
        """When verbose_reasoning is True, reasoning deltas are queued with formatting."""
        config = StreamConsumerConfig(verbose_reasoning=True)
        consumer = GatewayStreamConsumer(MagicMock(), "chat_123", config)
        
        # Reasoning delta should be formatted and queued
        consumer.on_reasoning_delta("Let me think about this...")
        
        # Check that the formatted text is in the queue
        # The queue should contain the formatted reasoning text
        items = []
        while not consumer._queue.empty():
            items.append(consumer._queue.get())
            
        assert len(items) == 1
        assert items[0] == "💭 **Reasoning:** Let me think about this..."

    def test_on_reasoning_delta_does_not_queue_when_verbose_reasoning_false(self):
        """When verbose_reasoning is False, reasoning deltas are not queued."""
        config = StreamConsumerConfig(verbose_reasoning=False)
        consumer = GatewayStreamConsumer(MagicMock(), "chat_123", config)
        
        # Reasoning delta should not be queued when verbose_reasoning is False
        consumer.on_reasoning_delta("Let me think about this...")
        
        # Check that the queue is empty
        assert consumer._queue.empty()

    def test_on_reasoning_delta_does_not_queue_empty_text(self):
        """When text is empty, reasoning deltas are not queued."""
        config = StreamConsumerConfig(verbose_reasoning=True)
        consumer = GatewayStreamConsumer(MagicMock(), "chat_123", config)
        
        # Empty reasoning delta should not be queued
        consumer.on_reasoning_delta("")
        
        # Check that the queue is empty
        assert consumer._queue.empty()

    @pytest.mark.asyncio
    async def test_stream_run_with_reasoning_delta(self):
        """Full stream run with reasoning_delta shows formatted reasoning text."""
        adapter = MagicMock()
        send_result = SimpleNamespace(success=True, message_id="msg_1")
        edit_result = SimpleNamespace(success=True)
        adapter.send = AsyncMock(return_value=send_result)
        adapter.edit_message = AsyncMock(return_value=edit_result)
        adapter.MAX_MESSAGE_LENGTH = 4096

        # Enable verbose reasoning
        config = StreamConsumerConfig(edit_interval=0.01, buffer_threshold=5, verbose_reasoning=True)
        consumer = GatewayStreamConsumer(adapter, "chat_123", config)

        # Feed regular deltas
        consumer.on_delta("Here is your analysis\n")
        
        # Feed reasoning delta
        consumer.on_reasoning_delta("Let me reason through this...")
        
        consumer.finish()

        await consumer.run()

        # Verify the final text sent/edited contains the formatted reasoning text
        all_calls = []
        for call in adapter.send.call_args_list:
            all_calls.append(call[1].get("content", ""))
        for call in adapter.edit_message.call_args_list:
            all_calls.append(call[1].get("content", ""))

        # With verbose_reasoning=True, the reasoning text should be present with formatting
        found_reasoning_text = False
        for sent_text in all_calls:
            if "💭 **Reasoning:**" in sent_text and "Let me reason through this..." in sent_text:
                found_reasoning_text = True
                break
        
        assert found_reasoning_text, "Formatted reasoning text should be present when verbose_reasoning=True"