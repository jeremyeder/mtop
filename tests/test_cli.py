import json
import subprocess
from pathlib import Path

BIN = "./mtop-main"
MOCK_ENV = {"LLD_MODE": "mock"}


def run_cmd(args, env=None):
    import sys

    result = subprocess.run(
        [sys.executable, BIN] + args,
        env=env or MOCK_ENV,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result


def test_list_topologies():
    result = run_cmd(["list-topologies"])
    assert "canary" in result.stdout
    assert "rolling" in result.stdout
    assert result.returncode == 0


def test_simulate_rollout():
    result = run_cmd(["simulate", "canary"])
    assert "Step 1" in result.stdout
    assert "gpt2" in result.stdout


def test_get_existing_cr():
    result = run_cmd(["get", "gpt2"])
    assert "metadata" in result.stdout or "name" in result.stdout


def test_config_output():
    result = run_cmd(["config"])
    assert "defaultRuntime" in result.stdout
    assert result.returncode == 0


def test_list_crs():
    result = run_cmd(["list"])
    assert "gpt2" in result.stdout
    assert result.returncode == 0


def test_delete_cr():
    # delete a mock CR and check it disappears
    import sys

    subprocess.run([sys.executable, BIN, "delete", "bert-base-cased"], env=MOCK_ENV)
    result = run_cmd(["list"])
    assert "bert-base-cased" not in result.stdout


def test_create_cr():
    sample = {
        "apiVersion": "serving.kserve.io/v1alpha1",
        "kind": "LLMInferenceService",
        "metadata": {"name": "test-model"},
        "spec": {"model": {"type": "gpt2"}},
    }
    file = Path("tests/test-cr.yaml")
    file.write_text(json.dumps(sample))
    result = run_cmd(["create", str(file)])
    assert "✅ Created" in result.stdout or result.returncode == 0


def test_invalid_topology_simulate():
    result = run_cmd(["simulate", "nonexistent"])
    assert "❌" in result.stdout or result.stderr
    assert result.returncode == 0


def test_help_output():
    result = run_cmd(["help"])
    assert "usage" in result.stdout.lower() or "Available commands" in result.stdout
