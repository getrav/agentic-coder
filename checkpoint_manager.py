import os
import shutil
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import threading
from checkpoint_persistence import CheckpointPersistence


class CheckpointManager:
    """Comprehensive checkpoint cleanup and management system."""
    
    def __init__(self, db_path: str = "checkpoints.db", 
                 backup_path: str = "backups"):
        self.persistence = CheckpointPersistence(db_path)
        self.backup_path = backup_path
        self._lock = threading.Lock()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.backup_path, exist_ok=True)
        archive_dir = os.path.join(self.backup_path, "archive")
        os.makedirs(archive_dir, exist_ok=True)
    
    def cleanup_old_checkpoints(self, max_age_days: int = 30,
                               create_backup: bool = True) -> Dict:
        """Clean up checkpoints older than specified days."""
        try:
            with self._lock:
                backup_result = None
                if create_backup:
                    backup_result = self._backup_old_checkpoints(max_age_days)
                
                deleted_count = self.persistence.cleanup_old_checkpoints(max_age_days)
                
                result = {
                    'deleted_count': deleted_count,
                    'max_age_days': max_age_days,
                    'backup_created': create_backup,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if backup_result is not None:
                    result['backup_result'] = backup_result
                
                return result
        except Exception as e:
            return {'error': str(e)}
    
    def cleanup_by_session_age(self, max_session_age_days: int = 7) -> Dict:
        """Clean up all checkpoints for sessions older than specified days."""
        try:
            sessions = self.persistence.list_sessions()
            cutoff_date = datetime.utcnow() - timedelta(days=max_session_age_days)
            
            deleted_sessions = []
            total_deleted = 0
            
            for session_id in sessions:
                checkpoints = self.persistence.load_checkpoints_by_session(session_id)
                if checkpoints:
                    latest_timestamp = checkpoints[0]['timestamp']
                    checkpoint_date = datetime.fromisoformat(latest_timestamp)
                    
                    if checkpoint_date < cutoff_date:
                        if self.persistence.delete_session_checkpoints(session_id):
                            deleted_sessions.append(session_id)
                            total_deleted += len(checkpoints)
            
            return {
                'deleted_sessions': deleted_sessions,
                'total_deleted': total_deleted,
                'max_session_age_days': max_session_age_days
            }
        except Exception as e:
            return {'error': str(e)}
    
    def cleanup_by_size_limit(self, max_checkpoints: int = 1000,
                            keep_newest: bool = True) -> Dict:
        """Clean up checkpoints when exceeding size limit."""
        try:
            total_count = self.persistence.get_checkpoint_count()
            
            if total_count <= max_checkpoints:
                return {
                    'current_count': total_count,
                    'max_limit': max_checkpoints,
                    'deleted_count': 0,
                    'message': 'No cleanup needed'
                }
            
            sessions = self.persistence.list_sessions()
            all_checkpoints = []
            
            # Collect all checkpoints with timestamps
            for session_id in sessions:
                checkpoints = self.persistence.load_checkpoints_by_session(session_id)
                for checkpoint in checkpoints:
                    all_checkpoints.append({
                        'checkpoint_id': checkpoint['checkpoint_id'],
                        'session_id': checkpoint['session_id'],
                        'timestamp': checkpoint['timestamp']
                    })
            
            # Sort by timestamp
            all_checkpoints.sort(key=lambda x: x['timestamp'])
            
            # Determine which to delete
            if keep_newest:
                to_delete = all_checkpoints[:-(max_checkpoints)]
            else:
                to_delete = all_checkpoints[max_checkpoints:]
            
            # Delete checkpoints
            deleted_count = 0
            for checkpoint in to_delete:
                if self.persistence.delete_checkpoint(checkpoint['checkpoint_id']):
                    deleted_count += 1
            
            return {
                'original_count': total_count,
                'max_limit': max_checkpoints,
                'deleted_count': deleted_count,
                'final_count': total_count - deleted_count,
                'keep_newest': keep_newest
            }
        except Exception as e:
            return {'error': str(e)}
    
    def cleanup_duplicate_checkpoints(self, session_id: Optional[str] = None) -> Dict:
        """Identify and remove duplicate checkpoints."""
        try:
            sessions = [session_id] if session_id else self.persistence.list_sessions()
            total_deleted = 0
            duplicates_found = {}
            
            for session in sessions:
                checkpoints = self.persistence.load_checkpoints_by_session(session)
                data_hashes = {}
                duplicates = []
                
                for checkpoint in checkpoints:
                    import hashlib
                    import json
                    
                    data_json = json.dumps(checkpoint['data'], sort_keys=True)
                    data_hash = hashlib.md5(data_json.encode()).hexdigest()
                    
                    if data_hash in data_hashes:
                        duplicates.append({
                            'checkpoint_id': checkpoint['checkpoint_id'],
                            'hash': data_hash,
                            'original_checkpoint': data_hashes[data_hash]
                        })
                    else:
                        data_hashes[data_hash] = checkpoint['checkpoint_id']
                
                # Keep the newest checkpoint in each duplicate group
                if duplicates:
                    deleted_in_session = 0
                    for dup in duplicates:
                        if self.persistence.delete_checkpoint(dup['checkpoint_id']):
                            deleted_in_session += 1
                            total_deleted += 1
                    
                    duplicates_found[session] = {
                        'duplicates': len(duplicates),
                        'deleted': deleted_in_session
                    }
            
            return {
                'total_duplicates_found': sum(d['duplicates'] for d in duplicates_found.values()),
                'total_deleted': total_deleted,
                'duplicates_by_session': duplicates_found
            }
        except Exception as e:
            return {'error': str(e)}
    
    def archive_checkpoints(self, session_id: str,
                          archive_name: Optional[str] = None) -> Dict:
        """Archive all checkpoints for a session."""
        try:
            if not archive_name:
                archive_name = f"archive_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            archive_file = os.path.join(self.backup_path, "archive", f"{archive_name}.json")
            
            checkpoints = self.persistence.load_checkpoints_by_session(session_id)
            
            if not checkpoints:
                return {'error': f'No checkpoints found for session {session_id}'}
            
            archive_data = {
                'archive_name': archive_name,
                'session_id': session_id,
                'created_at': datetime.utcnow().isoformat(),
                'checkpoint_count': len(checkpoints),
                'checkpoints': checkpoints
            }
            
            import json
            with open(archive_file, 'w') as f:
                json.dump(archive_data, f, indent=2)
            
            # Delete original checkpoints after successful archive
            deleted_count = 0
            if self.persistence.delete_session_checkpoints(session_id):
                deleted_count = len(checkpoints)
            
            return {
                'archive_file': archive_file,
                'session_id': session_id,
                'checkpoints_archived': len(checkpoints),
                'checkpoints_deleted': deleted_count,
                'archive_size': os.path.getsize(archive_file)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def restore_from_archive(self, archive_file: str, 
                           delete_archive: bool = False) -> Dict:
        """Restore checkpoints from an archive file."""
        try:
            import json
            with open(archive_file, 'r') as f:
                archive_data = json.load(f)
            
            session_id = archive_data['session_id']
            checkpoints = archive_data['checkpoints']
            restored_count = 0
            
            for checkpoint in checkpoints:
                if self.persistence.save_checkpoint(
                    checkpoint['checkpoint_id'],
                    checkpoint['session_id'],
                    checkpoint['data'],
                    checkpoint.get('metadata')
                ):
                    restored_count += 1
            
            if delete_archive:
                os.remove(archive_file)
            
            return {
                'session_id': session_id,
                'total_checkpoints': len(checkpoints),
                'restored_count': restored_count,
                'archive_file': archive_file,
                'archive_deleted': delete_archive
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _backup_old_checkpoints(self, max_age_days: int) -> Dict:
        """Create backup of checkpoints before cleanup."""
        try:
            backup_name = f"cleanup_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            backup_file = os.path.join(self.backup_path, f"{backup_name}.json")
            
            sessions = self.persistence.list_sessions()
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            
            backup_data = {
                'backup_name': backup_name,
                'created_at': datetime.utcnow().isoformat(),
                'max_age_days': max_age_days,
                'sessions': {}
            }
            
            total_checkpoints = 0
            
            for session_id in sessions:
                checkpoints = self.persistence.load_checkpoints_by_session(session_id)
                old_checkpoints = []
                
                for checkpoint in checkpoints:
                    checkpoint_date = datetime.fromisoformat(checkpoint['timestamp'])
                    if checkpoint_date < cutoff_date:
                        old_checkpoints.append(checkpoint)
                
                if old_checkpoints:
                    backup_data['sessions'][session_id] = old_checkpoints
                    total_checkpoints += len(old_checkpoints)
            
            import json
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            return {
                'backup_file': backup_file,
                'total_checkpoints': total_checkpoints,
                'sessions_backed_up': len(backup_data['sessions'])
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_storage_stats(self) -> Dict:
        """Get comprehensive storage statistics."""
        try:
            db_size = os.path.getsize(self.persistence.db_path) if os.path.exists(self.persistence.db_path) else 0
            
            backup_size = 0
            backup_files = []
            if os.path.exists(self.backup_path):
                for root, dirs, files in os.walk(self.backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        backup_size += os.path.getsize(file_path)
                        backup_files.append({
                            'file': file,
                            'size': os.path.getsize(file_path),
                            'path': file_path
                        })
            
            total_checkpoints = self.persistence.get_checkpoint_count()
            sessions = self.persistence.list_sessions()
            
            # Get checkpoint size distribution
            checkpoint_sizes = []
            for session_id in sessions:
                checkpoints = self.persistence.load_checkpoints_by_session(session_id)
                for checkpoint in checkpoints:
                    import json
                    size = len(json.dumps(checkpoint['data']))
                    checkpoint_sizes.append(size)
            
            avg_checkpoint_size = sum(checkpoint_sizes) / len(checkpoint_sizes) if checkpoint_sizes else 0
            max_checkpoint_size = max(checkpoint_sizes) if checkpoint_sizes else 0
            
            return {
                'database': {
                    'file': self.persistence.db_path,
                    'size_bytes': db_size,
                    'size_mb': round(db_size / (1024 * 1024), 2)
                },
                'backups': {
                    'total_size_bytes': backup_size,
                    'total_size_mb': round(backup_size / (1024 * 1024), 2),
                    'file_count': len(backup_files),
                    'files': backup_files[:10]  # First 10 files
                },
                'checkpoints': {
                    'total_count': total_checkpoints,
                    'total_sessions': len(sessions),
                    'sessions': sessions,
                    'avg_size_bytes': round(avg_checkpoint_size, 2),
                    'max_size_bytes': max_checkpoint_size
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def run_maintenance(self, config: Dict) -> Dict:
        """Run comprehensive maintenance with multiple cleanup strategies."""
        results = {
            'maintenance_run': datetime.utcnow().isoformat(),
            'config': config,
            'results': {}
        }
        
        try:
            # Age-based cleanup
            if 'max_age_days' in config:
                age_result = self.cleanup_old_checkpoints(
                    config['max_age_days'],
                    create_backup=config.get('create_backup', True)
                )
                results['results']['age_cleanup'] = age_result
            
            # Session age cleanup
            if 'max_session_age_days' in config:
                session_result = self.cleanup_by_session_age(
                    config['max_session_age_days']
                )
                results['results']['session_cleanup'] = session_result
            
            # Size limit cleanup
            if 'max_checkpoints' in config:
                size_result = self.cleanup_by_size_limit(
                    config['max_checkpoints'],
                    keep_newest=config.get('keep_newest', True)
                )
                results['results']['size_cleanup'] = size_result
            
            # Duplicate cleanup
            if config.get('remove_duplicates', False):
                dup_result = self.cleanup_duplicate_checkpoints()
                results['results']['duplicate_cleanup'] = dup_result
            
            # Get final statistics
            stats = self.get_storage_stats()
            results['final_stats'] = stats
            
            return results
        except Exception as e:
            results['error'] = str(e)
            return results