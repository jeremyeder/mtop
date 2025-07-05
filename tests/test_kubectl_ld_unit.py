"""Unit tests for KubectlLD class methods."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

# Import the KubectlLD class - we need to set up the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock the early Python version check and import KubectlLD
with patch('sys.version_info', (3, 11, 0)):
    # Execute the kubectl-ld script to define all classes
    kubectl_ld_path = Path(__file__).parent.parent / 'kubectl-ld'
    kubectl_ld_globals = {
        '__file__': str(kubectl_ld_path),  # Provide __file__ for Path(__file__) references
        '__name__': 'kubectl-ld'  # Don't use __main__ to avoid calling main()
    }
    with open(kubectl_ld_path) as f:
        exec(f.read(), kubectl_ld_globals)
    # Extract the classes we need
    KubectlLD = kubectl_ld_globals['KubectlLD']
    ModelMetrics = kubectl_ld_globals.get('ModelMetrics')  # May be needed by some tests


class TestKubectlLD:
    """Test cases for KubectlLD class."""
    
    @pytest.fixture
    def kubectl_ld_mock(self):
        """Create a KubectlLD instance with mocked paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            kubectl_ld = KubectlLD(mode="mock")
            kubectl_ld.mock_root = Path(temp_dir)
            kubectl_ld.crs_dir = kubectl_ld.mock_root / "crs"
            kubectl_ld.config_path = kubectl_ld.mock_root / "config" / "llminferenceserviceconfig.json"
            kubectl_ld.logs_dir = kubectl_ld.mock_root / "pod_logs"
            kubectl_ld.states_dir = kubectl_ld.mock_root / "states" / "rollout"
            
            # Create directories
            kubectl_ld.crs_dir.mkdir(parents=True, exist_ok=True)
            kubectl_ld.config_path.parent.mkdir(parents=True, exist_ok=True)
            kubectl_ld.logs_dir.mkdir(parents=True, exist_ok=True)
            kubectl_ld.states_dir.mkdir(parents=True, exist_ok=True)
            
            yield kubectl_ld
    
    @pytest.fixture
    def kubectl_ld_live(self):
        """Create a KubectlLD instance in live mode."""
        return KubectlLD(mode="live")
    
    @pytest.fixture
    def sample_cr_data(self):
        """Sample CR data for testing."""
        return {
            "apiVersion": "serving.kserve.io/v1alpha1",
            "kind": "LLMInferenceService",
            "metadata": {"name": "test-model", "namespace": "default"},
            "spec": {"model": {"type": "gpt2"}},
            "status": {
                "conditions": [
                    {"type": "Ready", "status": "True", "message": "Model loaded"}
                ]
            }
        }
    
    def test_init_mock_mode(self, kubectl_ld_mock):
        """Test initialization in mock mode."""
        assert kubectl_ld_mock.mode == "mock"
        assert not kubectl_ld_mock.is_live
        assert kubectl_ld_mock.mock_root.exists()
        assert kubectl_ld_mock.crs_dir.exists()
    
    def test_init_live_mode(self, kubectl_ld_live):
        """Test initialization in live mode."""
        assert kubectl_ld_live.mode == "live"
        assert kubectl_ld_live.is_live
    
    def test_list_crs_mock_mode(self, kubectl_ld_mock, sample_cr_data, capsys):
        """Test list_crs in mock mode."""
        # Create sample CR files
        cr_file = kubectl_ld_mock.crs_dir / "test-model.json"
        with open(cr_file, 'w') as f:
            json.dump(sample_cr_data, f)
        
        kubectl_ld_mock.list_crs()
        captured = capsys.readouterr()
        assert "test-model" in captured.out
        assert "Ready: True" in captured.out
    
    def test_list_crs_empty_mock(self, kubectl_ld_mock, capsys):
        """Test list_crs with no CRs in mock mode."""
        kubectl_ld_mock.list_crs()
        captured = capsys.readouterr()
        # Should still show the mode header
        assert "🔧 Mode:" in captured.out or len(captured.out.strip()) == 0
    
    @patch('subprocess.run')
    def test_list_crs_live_mode(self, mock_subprocess, kubectl_ld_live, sample_cr_data):
        """Test list_crs in live mode."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"items": [sample_cr_data]})
        mock_subprocess.return_value = mock_result
        
        with patch('builtins.print') as mock_print:
            kubectl_ld_live.list_crs()
            mock_print.assert_called()
    
    def test_get_cr_mock_mode(self, kubectl_ld_mock, sample_cr_data, capsys):
        """Test get_cr in mock mode."""
        # Create sample CR file
        cr_file = kubectl_ld_mock.crs_dir / "test-model.json"
        with open(cr_file, 'w') as f:
            json.dump(sample_cr_data, f)
        
        kubectl_ld_mock.get_cr("test-model", output_json=False)
        captured = capsys.readouterr()
        assert "metadata:" in captured.out
        assert "test-model" in captured.out
    
    def test_get_cr_json_output(self, kubectl_ld_mock, sample_cr_data, capsys):
        """Test get_cr with JSON output."""
        # Create sample CR file
        cr_file = kubectl_ld_mock.crs_dir / "test-model.json"
        with open(cr_file, 'w') as f:
            json.dump(sample_cr_data, f)
        
        kubectl_ld_mock.get_cr("test-model", output_json=True)
        captured = capsys.readouterr()
        
        # Should be valid JSON
        parsed = json.loads(captured.out)
        assert parsed["metadata"]["name"] == "test-model"
    
    def test_get_cr_not_found(self, kubectl_ld_mock, capsys):
        """Test get_cr with non-existent CR."""
        kubectl_ld_mock.get_cr("nonexistent", output_json=False)
        captured = capsys.readouterr()
        assert "nonexistent not found" in captured.out
    
    def test_get_config_mock_mode(self, kubectl_ld_mock, capsys):
        """Test get_config in mock mode."""
        # Create sample config file
        config_data = {"defaultRuntime": "vllm", "models": ["gpt2", "bert"]}
        with open(kubectl_ld_mock.config_path, 'w') as f:
            json.dump(config_data, f)
        
        kubectl_ld_mock.get_config(output_json=False)
        captured = capsys.readouterr()
        assert "defaultRuntime" in captured.out
    
    def test_get_config_json_output(self, kubectl_ld_mock, capsys):
        """Test get_config with JSON output."""
        config_data = {"defaultRuntime": "vllm", "models": ["gpt2", "bert"]}
        with open(kubectl_ld_mock.config_path, 'w') as f:
            json.dump(config_data, f)
        
        kubectl_ld_mock.get_config(output_json=True)
        captured = capsys.readouterr()
        
        # Should be valid JSON
        parsed = json.loads(captured.out)
        assert parsed["defaultRuntime"] == "vllm"
    
    def test_get_config_not_found(self, kubectl_ld_mock, capsys):
        """Test get_config when config file doesn't exist."""
        kubectl_ld_mock.get_config(output_json=False)
        captured = capsys.readouterr()
        assert "No config found" in captured.out
    
    def test_check_cr(self, kubectl_ld_mock, sample_cr_data, capsys):
        """Test check_cr function."""
        # Create sample CR file
        cr_file = kubectl_ld_mock.crs_dir / "test-model.json"
        with open(cr_file, 'w') as f:
            json.dump(sample_cr_data, f)
        
        kubectl_ld_mock.check_cr("test-model")
        captured = capsys.readouterr()
        assert "test-model status:" in captured.out
        assert "Ready" in captured.out
        assert "Model loaded" in captured.out
    
    def test_check_cr_not_found(self, kubectl_ld_mock, capsys):
        """Test check_cr with non-existent CR."""
        kubectl_ld_mock.check_cr("nonexistent")
        captured = capsys.readouterr()
        assert "nonexistent not found" in captured.out
    
    def test_show_logs_mock_mode(self, kubectl_ld_mock, capsys):
        """Test show_logs in mock mode."""
        # Create sample log file
        log_file = kubectl_ld_mock.logs_dir / "test-model.txt"
        log_content = "INFO: Model loaded successfully\\nINFO: Ready to serve requests"
        with open(log_file, 'w') as f:
            f.write(log_content)
        
        kubectl_ld_mock.show_logs("test-model")
        captured = capsys.readouterr()
        assert "Model loaded successfully" in captured.out
        assert "Ready to serve requests" in captured.out
    
    def test_show_logs_not_found(self, kubectl_ld_mock, capsys):
        """Test show_logs when log file doesn't exist."""
        kubectl_ld_mock.show_logs("nonexistent")
        captured = capsys.readouterr()
        assert "No logs found" in captured.out
    
    def test_delete_cr_success(self, kubectl_ld_mock, sample_cr_data, capsys):
        """Test successful CR deletion."""
        # Create sample CR file
        cr_file = kubectl_ld_mock.crs_dir / "test-model.json"
        with open(cr_file, 'w') as f:
            json.dump(sample_cr_data, f)
        
        assert cr_file.exists()
        kubectl_ld_mock.delete_cr("test-model")
        assert not cr_file.exists()
        
        captured = capsys.readouterr()
        assert "test-model deleted" in captured.out
    
    def test_delete_cr_not_found(self, kubectl_ld_mock, capsys):
        """Test deletion of non-existent CR."""
        kubectl_ld_mock.delete_cr("nonexistent")
        captured = capsys.readouterr()
        assert "nonexistent not found" in captured.out
    
    def test_create_cr_json(self, kubectl_ld_mock, sample_cr_data, capsys):
        """Test CR creation from JSON file."""
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_cr_data, f)
            temp_file = f.name
        
        try:
            kubectl_ld_mock.create_cr(temp_file)
            
            # Check if CR was created
            cr_file = kubectl_ld_mock.crs_dir / "test-model.json"
            assert cr_file.exists()
            
            with open(cr_file) as f:
                created_data = json.load(f)
            assert created_data["metadata"]["name"] == "test-model"
            
            captured = capsys.readouterr()
            assert "Created" in captured.out
        finally:
            os.unlink(temp_file)
    
    def test_create_cr_yaml(self, kubectl_ld_mock, sample_cr_data, capsys):
        """Test CR creation from YAML file."""
        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_cr_data, f)
            temp_file = f.name
        
        try:
            kubectl_ld_mock.create_cr(temp_file)
            
            # Check if CR was created
            cr_file = kubectl_ld_mock.crs_dir / "test-model.json"
            assert cr_file.exists()
            
            captured = capsys.readouterr()
            assert "Created" in captured.out
        finally:
            os.unlink(temp_file)
    
    def test_create_cr_file_not_found(self, kubectl_ld_mock, capsys):
        """Test CR creation with non-existent file."""
        kubectl_ld_mock.create_cr("/nonexistent/path.json")
        captured = capsys.readouterr()
        assert "File not found" in captured.out
    
    def test_list_topologies(self, kubectl_ld_mock, capsys):
        """Test list_topologies function."""
        # Create sample topology directories
        (kubectl_ld_mock.states_dir / "canary").mkdir(parents=True)
        (kubectl_ld_mock.states_dir / "rolling").mkdir(parents=True)
        (kubectl_ld_mock.states_dir / "bluegreen").mkdir(parents=True)
        
        kubectl_ld_mock.list_topologies()
        captured = capsys.readouterr()
        assert "canary" in captured.out
        assert "rolling" in captured.out
        assert "bluegreen" in captured.out
    
    def test_simulate_rollout(self, kubectl_ld_mock, capsys):
        """Test simulate_rollout function."""
        # Create sample rollout steps
        topology_dir = kubectl_ld_mock.states_dir / "canary"
        topology_dir.mkdir(parents=True)
        
        step_data = {
            "step": 1,
            "timestamp": "00:00",
            "traffic": {"old-model": 90, "new-model": 10},
            "status": {
                "old-model": {"status": "Ready"},
                "new-model": {"status": "Pending"}
            }
        }
        
        with open(topology_dir / "step1.json", 'w') as f:
            json.dump(step_data, f)
        
        kubectl_ld_mock.simulate_rollout("canary")
        captured = capsys.readouterr()
        assert "Step 1" in captured.out
        assert "old-model" in captured.out
        assert "new-model" in captured.out
    
    def test_simulate_rollout_not_found(self, kubectl_ld_mock, capsys):
        """Test simulate_rollout with non-existent topology."""
        kubectl_ld_mock.simulate_rollout("nonexistent")
        captured = capsys.readouterr()
        assert "No rollout steps found" in captured.out
    
    @patch('subprocess.run')
    def test_kubectl_get_success(self, mock_subprocess, kubectl_ld_live):
        """Test successful kubectl_get call."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"items": []}'
        mock_subprocess.return_value = mock_result
        
        result = kubectl_ld_live.kubectl_get("llminferenceservice")
        assert result == {"items": []}
    
    @patch('subprocess.run')
    def test_kubectl_get_failure(self, mock_subprocess, kubectl_ld_live):
        """Test kubectl_get failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: resource not found"
        mock_subprocess.return_value = mock_result
        
        with pytest.raises(SystemExit):
            kubectl_ld_live.kubectl_get("llminferenceservice")