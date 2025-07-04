"""kubectl-ld - Mock CLI tool for debugging LLMInferenceService CRDs."""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

__author__ = "Jeremy Eder"
__email__ = "jeder@redhat.com"
__all__ = ["main"]


def main():
    """Entry point for kubectl-ld command."""
    import sys
    from pathlib import Path
    
    # Add the parent directory to sys.path to import the main script
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    
    # Import and run the main function from the kubectl-ld script
    import subprocess
    import os
    
    script_path = parent_dir / "kubectl-ld"
    
    # Execute the script with the same arguments
    result = subprocess.run([sys.executable, str(script_path)] + sys.argv[1:])
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()