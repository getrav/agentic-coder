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
from structured_logger import get_logger, LogConfig, LogLevel


def main():
    """Demonstrate the checkpoint persistence system functionality."""
    # Configure structured logging
    logger_config = LogConfig(
        level=LogLevel.INFO,
        format_json=True,
        output_file="logs/demo.log"
    )
    logger = get_logger("demo", logger_config)
    
    logger.info("SQLite Checkpoint Persistence System Demo", 
                component="main", action="start_demo")
    
    # Initialize components
    db_path = "demo_checkpoints.db"
    persistence = CheckpointPersistence(db_path)
    saver = CheckpointSaver(db_path, backup_enabled=True)
    loader = CheckpointLoader(db_path)
    manager = CheckpointManager(db_path)
    
    logger.info("Components initialized", 
                database_path=db_path, 
                components=["persistence", "saver", "loader", "manager"])
    
    # Demo 1: Basic checkpoint operations
    logger.info("Starting basic checkpoint operations", 
                demo_section="basic_operations", step=1)
    
    # Create a session
    session_id = "demo_session_001"
    logger.info("Created session", session_id=session_id)
    
    # Save some checkpoints
    saved_count = 0
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
        if success:
            saved_count += 1
            logger.info("Checkpoint saved successfully", 
                       checkpoint_id=checkpoint_id, 
                       session_id=session_id, 
                       step=i+1)
        else:
            logger.error("Failed to save checkpoint", 
                        checkpoint_id=checkpoint_id, 
                        session_id=session_id, 
                        step=i+1)
    
    logger.info("Basic checkpoint operations completed", 
                total_attempted=3, 
                total_saved=saved_count, 
                success_rate=saved_count/3)
    
    # Demo 2: Enhanced saving features
    logger.info("Starting enhanced checkpoint saving", 
                demo_section="enhanced_saving", step=2)
    
    # Auto checkpoint
    auto_data = {"auto": True, "trigger": "timer", "value": "auto_generated"}
    auto_checkpoint_id = saver.save_auto_checkpoint(session_id, auto_data, "timer")
    logger.info("Auto checkpoint saved", 
               checkpoint_id=auto_checkpoint_id, 
               session_id=session_id, 
               trigger="timer")
    
    # Manual checkpoint
    manual_data = {"manual": True, "user_action": "save_point", "value": "manual_save"}
    manual_checkpoint_id = saver.save_manual_checkpoint(
        session_id, manual_data, "demo_user", "Manual save during demo"
    )
    logger.info("Manual checkpoint saved", 
               checkpoint_id=manual_checkpoint_id, 
               session_id=session_id, 
               user="demo_user",
               description="Manual save during demo")
    
    # Demo 3: Loading and querying
    logger.info("Starting checkpoint loading and querying", 
                demo_section="loading_querying", step=3)
    
    # Load all checkpoints for session
    session_checkpoints = loader.load_session_checkpoints(session_id)
    logger.info("Loaded session checkpoints", 
               session_id=session_id, 
               checkpoint_count=len(session_checkpoints))
    
    # Load latest checkpoint
    latest_checkpoint = loader.load_latest_checkpoint(session_id)
    if latest_checkpoint:
        logger.info("Loaded latest checkpoint", 
                   session_id=session_id,
                   checkpoint_id=latest_checkpoint['checkpoint_id'],
                   timestamp=latest_checkpoint['timestamp'])
    else:
        logger.warn("No latest checkpoint found", session_id=session_id)
    
    # Search checkpoints
    search_results = loader.search_checkpoints(session_id, "manual")
    logger.info("Searched checkpoints", 
               session_id=session_id, 
               search_term="manual", 
               results_count=len(search_results))
    
    # Demo 4: Checkpoint management
    logger.info("Starting checkpoint management", 
                demo_section="checkpoint_management", step=4)
    
    # Get storage statistics
    stats = manager.get_storage_stats()
    logger.info("Retrieved storage statistics", 
               total_checkpoints=stats['checkpoints']['total_count'],
               database_size_mb=stats['database']['size_mb'])
    
    # Backup and cleanup
    cleanup_result = manager.cleanup_by_size_limit(max_checkpoints=5)
    logger.info("Performed cleanup by size limit", 
               max_checkpoints=5, 
               deleted_count=cleanup_result.get('deleted_count', 0))
    
    # Demo 5: Batch operations
    logger.info("Starting batch operations", 
                demo_section="batch_operations", step=5)
    
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
    success_count = sum(1 for result in batch_results.values() if result)
    logger.info("Batch save completed", 
               session_id=batch_session, 
               attempted=len(batch_results), 
               successful=success_count,
               success_rate=success_count/len(batch_results))
    
    # Load in batch
    checkpoint_ids = [f'batch_{i}' for i in range(5)]
    batch_load_results = loader.batch_load_checkpoints(checkpoint_ids)
    loaded_count = sum(1 for result in batch_load_results.values() if result is not None)
    logger.info("Batch load completed", 
               session_id=batch_session,
               attempted=len(checkpoint_ids), 
               successful=loaded_count,
               success_rate=loaded_count/len(checkpoint_ids))
    
    # Demo 6: Checkpoint model usage
    logger.info("Starting checkpoint data model demo", 
                demo_section="data_model", step=6)
    
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
        logger.info("Checkpoint model created successfully", 
                   checkpoint_id=checkpoint.checkpoint_id,
                   session_id=checkpoint.session_id,
                   data_keys=list(checkpoint.data.keys()))
    except ValueError as e:
        logger.error("Checkpoint model creation failed", 
                    checkpoint_data=checkpoint_data, 
                    error=str(e))
    
    # Demo 7: Maintenance operations
    logger.info("Starting system maintenance", 
                demo_section="maintenance", step=7)
    
    # Run comprehensive maintenance
    maintenance_config = {
        'max_age_days': 30,
        'max_checkpoints': 50,
        'create_backup': True,
        'remove_duplicates': True
    }
    
    maintenance_result = manager.run_maintenance(maintenance_config)
    if 'error' not in maintenance_result:
        logger.info("Maintenance completed successfully", 
                   operations_count=len(maintenance_result['results']),
                   config=maintenance_config)
    else:
        logger.error("Maintenance failed", 
                    config=maintenance_config, 
                    error=maintenance_result['error'])
    
    # Final statistics
    final_stats = manager.get_storage_stats()
    logger.info("Final system statistics", 
               final_checkpoint_count=final_stats['checkpoints']['total_count'],
               final_database_size_mb=final_stats['database']['size_mb'],
               database_path=db_path,
               backup_path=manager.backup_path)
    
    logger.info("Demo completed successfully", 
                total_demos=7, 
                final_status="success")


def run_tests():
    """Run the test suite."""
    logger = get_logger("test_runner")
    logger.info("Running Checkpoint Persistence Tests", action="test_execution_start")
    
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
        
        if result.wasSuccessful():
            logger.info("All tests passed successfully", 
                       total_tests=result.testsRun,
                       failures=0,
                       errors=0)
        else:
            logger.error("Tests failed", 
                        total_tests=result.testsRun,
                        failures=len(result.failures),
                        errors=len(result.errors),
                        failure_details=[str(failure) for failure in result.failures])
        
        return result.wasSuccessful()
    except Exception as e:
        logger.exception("Test execution failed", exception=e)
        return False


def usage():
    """Print usage information."""
    logger = get_logger("usage")
    logger.info("SQLite Checkpoint Persistence System")
    logger.info("Usage:")
    logger.info("  python main.py demo    - Run the demo")
    logger.info("  python main.py test    - Run the tests")
    logger.info("  python main.py help    - Show this help")
    logger.info("Components:")
    logger.info("  - CheckpointPersistence: Basic SQLite operations")
    logger.info("  - CheckpointSaver: Enhanced saving with validation")
    logger.info("  - CheckpointLoader: Loading with caching and search")
    logger.info("  - CheckpointManager: Cleanup and management utilities")
    logger.info("  - Checkpoint: Data model for checkpoints")


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