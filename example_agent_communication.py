"""Example usage of the inter-agent message bus."""

import asyncio
import logging
from src.agent_communication import (
    MessageBus,
    MessagePriority,
    AgentMessageHandler,
    start_message_bus,
    stop_message_bus
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def planner_agent_example():
    """Example planner agent that creates and manages tasks."""
    handler = AgentMessageHandler("planner-agent")
    
    async def handle_task_requests(message):
        """Handle task creation requests."""
        logger.info(f"Planner received task request: {message.payload}")
        
        # Create a task
        task_id = f"task-{len(message.payload.get('tasks', [])) + 1}"
        task_info = {
            "id": task_id,
            "description": message.payload.get("description", "Unknown task"),
            "status": "created",
            "assigned_to": "worker-agent"
        }
        
        # Publish task created event
        await handler.publish_message(
            "task-created",
            {"task": task_info},
            MessagePriority.HIGH
        )
        
        logger.info(f"Created task: {task_info}")
    
    async def handle_status_updates(message):
        """Handle task status updates."""
        logger.info(f"Planner received status update: {message.payload}")
    
    # Subscribe to relevant topics
    await handler.subscribe_to_topic("task-request", handle_task_requests)
    await handler.subscribe_to_topic("status-update", handle_status_updates)
    
    logger.info("Planner agent started and subscribed to topics")
    
    return handler


async def worker_agent_example():
    """Example worker agent that executes tasks."""
    handler = AgentMessageHandler("worker-agent")
    
    async def handle_task_created(message):
        """Handle newly created tasks."""
        task = message.payload["task"]
        logger.info(f"Worker received task: {task}")
        
        # Simulate task execution
        await asyncio.sleep(1)
        
        # Update task status
        status_update = {
            "task_id": task["id"],
            "status": "completed",
            "result": f"Completed task {task['description']}"
        }
        
        await handler.publish_message(
            "status-update",
            status_update,
            MessagePriority.NORMAL
        )
        
        logger.info(f"Completed task: {task['id']}")
    
    async def handle_ping(message):
        """Handle ping messages."""
        logger.info(f"Worker received ping from {message.sender_id}")
        
        # Respond with pong
        await handler.publish_message(
            "pong",
            {"response": "Hello from worker", "to": message.sender_id},
            MessagePriority.LOW
        )
    
    # Subscribe to relevant topics
    await handler.subscribe_to_topic("task-created", handle_task_created)
    await handler.subscribe_to_topic("ping", handle_ping)
    
    logger.info("Worker agent started and subscribed to topics")
    
    return handler


async def reviewer_agent_example():
    """Example reviewer agent that validates work."""
    handler = AgentMessageHandler("reviewer-agent")
    
    async def handle_status_updates(message):
        """Handle task status updates for review."""
        update = message.payload
        
        if update.get("status") == "completed":
            logger.info(f"Reviewer reviewing completed task: {update['task_id']}")
            
            # Simulate review process
            await asyncio.sleep(0.5)
            
            # Approve the work
            review_result = {
                "task_id": update["task_id"],
                "review_status": "approved",
                "reviewer": "reviewer-agent",
                "comments": "Work meets quality standards"
            }
            
            await handler.publish_message(
                "review-completed",
                review_result,
                MessagePriority.HIGH
            )
            
            logger.info(f"Approved task: {update['task_id']}")
    
    # Subscribe to status updates
    await handler.subscribe_to_topic("status-update", handle_status_updates)
    
    logger.info("Reviewer agent started and subscribed to topics")
    
    return handler


async def main():
    """Main example demonstrating agent communication."""
    logger.info("Starting agent communication example")
    
    # Start the global message bus
    await start_message_bus()
    
    try:
        # Create agents
        planner = await planner_agent_example()
        worker = await worker_agent_example()
        reviewer = await reviewer_agent_example()
        
        # Simulate some interactions
        logger.info("\n=== Simulating Agent Interactions ===")
        
        # 1. Create a task request
        logger.info("\n1. Creating task request...")
        await planner.publish_message(
            "task-request",
            {"description": "Implement inter-agent message bus"},
            MessagePriority.HIGH
        )
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # 2. Send ping to worker
        logger.info("\n2. Sending ping to worker...")
        await planner.publish_message(
            "ping",
            {"message": "Are you there?"},
            MessagePriority.NORMAL
        )
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # 3. Check message history
        logger.info("\n3. Checking message history...")
        message_bus = handler.message_bus
        history = message_bus.get_message_history()
        
        logger.info(f"Total messages in history: {len(history)}")
        for msg in history[-5:]:  # Show last 5 messages
            logger.info(f"  - {msg.topic}: {msg.payload}")
        
        # 4. Show active topics
        topics = message_bus.get_topics()
        logger.info(f"\n4. Active topics: {topics}")
        
        # 5. Show subscribers for each topic
        logger.info("\n5. Topic subscribers:")
        for topic in topics:
            subscribers = message_bus.get_subscribers(topic)
            logger.info(f"  - {topic}: {subscribers}")
        
        logger.info("\n=== Example Complete ===")
        
        # Cleanup
        await planner.unsubscribe_all()
        await worker.unsubscribe_all()
        await reviewer.unsubscribe_all()
        
    finally:
        # Stop the message bus
        await stop_message_bus()


if __name__ == "__main__":
    asyncio.run(main())