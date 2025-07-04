"""kubectl-ld package with modern architecture."""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

__author__ = "Jeremy Eder"
__email__ = "jeder@redhat.com"
__all__ = ["main", "setup_container", "configure_logging"]


def setup_container() -> None:
    """Set up dependency injection container with default implementations."""
    from .container import get_container
    from .implementations import LocalFileSystem, MockKubernetesClient, KubectlClient
    from .logging import DefaultLogger
    from .cache import CacheManager
    from .interfaces import FileSystem, KubernetesClient, Logger
    import os
    
    container = get_container()
    
    # Register core services
    container.register_singleton(FileSystem, LocalFileSystem())
    container.register_singleton(Logger, DefaultLogger())
    container.register_singleton(CacheManager, CacheManager())
    
    # Register Kubernetes client based on mode
    mode = os.environ.get("LLD_MODE", "mock")
    if mode == "live":
        container.register_transient(KubernetesClient, KubectlClient)
    else:
        container.register_transient(KubernetesClient, MockKubernetesClient)


def configure_logging() -> None:
    """Configure logging from environment variables."""
    import os
    from .logging import configure_logging as _configure_logging
    
    level = os.environ.get("LDCTL_LOG_LEVEL", "INFO")
    log_file = os.environ.get("LDCTL_LOG_FILE")
    structured = os.environ.get("LDCTL_LOG_FORMAT", "structured") == "structured"
    
    _configure_logging(level, log_file, structured)


def main() -> None:
    """Entry point for kubectl-ld command."""
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
    
    script_path = parent_dir / "kubectl-ld"
    spec = importlib.util.spec_from_file_location("kubectl_ld_main", script_path)
    kubectl_ld_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kubectl_ld_main)
    
    # Call the main function directly
    kubectl_ld_main.main()


if __name__ == "__main__":
    main()