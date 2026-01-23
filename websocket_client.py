"""
WebSocket Client for Testing Event Streaming

A simple WebSocket client for testing the event streaming functionality.
"""

import asyncio
import json
import logging
import argparse
import sys
from typing import Dict, Any, Optional

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None
    WebSocketClientProtocol = None
    WEBSOCKETS_AVAILABLE = False


class WebSocketEventClient:
    """WebSocket client for connecting to event streams."""
    
    def __init__(self, uri: str):
        self.uri = uri
        self.websocket = None
        self.logger = logging.getLogger(__name__)
        self.received_events = []
        
    async def connect(self):
        """Connect to the WebSocket server."""
        if not WEBSOCKETS_AVAILABLE:
            self.logger.error("WebSocket library not available")
            return False
            
        try:
            self.websocket = await websockets.connect(
                self.uri,
                ping_interval=30,
                ping_timeout=10
            )
            self.logger.info(f"Connected to WebSocket server at {self.uri}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            return False
            
    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.logger.info("Disconnected from WebSocket server")
            
    async def listen(self, max_events: int = 10):
        """Listen for events from the server."""
        if not self.websocket:
            self.logger.error("Not connected to server")
            return
            
        event_count = 0
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    self.received_events.append(data)
                    event_count += 1
                    
                    print(f"Received event {event_count}:")
                    print(f"  Type: {data.get('type')}")
                    print(f"  ID: {data.get('id')}")
                    print(f"  Timestamp: {data.get('timestamp')}")
                    print(f"  Data: {data.get('data', {})}")
                    print("-" * 50)
                    
                    if event_count >= max_events:
                        break
                        
                except json.JSONDecodeError:
                    self.logger.error(f"Received invalid JSON: {message}")
                    
        except Exception as e:
            # Handle connection errors gracefully
            if WEBSOCKETS_AVAILABLE and websockets and hasattr(websockets, 'exceptions'):
                if hasattr(websockets.exceptions, 'ConnectionClosedOK'):
                    if isinstance(e, websockets.exceptions.ConnectionClosedOK):
                        self.logger.info("Connection closed normally")
                    elif hasattr(websockets.exceptions, 'ConnectionClosedError'):
                        if isinstance(e, websockets.exceptions.ConnectionClosedError):
                            self.logger.error("Connection closed with error")
                        else:
                            self.logger.error(f"Error while listening: {e}")
            else:
                self.logger.error(f"Error while listening: {e}")
            
    async def send_ping(self):
        """Send a ping message to the server."""
        if not self.websocket:
            self.logger.error("Not connected to server")
            return
            
        ping_message = {"type": "ping"}
        await self.websocket.send(json.dumps(ping_message))
        self.logger.info("Sent ping message")
        
    async def request_stats(self):
        """Request server statistics."""
        if not self.websocket:
            self.logger.error("Not connected to server")
            return
            
        stats_message = {"type": "get_stats"}
        await self.websocket.send(json.dumps(stats_message))
        self.logger.info("Requested server statistics")
        
    async def subscribe_to_events(self, event_types: list):
        """Subscribe to specific event types."""
        if not self.websocket:
            self.logger.error("Not connected to server")
            return
            
        subscribe_message = {
            "type": "subscribe",
            "event_types": event_types
        }
        await self.websocket.send(json.dumps(subscribe_message))
        self.logger.info(f"Subscribed to event types: {event_types}")
        
    def get_received_events(self) -> list:
        """Get all events received so far."""
        return self.received_events
        
    def print_summary(self):
        """Print a summary of received events."""
        print(f"\n=== Event Summary ===")
        print(f"Total events received: {len(self.received_events)}")
        
        # Group events by type
        event_types = {}
        for event in self.received_events:
            event_type = event.get('type', 'unknown')
            if event_type not in event_types:
                event_types[event_type] = 0
            event_types[event_type] += 1
            
        print("Events by type:")
        for event_type, count in event_types.items():
            print(f"  {event_type}: {count}")
            
        print("=====================")


async def test_connection(uri: str, duration: int = 10):
    """Test WebSocket connection and receive events."""
    client = WebSocketEventClient(uri)
    
    try:
        # Connect
        if not await client.connect():
            print("Failed to connect to server")
            return False
            
        print("✓ Connected successfully")
        
        # Send ping
        await client.send_ping()
        await asyncio.sleep(1)  # Wait for response
        
        # Request stats
        await client.request_stats()
        await asyncio.sleep(1)  # Wait for response
        
        # Subscribe to all events
        await client.subscribe_to_events(["session_created", "session_updated", "checkpoint_created", "error", "info", "debug"])
        await asyncio.sleep(1)  # Wait for response
        
        # Listen for events
        print(f"Listening for events for {duration} seconds...")
        listen_task = asyncio.create_task(client.listen(max_events=100))
        
        # Wait for specified duration
        await asyncio.sleep(duration)
        
        # Cancel the listen task
        listen_task.cancel()
        
        try:
            await listen_task
        except asyncio.CancelledError:
            pass
            
        # Print summary
        client.print_summary()
        
        return True
        
    finally:
        await client.disconnect()


def main():
    """Main entry point for the WebSocket client."""
    parser = argparse.ArgumentParser(
        description="WebSocket Event Stream Client"
    )
    parser.add_argument(
        "--uri",
        default="ws://localhost:8765",
        help="WebSocket server URI (default: ws://localhost:8765)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Duration to listen for events in seconds (default: 10)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run the test
    success = asyncio.run(test_connection(args.uri, args.duration))
    
    if success:
        print("\n✓ Test completed successfully")
    else:
        print("\n✗ Test failed")
        sys.exit(1)


if __name__ == "__main__":
    main()