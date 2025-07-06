#!/usr/bin/env python3
"""
Tests for user configuration management system.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mtop.user_config import (
    UserConfig,
    UserConfigManager,
    create_default_config_file,
    reset_config,
    set_config_value,
    show_config,
    unset_config_value,
)


class TestUserConfig:
    """Test UserConfig dataclass."""

    def test_user_config_defaults(self):
        """Test default configuration values."""
        config = UserConfig()

        assert config.default_mode == "mock"
        assert config.default_output_format == "yaml"
        assert config.mock_data_directory == "./mocks"
        assert config.verbose is False
        assert config.colors is True
        assert config.kubectl_context == ""
        assert config.kubectl_namespace == "default"
        assert config.kubectl_timeout == "30s"
        assert config.table_style == "simple"
        assert config.pager == "less"
        assert config.auto_pager is True
        assert config.cache_enabled is True
        assert config.cache_ttl_seconds == 300
        assert config.max_concurrent_requests == 10

    def test_user_config_validation(self):
        """Test configuration validation."""
        # Valid configurations
        UserConfig(default_mode="live")
        UserConfig(default_output_format="json")
        UserConfig(cache_ttl_seconds=0)
        UserConfig(max_concurrent_requests=1)

        # Invalid configurations
        with pytest.raises(ValueError, match="default_mode must be"):
            UserConfig(default_mode="invalid")

        with pytest.raises(ValueError, match="default_output_format must be"):
            UserConfig(default_output_format="invalid")

        with pytest.raises(ValueError, match="cache_ttl_seconds must be non-negative"):
            UserConfig(cache_ttl_seconds=-1)

        with pytest.raises(ValueError, match="max_concurrent_requests must be positive"):
            UserConfig(max_concurrent_requests=0)

    def test_user_config_custom_values(self):
        """Test configuration with custom values."""
        config = UserConfig(
            default_mode="live",
            default_output_format="json",
            verbose=True,
            colors=False,
            cache_ttl_seconds=600,
            max_concurrent_requests=5,
        )

        assert config.default_mode == "live"
        assert config.default_output_format == "json"
        assert config.verbose is True
        assert config.colors is False
        assert config.cache_ttl_seconds == 600
        assert config.max_concurrent_requests == 5


class TestUserConfigManager:
    """Test UserConfigManager class."""

    def test_manager_initialization(self):
        """Test manager initialization."""
        # Default initialization
        manager = UserConfigManager()
        assert manager.config_dir == Path.home() / ".mtop"
        assert manager.config_file == manager.config_dir / "config.yaml"

        # Custom config directory
        custom_dir = Path("/tmp/test_mtop")
        manager = UserConfigManager(custom_dir)
        assert manager.config_dir == custom_dir
        assert manager.config_file == custom_dir / "config.yaml"

    def test_load_config_defaults(self):
        """Test loading configuration with defaults only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserConfigManager(Path(temp_dir))
            config = manager.load_config()

            # Should return defaults when no config file exists
            assert config.default_mode == "mock"
            assert config.verbose is False
            assert config.colors is True

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserConfigManager(Path(temp_dir))

            # Create custom config
            custom_config = UserConfig(
                default_mode="live", verbose=True, colors=False, cache_ttl_seconds=600
            )

            # Save config
            manager.save_config(custom_config)
            assert manager.config_file.exists()

            # Load config
            loaded_config = manager.load_config()
            assert loaded_config.default_mode == "live"
            assert loaded_config.verbose is True
            assert loaded_config.colors is False
            assert loaded_config.cache_ttl_seconds == 600

    def test_environment_overrides(self):
        """Test environment variable overrides."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserConfigManager(Path(temp_dir))

            # Test string overrides
            with patch.dict(
                os.environ,
                {
                    "MTOP_MODE": "live",
                    "MTOP_OUTPUT_FORMAT": "json",
                    "MTOP_MOCK_DIR": "/custom/mocks",
                    "MTOP_KUBECTL_CONTEXT": "my-context",
                    "MTOP_KUBECTL_NAMESPACE": "my-namespace",
                    "MTOP_KUBECTL_TIMEOUT": "60s",
                    "MTOP_TABLE_STYLE": "fancy",
                    "MTOP_PAGER": "more",
                },
            ):
                config = manager.load_config()
                assert config.default_mode == "live"
                assert config.default_output_format == "json"
                assert config.mock_data_directory == "/custom/mocks"
                assert config.kubectl_context == "my-context"
                assert config.kubectl_namespace == "my-namespace"
                assert config.kubectl_timeout == "60s"
                assert config.table_style == "fancy"
                assert config.pager == "more"

            # Test boolean overrides
            with patch.dict(
                os.environ,
                {
                    "MTOP_VERBOSE": "true",
                    "MTOP_NO_COLOR": "true",
                    "MTOP_AUTO_PAGER": "false",
                    "MTOP_CACHE_ENABLED": "false",
                },
            ):
                config = manager.load_config()
                assert config.verbose is True
                assert config.colors is False  # NO_COLOR is negated
                assert config.auto_pager is False
                assert config.cache_enabled is False

            # Test integer overrides
            with patch.dict(
                os.environ,
                {
                    "MTOP_CACHE_TTL": "600",
                    "MTOP_MAX_CONCURRENT": "5",
                },
            ):
                config = manager.load_config()
                assert config.cache_ttl_seconds == 600
                assert config.max_concurrent_requests == 5

    def test_set_value(self):
        """Test setting configuration values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserConfigManager(Path(temp_dir))

            # Set a value
            manager.set_value("default_mode", "live")

            # Verify it was saved
            config = manager.load_config()
            assert config.default_mode == "live"

            # Test invalid key
            with pytest.raises(ValueError, match="Invalid configuration key"):
                manager.set_value("invalid_key", "value")

    def test_unset_value(self):
        """Test unsetting configuration values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserConfigManager(Path(temp_dir))

            # Save config with custom value
            custom_config = UserConfig(default_mode="live")
            manager.save_config(custom_config)

            # Unset the value
            manager.unset_value("default_mode")

            # Should revert to default
            config = manager.load_config()
            assert config.default_mode == "mock"  # Back to default

    def test_reset_config(self):
        """Test resetting configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserConfigManager(Path(temp_dir))

            # Save config
            custom_config = UserConfig(default_mode="live")
            manager.save_config(custom_config)
            assert manager.config_file.exists()

            # Reset config
            manager.reset_config()
            assert not manager.config_file.exists()

    def test_get_config_info(self):
        """Test getting configuration information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserConfigManager(Path(temp_dir))

            # Get info with no config file
            info = manager.get_config_info()
            assert "config_file" in info
            assert "config_file_exists" in info
            assert "current_config" in info
            assert "env_overrides" in info
            assert info["config_file_exists"] is False

            # Save config and check again
            custom_config = UserConfig(default_mode="live")
            manager.save_config(custom_config)

            info = manager.get_config_info()
            assert info["config_file_exists"] is True
            assert info["current_config"].default_mode == "live"


class TestConfigFileFunctions:
    """Test standalone configuration functions."""

    def test_create_default_config_file(self):
        """Test creating default configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            config_file = create_default_config_file(config_dir)

            assert config_file.exists()
            assert config_file == config_dir / "config.yaml"

            # Verify content
            manager = UserConfigManager(config_dir)
            config = manager.load_config()
            assert config.default_mode == "mock"  # Default value

    def test_cli_functions(self, capsys):
        """Test CLI integration functions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch UserConfigManager to use temp directory
            with patch("mtop.user_config.UserConfigManager") as mock_manager_class:
                mock_manager = mock_manager_class.return_value
                mock_manager.get_config_info.return_value = {
                    "config_file": "/tmp/config.yaml",
                    "config_file_exists": True,
                    "current_config": UserConfig(default_mode="live"),
                    "env_overrides": {"default_mode": "live"},
                }

                # Test show_config
                show_config()
                captured = capsys.readouterr()
                assert "Configuration file: /tmp/config.yaml" in captured.out
                assert "default_mode: live" in captured.out

                # Test set_config_value
                set_config_value("verbose", "true")
                mock_manager.set_value.assert_called_with("verbose", True)

                # Test unset_config_value
                unset_config_value("verbose")
                mock_manager.unset_value.assert_called_with("verbose")

                # Test reset_config
                reset_config()
                mock_manager.reset_config.assert_called_once()


class TestEnvironmentVariableHandling:
    """Test environment variable handling edge cases."""

    def test_boolean_environment_variables(self):
        """Test various boolean environment variable formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserConfigManager(Path(temp_dir))

            # Test true values
            for true_value in ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]:
                with patch.dict(os.environ, {"MTOP_VERBOSE": true_value}):
                    config = manager.load_config()
                    assert config.verbose is True, f"Failed for value: {true_value}"

            # Test false values
            for false_value in ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF"]:
                with patch.dict(os.environ, {"MTOP_VERBOSE": false_value}):
                    config = manager.load_config()
                    assert config.verbose is False, f"Failed for value: {false_value}"

    def test_invalid_integer_environment_variables(self):
        """Test handling of invalid integer environment variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserConfigManager(Path(temp_dir))

            # Invalid integer should be ignored
            with patch.dict(os.environ, {"MTOP_CACHE_TTL": "not_a_number"}):
                config = manager.load_config()
                assert config.cache_ttl_seconds == 300  # Should use default

    def test_precedence_order(self):
        """Test configuration precedence: ENV > file > defaults."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserConfigManager(Path(temp_dir))

            # Save file config
            file_config = UserConfig(default_mode="live", verbose=True)
            manager.save_config(file_config)

            # Override with environment variable
            with patch.dict(os.environ, {"MTOP_MODE": "mock"}):
                config = manager.load_config()
                assert config.default_mode == "mock"  # ENV override
                assert config.verbose is True  # From file
                assert config.colors is True  # Default
