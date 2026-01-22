import json
import os
from typing import Any, Dict, Optional
from datetime import datetime
import threading
from checkpoint_model import Checkpoint, CheckpointMetadata


class CheckpointSaver:
    """Enhanced checkpoint saving functionality with validation and error handling."""
    
    def __init__(self, db_path: str = "checkpoints.db", 
                 max_retries: int = 3, backup_enabled: bool = True):
        from checkpoint_persistence import CheckpointPersistence
        self.persistence = CheckpointPersistence(db_path)
        self.max_retries = max_retries
        self.backup_enabled = backup_enabled
        self._lock = threading.Lock()
        
        if backup_enabled:
            self._ensure_backup_directory()
    
    def _ensure_backup_directory(self):
        """Ensure backup directory exists."""
        backup_dir = os.path.join(os.path.dirname(self.persistence.db_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
    
    def save_checkpoint_with_validation(self, checkpoint_id: str, session_id: str,
                                      data: Any, metadata: Optional[Dict] = None,
                                      validate_data: bool = True) -> bool:
        """Save checkpoint with data validation and retry logic."""
        
        if validate_data:
            if not self._validate_checkpoint_data(data):
                print("Checkpoint data validation failed")
                return False
        
        if metadata is None:
            metadata = self._create_default_metadata()
        
        for attempt in range(self.max_retries):
            try:
                if self.persistence.save_checkpoint(checkpoint_id, session_id, data, metadata):
                    if self.backup_enabled:
                        self._create_backup_checkpoint(checkpoint_id, session_id, data, metadata)
                    return True
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"Failed to save checkpoint after {self.max_retries} attempts: {e}")
                    return False
                print(f"Retry {attempt + 1}/{self.max_retries} for checkpoint {checkpoint_id}")
        
        return False
    
    def save_auto_checkpoint(self, session_id: str, data: Any,
                           trigger_event: str = "auto") -> str:
        """Save an automatic checkpoint with generated ID."""
        import uuid
        checkpoint_id = f"auto_{uuid.uuid4().hex[:8]}"
        
        metadata = {
            'created_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'environment': 'auto',
            'trigger_event': trigger_event,
            'auto_generated': True
        }
        
        if self.save_checkpoint_with_validation(checkpoint_id, session_id, data, metadata):
            return checkpoint_id
        else:
            raise RuntimeError(f"Failed to save auto checkpoint for session {session_id}")
    
    def save_manual_checkpoint(self, session_id: str, data: Any,
                             user_id: str, description: str = "") -> str:
        """Save a manual checkpoint with user information."""
        import uuid
        checkpoint_id = f"manual_{uuid.uuid4().hex[:8]}"
        
        metadata = {
            'created_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'environment': 'manual',
            'user_id': user_id,
            'description': description,
            'manual_created': True
        }
        
        if self.save_checkpoint_with_validation(checkpoint_id, session_id, data, metadata):
            return checkpoint_id
        else:
            raise RuntimeError(f"Failed to save manual checkpoint for session {session_id}")
    
    def save_periodic_checkpoint(self, session_id: str, data: Any,
                               interval_minutes: int = 30) -> str:
        """Save a periodic checkpoint."""
        import uuid
        checkpoint_id = f"periodic_{uuid.uuid4().hex[:8]}"
        
        metadata = {
            'created_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'environment': 'periodic',
            'interval_minutes': interval_minutes,
            'periodic_created': True
        }
        
        if self.save_checkpoint_with_validation(checkpoint_id, session_id, data, metadata):
            return checkpoint_id
        else:
            raise RuntimeError(f"Failed to save periodic checkpoint for session {session_id}")
    
    def batch_save_checkpoints(self, checkpoints: list) -> Dict[str, bool]:
        """Save multiple checkpoints in batch."""
        results = {}
        
        for checkpoint_data in checkpoints:
            checkpoint_id = checkpoint_data.get('checkpoint_id')
            session_id = checkpoint_data.get('session_id')
            data = checkpoint_data.get('data')
            metadata = checkpoint_data.get('metadata')
            
            if not all([checkpoint_id, session_id, data]):
                results[checkpoint_id or 'unknown'] = False
                continue
            
            success = self.save_checkpoint_with_validation(
                checkpoint_id, session_id, data, metadata
            )
            results[checkpoint_id] = success
        
        return results
    
    def _validate_checkpoint_data(self, data: Any) -> bool:
        """Validate checkpoint data structure."""
        try:
            # Test JSON serialization
            json.dumps(data)
            
            # Check size (prevent extremely large checkpoints)
            data_size = len(json.dumps(data))
            if data_size > 50 * 1024 * 1024:  # 50MB limit
                print(f"Checkpoint data too large: {data_size} bytes")
                return False
            
            return True
        except (TypeError, ValueError) as e:
            print(f"Data validation error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected validation error: {e}")
            return False
    
    def _create_default_metadata(self) -> Dict:
        """Create default metadata for checkpoint."""
        return {
            'created_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'environment': 'default'
        }
    
    def _create_backup_checkpoint(self, checkpoint_id: str, session_id: str,
                                data: Any, metadata: Dict):
        """Create a backup of the checkpoint."""
        try:
            backup_dir = os.path.join(os.path.dirname(self.persistence.db_path), "backups")
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"checkpoint_{checkpoint_id}_{timestamp}.json")
            
            backup_data = {
                'checkpoint_id': checkpoint_id,
                'session_id': session_id,
                'timestamp': metadata.get('created_at'),
                'data': data,
                'metadata': metadata
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Failed to create backup checkpoint: {e}")
    
    def get_save_statistics(self) -> Dict:
        """Get statistics about saved checkpoints."""
        try:
            total_checkpoints = self.persistence.get_checkpoint_count()
            sessions = self.persistence.list_sessions()
            
            return {
                'total_checkpoints': total_checkpoints,
                'total_sessions': len(sessions),
                'sessions': sessions,
                'backup_enabled': self.backup_enabled
            }
        except Exception as e:
            return {'error': str(e)}