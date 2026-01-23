"""
Integration of WebSocket Event Streaming with Checkpoint System

Integrates the WebSocket event streaming functionality with the existing 
checkpoint persistence system to provide real-time updates.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from checkpoint_persistence import CheckpointPersistence
from websocket_event_stream import (
    EventStream, EventType, emit_session_created, emit_session_updated,
    emit_checkpoint_created, emit_error, emit_info
)


class CheckpointEventIntegration:
    """Integrates checkpoint operations with WebSocket event streaming."""
    
    def __init__(self, db_path: str, event_stream: Optional[EventStream] = None):
        self.db_path = db_path
        self.event_stream = event_stream or EventStream()
        self.persistence = CheckpointPersistence(db_path)
        self.logger = logging.getLogger(__name__)
        
    async def save_checkpoint_with_event(
        self,
        checkpoint_id: str,
        session_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save checkpoint and emit WebSocket event."""
        try:
            # Save checkpoint using the persistence layer
            success = self.persistence.save_checkpoint(
                checkpoint_id, session_id, data, metadata
            )
            
            if success:
                # Emit checkpoint created event
                await emit_checkpoint_created(
                    session_id, 
                    checkpoint_id, 
                    {
                        "data": data,
                        "metadata": metadata or {}
                    }
                )
                self.logger.debug(f"Checkpoint saved and event emitted: {checkpoint_id}")
            else:
                await emit_error(
                    f"Failed to save checkpoint: {checkpoint_id}",
                    "checkpoint_save_error"
                )
                self.logger.error(f"Failed to save checkpoint: {checkpoint_id}")
                
            return success
            
        except Exception as e:
            error_msg = f"Error saving checkpoint {checkpoint_id}: {str(e)}"
            await emit_error(error_msg, "checkpoint_save_exception")
            self.logger.error(error_msg)
            return False
            
    async def create_session_with_event(
        self,
        session_id: str,
        session_data: Dict[str, Any]
    ) -> bool:
        """Create session and emit WebSocket event."""
        try:
            # Create a session by saving its first checkpoint
            initial_checkpoint_id = f"{session_id}_initial"
            
            # Session metadata
            session_metadata = session_data.get("metadata", {})
            session_metadata.update({
                "session_created_at": datetime.utcnow().isoformat(),
                "session_type": "checkpoint_session"
            })
            
            success = await self.save_checkpoint_with_event(
                initial_checkpoint_id,
                session_id,
                session_data.get("data", {}),
                session_metadata
            )
            
            if success:
                # Emit session created event
                await emit_session_created(
                    session_id,
                    {
                        "initial_checkpoint": initial_checkpoint_id,
                        "session_data": session_data
                    }
                )
                self.logger.debug(f"Session created and event emitted: {session_id}")
            else:
                await emit_error(
                    f"Failed to create session: {session_id}",
                    "session_creation_error"
                )
                
            return success
            
        except Exception as e:
            error_msg = f"Error creating session {session_id}: {str(e)}"
            await emit_error(error_msg, "session_creation_exception")
            self.logger.error(error_msg)
            return False
            
    async def update_session_with_event(
        self,
        session_id: str,
        checkpoint_id: str,
        update_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update session with new checkpoint and emit WebSocket event."""
        try:
            # Save the checkpoint (update)
            success = await self.save_checkpoint_with_event(
                checkpoint_id,
                session_id,
                update_data,
                metadata
            )
            
            if success:
                # Emit session updated event
                await emit_session_updated(
                    session_id,
                    {
                        "checkpoint_id": checkpoint_id,
                        "update_data": update_data
                    }
                )
                self.logger.debug(f"Session updated and event emitted: {session_id}")
            else:
                await emit_error(
                    f"Failed to update session: {session_id}",
                    "session_update_error"
                )
                
            return success
            
        except Exception as e:
            error_msg = f"Error updating session {session_id}: {str(e)}"
            await emit_error(error_msg, "session_update_exception")
            self.logger.error(error_msg)
            return False
            
    async def get_session_with_realtime_updates(
        self,
        session_id: str,
        callback=None
    ) -> Dict[str, Any]:
        """Get session data and optionally register for real-time updates."""
        try:
            # Load session checkpoints using the persistence layer
            from checkpoint_loader import CheckpointLoader
            
            loader = CheckpointLoader(self.db_path)
            session_checkpoints = loader.load_session_checkpoints(session_id)
            
            session_data = {
                "session_id": session_id,
                "checkpoint_count": len(session_checkpoints),
                "checkpoints": session_checkpoints,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Emit info about session access
            await emit_info(
                f"Session accessed: {session_id} ({len(session_checkpoints)} checkpoints)",
                "session_access"
            )
            
            return session_data
            
        except Exception as e:
            error_msg = f"Error getting session {session_id}: {str(e)}"
            await emit_error(error_msg, "session_access_exception")
            self.logger.error(error_msg)
            return {"error": error_msg, "session_id": session_id}
            
    def get_event_stats(self) -> Dict[str, Any]:
        """Get event stream statistics."""
        return self.event_stream.get_event_stats()


# Global integration instance
integration_instance: Optional[CheckpointEventIntegration] = None


def get_integration(db_path: str) -> CheckpointEventIntegration:
    """Get or create the global integration instance."""
    global integration_instance
    if integration_instance is None:
        integration_instance = CheckpointEventIntegration(db_path)
    return integration_instance


# Example usage functions
async def demo_event_integration(db_path: str = "demo_checkpoints.db"):
    """Demonstrate the WebSocket event integration."""
    # Initialize integration
    integration = get_integration(db_path)
    
    print("WebSocket Event Integration Demo")
    print("=" * 40)
    
    # Create a session
    session_id = "demo_realtime_session"
    session_data = {
        "data": {
            "user": "demo_user",
            "environment": "development",
            "features": ["realtime", "websockets", "events"]
        },
        "metadata": {
            "demo": True,
            "description": "Real-time event streaming demo"
        }
    }
    
    success = await integration.create_session_with_event(session_id, session_data)
    print(f"Created session: {success}")
    
    # Add some checkpoints
    for i in range(3):
        checkpoint_id = f"{session_id}_checkpoint_{i}"
        checkpoint_data = {
            "step": i + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "data": f"Real-time checkpoint data for step {i + 1}",
            "user_action": "demo_step"
        }
        
        success = await integration.update_session_with_event(
            session_id,
            checkpoint_id,
            checkpoint_data
        )
        print(f"Added checkpoint {i + 1}: {success}")
        await asyncio.sleep(0.1)  # Small delay for demo
    
    # Get session stats
    session_info = await integration.get_session_with_realtime_updates(session_id)
    print(f"Session info: {session_info}")
    
    # Get event stream stats
    event_stats = integration.get_event_stats()
    print(f"Event stream stats: {event_stats}")
    
    print("\nDemo completed!")
    return integration