import subprocess
import os
import json
import pytest

CLI = "./kubectl-ld"

@pytest.fixture(scope="module", autouse=True)
def setup_env():
    os.environ["LLD_MODE"] = "mock"

def test_list_runs():
    result = subprocess.run([CLI, "list"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Ready" in result.stdout

def test_get_gpt2_yaml():
    result = subprocess.run([CLI, "get", "gpt2"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "metadata:" in result.stdout
    assert "gpt2" in result.stdout

def test_get_gpt2_json():
    result = subprocess.run([CLI, "get", "gpt2", "--json"], capture_output=True, text=True)
    assert result.returncode == 0
    assert json.loads(result.stdout)["metadata"]["name"] == "gpt2"

def test_config_outputs():
    result = subprocess.run([CLI, "config"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "defaultRuntime" in result.stdout

def test_help():
    result = subprocess.run([CLI, "help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Show usage help" in result.stdout
