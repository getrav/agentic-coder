"""Simple test runner for rate limiter without pytest."""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agentic_coder.rate_limiter import (
    TokenBucket,
    APIRateLimiter,
    APIProvider,
    RateLimitExceededError
)


class TestResult:
    def __init__(self, name, passed, error=None):
        self.name = name
        self.passed = passed
        self.error = error


class TestRunner:
    def __init__(self):
        self.results = []
    
    def test(self, func):
        """Test decorator."""
        async def wrapper():
            try:
                await func()
                self.results.append(TestResult(func.__name__, True))
                print(f"✓ {func.__name__}")
            except Exception as e:
                self.results.append(TestResult(func.__name__, False, str(e)))
                print(f"✗ {func.__name__}: {e}")
        
        return wrapper
    
    async def run_token_bucket_tests(self):
        """Run token bucket tests."""
        print("Running TokenBucket Tests...")
        print("-" * 30)
        
        @self.test
        async def test_initialization():
            bucket = TokenBucket(capacity=10, refill_rate=1.0)
            assert bucket.capacity == 10
            assert bucket.refill_rate == 1.0
            assert bucket.tokens == 10
        
        @self.test
        async def test_consumption():
            bucket = TokenBucket(capacity=10, refill_rate=1.0)
            result = await bucket.consume(1)
            assert result is True
            assert bucket.tokens == 9
        
        @self.test
        async def test_insufficient_tokens():
            bucket = TokenBucket(capacity=5, refill_rate=1.0)
            result = await bucket.consume(10)
            assert result is False
            assert bucket.tokens == 5
        
        @self.test
        async def test_wait_for_tokens():
            bucket = TokenBucket(capacity=10, refill_rate=10.0)
            await bucket.consume(10)
            assert bucket.tokens == 0
            await bucket.wait_for_tokens(5)
            assert bucket.tokens >= 0
        
        await test_initialization()
        await test_consumption()
        await test_insufficient_tokens()
        await test_wait_for_tokens()
    
    async def run_api_rate_limiter_tests(self):
        """Run API rate limiter tests."""
        print("\nRunning APIRateLimiter Tests...")
        print("-" * 30)
        
        @self.test
        async def test_initialization():
            limiter = APIRateLimiter()
            assert APIProvider.GITHUB in limiter.buckets
            assert APIProvider.OPENAI in limiter.buckets
            assert APIProvider.DEFAULT in limiter.buckets
        
        @self.test
        async def test_check_rate_limit():
            limiter = APIRateLimiter()
            can_make_request = await limiter.check_rate_limit(APIProvider.GITHUB)
            assert can_make_request is True
        
        @self.test
        async def test_wait_for_rate_limit():
            limiter = APIRateLimiter()
            await limiter.wait_for_rate_limit(APIProvider.GITHUB)  # Should not raise
        
        @self.test
        async def test_get_limiter():
            limiter = APIRateLimiter()
            github_limiter = limiter.get_limiter(APIProvider.GITHUB)
            assert isinstance(github_limiter, TokenBucket)
            assert github_limiter.provider == APIProvider.GITHUB
        
        await test_initialization()
        await test_check_rate_limit()
        await test_wait_for_rate_limit()
        await test_get_limiter()
    
    def print_summary(self):
        """Print test summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        print(f"\nTest Summary")
        print("=" * 40)
        print(f"Total: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if failed > 0:
            print(f"\nFailed Tests:")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.name}: {result.error}")


async def main():
    """Main test runner."""
    runner = TestRunner()
    
    await runner.run_token_bucket_tests()
    await runner.run_api_rate_limiter_tests()
    
    runner.print_summary()
    
    # Exit with appropriate code
    failed = sum(1 for r in runner.results if not r.passed)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())