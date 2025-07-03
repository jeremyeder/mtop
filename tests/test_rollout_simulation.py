import json
import pytest
from pathlib import Path

BASE = Path("mocks/states/rollout")

@pytest.mark.parametrize("topology", ["canary", "bluegreen", "rolling", "shadow"])
def test_rollout_topology_structure(topology):
    steps = sorted((BASE / topology).glob("step*.json"))
    assert steps, f"No steps found for {topology}"

    for path in steps:
        with open(path) as f:
            data = json.load(f)
        assert "traffic" in data
        assert "status" in data
        total_traffic = sum(data["traffic"].values())
        assert 0 <= total_traffic <= 100, f"Traffic out of bounds in {path}"
        for model, info in data["status"].items():
            assert "status" in info
