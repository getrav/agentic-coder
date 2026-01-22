"""Inter-agent message bus for pub/sub communication."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class MessagePriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Message:
    """Message passed between agents."""
    id: str
    topic: str
    payload: Dict[str, Any]
    sender_id: str
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "topic": self.topic,
            "payload": self.payload,
            "sender_id": self.sender_id,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            id=data["id"],
            topic=data["topic"],
            payload=data["payload"],
            sender_id=data["sender_id"],
            priority=MessagePriority(data["priority"]),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class Subscription:
    """Subscription to a message topic."""
    
    def __init__(self, topic: str, callback: Callable[[Message], Awaitable[None]], subscriber_id: str):
        self.topic = topic
        self.callback = callback
        self.subscriber_id = subscriber_id
        self.created_at = datetime.now()


class MessageBus:
    """Central message bus for inter-agent communication."""
    
    def __init__(self):
        self._subscriptions: Dict[str, List[Subscription]] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._logger = logging.getLogger(__name__)
        self._message_history: List[Message] = []
        self._max_history_size = 1000
        
    async def start(self):
        """Start the message bus worker."""
        if self._running:
            return
            
        self._running = True
        self._worker_task = asyncio.create_task(self._process_messages())
        self._logger.info("Message bus started")
    
    async def stop(self):
        """Stop the message bus worker."""
        if not self._running:
            return
            
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._logger.info("Message bus stopped")
    
    async def subscribe(self, topic: str, callback: Callable[[Message], Awaitable[None]], subscriber_id: str) -> Subscription:
        """Subscribe to a message topic.
        
        Args:
            topic: Topic to subscribe to
            callback: Async callback to handle messages
            subscriber_id: ID of the subscribing agent
            
        Returns:
            Subscription object
        """
        subscription = Subscription(topic, callback, subscriber_id)
        
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        
        self._subscriptions[topic].append(subscription)
        self._logger.info(f"Agent {subscriber_id} subscribed to topic: {topic}")
        
        return subscription
    
    async def unsubscribe(self, subscription: Subscription):
        """Unsubscribe from a topic."""
        if subscription.topic in self._subscriptions:
            try:
                self._subscriptions[subscription.topic].remove(subscription)
                self._logger.info(f"Agent {subscription.subscriber_id} unsubscribed from topic: {subscription.topic}")
            except ValueError:
                pass  # Subscription not found
    
    async def publish(self, topic: str, payload: Dict[str, Any], sender_id: str, priority: MessagePriority = MessagePriority.NORMAL):
        """Publish a message to a topic.
        
        Args:
            topic: Topic to publish to
            payload: Message payload
            sender_id: ID of the sending agent
            priority: Message priority
        """
        message = Message(
            id=str(uuid.uuid4()),
            topic=topic,
            payload=payload,
            sender_id=sender_id,
            priority=priority
        )
        
        await self._message_queue.put(message)
        self._logger.debug(f"Message published to topic {topic} from agent {sender_id}")
    
    async def _process_messages(self):
        """Process messages from the queue."""
        while self._running:
            try:
                message = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                await self._deliver_message(message)
            except asyncio.TimeoutError:
                continue  # No messages, continue loop
            except Exception as e:
                self._logger.error(f"Error processing message: {e}")
    
    async def _deliver_message(self, message: Message):
        """Deliver message to all subscribers of the topic."""
        # Add to history
        self._message_history.append(message)
        if len(self._message_history) > self._max_history_size:
            self._message_history.pop(0)
        
        # Find subscriptions for this topic
        topic_subscriptions = self._subscriptions.get(message.topic, [])
        
        # Also check for wildcard subscriptions
        wildcard_subscriptions = self._subscriptions.get("*", [])
        
        all_subscriptions = topic_subscriptions + wildcard_subscriptions
        
        if not all_subscriptions:
            self._logger.debug(f"No subscribers for topic: {message.topic}")
            return
        
        # Deliver message to all subscribers
        delivery_tasks = []
        for subscription in all_subscriptions:
            task = asyncio.create_task(self._safe_deliver(subscription, message))
            delivery_tasks.append(task)
        
        # Wait for all deliveries to complete (or fail)
        if delivery_tasks:
            await asyncio.gather(*delivery_tasks, return_exceptions=True)
    
    async def _safe_deliver(self, subscription: Subscription, message: Message):
        """Safely deliver message to a subscriber."""
        try:
            # Don't deliver message back to sender
            if subscription.subscriber_id == message.sender_id:
                return
                
            await subscription.callback(message)
        except Exception as e:
            self._logger.error(f"Error delivering message to agent {subscription.subscriber_id}: {e}")
    
    def get_subscribers(self, topic: str) -> List[str]:
        """Get list of subscriber IDs for a topic."""
        if topic not in self._subscriptions:
            return []
        
        return [sub.subscriber_id for sub in self._subscriptions[topic]]
    
    def get_topics(self) -> List[str]:
        """Get list of all topics with subscribers."""
        return list(self._subscriptions.keys())
    
    def get_message_history(self, topic: Optional[str] = None, limit: int = 100) -> List[Message]:
        """Get message history, optionally filtered by topic."""
        if topic:
            filtered = [msg for msg in self._message_history if msg.topic == topic]
        else:
            filtered = self._message_history.copy()
        
        return filtered[-limit:] if limit else filtered


# Global message bus instance
_message_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """Get the global message bus instance."""
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus


async def start_message_bus():
    """Start the global message bus."""
    bus = get_message_bus()
    await bus.start()


async def stop_message_bus():
    """Stop the global message bus."""
    bus = get_message_bus()
    await bus.stop()


class AgentMessageHandler:
    """Helper class for agents to handle message bus interactions."""
    
    def __init__(self, agent_id: str, message_bus: Optional[MessageBus] = None):
        self.agent_id = agent_id
        self.message_bus = message_bus or get_message_bus()
        self._subscriptions: List[Subscription] = []
    
    async def subscribe_to_topic(self, topic: str, callback: Callable[[Message], Awaitable[None]]) -> Subscription:
        """Subscribe to a topic."""
        subscription = await self.message_bus.subscribe(topic, callback, self.agent_id)
        self._subscriptions.append(subscription)
        return subscription
    
    async def publish_message(self, topic: str, payload: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL):
        """Publish a message to a topic."""
        await self.message_bus.publish(topic, payload, self.agent_id, priority)
    
    async def unsubscribe_all(self):
        """Unsubscribe from all topics."""
        for subscription in self._subscriptions:
            await self.message_bus.unsubscribe(subscription)
        self._subscriptions.clear()