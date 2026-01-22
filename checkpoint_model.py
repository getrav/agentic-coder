from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
import json


@dataclass
class Checkpoint:
    """Data model for a checkpoint."""
    checkpoint_id: str
    session_id: str
    timestamp: str
    data: Any
    metadata: Optional[Dict] = None
    
    def __post_init__(self):
        """Validate checkpoint data after initialization."""
        if not self.checkpoint_id:
            raise ValueError("checkpoint_id cannot be empty")
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.timestamp:
            raise ValueError("timestamp cannot be empty")
        
        # Ensure data is JSON serializable
        try:
            json.dumps(self.data)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Checkpoint data must be JSON serializable: {e}")
    
    def to_dict(self) -> Dict:
        """Convert checkpoint to dictionary representation."""
        return {
            'checkpoint_id': self.checkpoint_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp,
            'data': self.data,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Checkpoint':
        """Create checkpoint from dictionary representation."""
        return cls(
            checkpoint_id=data['checkpoint_id'],
            session_id=data['session_id'],
            timestamp=data['timestamp'],
            data=data['data'],
            metadata=data.get('metadata')
        )


@dataclass
class CheckpointMetadata:
    """Metadata for checkpoint operations."""
    created_at: str
    version: str
    environment: str
    tags: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict:
        """Convert metadata to dictionary representation."""
        return {
            'created_at': self.created_at,
            'version': self.version,
            'environment': self.environment,
            'tags': self.tags or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CheckpointMetadata':
        """Create metadata from dictionary representation."""
        return cls(
            created_at=data['created_at'],
            version=data['version'],
            environment=data['environment'],
            tags=data.get('tags')
        )


class CheckpointManager:
    """High-level manager for checkpoint operations."""
    
    def __init__(self, persistence_backend):
        """Initialize checkpoint manager with persistence backend."""
        self.persistence = persistence_backend
    
    def create_checkpoint(self, session_id: str, data: Any, 
                         metadata: Optional[Dict] = None) -> str:
        """Create a new checkpoint with generated ID."""
        import uuid
        checkpoint_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        if metadata is None:
            metadata = {
                'created_at': timestamp,
                'version': '1.0',
                'environment': 'production'
            }
        
        success = self.persistence.save_checkpoint(
            checkpoint_id=checkpoint_id,
            session_id=session_id,
            data=data,
            metadata=metadata
        )
        
        if not success:
            raise RuntimeError("Failed to create checkpoint")
        
        return checkpoint_id
    
    def restore_checkpoint(self, checkpoint_id: str) -> Dict:
        """Restore checkpoint data by ID."""
        checkpoint_data = self.persistence.load_checkpoint(checkpoint_id)
        
        if checkpoint_data is None:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        return checkpoint_data
    
    def list_session_checkpoints(self, session_id: str) -> List[Dict]:
        """List all checkpoints for a session."""
        return self.persistence.load_checkpoints_by_session(session_id)
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint by ID."""
        return self.persistence.delete_checkpoint(checkpoint_id)
    
    def clear_session(self, session_id: str) -> bool:
        """Delete all checkpoints for a session."""
        return self.persistence.delete_session_checkpoints(session_id)