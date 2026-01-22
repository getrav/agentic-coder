#!/usr/bin/env python3
"""
SQLite Checkpoint Persistence System

A comprehensive system for saving, loading, and managing checkpoints 
using SQLite as the persistence backend.

Features:
- SQLite-based checkpoint storage
- Thread-safe operations
- Checkpoint validation and error handling
- Automatic backup and cleanup
- Caching for improved performance
- Comprehensive management utilities
"""

import os
import sys
from datetime import datetime
from checkpoint_persistence import CheckpointPersistence
from checkpoint_model import Checkpoint, CheckpointManager as CheckpointModelManager
from checkpoint_saver import CheckpointSaver
from checkpoint_loader import CheckpointLoader
from checkpoint_manager import CheckpointManager


def main():
    """Demonstrate the checkpoint persistence system functionality."""
    print("SQLite Checkpoint Persistence System Demo")
    print("=" * 50)
    
    # Initialize components
    db_path = "demo_checkpoints.db"
    persistence = CheckpointPersistence(db_path)
    saver = CheckpointSaver(db_path, backup_enabled=True)
    loader = CheckpointLoader(db_path)
    manager = CheckpointManager(db_path)
    
    print(f"Database path: {db_path}")
    print()
    
    # Demo 1: Basic checkpoint operations
    print("1. Basic Checkpoint Operations")
    print("-" * 30)
    
    # Create a session
    session_id = "demo_session_001"
    print(f"Session ID: {session_id}")
    
    # Save some checkpoints
    for i in range(3):
        checkpoint_id = f"demo_checkpoint_{i}"
        data = {
            "step": i + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "data": f"Sample data for step {i + 1}",
            "metadata": {
                "user": "demo_user",
                "environment": "development"
            }
        }
        
        success = persistence.save_checkpoint(
            checkpoint_id, session_id, data, data["metadata"]
        )
        print(f"  Saved checkpoint {checkpoint_id}: {'✓' if success else '✗'}")
    
    print()
    
    # Demo 2: Enhanced saving features
    print("2. Enhanced Checkpoint Saving")
    print("-" * 30)
    
    # Auto checkpoint
    auto_data = {"auto": True, "trigger": "timer", "value": "auto_generated"}
    auto_checkpoint_id = saver.save_auto_checkpoint(session_id, auto_data, "timer")
    print(f"  Auto checkpoint: {auto_checkpoint_id}")
    
    # Manual checkpoint
    manual_data = {"manual": True, "user_action": "save_point", "value": "manual_save"}
    manual_checkpoint_id = saver.save_manual_checkpoint(
        session_id, manual_data, "demo_user", "Manual save during demo"
    )
    print(f"  Manual checkpoint: {manual_checkpoint_id}")
    
    print()
    
    # Demo 3: Loading and querying
    print("3. Checkpoint Loading and Querying")
    print("-" * 30)
    
    # Load all checkpoints for session
    session_checkpoints = loader.load_session_checkpoints(session_id)
    print(f"  Total checkpoints in session: {len(session_checkpoints)}")
    
    # Load latest checkpoint
    latest_checkpoint = loader.load_latest_checkpoint(session_id)
    if latest_checkpoint:
        print(f"  Latest checkpoint: {latest_checkpoint['checkpoint_id']}")
        print(f"    Timestamp: {latest_checkpoint['timestamp']}")
    
    # Search checkpoints
    search_results = loader.search_checkpoints(session_id, "manual")
    print(f"  Checkpoints containing 'manual': {len(search_results)}")
    
    print()
    
    # Demo 4: Checkpoint management
    print("4. Checkpoint Management")
    print("-" * 30)
    
    # Get storage statistics
    stats = manager.get_storage_stats()
    print(f"  Total checkpoints: {stats['checkpoints']['total_count']}")
    print(f"  Database size: {stats['database']['size_mb']} MB")
    
    # Backup and cleanup
    cleanup_result = manager.cleanup_by_size_limit(max_checkpoints=5)
    print(f"  Size limit cleanup: {cleanup_result.get('deleted_count', 0)} deleted")
    
    print()
    
    # Demo 5: Batch operations
    print("5. Batch Operations")
    print("-" * 30)
    
    # Create another session for batch demo
    batch_session = "batch_demo_session"
    batch_checkpoints = []
    
    for i in range(5):
        batch_checkpoints.append({
            'checkpoint_id': f'batch_{i}',
            'session_id': batch_session,
            'data': {
                'batch_id': i,
                'processed': False,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    
    # Save in batch
    batch_results = saver.batch_save_checkpoints(batch_checkpoints)
    print(f"  Batch save results: {len(batch_results)} checkpoints")
    success_count = sum(1 for result in batch_results.values() if result)
    print(f"  Successfully saved: {success_count}/{len(batch_results)}")
    
    # Load in batch
    checkpoint_ids = [f'batch_{i}' for i in range(5)]
    batch_load_results = loader.batch_load_checkpoints(checkpoint_ids)
    print(f"  Batch load results: {len(batch_load_results)} checkpoints")
    
    print()
    
    # Demo 6: Checkpoint model usage
    print("6. Checkpoint Data Model")
    print("-" * 30)
    
    # Create checkpoint using data model
    checkpoint_data = {
        'checkpoint_id': 'model_demo_001',
        'session_id': session_id,
        'timestamp': datetime.utcnow().isoformat(),
        'data': {'model': 'demo', 'structured': True},
        'metadata': {'version': '1.0', 'created_by': 'data_model'}
    }
    
    try:
        checkpoint = Checkpoint.from_dict(checkpoint_data)
        print(f"  Checkpoint model created: {checkpoint.checkpoint_id}")
        print(f"  Session: {checkpoint.session_id}")
        print(f"  Data: {checkpoint.data}")
    except ValueError as e:
        print(f"  Model creation failed: {e}")
    
    print()
    
    # Demo 7: Maintenance operations
    print("7. System Maintenance")
    print("-" * 30)
    
    # Run comprehensive maintenance
    maintenance_config = {
        'max_age_days': 30,
        'max_checkpoints': 50,
        'create_backup': True,
        'remove_duplicates': True
    }
    
    maintenance_result = manager.run_maintenance(maintenance_config)
    if 'error' not in maintenance_result:
        print("  Maintenance completed successfully")
        print(f"  Results: {len(maintenance_result['results'])} operations")
    else:
        print(f"  Maintenance failed: {maintenance_result['error']}")
    
    # Final statistics
    final_stats = manager.get_storage_stats()
    print(f"  Final checkpoint count: {final_stats['checkpoints']['total_count']}")
    print(f"  Final database size: {final_stats['database']['size_mb']} MB")
    
    print()
    print("Demo completed successfully!")
    print(f"Database file: {db_path}")
    print(f"Backup directory: {manager.backup_path}")


def run_tests():
    """Run the test suite."""
    print("Running Checkpoint Persistence Tests")
    print("=" * 40)
    
    try:
        import test_checkpoint_persistence
        import unittest
        
        # Run tests with specific test classes
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test classes
        test_classes = [
            test_checkpoint_persistence.TestCheckpointPersistence,
            test_checkpoint_persistence.TestCheckpointModel,
            test_checkpoint_persistence.TestCheckpointSaver,
            test_checkpoint_persistence.TestCheckpointLoader,
            test_checkpoint_persistence.TestCheckpointManager
        ]
        
        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        print()
        if result.wasSuccessful():
            print("All tests passed! ✓")
        else:
            print(f"Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        
        return result.wasSuccessful()
    except Exception as e:
        print(f"Test execution failed: {e}")
        return False


def usage():
    """Print usage information."""
    print("SQLite Checkpoint Persistence System")
    print()
    print("Usage:")
    print("  python main.py demo    - Run the demo")
    print("  python main.py test    - Run the tests")
    print("  python main.py help    - Show this help")
    print()
    print("Components:")
    print("  - CheckpointPersistence: Basic SQLite operations")
    print("  - CheckpointSaver: Enhanced saving with validation")
    print("  - CheckpointLoader: Loading with caching and search")
    print("  - CheckpointManager: Cleanup and management utilities")
    print("  - Checkpoint: Data model for checkpoints")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "demo":
            main()
        elif command == "test":
            success = run_tests()
            sys.exit(0 if success else 1)
        elif command == "help":
            usage()
        else:
            print(f"Unknown command: {command}")
            usage()
            sys.exit(1)
    else:
        # Default to demo
        main()