#!/usr/bin/env python3
"""
Tests for SLO (Service Level Objective) configuration functionality
"""

import os
import tempfile
import unittest
from unittest.mock import patch

import yaml

from config_loader import Config, ConfigLoader, SLOConfig


class TestSLOConfig(unittest.TestCase):
    """Test SLOConfig dataclass functionality"""

    def test_slo_config_creation(self):
        """Test basic SLOConfig creation with valid values"""
        slo = SLOConfig(ttft_p95_ms=500, error_rate_percent=0.1, tokens_per_second=1000)
        self.assertEqual(slo.ttft_p95_ms, 500)
        self.assertEqual(slo.error_rate_percent, 0.1)
        self.assertEqual(slo.tokens_per_second, 1000)

    def test_slo_config_zero_latency_invalid(self):
        """Test that zero TTFT latency raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            SLOConfig(ttft_p95_ms=0, error_rate_percent=0.1, tokens_per_second=1000)
        self.assertIn("TTFT latency must be positive", str(cm.exception))

    def test_slo_config_negative_latency_invalid(self):
        """Test that negative TTFT latency raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            SLOConfig(ttft_p95_ms=-100, error_rate_percent=0.1, tokens_per_second=1000)
        self.assertIn("TTFT latency must be positive", str(cm.exception))

    def test_slo_config_negative_error_rate_invalid(self):
        """Test that negative error rate raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            SLOConfig(ttft_p95_ms=500, error_rate_percent=-1.0, tokens_per_second=1000)
        self.assertIn("Error rate must be 0-100%", str(cm.exception))

    def test_slo_config_error_rate_over_100_invalid(self):
        """Test that error rate > 100% raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            SLOConfig(ttft_p95_ms=500, error_rate_percent=150.0, tokens_per_second=1000)
        self.assertIn("Error rate must be 0-100%", str(cm.exception))

    def test_slo_config_zero_error_rate_valid(self):
        """Test that zero error rate is valid (no errors allowed)"""
        slo = SLOConfig(ttft_p95_ms=500, error_rate_percent=0.0, tokens_per_second=1000)
        self.assertEqual(slo.error_rate_percent, 0.0)

    def test_slo_config_100_percent_error_rate_valid(self):
        """Test that 100% error rate is valid (edge case)"""
        slo = SLOConfig(ttft_p95_ms=500, error_rate_percent=100.0, tokens_per_second=1000)
        self.assertEqual(slo.error_rate_percent, 100.0)

    def test_slo_config_zero_tokens_per_second_invalid(self):
        """Test that zero tokens per second raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            SLOConfig(ttft_p95_ms=500, error_rate_percent=0.1, tokens_per_second=0)
        self.assertIn("Tokens per second must be positive", str(cm.exception))

    def test_slo_config_negative_tokens_per_second_invalid(self):
        """Test that negative tokens per second raises ValueError"""
        with self.assertRaises(ValueError) as cm:
            SLOConfig(ttft_p95_ms=500, error_rate_percent=0.1, tokens_per_second=-100)
        self.assertIn("Tokens per second must be positive", str(cm.exception))


class TestSLOConfigParsing(unittest.TestCase):
    """Test SLO configuration parsing from YAML"""

    def setUp(self):
        """Set up test fixtures"""
        self.loader = ConfigLoader()

    def test_parse_slo_config(self):
        """Test parsing valid SLO configuration"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "slo": {"ttft_p95_ms": 300, "error_rate_percent": 0.5, "tokens_per_second": 1500},
        }

        config = self.loader._parse_config(config_data)
        self.assertIsNotNone(config.slo)
        self.assertEqual(config.slo.ttft_p95_ms, 300)
        self.assertEqual(config.slo.error_rate_percent, 0.5)
        self.assertEqual(config.slo.tokens_per_second, 1500)

    def test_parse_missing_slo_section(self):
        """Test that missing SLO section results in None"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
        }

        config = self.loader._parse_config(config_data)
        self.assertIsNone(config.slo)

    def test_parse_slo_with_defaults(self):
        """Test parsing SLO with missing values (should use defaults)"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "slo": {},  # Empty SLO section
        }

        config = self.loader._parse_config(config_data)
        self.assertIsNotNone(config.slo)
        self.assertEqual(config.slo.ttft_p95_ms, 500)  # Default value
        self.assertEqual(config.slo.error_rate_percent, 0.1)  # Default value
        self.assertEqual(config.slo.tokens_per_second, 1000)  # Default value

    def test_parse_invalid_slo_not_dict(self):
        """Test that invalid SLO section (not dict) raises ValueError"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "slo": "invalid",  # Should be dict
        }

        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("'slo' section must be a dictionary", str(cm.exception))

    def test_parse_invalid_ttft_type(self):
        """Test that invalid TTFT type raises ValueError"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "slo": {
                "ttft_p95_ms": "invalid",  # Should be int
                "error_rate_percent": 0.1,
                "tokens_per_second": 1000,
            },
        }

        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("slo.ttft_p95_ms must be an integer", str(cm.exception))

    def test_parse_invalid_error_rate_type(self):
        """Test that invalid error rate type raises ValueError"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "slo": {
                "ttft_p95_ms": 500,
                "error_rate_percent": "invalid",  # Should be number
                "tokens_per_second": 1000,
            },
        }

        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("slo.error_rate_percent must be a number", str(cm.exception))

    def test_parse_invalid_tokens_per_second_type(self):
        """Test that invalid tokens per second type raises ValueError"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "slo": {
                "ttft_p95_ms": 500,
                "error_rate_percent": 0.1,
                "tokens_per_second": "invalid",  # Should be int
            },
        }

        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("slo.tokens_per_second must be an integer", str(cm.exception))

    def test_parse_invalid_slo_values_trigger_validation(self):
        """Test that parsed values still trigger SLOConfig validation"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "slo": {
                "ttft_p95_ms": -100,  # Invalid value
                "error_rate_percent": 0.1,
                "tokens_per_second": 1000,
            },
        }

        with self.assertRaises(ValueError) as cm:
            self.loader._parse_config(config_data)
        self.assertIn("TTFT latency must be positive", str(cm.exception))


class TestSLOEnvironmentOverrides(unittest.TestCase):
    """Test SLO configuration environment variable overrides"""

    def setUp(self):
        """Set up test fixtures"""
        self.loader = ConfigLoader()

    def test_env_override_ttft_latency(self):
        """Test MTOP_SLO_TTFT_P95_MS environment variable override"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "slo": {"ttft_p95_ms": 500, "error_rate_percent": 0.1, "tokens_per_second": 1000},
        }

        with patch.dict(os.environ, {"MTOP_SLO_TTFT_P95_MS": "200"}):
            config_with_env = self.loader._apply_env_overrides(config_data)
            config = self.loader._parse_config(config_with_env)

        self.assertEqual(config.slo.ttft_p95_ms, 200)

    def test_env_override_error_rate(self):
        """Test MTOP_SLO_ERROR_RATE_PERCENT environment variable override"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "slo": {"ttft_p95_ms": 500, "error_rate_percent": 0.1, "tokens_per_second": 1000},
        }

        with patch.dict(os.environ, {"MTOP_SLO_ERROR_RATE_PERCENT": "0.5"}):
            config_with_env = self.loader._apply_env_overrides(config_data)
            config = self.loader._parse_config(config_with_env)

        self.assertEqual(config.slo.error_rate_percent, 0.5)

    def test_env_override_tokens_per_second(self):
        """Test MTOP_SLO_TOKENS_PER_SECOND environment variable override"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            "slo": {"ttft_p95_ms": 500, "error_rate_percent": 0.1, "tokens_per_second": 1000},
        }

        with patch.dict(os.environ, {"MTOP_SLO_TOKENS_PER_SECOND": "2000"}):
            config_with_env = self.loader._apply_env_overrides(config_data)
            config = self.loader._parse_config(config_with_env)

        self.assertEqual(config.slo.tokens_per_second, 2000)

    def test_env_override_creates_slo_section(self):
        """Test that environment variables can create SLO section if missing"""
        config_data = {
            "build": {"program": {"name": "mtop"}, "branding": {"emoji": "📊"}},
            "display": {"columns": []},
            # No SLO section
        }

        with patch.dict(os.environ, {"MTOP_SLO_TTFT_P95_MS": "300"}):
            config_with_env = self.loader._apply_env_overrides(config_data)
            config = self.loader._parse_config(config_with_env)

        self.assertIsNotNone(config.slo)
        self.assertEqual(config.slo.ttft_p95_ms, 300)
        # Should use defaults for other values
        self.assertEqual(config.slo.error_rate_percent, 0.1)
        self.assertEqual(config.slo.tokens_per_second, 1000)


class TestSLOConfigIntegration(unittest.TestCase):
    """Test SLO configuration integration with full config loading"""

    def test_load_actual_config(self):
        """Test loading the actual config.yaml file includes SLO"""
        loader = ConfigLoader()
        config = loader.load_config("config.yaml")

        # Should have SLO configuration from config.yaml
        self.assertIsNotNone(config.slo)
        self.assertEqual(config.slo.ttft_p95_ms, 500)
        self.assertEqual(config.slo.error_rate_percent, 0.1)
        self.assertEqual(config.slo.tokens_per_second, 1000)

    def test_load_config_without_slo(self):
        """Test loading config file without SLO section"""
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

        self.assertIsNone(config.slo)


if __name__ == "__main__":
    unittest.main()
