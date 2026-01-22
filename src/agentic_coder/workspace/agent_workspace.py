"""
AgentWorkspace provides git worktree isolation for agent workspaces.

This module creates and manages isolated git worktrees for each agent,
ensuring that agent work is properly isolated and can be safely
managed without affecting the main repository.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
import subprocess
import logging

logger = logging.getLogger(__name__)


class AgentWorkspace:
    """Manages isolated git workspaces for agents using git worktree."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize AgentWorkspace manager.
        
        Args:
            base_path: Base directory for workspaces. Defaults to temp directory.
        """
        self.base_path = Path(base_path) if base_path else Path(tempfile.gettempdir()) / "agent-workspaces"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.active_workspaces: Dict[str, Path] = {}
        
    def create_workspace(self, agent_id: str, repo_url: str, 
                        branch: str = "main") -> Path:
        """
        Create a new isolated workspace for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            repo_url: URL of the git repository
            branch: Branch to checkout (default: main)
            
        Returns:
            Path to the created workspace
            
        Raises:
            RuntimeError: If workspace creation fails
        """
        workspace_path = self.base_path / agent_id
        
        # Clean up existing workspace if it exists
        if workspace_path.exists():
            self._cleanup_workspace(workspace_path)
            
        try:
            # Create a bare clone if it doesn't exist
            bare_repo_path = self.base_path / f"{agent_id}-bare.git"
            if not bare_repo_path.exists():
                subprocess.run(
                    ["git", "clone", "--bare", repo_url, str(bare_repo_path)],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
            # Create worktree from the bare repository
            subprocess.run(
                ["git", "worktree", "add", str(workspace_path), branch],
                cwd=bare_repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Configure the workspace
            self._configure_workspace(workspace_path, agent_id)
            
            self.active_workspaces[agent_id] = workspace_path
            logger.info(f"Created workspace for agent {agent_id} at {workspace_path}")
            
            return workspace_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create workspace for agent {agent_id}: {e}")
            raise RuntimeError(f"Workspace creation failed: {e.stderr}")
            
    def _configure_workspace(self, workspace_path: Path, agent_id: str):
        """Configure the workspace with agent-specific settings."""
        # Set git user info for the agent
        subprocess.run(
            ["git", "config", "user.name", f"Agent {agent_id}"],
            cwd=workspace_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", f"{agent_id}@agent.local"],
            cwd=workspace_path,
            check=True,
            capture_output=True
        )
        
    def get_workspace(self, agent_id: str) -> Optional[Path]:
        """Get the workspace path for an agent."""
        return self.active_workspaces.get(agent_id)
        
    def cleanup_workspace(self, agent_id: str):
        """Clean up a workspace and remove it from active workspaces."""
        if agent_id in self.active_workspaces:
            workspace_path = self.active_workspaces[agent_id]
            self._cleanup_workspace(workspace_path)
            del self.active_workspaces[agent_id]
            logger.info(f"Cleaned up workspace for agent {agent_id}")
            
    def _cleanup_workspace(self, workspace_path: Path):
        """Clean up a workspace directory and its worktree."""
        try:
            # Remove the worktree
            if workspace_path.exists():
                subprocess.run(
                    ["git", "worktree", "remove", str(workspace_path)],
                    cwd=workspace_path.parent,
                    check=False,  # Don't fail if worktree doesn't exist
                    capture_output=True
                )
                # Remove the directory
                shutil.rmtree(workspace_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup workspace {workspace_path}: {e}")
            
    def cleanup_all_workspaces(self):
        """Clean up all active workspaces."""
        for agent_id in list(self.active_workspaces.keys()):
            self.cleanup_workspace(agent_id)
            
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List all active workspaces."""
        workspaces = []
        for agent_id, path in self.active_workspaces.items():
            try:
                # Get current branch
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=path,
                    check=True,
                    capture_output=True,
                    text=True
                )
                current_branch = result.stdout.strip()
                
                # Check if working directory is clean
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=path,
                    check=True,
                    capture_output=True,
                    text=True
                )
                is_clean = len(result.stdout.strip()) == 0
                
                workspaces.append({
                    "agent_id": agent_id,
                    "path": str(path),
                    "branch": current_branch,
                    "is_clean": is_clean
                })
            except Exception as e:
                logger.warning(f"Failed to get info for workspace {agent_id}: {e}")
                workspaces.append({
                    "agent_id": agent_id,
                    "path": str(path),
                    "branch": "unknown",
                    "is_clean": False
                })
                
        return workspaces
        
    def commit_changes(self, agent_id: str, message: str) -> bool:
        """
        Commit changes in an agent's workspace.
        
        Args:
            agent_id: Agent identifier
            message: Commit message
            
        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.active_workspaces:
            logger.error(f"No workspace found for agent {agent_id}")
            return False
            
        workspace_path = self.active_workspaces[agent_id]
        
        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=workspace_path,
                check=True,
                capture_output=True
            )
            
            # Commit changes
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=workspace_path,
                check=True,
                capture_output=True
            )
            
            logger.info(f"Committed changes for agent {agent_id}: {message}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit changes for agent {agent_id}: {e}")
            return False
            
    def push_changes(self, agent_id: str, remote: str = "origin", 
                    branch: Optional[str] = None) -> bool:
        """
        Push changes from agent workspace to remote.
        
        Args:
            agent_id: Agent identifier
            remote: Remote name (default: origin)
            branch: Branch to push (default: current branch)
            
        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.active_workspaces:
            logger.error(f"No workspace found for agent {agent_id}")
            return False
            
        workspace_path = self.active_workspaces[agent_id]
        
        try:
            cmd = ["git", "push", remote]
            if branch:
                cmd.extend([f"HEAD:{branch}"])
            else:
                cmd.append("--set-upstream")
                # Get current branch
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=workspace_path,
                    check=True,
                    capture_output=True,
                    text=True
                )
                current_branch = result.stdout.strip()
                cmd.append(f"HEAD:{current_branch}")
                
            subprocess.run(
                cmd,
                cwd=workspace_path,
                check=True,
                capture_output=True
            )
            
            logger.info(f"Pushed changes for agent {agent_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push changes for agent {agent_id}: {e}")
            return False


# Global instance
workspace_manager = AgentWorkspace()