# Agentic Coder

A framework for multi-agent systems with inter-agent communication capabilities.

## Features

### Inter-Agent Message Bus

The framework includes a pub/sub message bus for agent-to-agent communication:

- **Publish/Subscribe**: Agents can publish messages to topics and subscribe to receive messages
- **Async Processing**: Built on asyncio for efficient asynchronous message handling  
- **Priority Support**: Messages can be prioritized (LOW, NORMAL, HIGH, URGENT)
- **Message History**: Tracks message history for debugging and auditing
- **Wildcard Subscriptions**: Subscribe to all topics with `*`
- **Self-Filtering**: Agents don't receive their own messages

## Quick Start

```python
import asyncio
from src.agent_communication import AgentMessageHandler, start_message_bus, stop_message_bus

async def my_agent():
    handler = AgentMessageHandler("my-agent-id")
    
    async def handle_message(message):
        print(f"Received: {message.payload}")
    
    # Start the message bus
    await start_message_bus()
    
    # Subscribe to a topic
    await handler.subscribe_to_topic("my-topic", handle_message)
    
    # Publish a message
    await handler.publish_message("my-topic", {"hello": "world"})
    
    # Cleanup
    await handler.unsubscribe_all()
    await stop_message_bus()

asyncio.run(my_agent())
```

See `example_agent_communication.py` for a complete example with multiple agents.
