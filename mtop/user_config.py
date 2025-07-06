#!/usr/bin/env python3
"""
User Configuration Management for mtop.

This module handles user-specific configuration files stored in ~/.mtop/config.yaml
and provides environment variable overrides for CI/CD scenarios.
"""

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class UserConfig:
    """User-specific configuration for mtop behavior."""

    default_mode: str = "mock"  # Default execution mode (mock/live)
    default_output_format: str = "yaml"  # Default output format (yaml/json/table)
    mock_data_directory: str = "./mocks"  # Custom mock data location
    verbose: bool = False  # Default verbosity level
    colors: bool = True  # Enable/disable colored output

    # Kubectl settings for live mode
    kubectl_context: str = ""  # Default kubectl context
    kubectl_namespace: str = "default"  # Default namespace
    kubectl_timeout: str = "30s"  # kubectl command timeout

    # UI preferences
    table_style: str = "simple"  # Table formatting style
    pager: str = "less"  # Pager for long output
    auto_pager: bool = True  # Auto-enable pager for long output

    # Performance settings
    cache_enabled: bool = True  # Enable response caching
    cache_ttl_seconds: int = 300  # Cache time-to-live
    max_concurrent_requests: int = 10  # Max concurrent API requests

    def __post_init__(self):
        """Validate user configuration."""
        if self.default_mode not in ["mock", "live"]:
            raise ValueError(f"default_mode must be 'mock' or 'live', got '{self.default_mode}'")

        if self.default_output_format not in ["yaml", "json", "table"]:
            raise ValueError(
                f"default_output_format must be 'yaml', 'json', or 'table', got '{self.default_output_format}'"
            )

        if self.cache_ttl_seconds < 0:
            raise ValueError(
                f"cache_ttl_seconds must be non-negative, got {self.cache_ttl_seconds}"
            )

        if self.max_concurrent_requests < 1:
            raise ValueError(
                f"max_concurrent_requests must be positive, got {self.max_concurrent_requests}"
            )


class UserConfigManager:
    """Manages user configuration files and environment variable overrides."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize user config manager.

        Args:
            config_dir: Custom config directory (defaults to ~/.mtop)
        """
        if config_dir is None:
            self.config_dir = Path.home() / ".mtop"
        else:
            self.config_dir = Path(config_dir)

        self.config_file = self.config_dir / "config.yaml"

    def load_config(self) -> UserConfig:
        """Load user configuration with environment variable overrides.

        Precedence order: ENV vars > config file > defaults

        Returns:
            UserConfig: Loaded configuration
        """
        # Start with defaults
        config_data = {}

        # Load from file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    file_data = yaml.safe_load(f) or {}
                    config_data.update(file_data)
            except (yaml.YAMLError, IOError) as e:
                raise ValueError(f"Error reading config file {self.config_file}: {e}")

        # Apply environment variable overrides
        env_overrides = self._get_env_overrides()
        config_data.update(env_overrides)

        return UserConfig(**config_data)

    def save_config(self, config: UserConfig) -> None:
        """Save user configuration to file.

        Args:
            config: User configuration to save
        """
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Convert dataclass to dict
        config_data = {
            "default_mode": config.default_mode,
            "default_output_format": config.default_output_format,
            "mock_data_directory": config.mock_data_directory,
            "verbose": config.verbose,
            "colors": config.colors,
            "kubectl_context": config.kubectl_context,
            "kubectl_namespace": config.kubectl_namespace,
            "kubectl_timeout": config.kubectl_timeout,
            "table_style": config.table_style,
            "pager": config.pager,
            "auto_pager": config.auto_pager,
            "cache_enabled": config.cache_enabled,
            "cache_ttl_seconds": config.cache_ttl_seconds,
            "max_concurrent_requests": config.max_concurrent_requests,
        }

        # Write to file
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=True)
        except IOError as e:
            raise ValueError(f"Error writing config file {self.config_file}: {e}")

    def set_value(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key (e.g., 'default_mode')
            value: Configuration value
        """
        config = self.load_config()

        if not hasattr(config, key):
            raise ValueError(f"Invalid configuration key: {key}")

        setattr(config, key, value)
        self.save_config(config)

    def unset_value(self, key: str) -> None:
        """Remove a configuration value (reset to default).

        Args:
            key: Configuration key to reset
        """
        if not self.config_file.exists():
            return

        # Load current config data
        with open(self.config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        # Remove the key if it exists
        config_data.pop(key, None)

        # Save updated config
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=True)

    def reset_config(self) -> None:
        """Reset configuration to defaults by removing config file."""
        if self.config_file.exists():
            self.config_file.unlink()

    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration information and sources.

        Returns:
            Dict with configuration values and their sources
        """
        config = self.load_config()
        env_overrides = self._get_env_overrides()

        info = {
            "config_file": str(self.config_file),
            "config_file_exists": self.config_file.exists(),
            "current_config": config,
            "env_overrides": env_overrides,
        }

        return info

    def _get_env_overrides(self) -> Dict[str, Any]:
        """Get configuration overrides from environment variables.

        Environment variables use MTOP_ prefix:
        - MTOP_MODE -> default_mode
        - MTOP_OUTPUT_FORMAT -> default_output_format
        - MTOP_MOCK_DIR -> mock_data_directory
        - MTOP_VERBOSE -> verbose
        - MTOP_NO_COLOR -> colors (negated)
        - MTOP_KUBECTL_CONTEXT -> kubectl_context
        - MTOP_KUBECTL_NAMESPACE -> kubectl_namespace
        - MTOP_KUBECTL_TIMEOUT -> kubectl_timeout

        Returns:
            Dict of configuration overrides
        """
        overrides = {}

        # String values
        if os.getenv("MTOP_MODE"):
            overrides["default_mode"] = os.getenv("MTOP_MODE")

        if os.getenv("MTOP_OUTPUT_FORMAT"):
            overrides["default_output_format"] = os.getenv("MTOP_OUTPUT_FORMAT")

        if os.getenv("MTOP_MOCK_DIR"):
            overrides["mock_data_directory"] = os.getenv("MTOP_MOCK_DIR")

        if os.getenv("MTOP_KUBECTL_CONTEXT"):
            overrides["kubectl_context"] = os.getenv("MTOP_KUBECTL_CONTEXT")

        if os.getenv("MTOP_KUBECTL_NAMESPACE"):
            overrides["kubectl_namespace"] = os.getenv("MTOP_KUBECTL_NAMESPACE")

        if os.getenv("MTOP_KUBECTL_TIMEOUT"):
            overrides["kubectl_timeout"] = os.getenv("MTOP_KUBECTL_TIMEOUT")

        if os.getenv("MTOP_TABLE_STYLE"):
            overrides["table_style"] = os.getenv("MTOP_TABLE_STYLE")

        if os.getenv("MTOP_PAGER"):
            overrides["pager"] = os.getenv("MTOP_PAGER")

        # Boolean values
        if os.getenv("MTOP_VERBOSE"):
            overrides["verbose"] = os.getenv("MTOP_VERBOSE").lower() in ("true", "1", "yes", "on")

        if os.getenv("MTOP_NO_COLOR"):
            overrides["colors"] = not os.getenv("MTOP_NO_COLOR").lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

        if os.getenv("MTOP_AUTO_PAGER"):
            overrides["auto_pager"] = os.getenv("MTOP_AUTO_PAGER").lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

        if os.getenv("MTOP_CACHE_ENABLED"):
            overrides["cache_enabled"] = os.getenv("MTOP_CACHE_ENABLED").lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

        # Integer values
        if os.getenv("MTOP_CACHE_TTL"):
            try:
                overrides["cache_ttl_seconds"] = int(os.getenv("MTOP_CACHE_TTL"))
            except ValueError:
                pass  # Ignore invalid integer values

        if os.getenv("MTOP_MAX_CONCURRENT"):
            try:
                overrides["max_concurrent_requests"] = int(os.getenv("MTOP_MAX_CONCURRENT"))
            except ValueError:
                pass  # Ignore invalid integer values

        return overrides


def create_default_config_file(config_dir: Optional[Path] = None) -> Path:
    """Create a default user configuration file.

    Args:
        config_dir: Custom config directory (defaults to ~/.mtop)

    Returns:
        Path to created config file
    """
    manager = UserConfigManager(config_dir)
    default_config = UserConfig()
    manager.save_config(default_config)
    return manager.config_file


# CLI integration functions for command-line interface
def show_config() -> None:
    """Show current configuration (for mtop config command)."""
    manager = UserConfigManager()
    info = manager.get_config_info()

    print(f"Configuration file: {info['config_file']}")
    print(f"File exists: {info['config_file_exists']}")
    print()

    config = info["current_config"]
    print("Current configuration:")
    print(f"  default_mode: {config.default_mode}")
    print(f"  default_output_format: {config.default_output_format}")
    print(f"  mock_data_directory: {config.mock_data_directory}")
    print(f"  verbose: {config.verbose}")
    print(f"  colors: {config.colors}")
    print(f"  kubectl_context: {config.kubectl_context}")
    print(f"  kubectl_namespace: {config.kubectl_namespace}")
    print(f"  kubectl_timeout: {config.kubectl_timeout}")
    print(f"  table_style: {config.table_style}")
    print(f"  pager: {config.pager}")
    print(f"  auto_pager: {config.auto_pager}")
    print(f"  cache_enabled: {config.cache_enabled}")
    print(f"  cache_ttl_seconds: {config.cache_ttl_seconds}")
    print(f"  max_concurrent_requests: {config.max_concurrent_requests}")

    if info["env_overrides"]:
        print()
        print("Environment variable overrides:")
        for key, value in info["env_overrides"].items():
            print(f"  {key}: {value}")


def set_config_value(key: str, value: str) -> None:
    """Set a configuration value (for mtop config --set command)."""
    manager = UserConfigManager()

    # Convert string value to appropriate type
    if key in ["verbose", "colors", "auto_pager", "cache_enabled"]:
        value = value.lower() in ("true", "1", "yes", "on")
    elif key in ["cache_ttl_seconds", "max_concurrent_requests"]:
        value = int(value)

    manager.set_value(key, value)
    print(f"Set {key} = {value}")


def unset_config_value(key: str) -> None:
    """Unset a configuration value (for mtop config --unset command)."""
    manager = UserConfigManager()
    manager.unset_value(key)
    print(f"Unset {key} (reset to default)")


def reset_config() -> None:
    """Reset configuration to defaults (for mtop config --reset command)."""
    manager = UserConfigManager()
    manager.reset_config()
    print("Configuration reset to defaults")


def edit_config() -> None:
    """Open config file in editor (for mtop config --edit command)."""
    manager = UserConfigManager()

    # Create config file if it doesn't exist
    if not manager.config_file.exists():
        create_default_config_file(manager.config_dir)

    # Get editor from environment
    editor = os.getenv("EDITOR", "nano")

    # Open editor
    import subprocess

    try:
        subprocess.run([editor, str(manager.config_file)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error opening editor: {e}")
    except FileNotFoundError:
        print(f"Editor '{editor}' not found. Set EDITOR environment variable.")
