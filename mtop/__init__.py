"""mtop package with modern architecture."""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

__author__ = "Jeremy Eder"
__email__ = "jeder@redhat.com"
__all__ = ["main", "setup_container", "configure_logging"]


def setup_container() -> None:
    """Set up dependency injection container with default implementations."""
    import os

    from .cache import CacheManager
    from .container import get_container
    from .implementations import LiveKubernetesClient, LocalFileSystem, MockKubernetesClient
    from .interfaces import FileSystem, KubernetesClient, Logger
    from .logging import DefaultLogger

    container = get_container()

    # Register core services
    container.register_singleton(FileSystem, LocalFileSystem())
    container.register_singleton(Logger, DefaultLogger())
    container.register_singleton(CacheManager, CacheManager())

    # Register Kubernetes client based on mode
    mode = os.environ.get("MTOP_MODE", "mock")
    if mode == "live":
        container.register_transient(KubernetesClient, LiveKubernetesClient)
    else:
        container.register_transient(KubernetesClient, MockKubernetesClient)


def configure_logging() -> None:
    """Configure logging from environment variables."""
    import os

    from .logging import configure_logging as _configure_logging

    level = os.environ.get("MTOP_LOG_LEVEL", "INFO")
    log_file = os.environ.get("MTOP_LOG_FILE")
    structured = os.environ.get("MTOP_LOG_FORMAT", "structured") == "structured"

    _configure_logging(level, log_file, structured)


def main() -> None:
    """Entry point for mtop command."""
    import sys
    from pathlib import Path

    # Set up the new architecture
    configure_logging()
    setup_container()

    # Add the parent directory to sys.path to import the main script
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))

    # Import and run the main function directly without subprocess
    # This is more efficient than subprocess.run()
    import importlib.util

    script_path = parent_dir / "mtop-main"
    spec = importlib.util.spec_from_file_location("mtop_main", script_path)
    mtop_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mtop_main)

    # Call the main function directly
    mtop_main.main()


if __name__ == "__main__":
    main()
