"""
WebSocket Event Streaming System

Provides real-time event streaming capabilities using WebSocket connections.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import weakref

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    # Handle missing websockets package gracefully
    websockets = None
    WebSocketServerProtocol = None
    WEBSOCKETS_AVAILABLE = False


class EventType(Enum):
    """Types of events that can be streamed."""
    SESSION_CREATED = "session_created"
    SESSION_UPDATED = "session_updated"
    SESSION_DELETED = "session_deleted"
    CHECKPOINT_CREATED = "checkpoint_created"
    CHECKPOINT_UPDATED = "checkpoint_updated"
    ERROR = "error"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class Event:
    """Represents a streaming event."""
    id: str
    type: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class EventStream:
    """Manages WebSocket event streaming."""
    
    def __init__(self):
        self.connections = set()  # Using regular set for now
        self.event_history: List[Event] = []
        self.max_history_size = 1000
        self.logger = logging.getLogger(__name__)
        
    async def register(self, websocket: Any):
        """Register a new WebSocket connection."""
        if WEBSOCKETS_AVAILABLE:
            self.connections.add(websocket)
            self.logger.info(f"WebSocket connection registered: {getattr(websocket, 'remote_address', 'unknown')}")
            
            # Send recent events to the new connection
            await self.send_recent_events(websocket)
        else:
            self.logger.warning("WebSocket library not available, connection registration ignored")
        
    async def unregister(self, websocket: Any):
        """Unregister a WebSocket connection."""
        if WEBSOCKETS_AVAILABLE:
            self.connections.discard(websocket)
            self.logger.info(f"WebSocket connection unregistered: {getattr(websocket, 'remote_address', 'unknown')}")
            
    async def send_recent_events(self, websocket: Any):
        """Send recent events from history to a new connection."""
        if not WEBSOCKETS_AVAILABLE:
            return
            
        try:
            # Send last 100 events
            recent_events = self.event_history[-100:] if len(self.event_history) > 100 else self.event_history
            
            for event in recent_events:
                message = json.dumps(event.to_dict())
                if hasattr(websocket, 'send'):
                    await websocket.send(message)
                    
            self.logger.debug(f"Sent {len(recent_events)} recent events to new connection")
        except Exception as e:
            self.logger.error(f"Error sending recent events: {e}")
            
    async def broadcast_event(self, event_type: EventType, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Broadcast an event to all connected clients."""
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type.value,
            timestamp=datetime.utcnow(),
            data=data,
            metadata=metadata
        )
        
        # Add to history
        self.event_history.append(event)
        
        # Limit history size
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
            
        # Broadcast to all connections
        message = json.dumps(event.to_dict())
        disconnected = set()
        
        if WEBSOCKETS_AVAILABLE:
            for websocket in self.connections:
                try:
                    if hasattr(websocket, 'send'):
                        await websocket.send(message)
                except Exception as e:
                    # Handle connection errors
                    self.logger.error(f"Error sending event to client: {e}")
                    disconnected.add(websocket)
                    
            # Remove disconnected clients
            for websocket in disconnected:
                self.connections.discard(websocket)
                
        self.logger.debug(f"Broadcasted event {event.id} to {len(self.connections) - len(disconnected)} clients")
        
    async def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.connections)
        
    def get_event_stats(self) -> Dict[str, Any]:
        """Get statistics about the event stream."""
        return {
            "total_events": len(self.event_history),
            "active_connections": len(self.connections),
            "max_history_size": self.max_history_size,
            "oldest_event": self.event_history[0].timestamp.isoformat() if self.event_history else None,
            "newest_event": self.event_history[-1].timestamp.isoformat() if self.event_history else None
        }


# Global event stream instance
event_stream = EventStream()


async def websocket_handler(websocket: Any, path: str):
    """WebSocket connection handler."""
    if not WEBSOCKETS_AVAILABLE:
        return
        
    try:
        # Register the connection
        await event_stream.register(websocket)
        
        # Keep the connection alive and handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                # Handle client messages (e.g., subscriptions, pings)
                await handle_client_message(websocket, data)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                await websocket.send(json.dumps({
                    "type": "error", 
                    "message": f"Error processing message: {str(e)}"
                }))
                
    except Exception as e:
        event_stream.logger.error(f"WebSocket handler error: {e}")
    finally:
        # Unregister the connection
        await event_stream.unregister(websocket)


async def handle_client_message(websocket: Any, data: Dict[str, Any]):
    """Handle messages received from WebSocket clients."""
    message_type = data.get("type")
    
    if message_type == "ping":
        await websocket.send(json.dumps({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }))
    elif message_type == "get_stats":
        stats = event_stream.get_event_stats()
        await websocket.send(json.dumps({
            "type": "stats",
            "data": stats
        }))
    elif message_type == "subscribe":
        # Handle subscription to specific event types
        event_types = data.get("event_types", [])
        await websocket.send(json.dumps({
            "type": "subscription_ack",
            "event_types": event_types,
            "message": f"Subscribed to {len(event_types)} event types"
        }))
    else:
        await websocket.send(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }))


# Helper functions for broadcasting specific events
async def emit_session_created(session_id: str, data: Dict[str, Any]):
    """Emit a session created event."""
    await event_stream.broadcast_event(
        EventType.SESSION_CREATED,
        {"session_id": session_id, **data},
        {"action": "create"}
    )


async def emit_session_updated(session_id: str, data: Dict[str, Any]):
    """Emit a session updated event."""
    await event_stream.broadcast_event(
        EventType.SESSION_UPDATED,
        {"session_id": session_id, **data},
        {"action": "update"}
    )


async def emit_checkpoint_created(session_id: str, checkpoint_id: str, data: Dict[str, Any]):
    """Emit a checkpoint created event."""
    await event_stream.broadcast_event(
        EventType.CHECKPOINT_CREATED,
        {"session_id": session_id, "checkpoint_id": checkpoint_id, **data},
        {"action": "create"}
    )


async def emit_error(message: str, error_type: str = "system_error"):
    """Emit an error event."""
    await event_stream.broadcast_event(
        EventType.ERROR,
        {"error_type": error_type, "message": message},
        {"severity": "error"}
    )


async def emit_info(message: str, info_type: str = "system_info"):
    """Emit an info event."""
    await event_stream.broadcast_event(
        EventType.INFO,
        {"info_type": info_type, "message": message},
        {"severity": "info"}
    )