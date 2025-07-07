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


def test_slo_dashboard_help():
    """SLO dashboard command help works."""
    result = subprocess.run(
        [sys.executable, "mtop-main", "slo-dashboard", "--help"], capture_output=True, timeout=5
    )
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "slo-dashboard" in output.lower()
    assert "--demo" in output.lower()
    assert "--interval" in output.lower()


def test_slo_dashboard_live_mode():
    """SLO dashboard live mode shows coming soon message."""
    result = subprocess.run(
        [sys.executable, "mtop-main", "slo-dashboard"],
        capture_output=True,
        timeout=5,
        env={"PYTHONPATH": "."},
    )
    assert result.returncode == 0
    output = result.stdout.decode()
    assert "SLO Dashboard" in output
    assert "coming soon" in output.lower() or "live mode" in output.lower()
