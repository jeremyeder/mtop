#!/usr/bin/env python3
"""
Integration tests for complete configuration system
Tests all configuration sections working together
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from config_loader import ConfigLoader


class TestConfigurationIntegration(unittest.TestCase):
    """Test complete configuration system integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.loader = ConfigLoader()

    def test_load_complete_configuration(self):
        """Test loading configuration with all sections present"""
        config = self.loader.load_config("config.yaml")

        # Verify all sections are loaded
        self.assertIsNotNone(config.build)
        self.assertIsNotNone(config.display)
        self.assertIsNotNone(config.technology)
        self.assertIsNotNone(config.slo)
        self.assertIsNotNone(config.workload)

        # Verify build configuration
        self.assertEqual(config.build.program.name, "mtop")
        self.assertEqual(config.build.branding.emoji, "📊")

        # Verify display configuration
        self.assertGreater(len(config.display.columns), 0)
        self.assertEqual(config.display.sorting["default_key"], "qps")

        # Verify technology configuration
        self.assertIn("nvidia-a100", config.technology.gpu_types)
        self.assertIn("nvidia-h100", config.technology.gpu_types)
        a100 = config.technology.gpu_types["nvidia-a100"]
        self.assertEqual(a100.memory_gb, 80)
        self.assertEqual(a100.hourly_cost, 3.00)

        # Verify SLO configuration
        self.assertEqual(config.slo.ttft_p95_ms, 500)
        self.assertEqual(config.slo.error_rate_percent, 0.1)
        self.assertEqual(config.slo.tokens_per_second, 1000)

        # Verify workload configuration
        self.assertEqual(config.workload.baseline_qps, 100)
        self.assertEqual(config.workload.spike_multiplier, 2.0)

    def test_minimal_configuration(self):
        """Test loading minimal configuration with only required sections"""
        minimal_config = """
build:
  program:
    name: "test-mtop"
  branding:
    emoji: "🧪"
display:
  columns:
    - name: "Test"
      field: "test"
      width: 10
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(minimal_config)
            f.flush()

            config = self.loader.load_config(f.name)

        # Required sections should be present
        self.assertIsNotNone(config.build)
        self.assertIsNotNone(config.display)

        # Optional sections should be None
        self.assertIsNone(config.technology)
        self.assertIsNone(config.slo)
        self.assertIsNone(config.workload)

        # Verify minimal config values
        self.assertEqual(config.build.program.name, "test-mtop")
        self.assertEqual(config.build.branding.emoji, "🧪")

    def test_environment_variable_overrides_all_sections(self):
        """Test environment variables can override values in all sections"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "technology": {"gpu_types": {"nvidia-a100": {"memory_gb": 80, "hourly_cost": 3.00}}},
            "slo": {"ttft_p95_ms": 500, "error_rate_percent": 0.1, "tokens_per_second": 1000},
            "workload": {"baseline_qps": 100, "spike_multiplier": 2.0},
        }

        env_vars = {
            "MTOP_TECHNOLOGY_GPU_A100_MEMORY": "96",  # Override A100 memory
            "MTOP_SLO_TTFT_P95_MS": "300",  # Override SLO latency
            "MTOP_WORKLOAD_BASELINE_QPS": "250",  # Override workload QPS
        }

        with patch.dict(os.environ, env_vars):
            config_with_env = self.loader._apply_env_overrides(config_data)
            config = self.loader._parse_config(config_with_env)

        # Verify environment overrides took effect
        self.assertEqual(config.technology.gpu_types["nvidia-a100"].memory_gb, 96)
        self.assertEqual(config.slo.ttft_p95_ms, 300)
        self.assertEqual(config.workload.baseline_qps, 250)

        # Verify non-overridden values remain unchanged
        self.assertEqual(config.technology.gpu_types["nvidia-a100"].hourly_cost, 3.00)
        self.assertEqual(config.slo.error_rate_percent, 0.1)
        self.assertEqual(config.workload.spike_multiplier, 2.0)

    def test_environment_variables_create_missing_sections(self):
        """Test that environment variables can create entire missing sections"""
        minimal_config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            # No technology, slo, or workload sections
        }

        env_vars = {
            "MTOP_SLO_TTFT_P95_MS": "400",
            "MTOP_WORKLOAD_BASELINE_QPS": "150",
            "MTOP_TECHNOLOGY_GPU_A100_MEMORY": "80",
        }

        with patch.dict(os.environ, env_vars):
            config_with_env = self.loader._apply_env_overrides(minimal_config_data)
            config = self.loader._parse_config(config_with_env)

        # Verify sections were created by environment variables
        self.assertIsNotNone(config.slo)
        self.assertEqual(config.slo.ttft_p95_ms, 400)
        self.assertEqual(config.slo.error_rate_percent, 0.1)  # Default

        self.assertIsNotNone(config.workload)
        self.assertEqual(config.workload.baseline_qps, 150)
        self.assertEqual(config.workload.spike_multiplier, 2.0)  # Default

        self.assertIsNotNone(config.technology)
        self.assertIn("nvidia-a100", config.technology.gpu_types)

    def test_configuration_validation_across_sections(self):
        """Test that validation works properly across all configuration sections"""
        invalid_config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "technology": {
                "gpu_types": {
                    "invalid-gpu": {"memory_gb": -10, "hourly_cost": 3.00}  # Negative memory
                }
            },
            "slo": {
                "ttft_p95_ms": -100,  # Negative latency
                "error_rate_percent": 0.1,
                "tokens_per_second": 1000,
            },
            "workload": {"baseline_qps": 100, "spike_multiplier": 0.5},  # Below 1.0
        }

        # Test technology validation
        config_data = invalid_config_data.copy()
        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("GPU memory must be positive", str(cm.exception))

        # Test SLO validation
        config_data = invalid_config_data.copy()
        config_data["technology"]["gpu_types"]["invalid-gpu"]["memory_gb"] = 80  # Fix GPU
        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("TTFT latency must be positive", str(cm.exception))

        # Test workload validation
        config_data["slo"]["ttft_p95_ms"] = 500  # Fix SLO
        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("Spike multiplier must be >= 1.0", str(cm.exception))

    def test_configuration_caching(self):
        """Test that configuration caching works properly"""
        # Load config twice - second load should use cache
        config1 = self.loader.load_config("config.yaml")
        config2 = self.loader.load_config("config.yaml")

        # Should be the same object (cached)
        self.assertIs(config1, config2)

        # Verify cache contains the config
        self.assertGreater(len(self.loader.config_cache), 0)

    def test_configuration_with_gpu_overrides(self):
        """Test overriding existing GPU types via environment variables"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "technology": {
                "gpu_types": {
                    "nvidia-a100": {"memory_gb": 80, "hourly_cost": 3.00},
                    "nvidia-h100": {"memory_gb": 80, "hourly_cost": 5.00},
                }
            },
        }

        # Override existing GPU configurations
        env_vars = {
            "MTOP_TECHNOLOGY_GPU_A100_MEMORY": "96",
            "MTOP_TECHNOLOGY_GPU_H100_COST": "4.50",
        }

        with patch.dict(os.environ, env_vars):
            config_with_env = self.loader._apply_env_overrides(config_data)
            config = self.loader._parse_config(config_with_env)

        # Verify GPU overrides took effect
        a100 = config.technology.gpu_types["nvidia-a100"]
        self.assertEqual(a100.memory_gb, 96)  # Overridden
        self.assertEqual(a100.hourly_cost, 3.00)  # Unchanged

        h100 = config.technology.gpu_types["nvidia-h100"]
        self.assertEqual(h100.memory_gb, 80)  # Unchanged
        self.assertEqual(h100.hourly_cost, 4.50)  # Overridden

    def test_realistic_production_configuration(self):
        """Test a realistic production-style configuration"""
        production_config = """
build:
  program:
    name: "mtop"
    monitor_name: "mtop"
    description: "Production ML Model Monitor"
    class_prefix: "MTop"
  branding:
    emoji: "🚀"
    tagline: "Production LLM Monitoring"
    github_repo: "company/mtop"

display:
  columns:
    - name: "Model"
      field: "name"
      width: 30
      truncate: 27
    - name: "Status"
      field: "status"
      width: 12
      justify: "center"
    - name: "QPS"
      field: "current_qps"
      width: 8
      format: "int"
      sortable: true
  sorting:
    default_key: "qps"
  summary:
    show_runtime: true
    show_mode: false

technology:
  gpu_types:
    nvidia-a100:
      memory_gb: 80
      hourly_cost: 2.50
    nvidia-h100:
      memory_gb: 80
      hourly_cost: 4.00
    nvidia-v100:
      memory_gb: 32
      hourly_cost: 1.50

slo:
  ttft_p95_ms: 200
  error_rate_percent: 0.01
  tokens_per_second: 2000

workload:
  baseline_qps: 500
  spike_multiplier: 3.0
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(production_config)
            f.flush()

            config = self.loader.load_config(f.name)

        # Verify production configuration loaded correctly
        self.assertEqual(config.build.program.description, "Production ML Model Monitor")
        self.assertEqual(config.build.branding.emoji, "🚀")

        # Verify tight SLOs for production
        self.assertEqual(config.slo.ttft_p95_ms, 200)
        self.assertEqual(config.slo.error_rate_percent, 0.01)
        self.assertEqual(config.slo.tokens_per_second, 2000)

        # Verify high-capacity workload
        self.assertEqual(config.workload.baseline_qps, 500)
        self.assertEqual(config.workload.spike_multiplier, 3.0)

        # Verify multiple GPU types
        self.assertEqual(len(config.technology.gpu_types), 3)
        self.assertIn("nvidia-v100", config.technology.gpu_types)
        v100 = config.technology.gpu_types["nvidia-v100"]
        self.assertEqual(v100.memory_gb, 32)
        self.assertEqual(v100.hourly_cost, 1.50)


if __name__ == "__main__":
    unittest.main()
