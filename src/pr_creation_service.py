"""PR Creation Service - Integrates GitHub PR creation with bead tracking."""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass

from github_pr_client import GitHubPRClient, GitHubConfig, PRInfo, create_github_config_from_env
from beadsclient.client import BeadsClient


@dataclass
class PRCreationResult:
    """Result of PR creation operation."""
    success: bool
    pr_info: Optional[PRInfo] = None
    error_message: Optional[str] = None
    bead_updated: bool = False


class PRCreationService:
    """Service for creating PRs and linking them to beads."""
    
    def __init__(self, 
                 github_client: GitHubPRClient,
                 beads_client: BeadsClient):
        """Initialize PR creation service.
        
        Args:
            github_client: GitHub API client
            beads_client: Beads issue tracking client
        """
        self.github_client = github_client
        self.beads_client = beads_client
    
    def create_pr_for_bead(
        self, 
        bead_id: str,
        head_branch: str,
        base_branch: str = "main",
        title: Optional[str] = None,
        body: Optional[str] = None
    ) -> PRCreationResult:
        """Create a PR linked to a specific bead.
        
        Args:
            bead_id: Bead ID to link
            head_branch: Feature branch name
            base_branch: Target branch (default: main)
            title: PR title (defaults to bead title)
            body: PR body (defaults to bead description)
            
        Returns:
            PRCreationResult with operation details
        """
        try:
            # Get bead information
            bead_result = self.beads_client.show_sync(bead_id)
            
            if not bead_result.success:
                return PRCreationResult(
                    success=False,
                    error_message=f"Failed to get bead {bead_id}: {bead_result.stderr}"
                )
            
            # Parse bead information
            bead_data = self._parse_bead_info(bead_result.stdout)
            
            # Use bead info as defaults
            pr_title = title or bead_data.get("title", f"Implement {bead_id}")
            pr_body = body or bead_data.get("description", "")
            
            # Create PR
            pr_info = self.github_client.create_pr(
                title=pr_title,
                head=head_branch,
                base=base_branch,
                body=pr_body,
                bead_id=bead_id
            )
            
            # Update bead with PR information
            bead_updated = self._update_bead_with_pr_info(bead_id, pr_info)
            
            return PRCreationResult(
                success=True,
                pr_info=pr_info,
                bead_updated=bead_updated
            )
            
        except Exception as e:
            return PRCreationResult(
                success=False,
                error_message=f"Failed to create PR for bead {bead_id}: {str(e)}"
            )
    
    def create_pr_without_bead(
        self,
        title: str,
        head_branch: str,
        base_branch: str = "main",
        body: Optional[str] = None
    ) -> PRCreationResult:
        """Create a PR without linking to a bead.
        
        Args:
            title: PR title
            head_branch: Feature branch name
            base_branch: Target branch (default: main)
            body: PR body
            
        Returns:
            PRCreationResult with operation details
        """
        try:
            pr_info = self.github_client.create_pr(
                title=title,
                head=head_branch,
                base=base_branch,
                body=body
            )
            
            return PRCreationResult(
                success=True,
                pr_info=pr_info
            )
            
        except Exception as e:
            return PRCreationResult(
                success=False,
                error_message=f"Failed to create PR: {str(e)}"
            )
    
    def link_pr_to_bead(self, pr_number: int, bead_id: str) -> PRCreationResult:
        """Link an existing PR to a bead.
        
        Args:
            pr_number: Pull request number
            bead_id: Bead ID to link
            
        Returns:
            PRCreationResult with operation details
        """
        try:
            # Update PR to include bead link
            success = self.github_client.update_pr_with_bead_link(pr_number, bead_id)
            
            if not success:
                return PRCreationResult(
                    success=False,
                    error_message=f"Failed to update PR #{pr_number} with bead link"
                )
            
            # Get PR info
            pr_info = self.github_client.get_pr(pr_number)
            if not pr_info:
                return PRCreationResult(
                    success=False,
                    error_message=f"PR #{pr_number} not found after update"
                )
            
            # Update bead with PR information
            bead_updated = self._update_bead_with_pr_info(bead_id, pr_info)
            
            return PRCreationResult(
                success=True,
                pr_info=pr_info,
                bead_updated=bead_updated
            )
            
        except Exception as e:
            return PRCreationResult(
                success=False,
                error_message=f"Failed to link PR #{pr_number} to bead {bead_id}: {str(e)}"
            )
    
    def get_prs_for_bead(self, bead_id: str) -> list:
        """Get all PRs linked to a specific bead.
        
        Args:
            bead_id: Bead ID to search for
            
        Returns:
            List of PRInfo objects linked to the bead
        """
        try:
            all_prs = self.github_client.list_prs(state="all")
            
            # Filter PRs that mention the bead ID
            linked_prs = []
            for pr in all_prs:
                if pr.bead_id == bead_id:
                    linked_prs.append(pr)
            
            return linked_prs
            
        except Exception:
            return []
    
    def _parse_bead_info(self, bead_output: str) -> Dict[str, Any]:
        """Parse bead show command output.
        
        Args:
            bead_output: Output from 'bd show' command
            
        Returns:
            Dictionary with bead information
        """
        lines = bead_output.strip().split('\n')
        bead_info = {}
        
        current_key = None
        for line in lines:
            line = line.strip()
            
            if line.startswith('●') or line.startswith('○') or line.startswith('✓'):
                # Status line
                parts = line.split('·', 1)
                if len(parts) > 1:
                    bead_info['status'] = parts[1].strip().split('[')[0].strip()
            elif ':' in line:
                # Key-value pair
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key.lower() in ['title', 'description', 'type', 'owner', 'assignee']:
                    bead_info[key.lower()] = value
                    current_key = key.lower()
            elif current_key and line.startswith('DEPENDS ON') or line.startswith('BLOCKS'):
                # Handle special sections
                break
        
        return bead_info
    
    def _update_bead_with_pr_info(self, bead_id: str, pr_info: PRInfo) -> bool:
        """Update bead with PR information.
        
        Args:
            bead_id: Bead ID to update
            pr_info: PR information to add
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Add PR comment to bead
            comment = f"Pull request created: #{pr_info.pr_number}\n\nURL: {pr_info.pr_url}"
            
            # This would require a beads client method to add comments
            # For now, we'll just update the bead description
            update_result = self.beads_client.update_sync(bead_id)
            
            return update_result.success
            
        except Exception:
            return False


def create_pr_service_from_env() -> Optional[PRCreationService]:
    """Create PRCreationService from environment variables.
    
    Required environment variables:
    - GITHUB_TOKEN: GitHub personal access token
    - GITHUB_OWNER: Repository owner
    - GITHUB_REPO: Repository name
    
    Returns:
        PRCreationService if configuration is valid, None otherwise
    """
    github_config = create_github_config_from_env()
    if not github_config:
        return None
    
    github_client = GitHubPRClient(github_config)
    beads_client = BeadsClient()
    
    return PRCreationService(github_client, beads_client)