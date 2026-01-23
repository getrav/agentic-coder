import json
import os
import threading
import time
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from checkpoint_loader import CheckpointLoader
from checkpoint_saver import CheckpointSaver
from checkpoint_persistence import CheckpointPersistence


class RecoveryStrategy(Enum):
    """Recovery strategies for automatic checkpoint recovery."""
    LATEST = "latest"              # Use most recent checkpoint
    BEST_MATCH = "best_match"      # Find best matching checkpoint based on criteria
    ROLLBACK = "rollback"          # Rollback to previous stable state
    HEALTH_CHECK = "health_check"  # Use healthiest checkpoint


class RecoveryEvent(Enum):
    """Events that can trigger automatic recovery."""
    SYSTEM_FAILURE = "system_failure"
    DATA_CORRUPTION = "data_corruption" 
    CRASH_RECOVERY = "crash_recovery"
    HEALTH_DEGRADATION = "health_degradation"
    MANUAL_TRIGGER = "manual_trigger"


class CheckpointRecovery:
    """Automatic checkpoint recovery system with multiple strategies and event handling."""
    
    def __init__(self, db_path: str = "checkpoints.db", 
                 recovery_config: Optional[Dict] = None):
        self.db_path = db_path
        self.persistence = CheckpointPersistence(db_path)
        self.loader = CheckpointLoader(db_path)
        self.saver = CheckpointSaver(db_path)
        
        # Default recovery configuration
        self.config = recovery_config or {
            'auto_recovery_enabled': True,
            'max_recovery_attempts': 3,
            'recovery_timeout': 30,
            'health_check_interval': 60,
            'backup_on_recovery': True,
            'recovery_log_file': 'recovery.log'
        }
        
        self._recovery_attempts = {}
        self._recovery_lock = threading.RLock()
        self._event_handlers = {}
        self._recovery_stats = {
            'total_recoveries': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'last_recovery_time': None
        }
        
        # Initialize recovery logging
        self._init_recovery_logging()
    
    def _init_recovery_logging(self):
        """Initialize recovery logging system."""
        self.log_file = self.config.get('recovery_log_file', 'recovery.log')
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("Checkpoint Recovery Log\n")
                f.write("=" * 50 + "\n")
    
    def _log_recovery_event(self, event_type: str, message: str, 
                           checkpoint_id: Optional[str] = None):
        """Log recovery events to file and console."""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] {event_type}: {message}"
        if checkpoint_id:
            log_entry += f" (Checkpoint: {checkpoint_id})"
        
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def register_recovery_handler(self, event: RecoveryEvent, 
                                handler: Callable):
        """Register a handler for recovery events."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    def trigger_recovery(self, session_id: str, 
                        event: RecoveryEvent = RecoveryEvent.SYSTEM_FAILURE,
                        strategy: RecoveryStrategy = RecoveryStrategy.LATEST,
                        recovery_criteria: Optional[Dict] = None) -> Dict:
        """Trigger automatic recovery for a session."""
        
        if not self.config.get('auto_recovery_enabled', True):
            return {'error': 'Auto recovery is disabled'}
        
        session_key = f"{session_id}_{event.value}"
        
        # Check recovery attempt limits
        if session_key in self._recovery_attempts:
            if self._recovery_attempts[session_key] >= self.config.get('max_recovery_attempts', 3):
                return {'error': f'Max recovery attempts exceeded for {session_key}'}
        
        with self._recovery_lock:
            self._recovery_attempts[session_key] = self._recovery_attempts.get(session_key, 0) + 1
            
            self._log_recovery_event(
                "RECOVERY_ATTEMPT", 
                f"Starting recovery for session {session_id} using {strategy.value} strategy",
                session_id
            )
            
            try:
                # Execute recovery based on strategy
                if strategy == RecoveryStrategy.LATEST:
                    result = self._recover_latest_checkpoint(session_id)
                elif strategy == RecoveryStrategy.BEST_MATCH:
                    result = self._recover_best_match_checkpoint(session_id, recovery_criteria)
                elif strategy == RecoveryStrategy.ROLLBACK:
                    result = self._recover_rollback_checkpoint(session_id)
                elif strategy == RecoveryStrategy.HEALTH_CHECK:
                    result = self._recover_healthiest_checkpoint(session_id)
                else:
                    result = {'error': f'Unknown recovery strategy: {strategy.value}'}
                
                # Update recovery statistics
                self._recovery_stats['total_recoveries'] += 1
                self._recovery_stats['last_recovery_time'] = datetime.utcnow().isoformat()
                
                if 'error' not in result:
                    self._recovery_stats['successful_recoveries'] += 1
                    self._log_recovery_event(
                        "RECOVERY_SUCCESS",
                        f"Successfully recovered session {session_id}",
                        result.get('checkpoint_id')
                    )
                    
                    # Trigger success handlers
                    self._trigger_event_handlers(event, result, success=True)
                else:
                    self._recovery_stats['failed_recoveries'] += 1
                    self._log_recovery_event(
                        "RECOVERY_FAILED",
                        f"Failed to recover session {session_id}: {result['error']}"
                    )
                    
                    # Trigger failure handlers
                    self._trigger_event_handlers(event, result, success=False)
                
                return result
                
            except Exception as e:
                error_msg = f"Recovery failed with exception: {str(e)}"
                self._recovery_stats['failed_recoveries'] += 1
                self._log_recovery_event("RECOVERY_EXCEPTION", error_msg)
                return {'error': error_msg}
    
    def _recover_latest_checkpoint(self, session_id: str) -> Dict:
        """Recover using the most recent checkpoint."""
        latest_checkpoint = self.loader.load_latest_checkpoint(session_id)
        
        if latest_checkpoint is None:
            return {'error': f'No checkpoints found for session {session_id}'}
        
        # Create backup before recovery if enabled
        if self.config.get('backup_on_recovery', True):
            self._create_recovery_backup(latest_checkpoint)
        
        return {
            'success': True,
            'checkpoint_id': latest_checkpoint['checkpoint_id'],
            'session_id': session_id,
            'recovery_strategy': 'latest',
            'timestamp': latest_checkpoint['timestamp'],
            'data': latest_checkpoint['data'],
            'metadata': latest_checkpoint['metadata']
        }
    
    def _recover_best_match_checkpoint(self, session_id: str, 
                                     criteria: Optional[Dict] = None) -> Dict:
        """Recover using the best matching checkpoint based on criteria."""
        checkpoints = self.loader.load_session_checkpoints(session_id)
        
        if not checkpoints:
            return {'error': f'No checkpoints found for session {session_id}'}
        
        if not criteria:
            criteria = {'prioritize_recent': True}
        
        # Score checkpoints based on criteria
        scored_checkpoints = []
        for checkpoint in checkpoints:
            score = self._score_checkpoint(checkpoint, criteria)
            scored_checkpoints.append((score, checkpoint))
        
        # Sort by score (descending)
        scored_checkpoints.sort(key=lambda x: x[0], reverse=True)
        best_checkpoint = scored_checkpoints[0][1]
        
        # Create backup before recovery if enabled
        if self.config.get('backup_on_recovery', True):
            self._create_recovery_backup(best_checkpoint)
        
        return {
            'success': True,
            'checkpoint_id': best_checkpoint['checkpoint_id'],
            'session_id': session_id,
            'recovery_strategy': 'best_match',
            'score': scored_checkpoints[0][0],
            'timestamp': best_checkpoint['timestamp'],
            'data': best_checkpoint['data'],
            'metadata': best_checkpoint['metadata']
        }
    
    def _recover_rollback_checkpoint(self, session_id: str, 
                                   steps_back: int = 1) -> Dict:
        """Recover by rolling back to a previous checkpoint."""
        checkpoints = self.loader.load_session_checkpoints(
            session_id, 
            sort_by='timestamp', 
            sort_order='desc'
        )
        
        if not checkpoints:
            return {'error': f'No checkpoints found for session {session_id}'}
        
        if len(checkpoints) <= steps_back:
            return {'error': f'Not enough checkpoints to rollback {steps_back} steps'}
        
        rollback_checkpoint = checkpoints[steps_back]
        
        # Create backup before recovery if enabled
        if self.config.get('backup_on_recovery', True):
            self._create_recovery_backup(rollback_checkpoint)
        
        return {
            'success': True,
            'checkpoint_id': rollback_checkpoint['checkpoint_id'],
            'session_id': session_id,
            'recovery_strategy': 'rollback',
            'steps_back': steps_back,
            'timestamp': rollback_checkpoint['timestamp'],
            'data': rollback_checkpoint['data'],
            'metadata': rollback_checkpoint['metadata']
        }
    
    def _recover_healthiest_checkpoint(self, session_id: str) -> Dict:
        """Recover using the healthiest checkpoint based on validation."""
        checkpoints = self.loader.load_session_checkpoints(session_id)
        
        if not checkpoints:
            return {'error': f'No checkpoints found for session {session_id}'}
        
        # Health score checkpoints based on validation
        healthiest_checkpoint = None
        best_health_score = -1
        
        for checkpoint in checkpoints:
            health_score = self._calculate_health_score(checkpoint)
            if health_score > best_health_score:
                best_health_score = health_score
                healthiest_checkpoint = checkpoint
        
        if healthiest_checkpoint is None:
            return {'error': f'No healthy checkpoints found for session {session_id}'}
        
        # Create backup before recovery if enabled
        if self.config.get('backup_on_recovery', True):
            self._create_recovery_backup(healthiest_checkpoint)
        
        return {
            'success': True,
            'checkpoint_id': healthiest_checkpoint['checkpoint_id'],
            'session_id': session_id,
            'recovery_strategy': 'health_check',
            'health_score': best_health_score,
            'timestamp': healthiest_checkpoint['timestamp'],
            'data': healthiest_checkpoint['data'],
            'metadata': healthiest_checkpoint['metadata']
        }
    
    def _score_checkpoint(self, checkpoint: Dict, criteria: Dict) -> float:
        """Score a checkpoint based on recovery criteria."""
        score = 0.0
        
        # Prioritize recent checkpoints
        if criteria.get('prioritize_recent', True):
            checkpoint_time = datetime.fromisoformat(checkpoint['timestamp'])
            age_hours = (datetime.utcnow() - checkpoint_time).total_seconds() / 3600
            recency_score = max(0, 1.0 - (age_hours / 24.0))  # Decay over 24 hours
            score += recency_score * 0.4
        
        # Check data completeness
        data = checkpoint.get('data', {})
        completeness_score = 1.0 if data else 0.0
        score += completeness_score * 0.3
        
        # Check metadata quality
        metadata = checkpoint.get('metadata', {})
        metadata_score = 1.0 if metadata else 0.5
        score += metadata_score * 0.2
        
        # Check size (prefer medium-sized checkpoints)
        try:
            data_size = len(json.dumps(data))
            if 1000 <= data_size <= 100000:  # 1KB to 100KB
                size_score = 1.0
            else:
                size_score = 0.5
            score += size_score * 0.1
        except:
            score += 0.05  # Small penalty for serialization issues
        
        return score
    
    def _calculate_health_score(self, checkpoint: Dict) -> float:
        """Calculate health score for a checkpoint."""
        health_score = 0.0
        
        try:
            # Data structure validation
            data = checkpoint.get('data', {})
            json.dumps(data)  # Test serialization
            health_score += 0.3
            
            # Metadata completeness
            metadata = checkpoint.get('metadata', {})
            if metadata:
                health_score += 0.2
                if 'created_at' in metadata:
                    health_score += 0.1
            
            # Checkpoint ID format
            checkpoint_id = checkpoint.get('checkpoint_id', '')
            if len(checkpoint_id) > 0:
                health_score += 0.2
            
            # Timestamp validity
            timestamp = checkpoint.get('timestamp', '')
            try:
                datetime.fromisoformat(timestamp)
                health_score += 0.2
            except:
                pass
            
        except Exception:
            health_score = 0.0
        
        return health_score
    
    def _create_recovery_backup(self, checkpoint: Dict):
        """Create a backup of the checkpoint being recovered."""
        try:
            backup_dir = os.path.join(os.path.dirname(self.db_path), "recovery_backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                backup_dir, 
                f"recovery_backup_{checkpoint['checkpoint_id']}_{timestamp}.json"
            )
            
            backup_data = {
                'recovery_timestamp': datetime.utcnow().isoformat(),
                'original_checkpoint': checkpoint
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
                
        except Exception as e:
            self._log_recovery_event("BACKUP_FAILED", f"Failed to create recovery backup: {str(e)}")
    
    def _trigger_event_handlers(self, event: RecoveryEvent, 
                              result: Dict, success: bool):
        """Trigger registered event handlers."""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    handler(event, result, success)
                except Exception as e:
                    self._log_recovery_event("HANDLER_ERROR", f"Event handler failed: {str(e)}")
    
    def start_auto_monitoring(self, check_interval: Optional[int] = None):
        """Start automatic monitoring for recovery needs."""
        if check_interval is None:
            check_interval = self.config.get('health_check_interval', 60)
        
        # Ensure check_interval is a valid number
        check_interval = max(1, int(check_interval) if check_interval is not None else 60)
        
        def monitoring_loop():
            while self.config.get('auto_recovery_enabled', True):
                self._perform_health_checks()
                time.sleep(float(check_interval))
        
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        
        self._log_recovery_event("MONITORING_START", f"Started auto-monitoring with {check_interval}s interval")
    
    def _perform_health_checks(self):
        """Perform health checks on all active sessions."""
        try:
            sessions = self.persistence.list_sessions()
            
            for session_id in sessions:
                health_status = self._check_session_health(session_id)
                
                if health_status.get('needs_recovery', False):
                    self.trigger_recovery(
                        session_id=session_id,
                        event=RecoveryEvent.HEALTH_DEGRADATION,
                        strategy=RecoveryStrategy.HEALTH_CHECK
                    )
                    
        except Exception as e:
            self._log_recovery_event("HEALTH_CHECK_ERROR", f"Health check failed: {str(e)}")
    
    def _check_session_health(self, session_id: str) -> Dict:
        """Check the health of a session's checkpoints."""
        checkpoints = self.loader.load_session_checkpoints(session_id)
        
        if not checkpoints:
            return {'session_id': session_id, 'healthy': False, 'needs_recovery': True}
        
        # Calculate overall health
        total_health = 0
        unhealthy_count = 0
        
        for checkpoint in checkpoints:
            health_score = self._calculate_health_score(checkpoint)
            total_health += health_score
            
            if health_score < 0.5:  # Consider checkpoints with health < 0.5 as unhealthy
                unhealthy_count += 1
        
        avg_health = total_health / len(checkpoints) if checkpoints else 0
        
        health_status = {
            'session_id': session_id,
            'healthy': avg_health > 0.7,
            'needs_recovery': unhealthy_count > len(checkpoints) * 0.3,  # 30% unhealthy threshold
            'avg_health_score': avg_health,
            'unhealthy_count': unhealthy_count,
            'total_checkpoints': len(checkpoints)
        }
        
        return health_status
    
    def get_recovery_statistics(self) -> Dict:
        """Get comprehensive recovery statistics."""
        return {
            'recovery_stats': self._recovery_stats.copy(),
            'config': self.config.copy(),
            'active_sessions': len(self.persistence.list_sessions()),
            'recovery_attempts_by_session': self._recovery_attempts.copy(),
            'registered_handlers': {event.value: len(handlers) 
                                 for event, handlers in self._event_handlers.items()}
        }
    
    def reset_recovery_attempts(self, session_id: Optional[str] = None):
        """Reset recovery attempt counters."""
        with self._recovery_lock:
            if session_id:
                # Reset attempts for specific session
                keys_to_remove = [key for key in self._recovery_attempts.keys() 
                                if key.startswith(session_id)]
                for key in keys_to_remove:
                    del self._recovery_attempts[key]
            else:
                # Reset all attempts
                self._recovery_attempts.clear()
    
    def validate_recovery_environment(self) -> Dict:
        """Validate that the recovery environment is properly configured."""
        validation_results = {
            'database_accessible': False,
            'backup_directory_exists': False,
            'log_file_accessible': False,
            'overall_health': False
        }
        
        try:
            # Test database access
            self.persistence.get_checkpoint_count()
            validation_results['database_accessible'] = True
        except:
            pass
        
        # Test backup directory
        backup_dir = os.path.join(os.path.dirname(self.db_path), "recovery_backups")
        try:
            os.makedirs(backup_dir, exist_ok=True)
            validation_results['backup_directory_exists'] = True
        except:
            pass
        
        # Test log file access
        try:
            with open(self.log_file, 'a') as f:
                f.write("")
            validation_results['log_file_accessible'] = True
        except:
            pass
        
        validation_results['overall_health'] = all(validation_results.values())
        
        return validation_results