"""Tests for the message bus implementation."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.agent_communication.message_bus import (
    MessageBus,
    Message,
    MessagePriority,
    Subscription,
    AgentMessageHandler,
    get_message_bus,
    start_message_bus,
    stop_message_bus
)


class TestMessage:
    """Test Message class."""
    
    def test_message_creation(self):
        """Test message creation."""
        message = Message(
            id="test-id",
            topic="test-topic",
            payload={"data": "test"},
            sender_id="agent-1"
        )
        
        assert message.id == "test-id"
        assert message.topic == "test-topic"
        assert message.payload == {"data": "test"}
        assert message.sender_id == "agent-1"
        assert message.priority == MessagePriority.NORMAL
    
    def test_message_to_dict(self):
        """Test message serialization to dictionary."""
        message = Message(
            id="test-id",
            topic="test-topic", 
            payload={"data": "test"},
            sender_id="agent-1"
        )
        
        data = message.to_dict()
        
        assert data["id"] == "test-id"
        assert data["topic"] == "test-topic"
        assert data["payload"] == {"data": "test"}
        assert data["sender_id"] == "agent-1"
        assert data["priority"] == "normal"
        assert "timestamp" in data
    
    def test_message_from_dict(self):
        """Test message deserialization from dictionary."""
        data = {
            "id": "test-id",
            "topic": "test-topic",
            "payload": {"data": "test"},
            "sender_id": "agent-1",
            "priority": "normal",
            "timestamp": "2026-01-22T10:00:00"
        }
        
        message = Message.from_dict(data)
        
        assert message.id == "test-id"
        assert message.topic == "test-topic"
        assert message.payload == {"data": "test"}
        assert message.sender_id == "agent-1"
        assert message.priority == MessagePriority.NORMAL


class TestMessageBus:
    """Test MessageBus class."""
    
    @pytest.fixture
    def message_bus(self):
        """Create a message bus for testing."""
        return MessageBus()
    
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, message_bus):
        """Test subscribing and publishing messages."""
        received_messages = []
        
        async def message_handler(message):
            received_messages.append(message)
        
        # Start the message bus
        await message_bus.start()
        
        # Subscribe to a topic
        subscription = await message_bus.subscribe("test-topic", message_handler, "agent-1")
        
        # Publish a message
        await message_bus.publish("test-topic", {"data": "test"}, "agent-2")
        
        # Wait for message processing
        await asyncio.sleep(0.1)
        
        # Check that message was received
        assert len(received_messages) == 1
        assert received_messages[0].topic == "test-topic"
        assert received_messages[0].payload == {"data": "test"}
        assert received_messages[0].sender_id == "agent-2"
        
        # Stop the message bus
        await message_bus.stop()
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, message_bus):
        """Test multiple subscribers to the same topic."""
        messages_agent1 = []
        messages_agent2 = []
        
        async def handler1(message):
            messages_agent1.append(message)
        
        async def handler2(message):
            messages_agent2.append(message)
        
        await message_bus.start()
        
        # Both agents subscribe
        await message_bus.subscribe("test-topic", handler1, "agent-1")
        await message_bus.subscribe("test-topic", handler2, "agent-2")
        
        # Publish a message
        await message_bus.publish("test-topic", {"data": "test"}, "agent-3")
        
        await asyncio.sleep(0.1)
        
        # Both agents should receive the message
        assert len(messages_agent1) == 1
        assert len(messages_agent2) == 1
        assert messages_agent1[0].payload == {"data": "test"}
        assert messages_agent2[0].payload == {"data": "test"}
        
        await message_bus.stop()
    
    @pytest.mark.asyncio
    async def test_no_self_delivery(self, message_bus):
        """Test that agents don't receive their own messages."""
        received_messages = []
        
        async def message_handler(message):
            received_messages.append(message)
        
        await message_bus.start()
        
        # Agent subscribes
        await message_bus.subscribe("test-topic", message_handler, "agent-1")
        
        # Agent publishes a message
        await message_bus.publish("test-topic", {"data": "test"}, "agent-1")
        
        await asyncio.sleep(0.1)
        
        # Agent should not receive its own message
        assert len(received_messages) == 0
        
        await message_bus.stop()
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, message_bus):
        """Test unsubscribing from topics."""
        received_messages = []
        
        async def message_handler(message):
            received_messages.append(message)
        
        await message_bus.start()
        
        # Subscribe
        subscription = await message_bus.subscribe("test-topic", message_handler, "agent-1")
        
        # Publish first message
        await message_bus.publish("test-topic", {"data": "test1"}, "agent-2")
        await asyncio.sleep(0.1)
        
        # Unsubscribe
        await message_bus.unsubscribe(subscription)
        
        # Publish second message
        await message_bus.publish("test-topic", {"data": "test2"}, "agent-2")
        await asyncio.sleep(0.1)
        
        # Should only receive first message
        assert len(received_messages) == 1
        assert received_messages[0].payload == {"data": "test1"}
        
        await message_bus.stop()
    
    @pytest.mark.asyncio
    async def test_message_history(self, message_bus):
        """Test message history functionality."""
        await message_bus.start()
        
        # Publish some messages
        await message_bus.publish("topic1", {"data": "test1"}, "agent-1")
        await message_bus.publish("topic2", {"data": "test2"}, "agent-2")
        await message_bus.publish("topic1", {"data": "test3"}, "agent-3")
        
        await asyncio.sleep(0.1)
        
        # Check all history
        all_history = message_bus.get_message_history()
        assert len(all_history) == 3
        
        # Check topic-filtered history
        topic1_history = message_bus.get_message_history("topic1")
        assert len(topic1_history) == 2
        assert all(msg.topic == "topic1" for msg in topic1_history)
        
        topic2_history = message_bus.get_message_history("topic2")
        assert len(topic2_history) == 1
        assert topic2_history[0].topic == "topic2"
        
        await message_bus.stop()
    
    @pytest.mark.asyncio
    async def test_wildcard_subscription(self, message_bus):
        """Test wildcard subscription to all topics."""
        received_messages = []
        
        async def message_handler(message):
            received_messages.append(message)
        
        await message_bus.start()
        
        # Subscribe to wildcard
        await message_bus.subscribe("*", message_handler, "agent-1")
        
        # Publish to different topics
        await message_bus.publish("topic1", {"data": "test1"}, "agent-2")
        await message_bus.publish("topic2", {"data": "test2"}, "agent-3")
        
        await asyncio.sleep(0.1)
        
        # Should receive both messages
        assert len(received_messages) == 2
        topics = {msg.topic for msg in received_messages}
        assert topics == {"topic1", "topic2"}
        
        await message_bus.stop()


class TestAgentMessageHandler:
    """Test AgentMessageHandler class."""
    
    @pytest.mark.asyncio
    async def test_agent_message_handler(self):
        """Test agent message handler functionality."""
        received_messages = []
        
        async def message_handler(message):
            received_messages.append(message)
        
        # Create agent handler
        handler = AgentMessageHandler("agent-1")
        
        # Start message bus
        await start_message_bus()
        
        # Subscribe to topic
        await handler.subscribe_to_topic("test-topic", message_handler)
        
        # Publish message
        await handler.publish_message("test-topic", {"data": "test"})
        
        await asyncio.sleep(0.1)
        
        # Check message was received
        assert len(received_messages) == 1
        assert received_messages[0].sender_id == "agent-1"
        assert received_messages[0].payload == {"data": "test"}
        
        # Unsubscribe from all topics
        await handler.unsubscribe_all()
        
        await stop_message_bus()
    
    @pytest.mark.asyncio
    async def test_multiple_agent_communication(self):
        """Test communication between multiple agents."""
        agent1_messages = []
        agent2_messages = []
        
        async def agent1_handler(message):
            agent1_messages.append(message)
        
        async def agent2_handler(message):
            agent2_messages.append(message)
        
        # Create agents
        agent1 = AgentMessageHandler("agent-1")
        agent2 = AgentMessageHandler("agent-2")
        
        await start_message_bus()
        
        # Both agents subscribe
        await agent1.subscribe_to_topic("chat", agent1_handler)
        await agent2.subscribe_to_topic("chat", agent2_handler)
        
        # Agent 1 sends message
        await agent1.publish_message("chat", {"text": "Hello from agent 1"})
        
        # Agent 2 sends message  
        await agent2.publish_message("chat", {"text": "Hello from agent 2"})
        
        await asyncio.sleep(0.1)
        
        # Check that both agents received both messages (but not their own)
        assert len(agent1_messages) == 1
        assert len(agent2_messages) == 1
        
        # Agent 1 should have received agent 2's message
        assert agent1_messages[0].sender_id == "agent-2"
        assert agent1_messages[0].payload["text"] == "Hello from agent 2"
        
        # Agent 2 should have received agent 1's message
        assert agent2_messages[0].sender_id == "agent-1"
        assert agent2_messages[0].payload["text"] == "Hello from agent 1"
        
        # Cleanup
        await agent1.unsubscribe_all()
        await agent2.unsubscribe_all()
        await stop_message_bus()


if __name__ == "__main__":
    pytest.main([__file__])