"""GitHub PR Client - Creates and manages pull requests with bead linking."""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from urllib.parse import urljoin
import requests


@dataclass
class PRInfo:
    """Information about a created pull request."""
    pr_number: int
    pr_url: str
    title: str
    body: str
    head_branch: str
    base_branch: str
    bead_id: Optional[str] = None


@dataclass
class GitHubConfig:
    """Configuration for GitHub API access."""
    token: str
    owner: str
    repo: str
    api_url: str = "https://api.github.com"


class GitHubPRClient:
    """Client for creating and managing GitHub pull requests."""
    
    def __init__(self, config: GitHubConfig):
        """Initialize GitHub PR client.
        
        Args:
            config: GitHub configuration
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "agentic-coder/1.0"
        })
    
    def create_pr(
        self, 
        title: str, 
        head: str, 
        base: str = "main", 
        body: Optional[str] = None,
        bead_id: Optional[str] = None
    ) -> PRInfo:
        """Create a pull request.
        
        Args:
            title: PR title
            head: Head branch name
            base: Base branch name (default: main)
            body: PR description
            bead_id: Associated bead ID for linking
            
        Returns:
            PRInfo object with created PR details
            
        Raises:
            requests.RequestException: If API call fails
        """
        # Enhance body with bead information if provided
        if bead_id:
            enhanced_body = self._enhance_pr_body(body or "", bead_id)
        else:
            enhanced_body = body or ""
        
        pr_data = {
            "title": title,
            "head": head,
            "base": base,
            "body": enhanced_body
        }
        
        url = f"/repos/{self.config.owner}/{self.config.repo}/pulls"
        full_url = urljoin(self.config.api_url, url)
        
        response = self.session.post(full_url, json=pr_data)
        response.raise_for_status()
        
        pr_data = response.json()
        
        return PRInfo(
            pr_number=pr_data["number"],
            pr_url=pr_data["html_url"],
            title=pr_data["title"],
            body=pr_data["body"],
            head_branch=pr_data["head"]["ref"],
            base_branch=pr_data["base"]["ref"],
            bead_id=bead_id
        )
    
    def get_pr(self, pr_number: int) -> Optional[PRInfo]:
        """Get information about an existing pull request.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            PRInfo object or None if not found
        """
        url = f"/repos/{self.config.owner}/{self.config.repo}/pulls/{pr_number}"
        full_url = urljoin(self.config.api_url, url)
        
        try:
            response = self.session.get(full_url)
            response.raise_for_status()
            
            pr_data = response.json()
            
            # Extract bead ID from PR body if present
            bead_id = self._extract_bead_id(pr_data.get("body", ""))
            
            return PRInfo(
                pr_number=pr_data["number"],
                pr_url=pr_data["html_url"],
                title=pr_data["title"],
                body=pr_data["body"],
                head_branch=pr_data["head"]["ref"],
                base_branch=pr_data["base"]["ref"],
                bead_id=bead_id
            )
            
        except requests.RequestException:
            return None
    
    def list_prs(self, state: str = "open") -> List[PRInfo]:
        """List pull requests.
        
        Args:
            state: PR state ("open", "closed", "all")
            
        Returns:
            List of PRInfo objects
        """
        url = f"/repos/{self.config.owner}/{self.config.repo}/pulls"
        full_url = urljoin(self.config.api_url, url)
        
        params = {"state": state}
        response = self.session.get(full_url, params=params)
        response.raise_for_status()
        
        prs = []
        for pr_data in response.json():
            bead_id = self._extract_bead_id(pr_data.get("body", ""))
            
            prs.append(PRInfo(
                pr_number=pr_data["number"],
                pr_url=pr_data["html_url"],
                title=pr_data["title"],
                body=pr_data["body"],
                head_branch=pr_data["head"]["ref"],
                base_branch=pr_data["base"]["ref"],
                bead_id=bead_id
            ))
        
        return prs
    
    def add_pr_comment(self, pr_number: int, comment: str) -> bool:
        """Add a comment to a pull request.
        
        Args:
            pr_number: Pull request number
            comment: Comment text
            
        Returns:
            True if successful, False otherwise
        """
        url = f"/repos/{self.config.owner}/{self.config.repo}/issues/{pr_number}/comments"
        full_url = urljoin(self.config.api_url, url)
        
        data = {"body": comment}
        
        try:
            response = self.session.post(full_url, json=data)
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False
    
    def _enhance_pr_body(self, body: str, bead_id: str) -> str:
        """Enhance PR body with bead information.
        
        Args:
            body: Original PR body
            bead_id: Bead ID to link
            
        Returns:
            Enhanced PR body
        """
        bead_info = f"\n\n---\n\n**Linked Bead:** {bead_id}\n\nThis PR is linked to bead [{bead_id}](https://github.com/beads/issues/{bead_id})."
        
        if body:
            return body + bead_info
        else:
            return "This PR implements the requirements specified in the linked bead." + bead_info
    
    def _extract_bead_id(self, body: str) -> Optional[str]:
        """Extract bead ID from PR body.
        
        Args:
            body: PR body text
            
        Returns:
            Bead ID if found, None otherwise
        """
        import re
        
        # Look for bead ID patterns
        patterns = [
            r"\*\*Linked Bead:\*\*\s*([A-Z]+-\w+)",
            r"bead\s+([A-Z]+-\w+)",
            r"([A-Z]+-\w+)(?:\s*\|\s*bead)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def update_pr_with_bead_link(self, pr_number: int, bead_id: str) -> bool:
        """Update an existing PR to include a bead link.
        
        Args:
            pr_number: Pull request number
            bead_id: Bead ID to link
            
        Returns:
            True if successful, False otherwise
        """
        # Get current PR info
        pr_info = self.get_pr(pr_number)
        if not pr_info:
            return False
        
        # Enhance body with bead information
        enhanced_body = self._enhance_pr_body(pr_info.body, bead_id)
        
        # Update PR
        url = f"/repos/{self.config.owner}/{self.config.repo}/pulls/{pr_number}"
        full_url = urljoin(self.config.api_url, url)
        
        data = {"body": enhanced_body}
        
        try:
            response = self.session.patch(full_url, json=data)
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False


def create_github_config_from_env() -> Optional[GitHubConfig]:
    """Create GitHubConfig from environment variables.
    
    Environment variables:
    - GITHUB_TOKEN: GitHub personal access token
    - GITHUB_OWNER: Repository owner
    - GITHUB_REPO: Repository name
    - GITHUB_API_URL: Custom API URL (optional)
    
    Returns:
        GitHubConfig if all required variables are present, None otherwise
    """
    token = os.getenv("GITHUB_TOKEN")
    owner = os.getenv("GITHUB_OWNER")
    repo = os.getenv("GITHUB_REPO")
    api_url = os.getenv("GITHUB_API_URL")
    
    if not all([token, owner, repo]):
        return None
    
    return GitHubConfig(
        token=str(token),
        owner=str(owner),
        repo=str(repo),
        api_url=api_url or "https://api.github.com"
    )