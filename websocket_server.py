"""
WebSocket Server for Event Streaming

Provides a standalone WebSocket server for real-time event broadcasting.
"""

import asyncio
import argparse
import logging
import signal
import sys
from typing import Optional

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None
    WebSocketServerProtocol = None
    WEBSOCKETS_AVAILABLE = False

from websocket_event_stream import websocket_handler, event_stream, emit_info, WEBSOCKETS_AVAILABLE as EVENT_STREAM_WEBSOCKETS_AVAILABLE


class WebSocketServer:
    """WebSocket server for event streaming."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.logger = logging.getLogger(__name__)
        
    async def start_server(self):
        """Start the WebSocket server."""
        if not WEBSOCKETS_AVAILABLE or not EVENT_STREAM_WEBSOCKETS_AVAILABLE:
            self.logger.error("WebSocket library not available")
            return
            
        self.server = await websockets.serve(
            websocket_handler,
            self.host,
            self.port,
            ping_interval=30,  # Send ping every 30 seconds
            ping_timeout=10,   # Wait 10 seconds for pong response
            close_timeout=1    # Close connection after 1 second
        )
        
        self.logger.info(f"WebSocket server started on {self.host}:{self.port}")
        await emit_info(f"WebSocket server started on {self.host}:{self.port}", "server_started")
        
    async def stop_server(self):
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("WebSocket server stopped")
            
    async def run_forever(self):
        """Run the server until interrupted."""
        await self.start_server()
        
        try:
            # Keep the server running
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            await self.stop_server()


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("websocket_server.log")
        ]
    )


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\nReceived signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point for the WebSocket server."""
    parser = argparse.ArgumentParser(
        description="WebSocket Event Streaming Server"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind the server to (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind the server to (default: 8765)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start server
    server = WebSocketServer(args.host, args.port)
    
    try:
        logger.info(f"Starting WebSocket server on {args.host}:{args.port}")
        asyncio.run(server.run_forever())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()