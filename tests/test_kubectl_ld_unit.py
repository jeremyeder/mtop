"""Unit tests for MTop class methods."""

import json
import os

# Import the MTop class - we need to set up the path
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock the early Python version check
with patch("sys.version_info", (3, 11, 0)):
    exec(open(Path(__file__).parent.parent / "mtop-main").read())


class TestMTop:
    """Test cases for MTop class."""

    @pytest.fixture
    def mtop_mock(self):
        """Create a MTop instance with mocked paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mtop = MTop(mode="mock")
            mtop.mock_root = Path(temp_dir)
            mtop.crs_dir = mtop.mock_root / "crs"
            mtop.config_path = (
                mtop.mock_root / "config" / "llminferenceserviceconfig.json"
            )
            mtop.logs_dir = mtop.mock_root / "pod_logs"
            mtop.states_dir = mtop.mock_root / "states" / "rollout"

            # Create directories
            mtop.crs_dir.mkdir(parents=True, exist_ok=True)
            mtop.config_path.parent.mkdir(parents=True, exist_ok=True)
            mtop.logs_dir.mkdir(parents=True, exist_ok=True)
            mtop.states_dir.mkdir(parents=True, exist_ok=True)

            yield mtop

    @pytest.fixture
    def mtop_live(self):
        """Create a MTop instance in live mode."""
        return MTop(mode="live")

    @pytest.fixture
    def sample_cr_data(self):
        """Sample CR data for testing."""
        return {
            "apiVersion": "serving.kserve.io/v1alpha1",
            "kind": "LLMInferenceService",
            "metadata": {"name": "test-model", "namespace": "default"},
            "spec": {"model": {"type": "gpt2"}},
            "status": {
                "conditions": [{"type": "Ready", "status": "True", "message": "Model loaded"}]
            },
        }

    def test_init_mock_mode(self, mtop_mock):
        """Test initialization in mock mode."""
        assert mtop_mock.mode == "mock"
        assert not mtop_mock.is_live
        assert mtop_mock.mock_root.exists()
        assert mtop_mock.crs_dir.exists()

    def test_init_live_mode(self, mtop_live):
        """Test initialization in live mode."""
        assert mtop_live.mode == "live"
        assert mtop_live.is_live

    def test_list_crs_mock_mode(self, mtop_mock, sample_cr_data, capsys):
        """Test list_crs in mock mode."""
        # Create sample CR files
        cr_file = mtop_mock.crs_dir / "test-model.json"
        with open(cr_file, "w") as f:
            json.dump(sample_cr_data, f)

        mtop_mock.list_crs()
        captured = capsys.readouterr()
        assert "test-model" in captured.out
        assert "Ready: True" in captured.out

    def test_list_crs_empty_mock(self, mtop_mock, capsys):
        """Test list_crs with no CRs in mock mode."""
        mtop_mock.list_crs()
        captured = capsys.readouterr()
        # Should still show the mode header
        assert "🔧 Mode:" in captured.out or len(captured.out.strip()) == 0

    @patch("subprocess.run")
    def test_list_crs_live_mode(self, mock_subprocess, mtop_live, sample_cr_data):
        """Test list_crs in live mode."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"items": [sample_cr_data]})
        mock_subprocess.return_value = mock_result

        with patch("builtins.print") as mock_print:
            mtop_live.list_crs()
            mock_print.assert_called()

    def test_get_cr_mock_mode(self, mtop_mock, sample_cr_data, capsys):
        """Test get_cr in mock mode."""
        # Create sample CR file
        cr_file = mtop_mock.crs_dir / "test-model.json"
        with open(cr_file, "w") as f:
            json.dump(sample_cr_data, f)

        mtop_mock.get_cr("test-model", output_json=False)
        captured = capsys.readouterr()
        assert "metadata:" in captured.out
        assert "test-model" in captured.out

    def test_get_cr_json_output(self, mtop_mock, sample_cr_data, capsys):
        """Test get_cr with JSON output."""
        # Create sample CR file
        cr_file = mtop_mock.crs_dir / "test-model.json"
        with open(cr_file, "w") as f:
            json.dump(sample_cr_data, f)

        mtop_mock.get_cr("test-model", output_json=True)
        captured = capsys.readouterr()

        # Should be valid JSON
        parsed = json.loads(captured.out)
        assert parsed["metadata"]["name"] == "test-model"

    def test_get_cr_not_found(self, mtop_mock, capsys):
        """Test get_cr with non-existent CR."""
        mtop_mock.get_cr("nonexistent", output_json=False)
        captured = capsys.readouterr()
        assert "nonexistent not found" in captured.out

    def test_get_config_mock_mode(self, mtop_mock, capsys):
        """Test get_config in mock mode."""
        # Create sample config file
        config_data = {"defaultRuntime": "vllm", "models": ["gpt2", "bert"]}
        with open(mtop_mock.config_path, "w") as f:
            json.dump(config_data, f)

        mtop_mock.get_config(output_json=False)
        captured = capsys.readouterr()
        assert "defaultRuntime" in captured.out

    def test_get_config_json_output(self, mtop_mock, capsys):
        """Test get_config with JSON output."""
        config_data = {"defaultRuntime": "vllm", "models": ["gpt2", "bert"]}
        with open(mtop_mock.config_path, "w") as f:
            json.dump(config_data, f)

        mtop_mock.get_config(output_json=True)
        captured = capsys.readouterr()

        # Should be valid JSON
        parsed = json.loads(captured.out)
        assert parsed["defaultRuntime"] == "vllm"

    def test_get_config_not_found(self, mtop_mock, capsys):
        """Test get_config when config file doesn't exist."""
        mtop_mock.get_config(output_json=False)
        captured = capsys.readouterr()
        assert "No config found" in captured.out

    def test_check_cr(self, mtop_mock, sample_cr_data, capsys):
        """Test check_cr function."""
        # Create sample CR file
        cr_file = mtop_mock.crs_dir / "test-model.json"
        with open(cr_file, "w") as f:
            json.dump(sample_cr_data, f)

        mtop_mock.check_cr("test-model")
        captured = capsys.readouterr()
        assert "test-model status:" in captured.out
        assert "Ready" in captured.out
        assert "Model loaded" in captured.out

    def test_check_cr_not_found(self, mtop_mock, capsys):
        """Test check_cr with non-existent CR."""
        mtop_mock.check_cr("nonexistent")
        captured = capsys.readouterr()
        assert "nonexistent not found" in captured.out

    def test_show_logs_mock_mode(self, mtop_mock, capsys):
        """Test show_logs in mock mode."""
        # Create sample log file
        log_file = mtop_mock.logs_dir / "test-model.txt"
        log_content = "INFO: Model loaded successfully\\nINFO: Ready to serve requests"
        with open(log_file, "w") as f:
            f.write(log_content)

        mtop_mock.show_logs("test-model")
        captured = capsys.readouterr()
        assert "Model loaded successfully" in captured.out
        assert "Ready to serve requests" in captured.out

    def test_show_logs_not_found(self, mtop_mock, capsys):
        """Test show_logs when log file doesn't exist."""
        mtop_mock.show_logs("nonexistent")
        captured = capsys.readouterr()
        assert "No logs found" in captured.out

    def test_delete_cr_success(self, mtop_mock, sample_cr_data, capsys):
        """Test successful CR deletion."""
        # Create sample CR file
        cr_file = mtop_mock.crs_dir / "test-model.json"
        with open(cr_file, "w") as f:
            json.dump(sample_cr_data, f)

        assert cr_file.exists()
        mtop_mock.delete_cr("test-model")
        assert not cr_file.exists()

        captured = capsys.readouterr()
        assert "test-model deleted" in captured.out

    def test_delete_cr_not_found(self, mtop_mock, capsys):
        """Test deletion of non-existent CR."""
        mtop_mock.delete_cr("nonexistent")
        captured = capsys.readouterr()
        assert "nonexistent not found" in captured.out

    def test_create_cr_json(self, mtop_mock, sample_cr_data, capsys):
        """Test CR creation from JSON file."""
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_cr_data, f)
            temp_file = f.name

        try:
            mtop_mock.create_cr(temp_file)

            # Check if CR was created
            cr_file = mtop_mock.crs_dir / "test-model.json"
            assert cr_file.exists()

            with open(cr_file) as f:
                created_data = json.load(f)
            assert created_data["metadata"]["name"] == "test-model"

            captured = capsys.readouterr()
            assert "Created" in captured.out
        finally:
            os.unlink(temp_file)

    def test_create_cr_yaml(self, mtop_mock, sample_cr_data, capsys):
        """Test CR creation from YAML file."""
        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_cr_data, f)
            temp_file = f.name

        try:
            mtop_mock.create_cr(temp_file)

            # Check if CR was created
            cr_file = mtop_mock.crs_dir / "test-model.json"
            assert cr_file.exists()

            captured = capsys.readouterr()
            assert "Created" in captured.out
        finally:
            os.unlink(temp_file)

    def test_create_cr_file_not_found(self, mtop_mock, capsys):
        """Test CR creation with non-existent file."""
        mtop_mock.create_cr("/nonexistent/path.json")
        captured = capsys.readouterr()
        assert "File not found" in captured.out

    def test_list_topologies(self, mtop_mock, capsys):
        """Test list_topologies function."""
        # Create sample topology directories
        (mtop_mock.states_dir / "canary").mkdir(parents=True)
        (mtop_mock.states_dir / "rolling").mkdir(parents=True)
        (mtop_mock.states_dir / "bluegreen").mkdir(parents=True)

        mtop_mock.list_topologies()
        captured = capsys.readouterr()
        assert "canary" in captured.out
        assert "rolling" in captured.out
        assert "bluegreen" in captured.out

    def test_simulate_rollout(self, mtop_mock, capsys):
        """Test simulate_rollout function."""
        # Create sample rollout steps
        topology_dir = mtop_mock.states_dir / "canary"
        topology_dir.mkdir(parents=True)

        step_data = {
            "step": 1,
            "timestamp": "00:00",
            "traffic": {"old-model": 90, "new-model": 10},
            "status": {"old-model": {"status": "Ready"}, "new-model": {"status": "Pending"}},
        }

        with open(topology_dir / "step1.json", "w") as f:
            json.dump(step_data, f)

        mtop_mock.simulate_rollout("canary")
        captured = capsys.readouterr()
        assert "Step 1" in captured.out
        assert "old-model" in captured.out
        assert "new-model" in captured.out

    def test_simulate_rollout_not_found(self, mtop_mock, capsys):
        """Test simulate_rollout with non-existent topology."""
        mtop_mock.simulate_rollout("nonexistent")
        captured = capsys.readouterr()
        assert "No rollout steps found" in captured.out

    @patch("subprocess.run")
    def test_k8s_get_success(self, mock_subprocess, mtop_live):
        """Test successful k8s_get call."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"items": []}'
        mock_subprocess.return_value = mock_result

        result = mtop_live.k8s_get("llminferenceservice")
        assert result == {"items": []}

    @patch("subprocess.run")
    def test_k8s_get_failure(self, mock_subprocess, mtop_live):
        """Test k8s_get failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: resource not found"
        mock_subprocess.return_value = mock_result

        with pytest.raises(SystemExit):
            mtop_live.k8s_get("llminferenceservice")
