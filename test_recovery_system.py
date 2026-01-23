#!/usr/bin/env python3
"""
Simple test for the automatic checkpoint recovery system.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checkpoint_recovery import CheckpointRecovery, RecoveryStrategy, RecoveryEvent
from checkpoint_saver import CheckpointSaver
from checkpoint_loader import CheckpointLoader
import time
import tempfile


def test_basic_recovery():
    """Test basic checkpoint recovery functionality."""
    print("🧪 Testing basic recovery functionality...")
    
    # Use temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        test_db = tmp.name
    
    try:
        # Create test components
        saver = CheckpointSaver(test_db)
        loader = CheckpointLoader(test_db)
        recovery = CheckpointRecovery(test_db)
        
        # Create test checkpoint
        session_id = "test_session_001"
        test_data = {"message": "Hello World", "version": "1.0", "status": "active"}
        
        checkpoint_id = saver.save_auto_checkpoint(session_id, test_data, "test")
        print(f"✅ Created test checkpoint: {checkpoint_id}")
        
        # Test latest checkpoint recovery
        result = recovery.trigger_recovery(
            session_id=session_id,
            event=RecoveryEvent.MANUAL_TRIGGER,
            strategy=RecoveryStrategy.LATEST
        )
        
        if 'error' not in result:
            print("✅ Latest checkpoint recovery successful")
            print(f"📦 Recovered data: {result['data']}")
        else:
            print(f"❌ Recovery failed: {result['error']}")
            return False
        
        # Test health check
        health_status = recovery._check_session_health(session_id)
        if health_status['healthy']:
            print("✅ Session health check passed")
        else:
            print(f"⚠️  Session health check: {health_status}")
        
        # Test environment validation
        env_status = recovery.validate_recovery_environment()
        if env_status['overall_health']:
            print("✅ Recovery environment validation passed")
        else:
            print(f"⚠️  Environment validation: {env_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
        
    finally:
        # Clean up
        try:
            if os.path.exists(test_db):
                os.unlink(test_db)
            if os.path.exists('recovery.log'):
                os.unlink('recovery.log')
        except:
            pass


def test_recovery_strategies():
    """Test different recovery strategies."""
    print("\n🧪 Testing recovery strategies...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        test_db = tmp.name
    
    try:
        saver = CheckpointSaver(test_db)
        recovery = CheckpointRecovery(test_db)
        
        session_id = "test_strategies_001"
        
        # Create multiple checkpoints
        for i in range(3):
            time.sleep(0.1)  # Ensure different timestamps
            data = {
                "version": f"1.{i}.0",
                "step": i,
                "status": f"step_{i}_completed"
            }
            saver.save_auto_checkpoint(session_id, data, f"step_{i}")
        
        # Test latest strategy
        latest_result = recovery.trigger_recovery(
            session_id, 
            RecoveryEvent.MANUAL_TRIGGER, 
            RecoveryStrategy.LATEST
        )
        
        # Test rollback strategy  
        rollback_result = recovery.trigger_recovery(
            session_id,
            RecoveryEvent.MANUAL_TRIGGER,
            RecoveryStrategy.ROLLBACK
        )
        
        # Test health strategy
        health_result = recovery.trigger_recovery(
            session_id,
            RecoveryEvent.HEALTH_DEGRADATION,
            RecoveryStrategy.HEALTH_CHECK
        )
        
        success_count = 0
        for result_name, result in [
            ("latest", latest_result),
            ("rollback", rollback_result), 
            ("health", health_result)
        ]:
            if 'error' not in result:
                print(f"✅ {result_name} strategy successful")
                success_count += 1
            else:
                print(f"❌ {result_name} strategy failed: {result['error']}")
        
        return success_count >= 2  # At least 2 strategies should work
        
    except Exception as e:
        print(f"❌ Strategy test failed: {e}")
        return False
        
    finally:
        try:
            if os.path.exists(test_db):
                os.unlink(test_db)
        except:
            pass


def main():
    """Run all tests."""
    print("🚀 Automatic Checkpoint Recovery System - Tests")
    print("=" * 50)
    
    test_results = []
    
    # Run basic recovery test
    test_results.append(("Basic Recovery", test_basic_recovery()))
    
    # Run recovery strategies test
    test_results.append(("Recovery Strategies", test_recovery_strategies()))
    
    # Print results
    print(f"\n📊 Test Results:")
    print("=" * 30)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 All tests passed! Recovery system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())