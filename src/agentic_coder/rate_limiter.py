"""Rate limiting utilities for external API calls."""

import time
import asyncio
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class APIProvider(Enum):
    """Supported API providers with their rate limits."""
    GITHUB = "github"
    OPENAI = "openai"
    DEFAULT = "default"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 5000
    burst_limit: int = 100
    
    # GitHub API specific limits
    GITHUB_RATE_LIMITS = {
        APIProvider.GITHUB: {
            "requests_per_minute": 60,
            "requests_per_hour": 5000,
            "burst_limit": 100
        },
        APIProvider.OPENAI: {
            "requests_per_minute": 20,
            "requests_per_hour": 200,
            "burst_limit": 50
        },
        APIProvider.DEFAULT: {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "burst_limit": 100
        }
    }


class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        provider: APIProvider = APIProvider.DEFAULT
    ):
        """Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Rate at which tokens are refilled (tokens per second)
            provider: API provider for specific rate limiting rules
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.provider = provider
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """Consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        async with self._lock:
            await self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    async def wait_for_tokens(self, tokens: int = 1) -> None:
        """Wait until enough tokens are available.
        
        Args:
            tokens: Number of tokens needed
            
        Raises:
            RateLimitExceededError: If wait time exceeds threshold
        """
        max_wait_time = 60.0  # Maximum wait time in seconds
        
        async with self._lock:
            while self.tokens < tokens:
                await self._refill()
                
                if self.tokens < tokens:
                    deficit = tokens - self.tokens
                    wait_time = deficit / self.refill_rate
                    
                    if wait_time > max_wait_time:
                        raise RateLimitExceededError(
                            f"Rate limit exceeded. Wait time {wait_time:.2f}s exceeds "
                            f"maximum allowed {max_wait_time}s"
                        )
                    
                    await asyncio.sleep(wait_time)
                    await self._refill()
            
            self.tokens -= tokens
    
    async def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bucket status."""
        return {
            "provider": self.provider.value,
            "tokens": self.tokens,
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "last_refill": self.last_refill
        }


class APIRateLimiter:
    """Main rate limiter for external API calls."""
    
    def __init__(self):
        """Initialize rate limiter with default configurations."""
        self.buckets: Dict[APIProvider, TokenBucket] = {}
        self._initialize_buckets()
    
    def _initialize_buckets(self) -> None:
        """Initialize token buckets for different API providers."""
        for provider, config in RateLimitConfig.GITHUB_RATE_LIMITS.items():
            # Convert per-minute rate to per-second for token bucket
            per_second_rate = config["requests_per_minute"] / 60
            
            self.buckets[provider] = TokenBucket(
                capacity=config["burst_limit"],
                refill_rate=per_second_rate,
                provider=provider
            )
    
    def get_limiter(self, provider: APIProvider) -> TokenBucket:
        """Get rate limiter for a specific provider.
        
        Args:
            provider: API provider
            
        Returns:
            TokenBucket for the provider
        """
        if provider not in self.buckets:
            # Use default limiter if provider not configured
            provider = APIProvider.DEFAULT
        
        return self.buckets[provider]
    
    async def check_rate_limit(
        self,
        provider: APIProvider,
        tokens: int = 1
    ) -> bool:
        """Check if request can be made without exceeding rate limit.
        
        Args:
            provider: API provider
            tokens: Number of tokens needed
            
        Returns:
            True if request can be made, False otherwise
        """
        limiter = self.get_limiter(provider)
        return await limiter.consume(tokens)
    
    async def wait_for_rate_limit(
        self,
        provider: APIProvider,
        tokens: int = 1
    ) -> None:
        """Wait until rate limit allows the request.
        
        Args:
            provider: API provider
            tokens: Number of tokens needed
            
        Raises:
            RateLimitExceededError: If rate limit would be exceeded
        """
        limiter = self.get_limiter(provider)
        await limiter.wait_for_tokens(tokens)
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all rate limiters."""
        return {
            provider.value: limiter.get_status()
            for provider, limiter in self.buckets.items()
        }


# Global rate limiter instance
api_rate_limiter = APIRateLimiter()


async def rate_limit_request(
    provider: APIProvider,
    func,
    *args,
    tokens: int = 1,
    **kwargs
) -> Any:
    """Execute a function with rate limiting.
    
    Args:
        provider: API provider
        func: Function to execute
        args: Function arguments
        tokens: Number of tokens needed
        kwargs: Function keyword arguments
        
    Returns:
        Result of the function
        
    Raises:
        RateLimitExceededError: If rate limit exceeded
    """
    await api_rate_limiter.wait_for_rate_limit(provider, tokens)
    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)