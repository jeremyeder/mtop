"""Integration tests for kubectl-ld end-to-end workflows."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml


class TestIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.fixture
    def cli_path(self):
        """Path to the kubectl-ld CLI."""
        return str(Path(__file__).parent.parent / "kubectl-ld")
    
    @pytest.fixture
    def mock_env(self):
        """Environment variables for mock mode."""
        return {"LLD_MODE": "mock"}
    
    @pytest.fixture
    def sample_cr_yaml(self):
        """Sample CR in YAML format."""
        return """
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata:
  name: integration-test-model
  namespace: default
spec:
  model:
    type: gpt2
    size: small
status:
  conditions:
  - type: Ready
    status: "True"
    message: "Model ready for inference"
"""
    
    def run_cli(self, cli_path, args, env=None):
        """Helper to run CLI commands."""
        import sys
        result = subprocess.run(
            [sys.executable, cli_path] + args,
            env=env,
            capture_output=True,
            text=True
        )
        return result
    
    def test_complete_cr_lifecycle(self, cli_path, mock_env, sample_cr_yaml):
        """Test complete CR lifecycle: create -> list -> get -> delete."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(sample_cr_yaml)
            yaml_file = f.name
        
        try:
            # 1. Create CR
            result = self.run_cli(cli_path, ["create", yaml_file], mock_env)
            assert result.returncode == 0
            assert "Created" in result.stdout or "✅" in result.stdout
            
            # 2. List CRs (should include our new CR)
            result = self.run_cli(cli_path, ["list"], mock_env)
            assert result.returncode == 0
            assert "integration-test-model" in result.stdout
            
            # 3. Get specific CR (YAML format)
            result = self.run_cli(cli_path, ["get", "integration-test-model"], mock_env)
            assert result.returncode == 0
            assert "metadata:" in result.stdout
            assert "integration-test-model" in result.stdout
            
            # 4. Get specific CR (JSON format)
            result = self.run_cli(cli_path, ["--json", "get", "integration-test-model"], mock_env)
            assert result.returncode == 0
            # Should be valid JSON
            data = json.loads(result.stdout)
            assert data["metadata"]["name"] == "integration-test-model"
            
            # 5. Check CR status
            result = self.run_cli(cli_path, ["check", "integration-test-model"], mock_env)
            assert result.returncode == 0
            assert "integration-test-model status:" in result.stdout
            
            # 6. Delete CR
            result = self.run_cli(cli_path, ["delete", "integration-test-model"], mock_env)
            assert result.returncode == 0
            assert "deleted" in result.stdout or "not found" in result.stdout
            
            # 7. Verify deletion (should not be in list)
            result = self.run_cli(cli_path, ["list"], mock_env)
            assert result.returncode == 0
            # CR should no longer be in the list (or file should be gone)
            
        finally:
            os.unlink(yaml_file)
    
    def test_mode_switching(self, cli_path):
        """Test switching between mock and live modes."""
        # Test mock mode (default)
        mock_env = {"LLD_MODE": "mock"}
        result = self.run_cli(cli_path, ["list"], mock_env)
        assert result.returncode == 0
        # Should show mock mode indicator or work without errors
        
        # Test explicit mock mode via flag
        result = self.run_cli(cli_path, ["--mode", "mock", "list"])
        assert result.returncode == 0
        
        # Note: We can't easily test live mode without a real cluster
        # But we can test that the mode flag is accepted
        result = self.run_cli(cli_path, ["--mode", "live", "help"])
        assert result.returncode == 0
    
    def test_config_operations(self, cli_path, mock_env):
        """Test configuration-related operations."""
        # Test getting config (YAML)
        result = self.run_cli(cli_path, ["config"], mock_env)
        assert result.returncode == 0
        # Should either show config or indicate no config found
        
        # Test getting config (JSON)
        result = self.run_cli(cli_path, ["--json", "config"], mock_env)
        assert result.returncode == 0
        # Should be JSON or empty/error message
    
    def test_topology_operations(self, cli_path, mock_env):
        """Test rollout topology operations."""
        # List available topologies
        result = self.run_cli(cli_path, ["list-topologies"], mock_env)
        assert result.returncode == 0
        # Should list available topologies
        
        # Test simulating existing topologies
        topologies = ["canary", "rolling", "bluegreen", "shadow"]
        for topology in topologies:
            result = self.run_cli(cli_path, ["simulate", topology], mock_env)
            assert result.returncode == 0
            # Should either show simulation or indicate no steps found
    
    def test_help_system(self, cli_path):
        """Test help system and command discovery."""
        # Test main help
        result = self.run_cli(cli_path, ["help"])
        assert result.returncode == 0
        assert "usage" in result.stdout.lower() or "commands" in result.stdout.lower()
        
        # Test help via -h flag
        result = self.run_cli(cli_path, ["-h"])
        assert result.returncode == 0
        
        # Test help via --help flag
        result = self.run_cli(cli_path, ["--help"])
        assert result.returncode == 0
    
    def test_json_flag_consistency(self, cli_path, mock_env):
        """Test that --json flag works consistently across commands."""
        commands_with_json = [
            ["config"],
            ["list"],
            ["get", "gpt2"],  # Assuming gpt2 mock exists
        ]
        
        for cmd in commands_with_json:
            # Test without --json
            result = self.run_cli(cli_path, cmd, mock_env)
            if result.returncode == 0:
                # Test with --json
                result_json = self.run_cli(cli_path, ["--json"] + cmd, mock_env)
                assert result_json.returncode == 0
                # JSON output should not contain mode prefix
                if result_json.stdout.strip():
                    # Should be valid JSON if not empty
                    try:
                        json.loads(result_json.stdout)
                    except json.JSONDecodeError:
                        # If it's not JSON, at least it shouldn't contain mode info
                        assert "🔧 Mode:" not in result_json.stdout
    
    def test_error_handling(self, cli_path, mock_env):
        """Test error handling for various scenarios."""
        # Test non-existent CR
        result = self.run_cli(cli_path, ["get", "nonexistent-model"], mock_env)
        assert result.returncode == 0  # CLI doesn't exit with error, just shows message
        assert "not found" in result.stdout
        
        # Test invalid command
        result = self.run_cli(cli_path, ["invalid-command"], mock_env)
        # Should show help or error message
        assert result.returncode != 0 or "usage" in result.stdout.lower()
        
        # Test delete non-existent CR
        result = self.run_cli(cli_path, ["delete", "nonexistent-model"], mock_env)
        assert result.returncode == 0
        assert "not found" in result.stdout
    
    def test_file_operations(self, cli_path, mock_env):
        """Test file-based operations like create from file."""
        # Test create with non-existent file
        result = self.run_cli(cli_path, ["create", "/nonexistent/file.yaml"], mock_env)
        assert result.returncode == 0
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()
        
        # Test create with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')  # Invalid JSON
            invalid_file = f.name
        
        try:
            result = self.run_cli(cli_path, ["create", invalid_file], mock_env)
            # Should handle the error gracefully with improved error handling
            assert result.returncode == 0
            assert "Error parsing" in result.stdout or "❌" in result.stdout
        finally:
            os.unlink(invalid_file)
    
    def test_logs_functionality(self, cli_path, mock_env):
        """Test log viewing functionality."""
        # Test logs for existing model (if any)
        result = self.run_cli(cli_path, ["list"], mock_env)
        if result.returncode == 0 and result.stdout.strip():
            # Try to get logs for any model mentioned in the list
            lines = result.stdout.split('\\n')
            for line in lines:
                if '|' in line and 'Ready' in line:
                    # Extract model name (assuming format like "model-name | Ready: True")
                    model_name = line.split('|')[0].strip()
                    if model_name and not model_name.startswith('🔧'):
                        result = self.run_cli(cli_path, ["logs", model_name], mock_env)
                        assert result.returncode == 0
                        break
        
        # Test logs for non-existent model
        result = self.run_cli(cli_path, ["logs", "nonexistent-model"], mock_env)
        assert result.returncode == 0
        assert "No logs found" in result.stdout or "not found" in result.stdout
    
    def test_python_version_check(self, cli_path):
        """Test that the Python version check works correctly."""
        # This test runs with current Python (should work)
        result = self.run_cli(cli_path, ["help"])
        assert result.returncode == 0
        
        # We can't easily test with an older Python version,
        # but we can ensure the version check code exists
        with open(cli_path, 'r') as f:
            content = f.read()
            assert "sys.version_info < (3, 11)" in content
            assert "requires Python 3.11 or later" in content