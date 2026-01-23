"""GitHub API client with built-in rate limiting."""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    httpx = None

from .rate_limiter import (
    APIRateLimiter,
    APIProvider,
    RateLimitExceededError,
    rate_limit_request
)


@dataclass
class GitHubRateLimit:
    """GitHub rate limit information."""
    limit: int
    remaining: int
    reset: int
    used: int
    
    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> "GitHubRateLimit":
        """Create from HTTP headers."""
        return cls(
            limit=int(headers.get("x-ratelimit-limit", "0")),
            remaining=int(headers.get("x-ratelimit-remaining", "0")),
            reset=int(headers.get("x-ratelimit-reset", "0")),
            used=int(headers.get("x-ratelimit-used", "0"))
        )


@dataclass
class GitHubRepository:
    """GitHub repository information."""
    name: str
    full_name: str
    description: Optional[str] = None
    html_url: str = ""
    clone_url: str = ""
    default_branch: str = "main"
    language: Optional[str] = None
    stargazers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "GitHubRepository":
        """Create from API response."""
        return cls(
            name=data.get("name", ""),
            full_name=data.get("full_name", ""),
            description=data.get("description"),
            html_url=data.get("html_url", ""),
            clone_url=data.get("clone_url", ""),
            default_branch=data.get("default_branch", "main"),
            language=data.get("language"),
            stargazers_count=data.get("stargazers_count", 0),
            forks_count=data.get("forks_count", 0),
            open_issues_count=data.get("open_issues_count", 0)
        )


class GitHubClient:
    """GitHub API client with rate limiting."""
    
    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = "https://api.github.com",
        rate_limiter: Optional[APIRateLimiter] = None
    ):
        """Initialize GitHub client.
        
        Args:
            token: GitHub personal access token
            base_url: GitHub API base URL
            rate_limiter: Rate limiter instance
        """
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.rate_limiter = rate_limiter or APIRateLimiter()
        
        # Set up HTTP client
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "agentic-coder/1.0"
        }
        
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        if httpx is None:
            raise ImportError("httpx is required for GitHub client functionality")
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0
        )
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make rate-limited API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            API response data
            
        Raises:
            RateLimitExceededError: If rate limit exceeded
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async def make_request():
            response = await self.client.request(
                method,
                url,
                params=params,
                json=data
            )
            
            # Check rate limit headers
            rate_limit = GitHubRateLimit.from_headers(response.headers)
            
            # If we're close to the limit, be more conservative
            if rate_limit.remaining < 10:
                raise RateLimitExceededError(
                    f"GitHub API rate limit almost exceeded: "
                    f"{rate_limit.remaining}/{rate_limit.limit} remaining"
                )
            
            response.raise_for_status()
            return response.json()
        
        try:
            # Use rate limiting wrapper
            return await rate_limit_request(
                APIProvider.GITHUB,
                make_request,
                tokens=1
            )
        except RateLimitExceededError as e:
            # If we hit rate limit, wait for reset
            reset_time = int(self.client.headers.get("x-ratelimit-reset", 0))
            current_time = int(asyncio.get_event_loop().time())
            
            if reset_time > current_time:
                wait_time = reset_time - current_time
                raise RateLimitExceededError(
                    f"GitHub API rate limit exceeded. "
                    f"Reset in {wait_time} seconds."
                )
            else:
                raise e
    
    async def get_repository(self, owner: str, repo: str) -> GitHubRepository:
        """Get repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository information
        """
        data = await self._request("GET", f"repos/{owner}/{repo}")
        return GitHubRepository.from_api(data)
    
    async def get_repositories(self, owner: str) -> List[GitHubRepository]:
        """Get all repositories for an owner.
        
        Args:
            owner: Repository owner
            
        Returns:
            List of repositories
        """
        data = await self._request("GET", f"users/{owner}/repos")
        return [GitHubRepository.from_api(repo) for repo in data]
    
    async def get_commits(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """Get commits for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            since: ISO 8601 timestamp
            until: ISO 8601 timestamp
            per_page: Number of results per page
            
        Returns:
            List of commits
        """
        params = {"per_page": per_page}
        
        if branch:
            params["sha"] = branch
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        
        data = await self._request("GET", f"repos/{owner}/{repo}/commits", params=params)
        return data if isinstance(data, list) else []
    
    async def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get issues for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open/closed/all)
            labels: List of labels to filter by
            
        Returns:
            List of issues
        """
        params = {"state": state}
        
        if labels:
            params["labels"] = ",".join(labels)
        
        data = await self._request("GET", f"repos/{owner}/{repo}/issues", params=params)
        return data if isinstance(data, list) else []
    
    async def get_rate_limit(self) -> Dict[str, Any]:
        """Get current rate limit status.
        
        Returns:
            Rate limit information
        """
        return await self._request("GET", "rate_limit")
    
    async def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 30
    ) -> Dict[str, Any]:
        """Search repositories.
        
        Args:
            query: Search query
            sort: Sort field
            order: Sort order
            per_page: Results per page
            
        Returns:
            Search results
        """
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page
        }
        
        return await self._request("GET", "search/repositories", params=params)
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


# Convenience function to create a GitHub client
def create_github_client(
    token: Optional[str] = None,
    rate_limiter: Optional[APIRateLimiter] = None
) -> GitHubClient:
    """Create a configured GitHub client.
    
    Args:
        token: GitHub personal access token
        rate_limiter: Rate limiter instance
        
    Returns:
        Configured GitHub client
    """
    return GitHubClient(token=token, rate_limiter=rate_limiter)