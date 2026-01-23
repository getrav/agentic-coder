#!/usr/bin/env python3
"""
Example usage of the automatic checkpoint recovery system.

This example demonstrates how to use the CheckpointRecovery class to automatically
recover from system failures, data corruption, and other events.
"""

import time
import json
from checkpoint_recovery import CheckpointRecovery, RecoveryStrategy, RecoveryEvent
from checkpoint_saver import CheckpointSaver
from checkpoint_loader import CheckpointLoader


def example_recovery_handler(event, result, success):
    """Example event handler for recovery events."""
    print(f"🎯 Recovery Event Handler: {event.value}")
    print(f"✅ Success: {success}")
    if success:
        print(f"📦 Recovered checkpoint: {result.get('checkpoint_id')}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


def create_sample_checkpoints():
    """Create sample checkpoints for testing recovery."""
    print("🔧 Creating sample checkpoints...")
    
    saver = CheckpointSaver()
    
    # Create some sample checkpoints
    session_id = "example_session_001"
    
    # Checkpoint 1: Initial state
    data1 = {
        "version": "1.0.0",
        "status": "initialized",
        "config": {"theme": "default", "language": "en"},
        "user_data": {"name": "Alice", "preferences": {}}
    }
    checkpoint1 = saver.save_auto_checkpoint(session_id, data1, "initialization")
    print(f"✅ Created checkpoint 1: {checkpoint1}")
    
    # Checkpoint 2: Updated state
    time.sleep(1)  # Ensure different timestamps
    data2 = {
        "version": "1.1.0",
        "status": "running",
        "config": {"theme": "dark", "language": "en"},
        "user_data": {"name": "Alice", "preferences": {"theme": "dark", "notifications": True}}
    }
    checkpoint2 = saver.save_auto_checkpoint(session_id, data2, "configuration_update")
    print(f"✅ Created checkpoint 2: {checkpoint2}")
    
    # Checkpoint 3: Corrupted data (will be used for health check testing)
    time.sleep(1)
    data3 = {
        "version": "1.2.0",
        "status": "running",
        "config": {"theme": "dark", "language": "es"},
        "user_data": {"name": "Alice", "preferences": {"theme": "dark", "notifications": False}}
    }
    checkpoint3 = saver.save_manual_checkpoint(session_id, data3, "user_123", "Spanish language update")
    print(f"✅ Created checkpoint 3: {checkpoint3}")
    
    return session_id, [checkpoint1, checkpoint2, checkpoint3]


def demonstrate_recovery_strategies(session_id):
    """Demonstrate different recovery strategies."""
    print("\n🔄 Demonstrating recovery strategies...")
    
    recovery = CheckpointRecovery()
    
    # Register event handler
    recovery.register_recovery_handler(RecoveryEvent.SYSTEM_FAILURE, example_recovery_handler)
    recovery.register_recovery_handler(RecoveryEvent.MANUAL_TRIGGER, example_recovery_handler)
    
    # Strategy 1: Latest checkpoint recovery
    print("\n📌 Strategy 1: Latest Checkpoint Recovery")
    result = recovery.trigger_recovery(
        session_id=session_id,
        event=RecoveryEvent.MANUAL_TRIGGER,
        strategy=RecoveryStrategy.LATEST
    )
    print(f"🎯 Recovery Result: {json.dumps(result, indent=2, default=str)}")
    
    # Strategy 2: Best match recovery with criteria
    print("\n📌 Strategy 2: Best Match Recovery")
    criteria = {
        "prioritize_recent": True,
        "min_data_size": 100  # At least 100 bytes of data
    }
    result = recovery.trigger_recovery(
        session_id=session_id,
        event=RecoveryEvent.MANUAL_TRIGGER,
        strategy=RecoveryStrategy.BEST_MATCH,
        recovery_criteria=criteria
    )
    print(f"🎯 Recovery Result: {json.dumps(result, indent=2, default=str)}")
    
    # Strategy 3: Rollback recovery
    print("\n📌 Strategy 3: Rollback Recovery (1 step back)")
    result = recovery.trigger_recovery(
        session_id=session_id,
        event=RecoveryEvent.MANUAL_TRIGGER,
        strategy=RecoveryStrategy.ROLLBACK
    )
    print(f"🎯 Recovery Result: {json.dumps(result, indent=2, default=str)}")
    
    # Strategy 4: Health check recovery
    print("\n📌 Strategy 4: Health Check Recovery")
    result = recovery.trigger_recovery(
        session_id=session_id,
        event=RecoveryEvent.HEALTH_DEGRADATION,
        strategy=RecoveryStrategy.HEALTH_CHECK
    )
    print(f"🎯 Recovery Result: {json.dumps(result, indent=2, default=str)}")


def demonstrate_auto_monitoring():
    """Demonstrate automatic monitoring and health checks."""
    print("\n🔍 Demonstrating auto-monitoring...")
    
    recovery = CheckpointRecovery()
    
    # Validate recovery environment
    print("\n🔧 Validating recovery environment...")
    env_status = recovery.validate_recovery_environment()
    print(f"🎯 Environment Status: {json.dumps(env_status, indent=2)}")
    
    # Start auto-monitoring (this will run in background)
    print("\n🚀 Starting auto-monitoring...")
    recovery.start_auto_monitoring(check_interval=5)  # Check every 5 seconds
    
    # Perform manual health check
    print("\n📊 Performing manual health check...")
    sessions = recovery.persistence.list_sessions()
    for session_id in sessions:
        health = recovery._check_session_health(session_id)
        print(f"🎯 Session {session_id} Health: {json.dumps(health, indent=2)}")
    
    # Let monitoring run for a bit
    print("\n⏳ Auto-monitoring running for 15 seconds...")
    time.sleep(15)


def demonstrate_recovery_statistics():
    """Demonstrate recovery statistics and reporting."""
    print("\n📊 Demonstrating recovery statistics...")
    
    recovery = CheckpointRecovery()
    
    # Get comprehensive statistics
    stats = recovery.get_recovery_statistics()
    print(f"🎯 Recovery Statistics: {json.dumps(stats, indent=2, default=str)}")
    
    # Show recovery log
    print("\n📋 Recovery Log:")
    try:
        with open('recovery.log', 'r') as f:
            log_content = f.read()
            print(log_content[-1000:] if len(log_content) > 1000 else log_content)  # Show last 1000 chars
    except FileNotFoundError:
        print("❌ Recovery log file not found")


def main():
    """Main example function."""
    print("🚀 Automatic Checkpoint Recovery System - Example Usage")
    print("=" * 60)
    
    # Create sample checkpoints
    session_id, checkpoint_ids = create_sample_checkpoints()
    
    # Demonstrate recovery strategies
    demonstrate_recovery_strategies(session_id)
    
    # Demonstrate auto-monitoring
    demonstrate_auto_monitoring()
    
    # Show statistics and logs
    demonstrate_recovery_statistics()
    
    print("\n✅ Example completed successfully!")
    print("🎯 Check the 'recovery.log' file for detailed recovery logs.")
    print("🎯 Check the 'recovery_backups' directory for recovery backups.")


if __name__ == "__main__":
    main()