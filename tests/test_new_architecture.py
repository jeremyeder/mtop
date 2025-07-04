"""Tests for the new architecture components."""

import asyncio
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from mtop.async_cli import AsyncKubectlLD, AsyncResourceMonitor
from mtop.cache import AsyncCache, CacheManager, LRUCache
from mtop.container import Container, get_container
from mtop.implementations import LocalFileSystem, MockKubernetesClient
from mtop.interfaces import FileSystem, KubernetesClient, Logger
from mtop.logging import OperationLogger, StructuredLogger


class TestDependencyInjection:
    """Test dependency injection container."""

    def test_container_singleton_registration(self) -> None:
        """Test singleton registration and retrieval."""
        container = Container()

        # Create mock logger
        mock_logger = Mock(spec=Logger)
        container.register_singleton(Logger, mock_logger)

        # Should return the same instance
        retrieved1 = container.get(Logger)
        retrieved2 = container.get(Logger)

        assert retrieved1 is mock_logger
        assert retrieved2 is mock_logger
        assert retrieved1 is retrieved2

    def test_container_transient_registration(self) -> None:
        """Test transient registration creates new instances."""
        container = Container()

        # Register a simple class
        class TestService:
            def __init__(self) -> None:
                self.id = id(self)

        container.register_transient(TestService, TestService)

        # Should return different instances
        instance1 = container.get(TestService)
        instance2 = container.get(TestService)

        assert instance1 is not instance2
        assert instance1.id != instance2.id

    def test_container_dependency_injection(self) -> None:
        """Test automatic dependency injection."""
        container = Container()

        # Register dependencies
        mock_logger = Mock(spec=Logger)
        mock_filesystem = Mock(spec=FileSystem)

        container.register_singleton(Logger, mock_logger)
        container.register_singleton(FileSystem, mock_filesystem)

        # Register service that depends on others
        container.register_transient(MockKubernetesClient, MockKubernetesClient)

        # Should inject dependencies automatically
        service = container.get(MockKubernetesClient)
        assert service.logger is mock_logger
        assert service.file_system is mock_filesystem


class TestAsyncOperations:
    """Test async CLI operations."""

    @pytest.fixture
    def mock_k8s_client(self) -> Mock:
        """Create mock Kubernetes client."""
        mock = Mock(spec=KubernetesClient)
        mock.get_resource.return_value = asyncio.coroutine(
            lambda: {"metadata": {"name": "test"}, "status": {"conditions": []}}
        )()
        return mock

    @pytest.fixture
    def async_kubectl_ld(self, mock_k8s_client: Mock) -> AsyncKubectlLD:
        """Create AsyncKubectlLD instance."""
        mock_logger = Mock(spec=Logger)
        return AsyncKubectlLD(mode="mock", k8s_client=mock_k8s_client, logger=mock_logger)

    @pytest.mark.asyncio
    async def test_list_crs(self, async_kubectl_ld: AsyncKubectlLD) -> None:
        """Test async CR listing."""
        async_kubectl_ld.k8s_client.get_resource.return_value = {
            "items": [{"metadata": {"name": "cr1"}}, {"metadata": {"name": "cr2"}}]
        }

        crs = await async_kubectl_ld.list_crs()
        assert len(crs) == 2
        assert crs[0]["metadata"]["name"] == "cr1"
        assert crs[1]["metadata"]["name"] == "cr2"

    @pytest.mark.asyncio
    async def test_get_multiple_crs(self, async_kubectl_ld: AsyncKubectlLD) -> None:
        """Test concurrent CR retrieval."""

        async def mock_get_resource(resource_type: str, name: str) -> Dict[str, Any]:
            return {"metadata": {"name": name}, "status": {"ready": True}}

        async_kubectl_ld.k8s_client.get_resource.side_effect = mock_get_resource

        names = ["cr1", "cr2", "cr3"]
        results = await async_kubectl_ld.get_multiple_crs(names)

        assert len(results) == 3
        for name in names:
            assert name in results
            assert results[name]["metadata"]["name"] == name

    @pytest.mark.asyncio
    async def test_resource_monitor(self) -> None:
        """Test async resource monitoring."""
        mock_kubectl_ld = Mock(spec=AsyncKubectlLD)
        mock_kubectl_ld.list_crs.return_value = [{"metadata": {"name": "test-cr"}}]
        mock_kubectl_ld.get_multiple_crs.return_value = {
            "test-cr": {"metadata": {"name": "test-cr"}, "status": {"ready": True}}
        }

        monitor = AsyncResourceMonitor(mock_kubectl_ld, interval=0.1)

        # Start monitor briefly
        monitor_task = asyncio.create_task(monitor.start())
        await asyncio.sleep(0.2)  # Let it run for a bit
        await monitor.stop()

        # Should have cached resources
        cache = monitor.get_cached_resources()
        assert "test-cr" in cache


class TestLogging:
    """Test logging infrastructure."""

    def test_structured_logger_creation(self) -> None:
        """Test structured logger creation."""
        logger = StructuredLogger("test", level="DEBUG")
        assert logger.name == "test"
        assert logger.structured is True

    def test_logger_with_context(self) -> None:
        """Test logger context."""
        logger = StructuredLogger("test")
        context_logger = logger.with_context(operation="test_op", user="test_user")

        assert context_logger.context["operation"] == "test_op"
        assert context_logger.context["user"] == "test_user"

    def test_operation_logger(self) -> None:
        """Test operation logger context manager."""
        mock_logger = Mock(spec=Logger)

        with OperationLogger(mock_logger, "test_operation") as op_logger:
            op_logger.add_context(resource="test-cr")
            op_logger.log_progress("halfway done")

        # Should log start, progress, and completion
        assert mock_logger.info.call_count >= 3


class TestCaching:
    """Test caching and performance optimization."""

    def test_lru_cache_basic_operations(self) -> None:
        """Test basic LRU cache operations."""
        cache = LRUCache[str](max_size=2)

        # Test put and get
        cache.put("key1", "value1")
        cache.put("key2", "value2")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.size == 2

        # Test eviction
        cache.put("key3", "value3")  # Should evict key1 (LRU)
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.size == 2

    def test_lru_cache_ttl(self) -> None:
        """Test TTL functionality."""
        import time

        cache = LRUCache[str](max_size=10, default_ttl=0.1)  # 100ms TTL

        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(0.15)
        assert cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_async_cache(self) -> None:
        """Test async cache with computation."""
        cache = AsyncCache[str](max_size=10)

        call_count = 0

        async def expensive_computation() -> str:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate work
            return f"result_{call_count}"

        # First call should compute
        result1 = await cache.get_or_compute("key1", expensive_computation())
        assert result1 == "result_1"
        assert call_count == 1

        # Second call should use cache
        result2 = await cache.get_or_compute("key1", expensive_computation())
        assert result2 == "result_1"  # Same result
        assert call_count == 1  # No additional computation

    def test_cache_manager(self) -> None:
        """Test cache manager."""
        manager = CacheManager()

        # Get caches
        cache1 = manager.get_cache("test_cache", max_size=10)
        cache2 = manager.get_cache("test_cache")  # Should return same instance

        assert cache1 is cache2

        # Add some data
        cache1.put("test", "value")
        assert cache2.get("test") == "value"

        # Test stats
        stats = manager.stats()
        assert "test_cache" in stats


class TestImplementations:
    """Test concrete implementations."""

    def test_local_filesystem(self, tmp_path: Path) -> None:
        """Test local filesystem implementation."""
        fs = LocalFileSystem()
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"

        # Test write
        fs.write_file(test_file, test_content)
        assert test_file.exists()

        # Test read
        content = fs.read_file(test_file)
        assert content == test_content

        # Test exists
        assert fs.exists(test_file) is True
        assert fs.exists(tmp_path / "nonexistent.txt") is False

        # Test list files
        files = fs.list_files(tmp_path, "*.txt")
        assert len(files) == 1
        assert files[0] == test_file


if __name__ == "__main__":
    pytest.main([__file__])
