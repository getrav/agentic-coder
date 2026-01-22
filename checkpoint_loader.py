import json
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import threading
from checkpoint_model import Checkpoint, CheckpointMetadata


class CheckpointLoader:
    """Enhanced checkpoint loading functionality with caching and validation."""
    
    def __init__(self, db_path: str = "checkpoints.db", 
                 cache_size: int = 100, cache_ttl: int = 300):
        from checkpoint_persistence import CheckpointPersistence
        self.persistence = CheckpointPersistence(db_path)
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_timestamps = {}
        self._lock = threading.RLock()
    
    def load_checkpoint(self, checkpoint_id: str, 
                       use_cache: bool = True,
                       validate: bool = True) -> Optional[Dict]:
        """Load a checkpoint with caching and validation."""
        
        if use_cache:
            cached_data = self._get_from_cache(checkpoint_id)
            if cached_data is not None:
                if validate and not self._validate_checkpoint_data(cached_data):
                    print(f"Cached checkpoint {checkpoint_id} failed validation")
                    return None
                return cached_data
        
        # Load from persistence
        checkpoint_data = self.persistence.load_checkpoint(checkpoint_id)
        
        if checkpoint_data is None:
            return None
        
        if validate and not self._validate_checkpoint_data(checkpoint_data):
            print(f"Checkpoint {checkpoint_id} failed validation")
            return None
        
        # Update cache
        if use_cache:
            self._add_to_cache(checkpoint_id, checkpoint_data)
        
        return checkpoint_data
    
    def load_session_checkpoints(self, session_id: str,
                               sort_by: str = 'timestamp',
                               sort_order: str = 'desc',
                               limit: Optional[int] = None) -> List[Dict]:
        """Load all checkpoints for a session with sorting and limiting."""
        
        checkpoints = self.persistence.load_checkpoints_by_session(session_id)
        
        if not checkpoints:
            return []
        
        # Sort checkpoints
        if sort_by in ['timestamp', 'checkpoint_id']:
            reverse = sort_order.lower() == 'desc'
            checkpoints.sort(key=lambda x: x[sort_by], reverse=reverse)
        
        # Apply limit
        if limit and len(checkpoints) > limit:
            checkpoints = checkpoints[:limit]
        
        return checkpoints
    
    def load_latest_checkpoint(self, session_id: str) -> Optional[Dict]:
        """Load the most recent checkpoint for a session."""
        checkpoints = self.load_session_checkpoints(
            session_id, 
            sort_by='timestamp', 
            sort_order='desc',
            limit=1
        )
        
        return checkpoints[0] if checkpoints else None
    
    def load_checkpoints_by_timerange(self, session_id: str,
                                    start_time: str,
                                    end_time: str) -> List[Dict]:
        """Load checkpoints within a specific time range."""
        all_checkpoints = self.persistence.load_checkpoints_by_session(session_id)
        
        filtered_checkpoints = []
        for checkpoint in all_checkpoints:
            checkpoint_time = checkpoint.get('timestamp', '')
            if start_time <= checkpoint_time <= end_time:
                filtered_checkpoints.append(checkpoint)
        
        # Sort by timestamp
        filtered_checkpoints.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return filtered_checkpoints
    
    def load_checkpoints_by_metadata(self, session_id: str,
                                   metadata_filter: Dict) -> List[Dict]:
        """Load checkpoints that match metadata criteria."""
        all_checkpoints = self.persistence.load_checkpoints_by_session(session_id)
        
        matching_checkpoints = []
        for checkpoint in all_checkpoints:
            metadata = checkpoint.get('metadata', {})
            if self._matches_metadata_filter(metadata, metadata_filter):
                matching_checkpoints.append(checkpoint)
        
        return matching_checkpoints
    
    def batch_load_checkpoints(self, checkpoint_ids: List[str],
                              use_cache: bool = True,
                              validate: bool = True) -> Dict[str, Optional[Dict]]:
        """Load multiple checkpoints in batch."""
        results = {}
        
        for checkpoint_id in checkpoint_ids:
            results[checkpoint_id] = self.load_checkpoint(
                checkpoint_id, 
                use_cache=use_cache, 
                validate=validate
            )
        
        return results
    
    def load_and_restore_checkpoint(self, checkpoint_id: str,
                                  use_cache: bool = True) -> Checkpoint:
        """Load checkpoint and return as Checkpoint object."""
        checkpoint_data = self.load_checkpoint(checkpoint_id, use_cache=use_cache)
        
        if checkpoint_data is None:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        return Checkpoint.from_dict(checkpoint_data)
    
    def search_checkpoints(self, session_id: str, 
                         search_term: str,
                         search_fields: List[str] = ['data', 'metadata']) -> List[Dict]:
        """Search checkpoints for specific content."""
        checkpoints = self.persistence.load_checkpoints_by_session(session_id)
        
        matching_checkpoints = []
        search_term_lower = search_term.lower()
        
        for checkpoint in checkpoints:
            for field in search_fields:
                if field in checkpoint:
                    field_value = checkpoint[field]
                    if isinstance(field_value, str):
                        if search_term_lower in field_value.lower():
                            matching_checkpoints.append(checkpoint)
                            break
                    elif isinstance(field_value, dict):
                        field_text = json.dumps(field_value, separators=(',', ':'))
                        if search_term_lower in field_text.lower():
                            matching_checkpoints.append(checkpoint)
                            break
        
        return matching_checkpoints
    
    def _get_from_cache(self, checkpoint_id: str) -> Optional[Dict]:
        """Get checkpoint from cache if valid."""
        with self._lock:
            if checkpoint_id in self._cache:
                timestamp = self._cache_timestamps.get(checkpoint_id, 0)
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    return self._cache[checkpoint_id]
                else:
                    # Remove expired cache entry
                    del self._cache[checkpoint_id]
                    if checkpoint_id in self._cache_timestamps:
                        del self._cache_timestamps[checkpoint_id]
        return None
    
    def _add_to_cache(self, checkpoint_id: str, checkpoint_data: Dict):
        """Add checkpoint to cache with size management."""
        with self._lock:
            # Remove oldest entries if cache is full
            if len(self._cache) >= self.cache_size:
                oldest_key = min(self._cache_timestamps.keys(), 
                               key=lambda k: self._cache_timestamps[k])
                del self._cache[oldest_key]
                del self._cache_timestamps[oldest_key]
            
            self._cache[checkpoint_id] = checkpoint_data
            self._cache_timestamps[checkpoint_id] = datetime.now().timestamp()
    
    def clear_cache(self):
        """Clear all cached checkpoints."""
        with self._lock:
            self._cache.clear()
            self._cache_timestamps.clear()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        with self._lock:
            return {
                'cache_size': len(self._cache),
                'max_cache_size': self.cache_size,
                'cache_ttl': self.cache_ttl,
                'cached_checkpoints': list(self._cache.keys())
            }
    
    def _validate_checkpoint_data(self, checkpoint_data: Dict) -> bool:
        """Validate loaded checkpoint data."""
        try:
            required_fields = ['checkpoint_id', 'session_id', 'timestamp', 'data']
            for field in required_fields:
                if field not in checkpoint_data:
                    return False
                if not checkpoint_data[field]:
                    return False
            
            # Test data structure
            data = checkpoint_data['data']
            json.dumps(data)  # Test JSON serialization
            
            return True
        except Exception:
            return False
    
    def _matches_metadata_filter(self, metadata: Dict, filter_criteria: Dict) -> bool:
        """Check if metadata matches filter criteria."""
        for key, value in filter_criteria.items():
            if key not in metadata:
                return False
            if metadata[key] != value:
                return False
        return True
    
    def get_load_statistics(self) -> Dict:
        """Get statistics about loaded checkpoints."""
        try:
            total_checkpoints = self.persistence.get_checkpoint_count()
            sessions = self.persistence.list_sessions()
            cache_stats = self.get_cache_stats()
            
            return {
                'total_checkpoints': total_checkpoints,
                'total_sessions': len(sessions),
                'sessions': sessions,
                'cache_stats': cache_stats
            }
        except Exception as e:
            return {'error': str(e)}