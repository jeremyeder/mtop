"""Type interfaces and protocols for mtop components."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class Formatter(Protocol):
    """Protocol for column formatters."""

    def format(self, value: Any, config: Dict[str, Any]) -> str:
        """Format a value according to the formatter's rules."""
        raise NotImplementedError

    def get_sort_key(self, value: Any) -> Any:
        """Get sort key for the value."""
        raise NotImplementedError


@runtime_checkable
class Renderer(Protocol):
    """Protocol for table renderers."""

    def create_table(self, columns: List[Dict[str, Any]]) -> Any:
        """Create a table structure."""
        raise NotImplementedError

    def add_row(self, table: Any, row_data: Dict[str, Any]) -> None:
        """Add a row to the table."""
        raise NotImplementedError

    def render(self, table: Any) -> str:
        """Render the table to string."""
        raise NotImplementedError


@runtime_checkable
class Monitor(Protocol):
    """Protocol for monitoring implementations."""

    async def start(self) -> None:
        """Start monitoring."""
        raise NotImplementedError

    async def stop(self) -> None:
        """Stop monitoring."""
        raise NotImplementedError

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        raise NotImplementedError


@runtime_checkable
class FileSystem(Protocol):
    """Protocol for file system operations."""

    def read_file(self, path: Path) -> str:
        """Read file contents."""
        raise NotImplementedError

    def write_file(self, path: Path, content: str) -> None:
        """Write file contents."""
        raise NotImplementedError

    def exists(self, path: Path) -> bool:
        """Check if path exists."""
        raise NotImplementedError

    def list_files(self, path: Path, pattern: str = "*") -> List[Path]:
        """List files matching pattern."""
        raise NotImplementedError


@runtime_checkable
class KubernetesClient(Protocol):
    """Protocol for Kubernetes operations."""

    async def get_resource(
        self, resource_type: str, name: Optional[str] = None, namespace: str = "default"
    ) -> Dict[str, Any]:
        """Get Kubernetes resource."""
        raise NotImplementedError

    async def create_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Kubernetes resource."""
        raise NotImplementedError

    async def delete_resource(
        self, resource_type: str, name: str, namespace: str = "default"
    ) -> bool:
        """Delete Kubernetes resource."""
        raise NotImplementedError

    async def get_logs(self, deployment_name: str, namespace: str = "default") -> str:
        """Get deployment logs."""
        raise NotImplementedError


@runtime_checkable
class ConfigProvider(Protocol):
    """Protocol for configuration providers."""

    def load_config(self, path: Optional[Path] = None) -> Dict[str, Any]:
        """Load configuration."""
        raise NotImplementedError

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get specific setting."""
        raise NotImplementedError

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return warnings."""
        raise NotImplementedError


@runtime_checkable
class Logger(Protocol):
    """Protocol for logging operations."""

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        raise NotImplementedError

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        raise NotImplementedError

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        raise NotImplementedError

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        raise NotImplementedError


class BaseFormatter(ABC):
    """Abstract base class for formatters."""

    @abstractmethod
    def format(self, value: Any, config: Dict[str, Any]) -> str:
        """Format a value according to the formatter's rules."""
        pass

    def get_sort_key(self, value: Any) -> Any:
        """Get sort key for the value. Default implementation returns value as-is."""
        return value


class BaseRenderer(ABC):
    """Abstract base class for renderers."""

    @abstractmethod
    def create_table(self, columns: List[Dict[str, Any]]) -> Any:
        """Create a table structure."""
        pass

    @abstractmethod
    def add_row(self, table: Any, row_data: Dict[str, Any]) -> None:
        """Add a row to the table."""
        pass

    @abstractmethod
    def render(self, table: Any) -> str:
        """Render the table to string."""
        pass


class BaseMonitor(ABC):
    """Abstract base class for monitors."""

    def __init__(self) -> None:
        self._running = False

    @abstractmethod
    async def start(self) -> None:
        """Start monitoring."""
        self._running = True

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        pass
