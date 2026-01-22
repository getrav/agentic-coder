"""Tests for BeadsClient."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from beadsclient import BeadsClient
from beadsclient.client import CommandResult


@pytest.fixture
def client():
    """Create a BeadsClient instance for testing."""
    return BeadsClient()


class TestCommandResult:
    """Test CommandResult class."""
    
    def test_json_parse_success(self):
        """Test successful JSON parsing."""
        result = CommandResult(
            stdout='{"key": "value"}',
            stderr="",
            returncode=0,
            success=True
        )
        assert result.json == {"key": "value"}
    
    def test_json_parse_failure(self):
        """Test JSON parsing failure returns original text."""
        result = CommandResult(
            stdout="not json",
            stderr="",
            returncode=0,
            success=True
        )
        assert result.json == "not json"


class TestBeadsClient:
    """Test BeadsClient class."""
    
    @pytest.mark.asyncio
    async def test_run_command_success(self, client):
        """Test successful command execution."""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"error")
            mock_exec.return_value = mock_process
            
            result = await client.run_command(["show", "AC-pf4"])
            
            assert result.success is True
            assert result.stdout == "output"
            assert result.stderr == "error"
            assert result.returncode == 0
    
    @pytest.mark.asyncio
    async def test_run_command_timeout(self, client):
        """Test command timeout."""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_exec.side_effect = asyncio.TimeoutError()
            
            result = await client.run_command(["show", "AC-pf4"])
            
            assert result.success is False
            assert "timed out" in result.stderr
    
    def test_run_command_sync_success(self, client):
        """Test successful synchronous command execution."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = "error"
            mock_run.return_value = mock_result
            
            result = client.run_command_sync(["show", "AC-pf4"])
            
            assert result.success is True
            assert result.stdout == "output"
            assert result.stderr == "error"
            assert result.returncode == 0
    
    @pytest.mark.asyncio
    async def test_show_method(self, client):
        """Test show method."""
        client.run_command = AsyncMock(return_value=CommandResult(
            stdout="success", stderr="", returncode=0, success=True
        ))
        
        result = await client.show("AC-pf4")
        
        assert result.success is True
        client.run_command.assert_called_once_with(["show", "AC-pf4"])
    
    def test_show_sync_method(self, client):
        """Test show_sync method."""
        client.run_command_sync = MagicMock(return_value=CommandResult(
            stdout="success", stderr="", returncode=0, success=True
        ))
        
        result = client.show_sync("AC-pf4")
        
        assert result.success is True
        client.run_command_sync.assert_called_once_with(["show", "AC-pf4"])
    
    @pytest.mark.asyncio
    async def test_create_method(self, client):
        """Test create method."""
        client.run_command = AsyncMock(return_value=CommandResult(
            stdout="created", stderr="", returncode=0, success=True
        ))
        
        result = await client.create("Test Issue")
        
        assert result.success is True
        client.run_command.assert_called_once_with(["create", "--title", "Test Issue", "--type", "task"])
    
    @pytest.mark.asyncio
    async def test_update_method(self, client):
        """Test update method."""
        client.run_command = AsyncMock(return_value=CommandResult(
            stdout="updated", stderr="", returncode=0, success=True
        ))
        
        result = await client.update("AC-pf4", status="in_progress")
        
        assert result.success is True
        client.run_command.assert_called_once_with(["update", "AC-pf4", "--status", "in_progress"])
    
    @pytest.mark.asyncio
    async def test_close_method(self, client):
        """Test close method."""
        client.run_command = AsyncMock(return_value=CommandResult(
            stdout="closed", stderr="", returncode=0, success=True
        ))
        
        result = await client.close("AC-pf4")
        
        assert result.success is True
        client.run_command.assert_called_once_with(["close", "AC-pf4"])
    
    @pytest.mark.asyncio
    async def test_ready_method(self, client):
        """Test ready method."""
        client.run_command = AsyncMock(return_value=CommandResult(
            stdout="ready list", stderr="", returncode=0, success=True
        ))
        
        result = await client.ready()
        
        assert result.success is True
        client.run_command.assert_called_once_with(["ready"])
    
    @pytest.mark.asyncio
    async def test_sync_method(self, client):
        """Test sync method."""
        client.run_command = AsyncMock(return_value=CommandResult(
            stdout="synced", stderr="", returncode=0, success=True
        ))
        
        result = await client.sync()
        
        assert result.success is True
        client.run_command.assert_called_once_with(["sync"])


if __name__ == "__main__":
    pytest.main([__file__])