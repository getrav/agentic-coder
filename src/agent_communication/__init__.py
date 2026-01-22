"""Agent communication package for inter-agent messaging."""

from .message_bus import (
    MessageBus,
    Message,
    MessagePriority,
    Subscription,
    AgentMessageHandler,
    get_message_bus,
    start_message_bus,
    stop_message_bus
)

__all__ = [
    "MessageBus",
    "Message", 
    "MessagePriority",
    "Subscription",
    "AgentMessageHandler",
    "get_message_bus",
    "start_message_bus",
    "stop_message_bus"
]