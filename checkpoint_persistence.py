import sqlite3
import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import threading


class CheckpointPersistence:
    def __init__(self, db_path: str = "checkpoints.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    checkpoint_id TEXT UNIQUE NOT NULL,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    data TEXT NOT NULL,
                    metadata TEXT
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_id 
                ON checkpoints(session_id)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON checkpoints(timestamp)
            ''')
    
    def save_checkpoint(self, checkpoint_id: str, session_id: str, 
                       data: Any, metadata: Optional[Dict] = None) -> bool:
        """Save a checkpoint to the database."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        INSERT OR REPLACE INTO checkpoints 
                        (checkpoint_id, session_id, timestamp, data, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        checkpoint_id,
                        session_id,
                        datetime.utcnow().isoformat(),
                        json.dumps(data) if not isinstance(data, str) else data,
                        json.dumps(metadata) if metadata else None
                    ))
                    conn.commit()
            return True
        except Exception as e:
            print(f"Error saving checkpoint: {e}")
            return False
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict]:
        """Load a specific checkpoint by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT checkpoint_id, session_id, timestamp, data, metadata
                    FROM checkpoints 
                    WHERE checkpoint_id = ?
                ''', (checkpoint_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'checkpoint_id': row['checkpoint_id'],
                        'session_id': row['session_id'],
                        'timestamp': row['timestamp'],
                        'data': json.loads(row['data']) if row['data'] else None,
                        'metadata': json.loads(row['metadata']) if row['metadata'] else None
                    }
                return None
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            return None
    
    def load_checkpoints_by_session(self, session_id: str) -> List[Dict]:
        """Load all checkpoints for a specific session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT checkpoint_id, session_id, timestamp, data, metadata
                    FROM checkpoints 
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                ''', (session_id,))
                
                checkpoints = []
                for row in cursor.fetchall():
                    checkpoints.append({
                        'checkpoint_id': row['checkpoint_id'],
                        'session_id': row['session_id'],
                        'timestamp': row['timestamp'],
                        'data': json.loads(row['data']) if row['data'] else None,
                        'metadata': json.loads(row['metadata']) if row['metadata'] else None
                    })
                return checkpoints
        except Exception as e:
            print(f"Error loading session checkpoints: {e}")
            return []
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a specific checkpoint."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute('''
                        DELETE FROM checkpoints 
                        WHERE checkpoint_id = ?
                    ''', (checkpoint_id,))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting checkpoint: {e}")
            return False
    
    def delete_session_checkpoints(self, session_id: str) -> bool:
        """Delete all checkpoints for a specific session."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute('''
                        DELETE FROM checkpoints 
                        WHERE session_id = ?
                    ''', (session_id,))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting session checkpoints: {e}")
            return False
    
    def cleanup_old_checkpoints(self, max_age_days: int = 30) -> int:
        """Delete checkpoints older than specified days."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    cutoff_date = cutoff_date.replace(day=cutoff_date.day - max_age_days)
                    
                    cursor = conn.execute('''
                        DELETE FROM checkpoints 
                        WHERE timestamp < ?
                    ''', (cutoff_date.isoformat(),))
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            print(f"Error cleaning up old checkpoints: {e}")
            return 0
    
    def get_checkpoint_count(self) -> int:
        """Get total number of checkpoints."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM checkpoints')
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting checkpoint count: {e}")
            return 0
    
    def list_sessions(self) -> List[str]:
        """Get list of all session IDs."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT DISTINCT session_id FROM checkpoints')
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []