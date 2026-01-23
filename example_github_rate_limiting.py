"""Example usage of GitHub API rate limiting."""

import asyncio
import os
from typing import Optional

from src.agentic_coder.github_client import create_github_client
from src.agentic_coder.rate_limiter import (
    APIRateLimiter,
    APIProvider,
    rate_limit_request
)


async def example_github_rate_limiting():
    """Example of using GitHub API with rate limiting."""
    
    # Create rate limiter
    rate_limiter = APIRateLimiter()
    
    # Create GitHub client (token is optional but recommended)
    token = os.getenv("GITHUB_TOKEN")  # Set this in your environment
    client = create_github_client(token=token, rate_limiter=rate_limiter)
    
    try:
        print("GitHub API Rate Limiting Example")
        print("=" * 40)
        
        # Show initial rate limiter status
        print("Rate Limiter Status:")
        status = rate_limiter.get_all_status()
        for provider, limiter_status in status.items():
            print(f"  {provider}: {limiter_status['tokens']:.1f} tokens")
        print()
        
        # Get rate limit information
        try:
            rate_limit_info = await client.get_rate_limit()
            print("GitHub Rate Limit Info:")
            print(f"  Core Limit: {rate_limit_info['core']['limit']}")
            print(f"  Core Remaining: {rate_limit_info['core']['remaining']}")
            print(f"  Core Reset: {rate_limit_info['core']['reset']}")
            print()
        except Exception as e:
            print(f"Failed to get rate limit info: {e}")
            print()
        
        # Example: Get repository information
        try:
            repo = await client.get_repository("octocat", "Hello-World")
            print("Repository Info:")
            print(f"  Name: {repo.full_name}")
            print(f"  Description: {repo.description}")
            print(f"  Stars: {repo.stargazers_count}")
            print(f"  Forks: {repo.forks_count}")
            print()
        except Exception as e:
            print(f"Failed to get repository: {e}")
            print()
        
        # Example: Search repositories
        try:
            search_results = await client.search_repositories("python", per_page=5)
            print("Search Results (Python repositories):")
            for item in search_results.get("items", [])[:3]:
                print(f"  - {item['full_name']}: {item['stargazers_count']} stars")
            print()
        except Exception as e:
            print(f"Failed to search repositories: {e}")
            print()
        
        # Show final rate limiter status
        print("Final Rate Limiter Status:")
        status = rate_limiter.get_all_status()
        for provider, limiter_status in status.items():
            print(f"  {provider}: {limiter_status['tokens']:.1f} tokens")
        print()
        
    finally:
        # Clean up
        await client.close()


async def example_custom_rate_limited_function():
    """Example of using rate limiting with custom functions."""
    
    async def api_call():
        """Mock API call function."""
        await asyncio.sleep(0.1)  # Simulate network delay
        return {"data": "success", "timestamp": asyncio.get_event_loop().time()}
    
    print("Custom Rate Limited Function Example")
    print("=" * 40)
    
    # Make 5 rate-limited calls
    for i in range(5):
        try:
            result = await rate_limit_request(APIProvider.GITHUB, api_call)
            print(f"Call {i+1}: {result}")
        except Exception as e:
            print(f"Call {i+1} failed: {e}")


async def main():
    """Main example function."""
    await example_github_rate_limiting()
    print()
    await example_custom_rate_limited_function()


if __name__ == "__main__":
    asyncio.run(main())