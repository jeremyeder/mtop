"""Tests for TechnologyConfig dataclass and parsing."""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from config_loader import Config, ConfigLoader, GPUType, TechnologyConfig


class TestGPUType:
    """Test cases for GPUType dataclass."""

    def test_gpu_type_creation(self):
        """Test creating a valid GPU type."""
        gpu = GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.00)
        assert gpu.name == "nvidia-a100"
        assert gpu.memory_gb == 80
        assert gpu.hourly_cost == 3.00

    def test_gpu_type_zero_memory_invalid(self):
        """Test that zero memory is invalid."""
        with pytest.raises(ValueError, match="GPU memory must be positive"):
            GPUType(name="test-gpu", memory_gb=0, hourly_cost=1.00)

    def test_gpu_type_negative_memory_invalid(self):
        """Test that negative memory is invalid."""
        with pytest.raises(ValueError, match="GPU memory must be positive"):
            GPUType(name="test-gpu", memory_gb=-10, hourly_cost=1.00)

    def test_gpu_type_negative_cost_invalid(self):
        """Test that negative cost is invalid."""
        with pytest.raises(ValueError, match="GPU hourly cost cannot be negative"):
            GPUType(name="test-gpu", memory_gb=80, hourly_cost=-1.00)

    def test_gpu_type_zero_cost_valid(self):
        """Test that zero cost is valid (free tier)."""
        gpu = GPUType(name="free-gpu", memory_gb=8, hourly_cost=0.00)
        assert gpu.hourly_cost == 0.00


class TestTechnologyConfig:
    """Test cases for TechnologyConfig dataclass."""

    def test_technology_config_empty(self):
        """Test creating empty technology config."""
        tech = TechnologyConfig()
        assert tech.gpu_types == {}

    def test_technology_config_with_gpus(self):
        """Test creating technology config with GPU types."""
        gpu1 = GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.00)
        gpu2 = GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=5.00)

        tech = TechnologyConfig(gpu_types={"nvidia-a100": gpu1, "nvidia-h100": gpu2})

        assert len(tech.gpu_types) == 2
        assert tech.gpu_types["nvidia-a100"] == gpu1
        assert tech.gpu_types["nvidia-h100"] == gpu2


class TestTechnologyConfigParsing:
    """Test cases for parsing technology configuration from YAML."""

    @pytest.fixture
    def config_loader(self):
        """Create a ConfigLoader instance."""
        return ConfigLoader()

    def test_parse_technology_config(self, config_loader):
        """Test parsing valid technology configuration."""
        yaml_content = """
build:
  program:
    name: "mtop"
    monitor_name: "mtop"
    description: "Test"
    class_prefix: "MTop"
  branding:
    emoji: "📊"
    tagline: "Test"
    github_repo: "test/test"

display:
  columns:
    - name: "Model"
      field: "name"
      width: 20
  sorting:
    default_key: "name"
    available_keys: ["name"]
  summary:
    show_runtime: true

technology:
  gpu_types:
    nvidia-a100:
      memory_gb: 80
      hourly_cost: 3.00
    nvidia-h100:
      memory_gb: 80
      hourly_cost: 5.00
"""

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = config_loader.load_config("test.yaml")

        assert config.technology is not None
        assert len(config.technology.gpu_types) == 2
        assert "nvidia-a100" in config.technology.gpu_types
        assert "nvidia-h100" in config.technology.gpu_types

        a100 = config.technology.gpu_types["nvidia-a100"]
        assert a100.name == "nvidia-a100"
        assert a100.memory_gb == 80
        assert a100.hourly_cost == 3.00

    def test_parse_missing_technology_section(self, config_loader):
        """Test parsing config without technology section."""
        yaml_content = """
build:
  program:
    name: "mtop"
    monitor_name: "mtop"
    description: "Test"
    class_prefix: "MTop"
  branding:
    emoji: "📊"
    tagline: "Test"
    github_repo: "test/test"

display:
  columns:
    - name: "Model"
      field: "name"
      width: 20
  sorting:
    default_key: "name"
    available_keys: ["name"]
  summary:
    show_runtime: true
"""

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = config_loader.load_config("test.yaml")

        assert config.technology is None

    def test_parse_empty_gpu_types(self, config_loader):
        """Test parsing technology config with empty GPU types."""
        yaml_content = """
build:
  program:
    name: "mtop"
    monitor_name: "mtop"
    description: "Test"
    class_prefix: "MTop"
  branding:
    emoji: "📊"
    tagline: "Test"
    github_repo: "test/test"

display:
  columns:
    - name: "Model"
      field: "name"
      width: 20
  sorting:
    default_key: "name"
    available_keys: ["name"]
  summary:
    show_runtime: true

technology:
  gpu_types: {}
"""

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = config_loader.load_config("test.yaml")

        assert config.technology is not None
        assert config.technology.gpu_types == {}

    def test_parse_invalid_technology_not_dict(self, config_loader):
        """Test that technology section must be a dictionary."""
        yaml_content = """
build:
  program:
    name: "mtop"
    monitor_name: "mtop"
    description: "Test"
    class_prefix: "MTop"
  branding:
    emoji: "📊"
    tagline: "Test"
    github_repo: "test/test"

display:
  columns:
    - name: "Model"
      field: "name"
      width: 20
  sorting:
    default_key: "name"
    available_keys: ["name"]
  summary:
    show_runtime: true

technology: "not a dict"
"""

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with pytest.raises(ValueError, match="'technology' section must be a dictionary"):
                config_loader.load_config("test.yaml")

    def test_parse_invalid_gpu_types_not_dict(self, config_loader):
        """Test that gpu_types must be a dictionary."""
        yaml_content = """
build:
  program:
    name: "mtop"
    monitor_name: "mtop"
    description: "Test"
    class_prefix: "MTop"
  branding:
    emoji: "📊"
    tagline: "Test"
    github_repo: "test/test"

display:
  columns:
    - name: "Model"
      field: "name"
      width: 20
  sorting:
    default_key: "name"
    available_keys: ["name"]
  summary:
    show_runtime: true

technology:
  gpu_types: ["not", "a", "dict"]
"""

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with pytest.raises(ValueError, match="technology.gpu_types must be a dictionary"):
                config_loader.load_config("test.yaml")

    def test_parse_invalid_gpu_memory(self, config_loader):
        """Test invalid GPU memory values."""
        yaml_content = """
build:
  program:
    name: "mtop"
    monitor_name: "mtop"
    description: "Test"
    class_prefix: "MTop"
  branding:
    emoji: "📊"
    tagline: "Test"
    github_repo: "test/test"

display:
  columns:
    - name: "Model"
      field: "name"
      width: 20
  sorting:
    default_key: "name"
    available_keys: ["name"]
  summary:
    show_runtime: true

technology:
  gpu_types:
    bad-gpu:
      memory_gb: "not a number"
      hourly_cost: 1.00
"""

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with pytest.raises(ValueError, match="memory_gb must be a number"):
                config_loader.load_config("test.yaml")

    def test_parse_invalid_gpu_cost(self, config_loader):
        """Test invalid GPU cost values."""
        yaml_content = """
build:
  program:
    name: "mtop"
    monitor_name: "mtop"
    description: "Test"
    class_prefix: "MTop"
  branding:
    emoji: "📊"
    tagline: "Test"
    github_repo: "test/test"

display:
  columns:
    - name: "Model"
      field: "name"
      width: 20
  sorting:
    default_key: "name"
    available_keys: ["name"]
  summary:
    show_runtime: true

technology:
  gpu_types:
    bad-gpu:
      memory_gb: 80
      hourly_cost: "expensive"
"""

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with pytest.raises(ValueError, match="hourly_cost must be a number"):
                config_loader.load_config("test.yaml")


class TestTechnologyEnvironmentOverrides:
    """Test environment variable overrides for technology config."""

    @pytest.fixture
    def config_loader(self):
        """Create a ConfigLoader instance."""
        return ConfigLoader()

    @pytest.fixture
    def base_yaml(self):
        """Base YAML content for testing."""
        return """
build:
  program:
    name: "mtop"
    monitor_name: "mtop"
    description: "Test"
    class_prefix: "MTop"
  branding:
    emoji: "📊"
    tagline: "Test"
    github_repo: "test/test"

display:
  columns:
    - name: "Model"
      field: "name"
      width: 20
  sorting:
    default_key: "name"
    available_keys: ["name"]
  summary:
    show_runtime: true

technology:
  gpu_types:
    nvidia-a100:
      memory_gb: 80
      hourly_cost: 3.00
"""

    def test_env_override_gpu_memory(self, config_loader, base_yaml):
        """Test overriding GPU memory via environment variable."""
        with patch("builtins.open", mock_open(read_data=base_yaml)):
            with patch.dict("os.environ", {"MTOP_TECHNOLOGY_GPU_A100_MEMORY": "128"}):
                config = config_loader.load_config("test.yaml")

        assert config.technology.gpu_types["nvidia-a100"].memory_gb == 128

    def test_env_override_gpu_cost(self, config_loader, base_yaml):
        """Test overriding GPU cost via environment variable."""
        with patch("builtins.open", mock_open(read_data=base_yaml)):
            with patch.dict("os.environ", {"MTOP_TECHNOLOGY_GPU_A100_COST": "2.50"}):
                config = config_loader.load_config("test.yaml")

        assert config.technology.gpu_types["nvidia-a100"].hourly_cost == 2.50

    def test_env_override_new_gpu(self, config_loader, base_yaml):
        """Test adding new GPU via environment variables."""
        with patch("builtins.open", mock_open(read_data=base_yaml)):
            with patch.dict(
                "os.environ",
                {"MTOP_TECHNOLOGY_GPU_H100_MEMORY": "80", "MTOP_TECHNOLOGY_GPU_H100_COST": "5.00"},
            ):
                config = config_loader.load_config("test.yaml")

        assert "nvidia-h100" in config.technology.gpu_types
        h100 = config.technology.gpu_types["nvidia-h100"]
        assert h100.memory_gb == 80
        assert h100.hourly_cost == 5.00


class TestTechnologyConfigIntegration:
    """Integration tests with actual config file."""

    def test_load_actual_config(self):
        """Test loading the actual config.yaml file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            loader = ConfigLoader()
            config = loader.load_config(str(config_path))

            assert config.technology is not None
            assert "nvidia-a100" in config.technology.gpu_types
            assert "nvidia-h100" in config.technology.gpu_types

            a100 = config.technology.gpu_types["nvidia-a100"]
            assert a100.memory_gb == 80
            assert a100.hourly_cost == 3.00

            h100 = config.technology.gpu_types["nvidia-h100"]
            assert h100.memory_gb == 80
            assert h100.hourly_cost == 5.00
