"""Benchmark tests for ConfigDiscoveryService."""

from pathlib import Path
from typing import Any

from pytest_benchmark.fixture import BenchmarkFixture

from lazyclaude.services.discovery import ConfigDiscoveryService


class TestDiscoveryBenchmarkSmall:
    """Benchmark discovery with small dataset (~20 customizations)."""

    def test_discover_all_cold(
        self,
        benchmark: BenchmarkFixture,
        benchmark_small_config: tuple[Path, Path],
    ) -> None:
        """Measure full discovery without cache."""
        user_config, project_config = benchmark_small_config

        def setup() -> ConfigDiscoveryService:
            return ConfigDiscoveryService(
                user_config_path=user_config,
                project_config_path=project_config,
            )

        def run(service: ConfigDiscoveryService) -> list[Any]:
            return service.discover_all()

        service = setup()
        result = benchmark.pedantic(run, args=(service,), rounds=5, warmup_rounds=1)
        assert len(result) > 0

    def test_discover_all_cached(
        self,
        benchmark: BenchmarkFixture,
        benchmark_small_config: tuple[Path, Path],
    ) -> None:
        """Measure cached discovery (should be near-instant)."""
        user_config, project_config = benchmark_small_config
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        service.discover_all()

        result = benchmark(service.discover_all)
        assert len(result) > 0

    def test_refresh(
        self,
        benchmark: BenchmarkFixture,
        benchmark_small_config: tuple[Path, Path],
    ) -> None:
        """Measure refresh operation (cache clear + rediscover)."""
        user_config, project_config = benchmark_small_config
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        service.discover_all()

        result = benchmark(service.refresh)
        assert len(result) > 0


class TestDiscoveryBenchmarkMedium:
    """Benchmark discovery with medium dataset (~100 customizations)."""

    def test_discover_all_cold(
        self,
        benchmark: BenchmarkFixture,
        benchmark_medium_config: tuple[Path, Path],
    ) -> None:
        """Measure full discovery without cache."""
        user_config, project_config = benchmark_medium_config

        def setup() -> ConfigDiscoveryService:
            return ConfigDiscoveryService(
                user_config_path=user_config,
                project_config_path=project_config,
            )

        def run(service: ConfigDiscoveryService) -> list[Any]:
            return service.discover_all()

        service = setup()
        result = benchmark.pedantic(run, args=(service,), rounds=5, warmup_rounds=1)
        assert len(result) > 0

    def test_discover_all_cached(
        self,
        benchmark: BenchmarkFixture,
        benchmark_medium_config: tuple[Path, Path],
    ) -> None:
        """Measure cached discovery (should be near-instant)."""
        user_config, project_config = benchmark_medium_config
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        service.discover_all()

        result = benchmark(service.discover_all)
        assert len(result) > 0

    def test_refresh(
        self,
        benchmark: BenchmarkFixture,
        benchmark_medium_config: tuple[Path, Path],
    ) -> None:
        """Measure refresh operation (cache clear + rediscover)."""
        user_config, project_config = benchmark_medium_config
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        service.discover_all()

        result = benchmark(service.refresh)
        assert len(result) > 0


class TestDiscoveryBenchmarkLarge:
    """Benchmark discovery with large dataset (~250 customizations)."""

    def test_discover_all_cold(
        self,
        benchmark: BenchmarkFixture,
        benchmark_large_config: tuple[Path, Path],
    ) -> None:
        """Measure full discovery without cache (stress test)."""
        user_config, project_config = benchmark_large_config

        def setup() -> ConfigDiscoveryService:
            return ConfigDiscoveryService(
                user_config_path=user_config,
                project_config_path=project_config,
            )

        def run(service: ConfigDiscoveryService) -> list[Any]:
            return service.discover_all()

        service = setup()
        result = benchmark.pedantic(run, args=(service,), rounds=3, warmup_rounds=1)
        assert len(result) > 0

    def test_refresh(
        self,
        benchmark: BenchmarkFixture,
        benchmark_large_config: tuple[Path, Path],
    ) -> None:
        """Measure refresh operation (stress test)."""
        user_config, project_config = benchmark_large_config
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        service.discover_all()

        result = benchmark.pedantic(service.refresh, rounds=3, warmup_rounds=1)
        assert len(result) > 0
