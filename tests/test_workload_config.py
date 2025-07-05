#!/usr/bin/env python3
"""
Tests for Workload configuration functionality
"""

import os
import tempfile
import unittest
from unittest.mock import patch


from config_loader import ConfigLoader, WorkloadConfig


class TestWorkloadConfig(unittest.TestCase):
    """Test WorkloadConfig dataclass functionality"""

    def test_workload_config_creation(self):
        """Test basic WorkloadConfig creation with valid values"""
        workload = WorkloadConfig(baseline_qps=100, spike_multiplier=2.0)
        self.assertEqual(workload.baseline_qps, 100)
        self.assertEqual(workload.spike_multiplier, 2.0)

    def test_workload_config_zero_qps_invalid(self):
        """Test that zero baseline QPS raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            WorkloadConfig(baseline_qps=0, spike_multiplier=2.0)
        self.assertIn("Baseline QPS must be positive", str(cm.exception))

    def test_workload_config_negative_qps_invalid(self):
        """Test that negative baseline QPS raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            WorkloadConfig(baseline_qps=-50, spike_multiplier=2.0)
        self.assertIn("Baseline QPS must be positive", str(cm.exception))

    def test_workload_config_spike_multiplier_below_one_invalid(self):
        """Test that spike multiplier < 1.0 raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            WorkloadConfig(baseline_qps=100, spike_multiplier=0.5)
        self.assertIn("Spike multiplier must be >= 1.0", str(cm.exception))

    def test_workload_config_spike_multiplier_one_valid(self):
        """Test that spike multiplier = 1.0 is valid (no spike)"""
        workload = WorkloadConfig(baseline_qps=100, spike_multiplier=1.0)
        self.assertEqual(workload.spike_multiplier, 1.0)

    def test_workload_config_large_spike_multiplier_valid(self):
        """Test that large spike multiplier is valid"""
        workload = WorkloadConfig(baseline_qps=50, spike_multiplier=10.0)
        self.assertEqual(workload.spike_multiplier, 10.0)

    def test_workload_config_float_spike_multiplier_valid(self):
        """Test that fractional spike multiplier > 1.0 is valid"""
        workload = WorkloadConfig(baseline_qps=100, spike_multiplier=1.5)
        self.assertEqual(workload.spike_multiplier, 1.5)


class TestWorkloadConfigParsing(unittest.TestCase):
    """Test workload configuration parsing from YAML"""

    def setUp(self):
        """Set up test fixtures"""
        self.loader = ConfigLoader()

    def test_parse_workload_config(self):
        """Test parsing valid workload configuration"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": {"baseline_qps": 200, "spike_multiplier": 3.0},
        }

        config = self.loader._parse_config(config_data)
        self.assertIsNotNone(config.workload)
        self.assertEqual(config.workload.baseline_qps, 200)
        self.assertEqual(config.workload.spike_multiplier, 3.0)

    def test_parse_missing_workload_section(self):
        """Test that missing workload section results in None"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
        }

        config = self.loader._parse_config(config_data)
        self.assertIsNone(config.workload)

    def test_parse_workload_with_defaults(self):
        """Test parsing workload with missing values (should use defaults)"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": {},  # Empty workload section
        }

        config = self.loader._parse_config(config_data)
        self.assertIsNotNone(config.workload)
        self.assertEqual(config.workload.baseline_qps, 100)  # Default value
        self.assertEqual(config.workload.spike_multiplier, 2.0)  # Default value

    def test_parse_workload_partial_config(self):
        """Test parsing workload with only baseline_qps specified"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": {"baseline_qps": 250},  # Only baseline specified
        }

        config = self.loader._parse_config(config_data)
        self.assertIsNotNone(config.workload)
        self.assertEqual(config.workload.baseline_qps, 250)
        self.assertEqual(config.workload.spike_multiplier, 2.0)  # Default value

    def test_parse_invalid_workload_not_dict(self):
        """Test that invalid workload section (not dict) raises ValueError"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": "invalid",  # Should be dict
        }

        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("'workload' section must be a dictionary", str(cm.exception))

    def test_parse_invalid_baseline_qps_type(self):
        """Test that invalid baseline QPS type raises ValueError"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": {
                "baseline_qps": "invalid",  # Should be int
                "spike_multiplier": 2.0,
            },
        }

        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("workload.baseline_qps must be an integer", str(cm.exception))

    def test_parse_invalid_spike_multiplier_type(self):
        """Test that invalid spike multiplier type raises ValueError"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": {
                "baseline_qps": 100,
                "spike_multiplier": "invalid",  # Should be number
            },
        }

        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("workload.spike_multiplier must be a number", str(cm.exception))

    def test_parse_invalid_workload_values_trigger_validation(self):
        """Test that parsed values still trigger WorkloadConfig validation"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": {
                "baseline_qps": -50,  # Invalid value
                "spike_multiplier": 2.0,
            },
        }

        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("Baseline QPS must be positive", str(cm.exception))

    def test_parse_workload_spike_validation_triggered(self):
        """Test that spike multiplier validation is triggered during parsing"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": {
                "baseline_qps": 100,
                "spike_multiplier": 0.5,  # Invalid value < 1.0
            },
        }

        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("Spike multiplier must be >= 1.0", str(cm.exception))


class TestWorkloadEnvironmentOverrides(unittest.TestCase):
    """Test workload configuration environment variable overrides"""

    def setUp(self):
        """Set up test fixtures"""
        self.loader = ConfigLoader()

    def test_env_override_baseline_qps(self):
        """Test MTOP_WORKLOAD_BASELINE_QPS environment variable override"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": {"baseline_qps": 100, "spike_multiplier": 2.0},
        }

        with patch.dict(os.environ, {"MTOP_WORKLOAD_BASELINE_QPS": "300"}):
            config_with_env = self.loader._apply_env_overrides(config_data)
            config = self.loader._parse_config(config_with_env)

        self.assertEqual(config.workload.baseline_qps, 300)

    def test_env_override_spike_multiplier(self):
        """Test MTOP_WORKLOAD_SPIKE_MULTIPLIER environment variable override"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": {"baseline_qps": 100, "spike_multiplier": 2.0},
        }

        with patch.dict(os.environ, {"MTOP_WORKLOAD_SPIKE_MULTIPLIER": "5.0"}):
            config_with_env = self.loader._apply_env_overrides(config_data)
            config = self.loader._parse_config(config_with_env)

        self.assertEqual(config.workload.spike_multiplier, 5.0)

    def test_env_override_both_values(self):
        """Test overriding both workload values via environment variables"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": {"baseline_qps": 100, "spike_multiplier": 2.0},
        }

        env_vars = {
            "MTOP_WORKLOAD_BASELINE_QPS": "500",
            "MTOP_WORKLOAD_SPIKE_MULTIPLIER": "3.5",
        }

        with patch.dict(os.environ, env_vars):
            config_with_env = self.loader._apply_env_overrides(config_data)
            config = self.loader._parse_config(config_with_env)

        self.assertEqual(config.workload.baseline_qps, 500)
        self.assertEqual(config.workload.spike_multiplier, 3.5)

    def test_env_override_creates_workload_section(self):
        """Test that environment variables can create workload section if missing"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            # No workload section
        }

        with patch.dict(os.environ, {"MTOP_WORKLOAD_BASELINE_QPS": "150"}):
            config_with_env = self.loader._apply_env_overrides(config_data)
            config = self.loader._parse_config(config_with_env)

        self.assertIsNotNone(config.workload)
        self.assertEqual(config.workload.baseline_qps, 150)
        # Should use default for spike_multiplier
        self.assertEqual(config.workload.spike_multiplier, 2.0)

    def test_env_override_integer_conversion(self):
        """Test that environment variable string is properly converted to int"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": {"baseline_qps": 100, "spike_multiplier": 2.0},
        }

        with patch.dict(os.environ, {"MTOP_WORKLOAD_BASELINE_QPS": "999"}):
            config_with_env = self.loader._apply_env_overrides(config_data)
            config = self.loader._parse_config(config_with_env)

        self.assertEqual(config.workload.baseline_qps, 999)
        self.assertIsInstance(config.workload.baseline_qps, int)

    def test_env_override_float_conversion(self):
        """Test that environment variable string is properly converted to float"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "workload": {"baseline_qps": 100, "spike_multiplier": 2.0},
        }

        with patch.dict(os.environ, {"MTOP_WORKLOAD_SPIKE_MULTIPLIER": "4.25"}):
            config_with_env = self.loader._apply_env_overrides(config_data)
            config = self.loader._parse_config(config_with_env)

        self.assertEqual(config.workload.spike_multiplier, 4.25)
        self.assertIsInstance(config.workload.spike_multiplier, float)


class TestWorkloadConfigIntegration(unittest.TestCase):
    """Test workload configuration integration with full config loading"""

    def test_load_actual_config(self):
        """Test loading the actual config.yaml file includes workload"""
        loader = ConfigLoader()
        config = loader.load_config("config.yaml")

        # Should have workload configuration from config.yaml
        self.assertIsNotNone(config.workload)
        self.assertEqual(config.workload.baseline_qps, 100)
        self.assertEqual(config.workload.spike_multiplier, 2.0)

    def test_load_config_without_workload(self):
        """Test loading config file without workload section"""
        config_content = """
build:
  program:
    name: "mtop"
  branding:
    emoji: "📊"
display:
  columns: []
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()

            loader = ConfigLoader()
            config = loader.load_config(f.name)

        self.assertIsNone(config.workload)

    def test_load_config_with_all_sections(self):
        """Test loading config with technology, slo, and workload sections"""
        config_content = """
build:
  program:
    name: "mtop"
  branding:
    emoji: "📊"
display:
  columns: []
technology:
  gpu_types:
    nvidia-a100:
      memory_gb: 80
      hourly_cost: 3.00
slo:
  ttft_p95_ms: 300
  error_rate_percent: 0.2
  tokens_per_second: 1500
workload:
  baseline_qps: 250
  spike_multiplier: 4.0
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            f.flush()

            loader = ConfigLoader()
            config = loader.load_config(f.name)

        # Verify all sections are loaded correctly
        self.assertIsNotNone(config.technology)
        self.assertIsNotNone(config.slo)
        self.assertIsNotNone(config.workload)

        # Verify workload values
        self.assertEqual(config.workload.baseline_qps, 250)
        self.assertEqual(config.workload.spike_multiplier, 4.0)

        # Verify other sections still work
        self.assertEqual(config.slo.ttft_p95_ms, 300)
        self.assertIn("nvidia-a100", config.technology.gpu_types)


if __name__ == "__main__":
    unittest.main()
