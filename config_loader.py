#!/usr/bin/env python3
"""
Configuration loader for unified build-time and runtime settings
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ColorThreshold:
    """Color threshold configuration for metrics"""

    color: str
    min: Optional[float] = None
    max: Optional[float] = None


@dataclass
class ColumnConfig:
    """Configuration for a single display column"""

    name: str
    field: str
    width: int
    justify: str = "left"
    format: str = "string"
    color_thresholds: List[ColorThreshold] = field(default_factory=list)
    sortable: bool = False
    sort_key: Optional[str] = None
    enabled: bool = True
    truncate: Optional[int] = None


@dataclass
class DisplayConfig:
    """Runtime display configuration"""

    columns: List[ColumnConfig]
    sorting: Dict[str, Any]
    summary: Dict[str, bool]


@dataclass
class ProgramConfig:
    """Build-time program configuration"""

    name: str
    monitor_name: str
    description: str
    class_prefix: str


@dataclass
class BrandingConfig:
    """Build-time branding configuration"""

    emoji: str
    tagline: str
    github_repo: str


@dataclass
class BuildConfig:
    """Build-time configuration"""

    program: ProgramConfig
    branding: BrandingConfig


@dataclass
class GPUType:
    """GPU type configuration"""

    name: str
    memory_gb: int
    hourly_cost: float

    def __post_init__(self):
        """Validate GPU configuration"""
        if self.memory_gb <= 0:
            raise ValueError(f"GPU memory must be positive, got {self.memory_gb}")
        if self.hourly_cost < 0:
            raise ValueError(f"GPU hourly cost cannot be negative, got {self.hourly_cost}")


@dataclass
class TechnologyConfig:
    """Technology capabilities configuration"""

    gpu_types: Dict[str, GPUType] = field(default_factory=dict)


@dataclass
class SLOConfig:
    """Service Level Objective configuration"""

    ttft_p95_ms: int  # Time to first token, 95th percentile (milliseconds)
    error_rate_percent: float  # Error rate percentage (0-100)
    tokens_per_second: int  # Target tokens per second throughput

    def __post_init__(self):
        """Validate SLO configuration"""
        if self.ttft_p95_ms <= 0:
            raise ValueError(f"TTFT latency must be positive, got {self.ttft_p95_ms}")
        if not 0 <= self.error_rate_percent <= 100:
            raise ValueError(f"Error rate must be 0-100%, got {self.error_rate_percent}")
        if self.tokens_per_second <= 0:
            raise ValueError(f"Tokens per second must be positive, got {self.tokens_per_second}")


@dataclass
class WorkloadConfig:
    """Workload configuration for simulation and testing"""

    baseline_qps: int  # Baseline queries per second
    spike_multiplier: float  # Multiplier for spike testing (e.g., 2.0 = 2x baseline)

    def __post_init__(self):
        """Validate workload configuration"""
        if self.baseline_qps <= 0:
            raise ValueError(f"Baseline QPS must be positive, got {self.baseline_qps}")
        if self.spike_multiplier < 1.0:
            raise ValueError(f"Spike multiplier must be >= 1.0, got {self.spike_multiplier}")


@dataclass
class Config:
    """Complete configuration"""

    build: BuildConfig
    display: DisplayConfig
    technology: Optional[TechnologyConfig] = None
    slo: Optional[SLOConfig] = None
    workload: Optional[WorkloadConfig] = None


class ConfigLoader:
    """Loads and validates configuration from YAML"""

    def __init__(self):
        self.config_cache = {}

    def load_config(self, config_path: str = "config.yaml") -> Config:
        """Load configuration from YAML file with environment variable support"""
        import os

        config_path = Path(config_path)

        # Check for environment variable override
        env_config_path = os.environ.get("LDCTL_CONFIG_PATH")
        if env_config_path:
            config_path = Path(env_config_path)

        if not config_path.exists():
            # Try fallback config locations
            fallback_paths = [
                Path.home() / ".mtop" / "config.yaml",
                Path("/etc/mtop/config.yaml"),
                Path("config.yaml"),
            ]

            config_found = False
            for fallback in fallback_paths:
                if fallback.exists():
                    config_path = fallback
                    config_found = True
                    break

            if not config_found:
                raise FileNotFoundError(
                    f"Configuration file not found: {config_path}. Tried: {[str(p) for p in fallback_paths]}"
                )

        # Check cache
        cache_key = f"{config_path}:{config_path.stat().st_mtime}"
        if cache_key in self.config_cache:
            return self.config_cache[cache_key]

        try:
            with open(config_path, "r") as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise IOError(f"Error reading config file {config_path}: {e}")

        # Apply environment variable overrides
        raw_config = self._apply_env_overrides(raw_config)

        # Validate and parse configuration
        config = self._parse_config(raw_config)

        # Clear old cache entries and cache the result
        self.config_cache.clear()
        self.config_cache[cache_key] = config

        return config

    def _apply_env_overrides(self, config: dict) -> dict:
        """Apply environment variable overrides to configuration"""
        import os

        # Define environment variable mappings
        env_mappings = {
            "MTOP_MODE": ["build", "mode"],
            "MTOP_OUTPUT_FORMAT": ["build", "output_format"],
            "MTOP_VERBOSE": ["build", "verbose"],
            "MTOP_COLOR_ENABLED": ["display", "colors", "enabled"],
            "MTOP_MAX_WIDTH": ["display", "table", "max_width"],
            "MTOP_TRUNCATE_LONG": ["display", "table", "truncate_long"],
            "MTOP_SORT_KEY": ["display", "table", "default_sort_key"],
            # Technology configuration overrides
            "MTOP_TECHNOLOGY_GPU_A100_MEMORY": [
                "technology",
                "gpu_types",
                "nvidia-a100",
                "memory_gb",
            ],
            "MTOP_TECHNOLOGY_GPU_A100_COST": [
                "technology",
                "gpu_types",
                "nvidia-a100",
                "hourly_cost",
            ],
            "MTOP_TECHNOLOGY_GPU_H100_MEMORY": [
                "technology",
                "gpu_types",
                "nvidia-h100",
                "memory_gb",
            ],
            "MTOP_TECHNOLOGY_GPU_H100_COST": [
                "technology",
                "gpu_types",
                "nvidia-h100",
                "hourly_cost",
            ],
            # SLO configuration overrides
            "MTOP_SLO_TTFT_P95_MS": ["slo", "ttft_p95_ms"],
            "MTOP_SLO_ERROR_RATE_PERCENT": ["slo", "error_rate_percent"],
            "MTOP_SLO_TOKENS_PER_SECOND": ["slo", "tokens_per_second"],
            # Workload configuration overrides
            "MTOP_WORKLOAD_BASELINE_QPS": ["workload", "baseline_qps"],
            "MTOP_WORKLOAD_SPIKE_MULTIPLIER": ["workload", "spike_multiplier"],
        }

        for env_var, config_path in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                if env_value.lower() in ("true", "false"):
                    env_value = env_value.lower() == "true"
                elif env_value.isdigit():
                    env_value = int(env_value)
                else:
                    # Try to convert to float for decimal numbers
                    try:
                        env_value = float(env_value)
                    except ValueError:
                        # Keep as string if not a number
                        pass

                # Navigate to the config path and set the value
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[config_path[-1]] = env_value

        return config

    def validate_config(self, config: Config) -> List[str]:
        """Validate configuration and return list of warnings/issues"""
        warnings = []

        # Check for duplicate column names
        column_names = [col.name for col in config.display.columns]
        duplicates = set([name for name in column_names if column_names.count(name) > 1])
        if duplicates:
            warnings.append(f"Duplicate column names found: {', '.join(duplicates)}")

        # Check for duplicate field mappings
        field_names = [col.field for col in config.display.columns]
        duplicate_fields = set([field for field in field_names if field_names.count(field) > 1])
        if duplicate_fields:
            warnings.append(f"Duplicate field mappings found: {', '.join(duplicate_fields)}")

        # Check for unreasonably wide columns
        wide_columns = [col.name for col in config.display.columns if col.width > 100]
        if wide_columns:
            warnings.append(f"Very wide columns detected (>100 chars): {', '.join(wide_columns)}")

        # Check if any columns are sortable but don't have sort_key
        no_sort_key = [
            col.name for col in config.display.columns if col.sortable and not col.sort_key
        ]
        if no_sort_key:
            warnings.append(f"Sortable columns without sort_key: {', '.join(no_sort_key)}")

        # Check for disabled but critical columns
        disabled_critical = [
            col.name
            for col in config.display.columns
            if not col.enabled and col.name.lower() in ["name", "status"]
        ]
        if disabled_critical:
            warnings.append(f"Critical columns are disabled: {', '.join(disabled_critical)}")

        return warnings

    def _parse_config(self, raw_config: Dict[str, Any]) -> Config:
        """Parse raw config dictionary into structured objects with validation"""
        try:
            # Validate top-level structure
            if not isinstance(raw_config, dict):
                raise ValueError("Configuration must be a dictionary")

            # Parse build configuration with validation
            build_raw = raw_config.get("build", {})
            if not isinstance(build_raw, dict):
                raise ValueError("'build' section must be a dictionary")

            program_raw = build_raw.get("program", {})
            branding_raw = build_raw.get("branding", {})

            # Validate program config
            program_name = program_raw.get("name", "mtop")
            if not isinstance(program_name, str) or not program_name.strip():
                raise ValueError("program.name must be a non-empty string")

            program_config = ProgramConfig(
                name=program_name,
                monitor_name=program_raw.get("monitor_name", "mtop"),
                description=program_raw.get("description", "Mock CLI tool"),
                class_prefix=program_raw.get("class_prefix", "MTOP"),
            )

            # Validate branding config
            branding_config = BrandingConfig(
                emoji=branding_raw.get("emoji", "🚀"),
                tagline=branding_raw.get("tagline", "CLI tool"),
                github_repo=branding_raw.get("github_repo", "jeremyeder/mtop"),
            )

            build_config = BuildConfig(program=program_config, branding=branding_config)

            # Parse display configuration with validation
            display_raw = raw_config.get("display", {})
            if not isinstance(display_raw, dict):
                raise ValueError("'display' section must be a dictionary")

            columns_raw = display_raw.get("columns", [])
            if not isinstance(columns_raw, list):
                raise ValueError("display.columns must be a list")

            columns = []
            for i, col_raw in enumerate(columns_raw):
                if not isinstance(col_raw, dict):
                    raise ValueError(f"Column {i} must be a dictionary")

                # Validate required column fields
                col_name = col_raw.get("name")
                if not col_name or not isinstance(col_name, str):
                    raise ValueError(f"Column {i}: 'name' is required and must be a string")

                col_field = col_raw.get("field")
                if not col_field or not isinstance(col_field, str):
                    raise ValueError(
                        f"Column {i} ({col_name}): 'field' is required and must be a string"
                    )

                # Validate width
                col_width = col_raw.get("width", 10)
                if not isinstance(col_width, int) or col_width <= 0:
                    raise ValueError(f"Column {i} ({col_name}): 'width' must be a positive integer")

                # Validate justify
                col_justify = col_raw.get("justify", "left")
                if col_justify not in ["left", "right", "center"]:
                    raise ValueError(
                        f"Column {i} ({col_name}): 'justify' must be 'left', 'right', or 'center'"
                    )

                # Validate format
                col_format = col_raw.get("format", "string")
                valid_formats = ["string", "int", "float", "percent", "bytes", "duration"]
                if col_format not in valid_formats:
                    raise ValueError(
                        f"Column {i} ({col_name}): 'format' must be one of {valid_formats}"
                    )

                # Parse color thresholds with validation
                thresholds = []
                for j, threshold_raw in enumerate(col_raw.get("color_thresholds", [])):
                    if not isinstance(threshold_raw, dict):
                        raise ValueError(
                            f"Column {i} ({col_name}), threshold {j}: must be a dictionary"
                        )

                    threshold_color = threshold_raw.get("color")
                    if not threshold_color or not isinstance(threshold_color, str):
                        raise ValueError(
                            f"Column {i} ({col_name}), threshold {j}: 'color' is required"
                        )

                    threshold_min = threshold_raw.get("min")
                    threshold_max = threshold_raw.get("max")

                    # Validate min/max values
                    if threshold_min is not None and not isinstance(threshold_min, (int, float)):
                        raise ValueError(
                            f"Column {i} ({col_name}), threshold {j}: 'min' must be a number"
                        )
                    if threshold_max is not None and not isinstance(threshold_max, (int, float)):
                        raise ValueError(
                            f"Column {i} ({col_name}), threshold {j}: 'max' must be a number"
                        )
                    if (
                        threshold_min is not None
                        and threshold_max is not None
                        and threshold_min > threshold_max
                    ):
                        raise ValueError(
                            f"Column {i} ({col_name}), threshold {j}: 'min' cannot be greater than 'max'"
                        )

                    thresholds.append(
                        ColorThreshold(color=threshold_color, min=threshold_min, max=threshold_max)
                    )

                column = ColumnConfig(
                    name=col_name,
                    field=col_field,
                    width=col_width,
                    justify=col_justify,
                    format=col_format,
                    color_thresholds=thresholds,
                    sortable=col_raw.get("sortable", False),
                    sort_key=col_raw.get("sort_key"),
                    enabled=col_raw.get("enabled", True),
                    truncate=col_raw.get("truncate"),
                )
                columns.append(column)

            # Validate sorting configuration
            sorting_raw = display_raw.get("sorting", {})
            if not isinstance(sorting_raw, dict):
                raise ValueError("display.sorting must be a dictionary")

            # Validate summary configuration
            summary_raw = display_raw.get("summary", {})
            if not isinstance(summary_raw, dict):
                raise ValueError("display.summary must be a dictionary")

            display_config = DisplayConfig(
                columns=columns, sorting=sorting_raw, summary=summary_raw
            )

            # Parse technology configuration (optional)
            technology_config = None
            if "technology" in raw_config:
                technology_raw = raw_config["technology"]
                if not isinstance(technology_raw, dict):
                    raise ValueError("'technology' section must be a dictionary")

                gpu_types = {}
                gpu_types_raw = technology_raw.get("gpu_types", {})
                if not isinstance(gpu_types_raw, dict):
                    raise ValueError("technology.gpu_types must be a dictionary")

                for gpu_name, gpu_data in gpu_types_raw.items():
                    if not isinstance(gpu_data, dict):
                        raise ValueError(f"GPU type '{gpu_name}' must be a dictionary")

                    memory_gb = gpu_data.get("memory_gb", 0)
                    if not isinstance(memory_gb, (int, float)):
                        raise ValueError(f"GPU type '{gpu_name}': memory_gb must be a number")

                    hourly_cost = gpu_data.get("hourly_cost", 0.0)
                    if not isinstance(hourly_cost, (int, float)):
                        raise ValueError(f"GPU type '{gpu_name}': hourly_cost must be a number")

                    gpu_types[gpu_name] = GPUType(
                        name=gpu_name, memory_gb=int(memory_gb), hourly_cost=float(hourly_cost)
                    )

                technology_config = TechnologyConfig(gpu_types=gpu_types)

            # Parse SLO configuration (optional)
            slo_config = None
            if "slo" in raw_config:
                slo_raw = raw_config["slo"]
                if not isinstance(slo_raw, dict):
                    raise ValueError("'slo' section must be a dictionary")

                # Parse SLO values with defaults
                ttft_p95_ms = slo_raw.get("ttft_p95_ms", 500)
                error_rate_percent = slo_raw.get("error_rate_percent", 0.1)
                tokens_per_second = slo_raw.get("tokens_per_second", 1000)

                # Validate types
                if not isinstance(ttft_p95_ms, int):
                    raise ValueError("slo.ttft_p95_ms must be an integer")
                if not isinstance(error_rate_percent, (int, float)):
                    raise ValueError("slo.error_rate_percent must be a number")
                if not isinstance(tokens_per_second, int):
                    raise ValueError("slo.tokens_per_second must be an integer")

                slo_config = SLOConfig(
                    ttft_p95_ms=ttft_p95_ms,
                    error_rate_percent=float(error_rate_percent),
                    tokens_per_second=tokens_per_second,
                )

            # Parse workload configuration (optional)
            workload_config = None
            if "workload" in raw_config:
                workload_raw = raw_config["workload"]
                if not isinstance(workload_raw, dict):
                    raise ValueError("'workload' section must be a dictionary")

                # Parse workload values with defaults
                baseline_qps = workload_raw.get("baseline_qps", 100)
                spike_multiplier = workload_raw.get("spike_multiplier", 2.0)

                # Validate types
                if not isinstance(baseline_qps, int):
                    raise ValueError("workload.baseline_qps must be an integer")
                if not isinstance(spike_multiplier, (int, float)):
                    raise ValueError("workload.spike_multiplier must be a number")

                workload_config = WorkloadConfig(
                    baseline_qps=baseline_qps,
                    spike_multiplier=float(spike_multiplier),
                )

            return Config(
                build=build_config,
                display=display_config,
                technology=technology_config,
                slo=slo_config,
                workload=workload_config,
            )

        except KeyError as e:
            raise ValueError(f"Missing required configuration key: {e}")
        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            raise ValueError(f"Error parsing configuration: {e}")

    def get_enabled_columns(self, config: Config) -> List[ColumnConfig]:
        """Get only enabled columns from configuration"""
        return [col for col in config.display.columns if col.enabled]

    def get_sortable_columns(self, config: Config) -> Dict[str, ColumnConfig]:
        """Get mapping of sort keys to column configurations"""
        sortable = {}
        for col in config.display.columns:
            if col.sortable and col.sort_key:
                sortable[col.sort_key] = col
        return sortable


# Convenience functions
def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration - convenience function"""
    return ConfigLoader().load_config(config_path)


def get_default_config() -> Config:
    """Get default configuration for mtop compatibility"""
    # This maintains backward compatibility
    default_yaml = """
build:
  program:
    name: "mtop"
    monitor_name: "mtop"
    description: "Mock CLI tool for debugging LLMInferenceService CRDs"
    class_prefix: "KubectlLD"
  branding:
    emoji: "🚀"
    tagline: "Mock CLI tool for debugging LLMInferenceService CRDs"
    github_repo: "jeremyeder/mtop"

display:
  columns:
    - name: "Model"
      field: "name"
      width: 30
      justify: "left"
      truncate: 23
    - name: "Status"
      field: "status"
      width: 12
      justify: "center"
      format: "emoji_status"
    - name: "QPS"
      field: "current_qps"
      width: 8
      justify: "right"
      format: "integer_comma"
      sortable: true
      sort_key: "qps"
    - name: "GPU %util"
      field: "cpu_percent"
      width: 9
      justify: "center"
      format: "percentage"
      color_thresholds:
        - max: 50
          color: "green"
        - max: 80
          color: "yellow"
        - min: 80
          color: "red"
      sortable: true
      sort_key: "gpu"
    - name: "Errors"
      field: "error_rate"
      width: 7
      justify: "center"
      format: "percentage_1dp"
      color_thresholds:
        - max: 1.0
          color: "green"
        - max: 3.0
          color: "yellow"
        - min: 3.0
          color: "red"
      sortable: true
      sort_key: "errors"
    - name: "Latency"
      field: "latency_p95"
      width: 8
      justify: "center"
      format: "latency_ms"
    - name: "Replicas"
      field: "replicas"
      width: 8
      justify: "center"
      format: "integer"
  sorting:
    default_key: "qps"
    available_keys: ["qps", "gpu", "errors", "name"]
  summary:
    show_runtime: true
    show_sort_key: true
    show_mode: true
    show_namespace: true
"""

    raw_config = yaml.safe_load(default_yaml)
    return ConfigLoader()._parse_config(raw_config)


if __name__ == "__main__":
    # Test the configuration loader
    try:
        config = load_config()
        print("✅ Configuration loaded successfully")
        print(f"Program name: {config.build.program.name}")
        print(f"Columns: {len(config.display.columns)}")
        print(f"Enabled columns: {len(ConfigLoader().get_enabled_columns(config))}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
