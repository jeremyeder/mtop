import json
import os
import subprocess

import pytest

CLI = "./kubectl-ld"


@pytest.fixture(scope="module", autouse=True)
def setup_env():
    os.environ["LLD_MODE"] = "mock"


def test_list_runs():
    import sys

    result = subprocess.run([sys.executable, CLI, "list"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Ready" in result.stdout


def test_get_gpt2_yaml():
    import sys

    result = subprocess.run([sys.executable, CLI, "get", "gpt2"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "metadata:" in result.stdout
    assert "gpt2" in result.stdout


def test_get_gpt2_json():
    import sys

    result = subprocess.run(
        [sys.executable, CLI, "--json", "get", "gpt2"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["metadata"]["name"] == "gpt2"


def test_config_outputs():
    import sys

    result = subprocess.run([sys.executable, CLI, "config"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "defaultRuntime" in result.stdout


def test_help():
    import sys

    result = subprocess.run([sys.executable, CLI, "help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "usage" in result.stdout.lower() or "Available commands" in result.stdout
