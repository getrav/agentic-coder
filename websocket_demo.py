#!/usr/bin/env python3
"""
Demo script for WebSocket Event Streaming System

This script demonstrates the WebSocket event streaming functionality
by running a server and simulating checkpoint events.
"""

import asyncio
import logging
import sys
import signal
from datetime import datetime

# Import our WebSocket components
from websocket_server import WebSocketServer
from checkpoint_event_integration import demo_event_integration


async def run_websocket_demo():
    """Run the complete WebSocket event streaming demo."""
    print("WebSocket Event Streaming Demo")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create WebSocket server
    server = WebSocketServer(host="localhost", port=8765)
    
    try:
        # Start the server
        server_task = asyncio.create_task(server.start_server())
        
        # Wait a moment for server to start
        await asyncio.sleep(1)
        
        # Run the integration demo
        await demo_event_integration()
        
        print("\n" + "=" * 50)
        print("WebSocket server is running on ws://localhost:8765")
        print("You can connect with the WebSocket client to see events:")
        print("  python websocket_client.py --duration 20")
        print("\nPress Ctrl+C to stop the server")
        
        # Keep server running
        await server_task
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
        if hasattr(server, 'stop_server'):
            await server.stop_server()
    except Exception as e:
        print(f"Demo error: {e}")
        logging.error(f"Demo error: {e}")


if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(run_websocket_demo())
    except KeyboardInterrupt:
        print("\nDemo stopped by user")
    except Exception as e:
        print(f"Error running demo: {e}")
        sys.exit(1)