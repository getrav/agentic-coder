"""Tests for AgentWorkspace functionality."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.agentic_coder.workspace import AgentWorkspace


class TestAgentWorkspace:
    """Test cases for AgentWorkspace class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = AgentWorkspace(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        self.workspace.cleanup_all_workspaces()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    @patch('subprocess.run')
    def test_create_workspace_success(self, mock_subprocess):
        """Test successful workspace creation."""
        # Mock git commands
        mock_subprocess.return_value = Mock(returncode=0)
        
        workspace_path = self.workspace.create_workspace(
            "test-agent", "https://github.com/test/repo.git"
        )
        
        expected_path = Path(self.temp_dir) / "test-agent"
        assert workspace_path == expected_path
        assert "test-agent" in self.workspace.active_workspaces
        
    def test_get_workspace_existing(self):
        """Test getting existing workspace."""
        self.workspace.active_workspaces["test-agent"] = Path("/test/path")
        
        result = self.workspace.get_workspace("test-agent")
        assert result == Path("/test/path")
        
    def test_get_workspace_nonexistent(self):
        """Test getting non-existent workspace."""
        result = self.workspace.get_workspace("nonexistent")
        assert result is None
        
    @patch('subprocess.run')
    def test_commit_changes_success(self, mock_subprocess):
        """Test successful commit of changes."""
        self.workspace.active_workspaces["test-agent"] = Path("/test/path")
        mock_subprocess.return_value = Mock(returncode=0)
        
        result = self.workspace.commit_changes("test-agent", "test commit")
        
        assert result is True
        assert mock_subprocess.call_count == 2  # git add and git commit
        
    def test_commit_changes_no_workspace(self):
        """Test committing changes without workspace."""
        result = self.workspace.commit_changes("nonexistent", "test commit")
        assert result is False
        
    @patch('subprocess.run')
    def test_push_changes_success(self, mock_subprocess):
        """Test successful push of changes."""
        self.workspace.active_workspaces["test-agent"] = Path("/test/path")
        
        # Mock git branch and git push
        mock_subprocess.side_effect = [
            Mock(stdout="main\n", returncode=0),  # git branch
            Mock(returncode=0)  # git push
        ]
        
        result = self.workspace.push_changes("test-agent")
        
        assert result is True
        assert mock_subprocess.call_count == 2
        
    def test_push_changes_no_workspace(self):
        """Test pushing changes without workspace."""
        result = self.workspace.push_changes("nonexistent")
        assert result is False
        
    def test_cleanup_workspace(self):
        """Test workspace cleanup."""
        workspace_path = Path(self.temp_dir) / "test-agent"
        self.workspace.active_workspaces["test-agent"] = workspace_path
        
        self.workspace.cleanup_workspace("test-agent")
        
        assert "test-agent" not in self.workspace.active_workspaces
        
    def test_cleanup_all_workspaces(self):
        """Test cleanup of all workspaces."""
        self.workspace.active_workspaces = {
            "agent1": Path("/test1"),
            "agent2": Path("/test2")
        }
        
        self.workspace.cleanup_all_workspaces()
        
        assert len(self.workspace.active_workspaces) == 0
        
    @patch('subprocess.run')
    def test_list_workspaces_success(self, mock_subprocess):
        """Test successful listing of workspaces."""
        workspace_path = Path(self.temp_dir) / "test-agent"
        self.workspace.active_workspaces["test-agent"] = workspace_path
        
        # Mock git commands
        mock_subprocess.side_effect = [
            Mock(stdout="main\n", returncode=0),  # git branch
            Mock(stdout="", returncode=0)  # git status (clean)
        ]
        
        workspaces = self.workspace.list_workspaces()
        
        assert len(workspaces) == 1
        assert workspaces[0]["agent_id"] == "test-agent"
        assert workspaces[0]["branch"] == "main"
        assert workspaces[0]["is_clean"] is True