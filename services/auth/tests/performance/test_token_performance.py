"""Performance tests for JWT token generation and validation.

These tests validate the <100ms p95 requirement for token operations.
"""

import pytest
import time
import asyncio
import numpy as np
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from services.auth.services.jwt_service import JWTService
from services.auth.models.user import User
from services.auth.repositories.refresh_token_repository import RefreshTokenRepository
from services.auth.core.cache import RedisClient


@pytest.fixture
async def jwt_service(refresh_token_repo: RefreshTokenRepository, redis_client: RedisClient):
    """Create JWT service instance."""
    return JWTService(token_repo=refresh_token_repo, redis=redis_client)


@pytest.mark.performance
class TestTokenGenerationPerformance:
    """Performance tests for token generation."""

    @pytest.mark.asyncio
    async def test_access_token_generation_p95(
        self,
        jwt_service: JWTService,
        test_user: User
    ):
        """Validate access token generation p95 < 100ms."""
        iterations = 1000
        times = []

        for _ in range(iterations):
            start = time.perf_counter()

            await jwt_service.create_access_token(
                user_id=test_user.id,
                email=test_user.email,
                role=test_user.role
            )

            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            times.append(elapsed)

        # Calculate percentiles
        p50 = np.percentile(times, 50)
        p95 = np.percentile(times, 95)
        p99 = np.percentile(times, 99)
        mean = np.mean(times)
        std = np.std(times)

        print(f"\n=== Access Token Generation Performance ===")
        print(f"Iterations: {iterations}")
        print(f"Mean: {mean:.2f}ms")
        print(f"Std Dev: {std:.2f}ms")
        print(f"p50: {p50:.2f}ms")
        print(f"p95: {p95:.2f}ms")
        print(f"p99: {p99:.2f}ms")
        print(f"Min: {min(times):.2f}ms")
        print(f"Max: {max(times):.2f}ms")

        # Assert p95 requirement
        assert p95 < 100, f"p95 ({p95:.2f}ms) exceeds 100ms target"

    @pytest.mark.asyncio
    async def test_refresh_token_generation_p95(
        self,
        jwt_service: JWTService,
        test_user: User
    ):
        """Validate refresh token generation p95 < 100ms."""
        iterations = 1000
        times = []

        for _ in range(iterations):
            start = time.perf_counter()

            await jwt_service.create_refresh_token(user_id=test_user.id)

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        p95 = np.percentile(times, 95)

        print(f"\n=== Refresh Token Generation Performance ===")
        print(f"p95: {p95:.2f}ms")

        assert p95 < 100, f"p95 ({p95:.2f}ms) exceeds 100ms target"

    @pytest.mark.asyncio
    async def test_token_verification_p95(
        self,
        jwt_service: JWTService,
        test_user: User
    ):
        """Validate token verification p95 < 50ms."""
        # Pre-generate tokens
        tokens = []
        for _ in range(100):
            token, _ = await jwt_service.create_access_token(
                user_id=test_user.id,
                email=test_user.email,
                role=test_user.role
            )
            tokens.append(token)

        times = []

        for _ in range(1000):
            token = tokens[_ % len(tokens)]

            start = time.perf_counter()

            await jwt_service.verify_token(token, "access")

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        p95 = np.percentile(times, 95)

        print(f"\n=== Token Verification Performance ===")
        print(f"p95: {p95:.2f}ms")

        # Verification should be faster than generation
        assert p95 < 50, f"p95 ({p95:.2f}ms) exceeds 50ms target"

    @pytest.mark.asyncio
    async def test_token_rotation_p95(
        self,
        jwt_service: JWTService,
        test_user: User
    ):
        """Validate token rotation p95 < 200ms."""
        iterations = 100  # Fewer iterations due to DB operations
        times = []

        for _ in range(iterations):
            # Create initial refresh token
            old_token = await jwt_service.create_refresh_token(user_id=test_user.id)

            start = time.perf_counter()

            await jwt_service.rotate_refresh_token(old_token)

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        p95 = np.percentile(times, 95)

        print(f"\n=== Token Rotation Performance ===")
        print(f"p95: {p95:.2f}ms")

        # Rotation includes DB operations, so higher threshold
        assert p95 < 200, f"p95 ({p95:.2f}ms) exceeds 200ms target"


@pytest.mark.performance
class TestConcurrentTokenGeneration:
    """Test token generation under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_token_generation(
        self,
        jwt_service: JWTService,
        test_user: User
    ):
        """Test token generation under concurrent load."""
        concurrent_requests = 50
        requests_per_task = 20

        async def generate_tokens():
            times = []
            for _ in range(requests_per_task):
                start = time.perf_counter()

                await jwt_service.create_access_token(
                    user_id=test_user.id,
                    email=test_user.email,
                    role=test_user.role
                )

                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)

            return times

        # Run concurrent tasks
        start_total = time.perf_counter()

        tasks = [generate_tokens() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)

        total_elapsed = time.perf_counter() - start_total

        # Flatten all times
        all_times = [t for times in results for t in times]

        p95 = np.percentile(all_times, 95)
        total_tokens = concurrent_requests * requests_per_task

        print(f"\n=== Concurrent Token Generation ===")
        print(f"Total tokens: {total_tokens}")
        print(f"Concurrent tasks: {concurrent_requests}")
        print(f"Total time: {total_elapsed:.2f}s")
        print(f"Tokens/second: {total_tokens / total_elapsed:.2f}")
        print(f"p95: {p95:.2f}ms")

        # Even under load, p95 should be reasonable
        assert p95 < 150, f"p95 ({p95:.2f}ms) under load exceeds 150ms threshold"

    @pytest.mark.asyncio
    async def test_concurrent_verification(
        self,
        jwt_service: JWTService,
        test_user: User
    ):
        """Test token verification under concurrent load."""
        # Pre-generate tokens
        tokens = []
        for _ in range(100):
            token, _ = await jwt_service.create_access_token(
                user_id=test_user.id,
                email=test_user.email,
                role=test_user.role
            )
            tokens.append(token)

        concurrent_requests = 100
        verifications_per_task = 50

        async def verify_tokens():
            times = []
            for i in range(verifications_per_task):
                token = tokens[i % len(tokens)]

                start = time.perf_counter()

                await jwt_service.verify_token(token, "access")

                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)

            return times

        # Run concurrent verifications
        tasks = [verify_tokens() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)

        all_times = [t for times in results for t in times]
        p95 = np.percentile(all_times, 95)

        print(f"\n=== Concurrent Verification ===")
        print(f"Total verifications: {len(all_times)}")
        print(f"p95: {p95:.2f}ms")

        # Verification should be fast even under load
        assert p95 < 75, f"p95 ({p95:.2f}ms) under load exceeds 75ms threshold"


@pytest.mark.performance
class TestCachePerformance:
    """Test Redis caching performance."""

    @pytest.mark.asyncio
    async def test_redis_operations_performance(self, redis_client: RedisClient):
        """Test Redis operation performance."""
        iterations = 1000
        set_times = []
        get_times = []

        for i in range(iterations):
            key = f"test:key:{i}"
            value = f"test_value_{i}"

            # Test SET performance
            start = time.perf_counter()
            await redis_client.set(key, value, ex=60)
            set_times.append((time.perf_counter() - start) * 1000)

            # Test GET performance
            start = time.perf_counter()
            await redis_client.get(key)
            get_times.append((time.perf_counter() - start) * 1000)

        set_p95 = np.percentile(set_times, 95)
        get_p95 = np.percentile(get_times, 95)

        print(f"\n=== Redis Performance ===")
        print(f"SET p95: {set_p95:.2f}ms")
        print(f"GET p95: {get_p95:.2f}ms")

        # Redis operations should be very fast
        assert set_p95 < 10, f"Redis SET p95 ({set_p95:.2f}ms) too slow"
        assert get_p95 < 5, f"Redis GET p95 ({get_p95:.2f}ms) too slow"

    @pytest.mark.asyncio
    async def test_token_revocation_check_performance(
        self,
        jwt_service: JWTService,
        redis_client: RedisClient
    ):
        """Test revocation check performance."""
        # Pre-populate with revoked tokens
        revoked_tokens = []
        for _ in range(100):
            jti = str(uuid4())
            await redis_client.sadd("token:deny_list", jti)
            revoked_tokens.append(jti)

        times = []

        for _ in range(1000):
            jti = revoked_tokens[_ % len(revoked_tokens)]

            start = time.perf_counter()

            await jwt_service._is_token_revoked(jti)

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        p95 = np.percentile(times, 95)

        print(f"\n=== Revocation Check Performance ===")
        print(f"p95: {p95:.2f}ms")

        # Revocation checks should be very fast (Redis operation)
        assert p95 < 5, f"Revocation check p95 ({p95:.2f}ms) too slow"
