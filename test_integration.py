"""Integration tests for the agentic coding system."""

import unittest
import tempfile
import shutil
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Try to import pytest, but handle if it's not available
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create a dummy pytest module for testing
    class DummyPytest:
        @staticmethod
        def mark():
            class DummyMark:
                def asyncio(func):
                    return func
            return DummyMark()
    
    pytest = DummyPytest()

# Import the modules we need to test
from checkpoint_persistence import CheckpointPersistence
from checkpoint_manager import CheckpointManager
from checkpoint_saver import CheckpointSaver
from checkpoint_loader import CheckpointLoader
from checkpoint_model import Checkpoint, CheckpointMetadata

try:
    from src.agentic_coder.workspace import AgentWorkspace
    WORKSPACE_AVAILABLE = True
except ImportError:
    WORKSPACE_AVAILABLE = False

try:
    from beadsclient import BeadsClient
    BEADSCLIENT_AVAILABLE = True
except ImportError:
    BEADSCLIENT_AVAILABLE = False


class TestCheckpointIntegration(unittest.TestCase):
    """Integration tests for checkpoint system components."""
    
    def setUp(self):
        """Set up test environment with temporary directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_checkpoints.db")
        self.backup_path = os.path.join(self.temp_dir, "backups")
        os.makedirs(self.backup_path, exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_checkpoint_workflow(self):
        """Test complete checkpoint workflow from creation to cleanup."""
        # Initialize all components
        persistence = CheckpointPersistence(self.db_path)
        saver = CheckpointSaver(self.db_path, backup_enabled=False)
        loader = CheckpointLoader(self.db_path)
        manager = CheckpointManager(self.db_path, self.backup_path)
        
        # Create test data
        session_id = "integration_test_session"
        checkpoints_data = []
        
        # Step 1: Save multiple checkpoints using the saver
        for i in range(5):
            data = {
                "step": i + 1,
                "data": f"integration_test_data_{i}",
                "metadata": {"version": "1.0", "test": True}
            }
            checkpoint_id = saver.save_auto_checkpoint(session_id, data)
            self.assertIsNotNone(checkpoint_id)
            checkpoints_data.append((checkpoint_id, data))
        
        # Step 2: Load checkpoints using the loader
        session_checkpoints = loader.load_session_checkpoints(session_id)
        self.assertEqual(len(session_checkpoints), 5)
        
        # Step 3: Verify checkpoint order (should be descending by timestamp)
        for i in range(1, len(session_checkpoints)):
            self.assertGreaterEqual(
                session_checkpoints[i-1]['timestamp'],
                session_checkpoints[i]['timestamp']
            )
        
        # Step 4: Batch load specific checkpoints
        checkpoint_ids = [cp_id for cp_id, _ in checkpoints_data[:3]]
        batch_results = loader.batch_load_checkpoints(checkpoint_ids)
        self.assertEqual(len(batch_results), 3)
        
        # Step 5: Test manager operations
        stats = manager.get_storage_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('checkpoints', stats)
        self.assertEqual(stats['checkpoints']['total_count'], 5)
        
        # Step 6: Test cleanup operations
        maintenance_result = manager.run_maintenance({
            'max_age_days': 30,
            'max_checkpoints': 1000,
            'create_backup': False,
            'remove_duplicates': True
        })
        self.assertIsInstance(maintenance_result, dict)
        self.assertIn('maintenance_run', maintenance_result)
    
    def test_checkpoint_persistence_with_validation(self):
        """Test checkpoint persistence with data validation integration."""
        persistence = CheckpointPersistence(self.db_path)
        saver = CheckpointSaver(self.db_path, backup_enabled=False)
        loader = CheckpointLoader(self.db_path)
        
        # Test valid data
        valid_data = {
            "user_id": "test_user",
            "workspace": "/path/to/workspace",
            "changes": ["file1.py", "file2.py"],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        checkpoint_id = saver.save_manual_checkpoint(
            "valid_session", valid_data, "test_user", "Manual checkpoint"
        )
        self.assertIsNotNone(checkpoint_id)
        
        # Load and validate
        loaded = loader.load_checkpoint(checkpoint_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['data'], valid_data)
        self.assertTrue(loaded['metadata']['manual_created'])
        
        # Test invalid data (non-serializable)
        invalid_data = {
            "function": lambda x: x,  # Non-serializable
            "valid_data": "this should fail"
        }
        
        result = saver.save_checkpoint_with_validation(
            "invalid_checkpoint_id", "invalid_session", invalid_data
        )
        self.assertFalse(result)
    
    def test_concurrent_checkpoint_operations(self):
        """Test concurrent checkpoint operations."""
        import threading
        import time
        
        persistence = CheckpointPersistence(self.db_path)
        results = []
        errors = []
        
        def worker_function(worker_id):
            """Worker function for concurrent operations."""
            try:
                session_id = f"concurrent_session_{worker_id}"
                data = {"worker_id": worker_id, "timestamp": time.time()}
                
                # Save checkpoint
                success = persistence.save_checkpoint(
                    f"checkpoint_{worker_id}", session_id, data
                )
                
                # Load all checkpoints for this session
                checkpoints = persistence.load_checkpoints_by_session(session_id)
                
                results.append({
                    'worker_id': worker_id,
                    'save_success': success,
                    'checkpoint_count': len(checkpoints)
                })
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_function, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)
        
        for result in results:
            self.assertTrue(result['save_success'])
            self.assertEqual(result['checkpoint_count'], 1)


class TestWorkspaceIntegration(unittest.TestCase):
    """Integration tests for workspace management."""
    
    def setUp(self):
        """Set up test environment."""
        if not WORKSPACE_AVAILABLE:
            self.skipTest("AgentWorkspace not available")
        
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = AgentWorkspace(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        if WORKSPACE_AVAILABLE:
            self.workspace.cleanup_all_workspaces()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_workspace_lifecycle_with_checkpoints(self, mock_subprocess):
        """Test complete workspace lifecycle with checkpoint integration."""
        # Mock successful subprocess calls
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Step 1: Create workspace
        agent_id = "test_integration_agent"
        repo_url = "https://github.com/test/repo.git"
        
        workspace_path = self.workspace.create_workspace(agent_id, repo_url)
        self.assertIsNotNone(workspace_path)
        self.assertEqual(str(workspace_path), os.path.join(self.temp_dir, agent_id))
        
        # Step 2: Simulate workspace operations
        mock_subprocess.side_effect = [
            Mock(returncode=0, stdout="main\n", stderr=""),  # git branch
            Mock(returncode=0, stdout="", stderr=""),  # git status (clean)
        ]
        
        workspaces = self.workspace.list_workspaces()
        self.assertEqual(len(workspaces), 1)
        self.assertEqual(workspaces[0]['agent_id'], agent_id)
        self.assertTrue(workspaces[0]['is_clean'])
        
        # Step 3: Commit changes
        mock_subprocess.side_effect = None
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        commit_success = self.workspace.commit_changes(
            agent_id, "Integration test commit"
        )
        self.assertTrue(commit_success)
        
        # Step 4: Push changes
        mock_subprocess.side_effect = [
            Mock(returncode=0, stdout="main\n", stderr=""),  # git branch
            Mock(returncode=0, stdout="", stderr=""),  # git push
        ]
        
        push_success = self.workspace.push_changes(agent_id)
        self.assertTrue(push_success)
        
        # Step 5: Cleanup workspace
        self.workspace.cleanup_workspace(agent_id)
        
        # Verify workspace was cleaned up
        remaining_workspaces = self.workspace.list_workspaces()
        self.assertEqual(len(remaining_workspaces), 0)


class TestBeadsClientIntegration(unittest.TestCase):
    """Integration tests for BeadsClient."""
    
    def setUp(self):
        """Set up test environment."""
        if not BEADSCLIENT_AVAILABLE:
            self.skipTest("BeadsClient not available")
        
        self.client = BeadsClient()
    
    def test_beadsclient_workflow(self):
        """Test complete BeadsClient workflow."""
        if not BEADSCLIENT_AVAILABLE:
            return
        
        # Run the async test
        asyncio.run(self._async_beadsclient_workflow())
    
    async def _async_beadsclient_workflow(self):
        """Async implementation of the test."""
        if not BEADSCLIENT_AVAILABLE:
            return
        
        # Mock the BeadsClient methods
        with patch.object(self.client, 'run_command') as mock_run:
            mock_result = Mock()
            mock_result.success = True
            mock_result.stdout = '{"id": "AC-test-123", "title": "Test Issue"}'
            mock_result.stderr = ""
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            # Test creating an issue
            result = await self.client.create("Integration Test Issue")
            self.assertTrue(result.success)
            
            # Test updating the issue
            result = await self.client.update("AC-test-123", status="in_progress")
            self.assertTrue(result.success)
            
            # Test showing the issue
            result = await self.client.show("AC-test-123")
            self.assertTrue(result.success)
            
            # Test closing the issue
            result = await self.client.close("AC-test-123")
            self.assertTrue(result.success)


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests for the entire system."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "e2e_checkpoints.db")
        self.backup_path = os.path.join(self.temp_dir, "backups")
        os.makedirs(self.backup_path, exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_complete_agent_workflow(self, mock_subprocess):
        """Test complete agent workflow from workspace creation to cleanup."""
        if not WORKSPACE_AVAILABLE:
            self.skipTest("AgentWorkspace not available")
        
        # Initialize components
        persistence = CheckpointPersistence(self.db_path)
        saver = CheckpointSaver(self.db_path, backup_enabled=False)
        loader = CheckpointLoader(self.db_path)
        manager = CheckpointManager(self.db_path, self.backup_path)
        workspace = AgentWorkspace(self.temp_dir)
        
        # Mock subprocess calls
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Step 1: Create workspace for agent
        agent_id = "e2e_test_agent"
        repo_url = "https://github.com/test/repo.git"
        
        workspace_path = workspace.create_workspace(agent_id, repo_url)
        self.assertIsNotNone(workspace_path)
        
        # Step 2: Create initial checkpoint
        initial_data = {
            "agent_id": agent_id,
            "workspace": str(workspace_path),
            "status": "initialized",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        checkpoint_id = saver.save_manual_checkpoint(
            f"session_{agent_id}", initial_data, agent_id, "Initial setup"
        )
        self.assertIsNotNone(checkpoint_id)
        
        # Step 3: Simulate work progress with checkpoints
        mock_subprocess.side_effect = [
            Mock(returncode=0, stdout="main\n", stderr=""),  # git branch
            Mock(returncode=0, stdout="", stderr=""),  # git status
        ]
        
        workspaces = workspace.list_workspaces()
        self.assertEqual(len(workspaces), 1)
        
        # Create progress checkpoint
        progress_data = {
            "agent_id": agent_id,
            "progress": 50,
            "files_modified": ["test_file.py"],
            "status": "in_progress"
        }
        
        progress_checkpoint_id = saver.save_auto_checkpoint(
            f"session_{agent_id}", progress_data
        )
        self.assertIsNotNone(progress_checkpoint_id)
        
        # Step 4: Verify checkpoint history
        session_checkpoints = loader.load_session_checkpoints(f"session_{agent_id}")
        self.assertEqual(len(session_checkpoints), 2)
        
        # Step 5: Commit changes and create final checkpoint
        mock_subprocess.side_effect = None
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        commit_success = workspace.commit_changes(agent_id, "E2E test changes")
        self.assertTrue(commit_success)
        
        final_data = {
            "agent_id": agent_id,
            "progress": 100,
            "status": "completed",
            "commit_successful": True
        }
        
        final_checkpoint_id = saver.save_manual_checkpoint(
            f"session_{agent_id}", final_data, agent_id, "Work completed"
        )
        self.assertIsNotNone(final_checkpoint_id)
        
        # Step 6: Run maintenance and verify system state
        stats = manager.get_storage_stats()
        self.assertGreaterEqual(stats['checkpoints']['total_count'], 3)
        
        maintenance_result = manager.run_maintenance({
            'max_age_days': 1,
            'max_checkpoints': 10,
            'create_backup': True,
            'remove_duplicates': False
        })
        self.assertIsInstance(maintenance_result, dict)
        self.assertIn('maintenance_run', maintenance_result)
        
        # Step 7: Cleanup
        workspace.cleanup_workspace(agent_id)
        
        # Verify cleanup
        remaining_workspaces = workspace.list_workspaces()
        self.assertEqual(len(remaining_workspaces), 0)
        
        # Verify checkpoints are still preserved
        final_session_checkpoints = loader.load_session_checkpoints(f"session_{agent_id}")
        self.assertEqual(len(final_session_checkpoints), 3)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios."""
        persistence = CheckpointPersistence(self.db_path)
        saver = CheckpointSaver(self.db_path, backup_enabled=False)
        loader = CheckpointLoader(self.db_path)
        
        # Test 1: Attempt to save invalid data
        invalid_data = {
            "valid_field": "value",
            "invalid_field": lambda x: x  # Non-serializable
        }
        
        result = saver.save_checkpoint_with_validation("error_checkpoint_id", "error_test", invalid_data)
        self.assertFalse(result)
        
        # Test 2: Verify system is still functional after error
        valid_data = {"recovery": "successful", "test": True}
        checkpoint_id = saver.save_auto_checkpoint("recovery_test", valid_data)
        self.assertIsNotNone(checkpoint_id)
        
        # Test 3: Load checkpoint after recovery
        loaded = loader.load_checkpoint(checkpoint_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['data'], valid_data)
        
        # Test 4: Attempt to load non-existent checkpoint
        non_existent = loader.load_checkpoint("non_existent_id")
        self.assertIsNone(non_existent)
        
        # Test 5: Session with no checkpoints
        empty_checkpoints = loader.load_session_checkpoints("empty_session")
        self.assertEqual(len(empty_checkpoints), 0)


class TestPerformanceIntegration(unittest.TestCase):
    """Performance-focused integration tests."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "perf_checkpoints.db")
        self.persistence = CheckpointPersistence(self.db_path)
        self.saver = CheckpointSaver(self.db_path, backup_enabled=False)
        self.loader = CheckpointLoader(self.db_path, cache_size=100)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_bulk_checkpoint_operations(self):
        """Test performance with bulk checkpoint operations."""
        session_id = "bulk_test_session"
        num_checkpoints = 50
        
        # Create many checkpoints
        checkpoint_ids = []
        for i in range(num_checkpoints):
            data = {
                "bulk_test": True,
                "iteration": i,
                "data_size": "medium",
                "timestamp": f"2024-01-01T{i:02d}:00:00Z"
            }
            
            checkpoint_id = self.saver.save_auto_checkpoint(session_id, data)
            checkpoint_ids.append(checkpoint_id)
        
        self.assertEqual(len(checkpoint_ids), num_checkpoints)
        
        # Load all checkpoints for the session
        session_checkpoints = self.loader.load_session_checkpoints(session_id)
        self.assertEqual(len(session_checkpoints), num_checkpoints)
        
        # Test batch loading
        sample_ids = checkpoint_ids[:10]
        batch_results = self.loader.batch_load_checkpoints(sample_ids)
        self.assertEqual(len(batch_results), 10)
        
        # Test cache performance
        first_load = self.loader.load_checkpoint(checkpoint_ids[0], use_cache=True)
        second_load = self.loader.load_checkpoint(checkpoint_ids[0], use_cache=True)
        
        self.assertEqual(first_load, second_load)
        
        # Verify cache stats
        cache_stats = self.loader.get_cache_stats()
        self.assertGreaterEqual(cache_stats['cache_size'], 1)


if __name__ == '__main__':
    # Run the integration tests
    unittest.main(verbosity=2)