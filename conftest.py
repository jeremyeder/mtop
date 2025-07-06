"""Global pytest configuration."""
import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


# Skip slow tests in CI by default
def pytest_collection_modifyitems(config, items):
    """Skip slow/integration tests in CI."""
    import os

    if os.environ.get("CI"):
        skip_slow = pytest.mark.skip(reason="Slow test skipped in CI")

        for item in items:
            # Skip any test that takes more than a few seconds
            if any(marker in item.keywords for marker in ["slow", "integration"]):
                item.add_marker(skip_slow)

            # Skip specific slow test patterns
            if any(
                pattern in item.nodeid
                for pattern in [
                    "test_simulation",
                    "test_scenario",
                    "test_performance",
                    "test_stress",
                    "test_thread_safety",
                    "test_workload",
                    "test_integration",
                    "test_phase1",
                ]
            ):
                item.add_marker(skip_slow)
