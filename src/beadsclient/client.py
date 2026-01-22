"""BeadsClient - Python wrapper around bd CLI with async support."""

import asyncio
import json
import subprocess
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of executing a bd command."""
    stdout: str
    stderr: str
    returncode: int
    success: bool

    @property
    def json(self) -> Any:
        """Parse stdout as JSON if possible."""
        try:
            return json.loads(self.stdout.strip())
        except json.JSONDecodeError:
            return self.stdout.strip()


class BeadsClient:
    """Python wrapper around bd CLI with async support."""

    def __init__(self, base_path: Optional[str] = None):
        """Initialize BeadsClient.
        
        Args:
            base_path: Base path for bd operations. If None, uses current directory.
        """
        self.base_path = base_path or "."

    async def run_command(
        self, 
        args: List[str], 
        cwd: Optional[str] = None,
        timeout: int = 30
    ) -> CommandResult:
        """Run a bd command asynchronously.
        
        Args:
            args: List of command arguments (e.g., ["show", "AC-pf4"])
            cwd: Working directory. If None, uses base_path.
            timeout: Command timeout in seconds.
            
        Returns:
            CommandResult containing stdout, stderr, and return code.
        """
        cmd = ["bd"] + args
        working_dir = cwd or self.base_path
        
        try:
            process = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=working_dir
                ),
                timeout=timeout
            )
            
            stdout, stderr = await process.communicate()
            
            return_code = process.returncode if process.returncode is not None else -1
            return CommandResult(
                stdout=stdout.decode('utf-8'),
                stderr=stderr.decode('utf-8'),
                returncode=return_code,
                success=return_code == 0
            )
            
        except asyncio.TimeoutError:
            return CommandResult(
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                returncode=-1,
                success=False
            )
        except Exception as e:
            return CommandResult(
                stdout="",
                stderr=f"Command failed: {str(e)}",
                returncode=-1,
                success=False
            )

    def run_command_sync(
        self, 
        args: List[str], 
        cwd: Optional[str] = None,
        timeout: int = 30
    ) -> CommandResult:
        """Run a bd command synchronously.
        
        Args:
            args: List of command arguments (e.g., ["show", "AC-pf4"])
            cwd: Working directory. If None, uses base_path.
            timeout: Command timeout in seconds.
            
        Returns:
            CommandResult containing stdout, stderr, and return code.
        """
        cmd = ["bd"] + args
        working_dir = cwd or self.base_path
        
        try:
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return CommandResult(
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                success=result.returncode == 0
            )
            
        except subprocess.TimeoutExpired:
            return CommandResult(
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                returncode=-1,
                success=False
            )
        except Exception as e:
            return CommandResult(
                stdout="",
                stderr=f"Command failed: {str(e)}",
                returncode=-1,
                success=False
            )

    # Convenience methods for common bd operations
    
    async def show(self, bead_id: str, **kwargs) -> CommandResult:
        """Show details for a bead."""
        return await self.run_command(["show", bead_id], **kwargs)
    
    def show_sync(self, bead_id: str, **kwargs) -> CommandResult:
        """Show details for a bead (synchronous)."""
        return self.run_command_sync(["show", bead_id], **kwargs)
    
    async def list_beads(self, **kwargs) -> CommandResult:
        """List beads."""
        return await self.run_command(["list"], **kwargs)
    
    def list_beads_sync(self, **kwargs) -> CommandResult:
        """List beads (synchronous)."""
        return self.run_command_sync(["list"], **kwargs)
    
    async def create(
        self, 
        title: str, 
        bead_type: str = "task",
        **kwargs
    ) -> CommandResult:
        """Create a new bead."""
        args = ["create", "--title", title, "--type", bead_type]
        return await self.run_command(args, **kwargs)
    
    def create_sync(
        self, 
        title: str, 
        bead_type: str = "task",
        **kwargs
    ) -> CommandResult:
        """Create a new bead (synchronous)."""
        args = ["create", "--title", title, "--type", bead_type]
        return self.run_command_sync(args, **kwargs)
    
    async def update(
        self, 
        bead_id: str, 
        status: Optional[str] = None,
        **kwargs
    ) -> CommandResult:
        """Update a bead."""
        args = ["update", bead_id]
        if status:
            args.extend(["--status", status])
        return await self.run_command(args, **kwargs)
    
    def update_sync(
        self, 
        bead_id: str, 
        status: Optional[str] = None,
        **kwargs
    ) -> CommandResult:
        """Update a bead (synchronous)."""
        args = ["update", bead_id]
        if status:
            args.extend(["--status", status])
        return self.run_command_sync(args, **kwargs)
    
    async def close(self, bead_id: str, **kwargs) -> CommandResult:
        """Close a bead."""
        return await self.run_command(["close", bead_id], **kwargs)
    
    def close_sync(self, bead_id: str, **kwargs) -> CommandResult:
        """Close a bead (synchronous)."""
        return self.run_command_sync(["close", bead_id], **kwargs)
    
    async def ready(self, **kwargs) -> CommandResult:
        """Show ready beads."""
        return await self.run_command(["ready"], **kwargs)
    
    def ready_sync(self, **kwargs) -> CommandResult:
        """Show ready beads (synchronous)."""
        return self.run_command_sync(["ready"], **kwargs)
    
    async def sync(self, **kwargs) -> CommandResult:
        """Sync beads."""
        return await self.run_command(["sync"], **kwargs)
    
    def sync_sync(self, **kwargs) -> CommandResult:
        """Sync beads (synchronous)."""
        return self.run_command_sync(["sync"], **kwargs)