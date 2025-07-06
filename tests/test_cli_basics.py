"""Basic CLI tests to ensure command-line interface works."""

import subprocess
import sys


def test_help_command():
    """CLI shows help without crashing."""
    result = subprocess.run([sys.executable, "mtop-main", "help"], capture_output=True, timeout=5)
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "usage" in output.lower() or "mtop" in output.lower()


def test_list_command():
    """CLI list command works."""
    result = subprocess.run([sys.executable, "mtop-main", "list"], capture_output=True, timeout=5)
    assert result.returncode == 0
