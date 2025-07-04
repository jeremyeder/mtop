#!/usr/bin/env python3
"""
Configuration loader for unified build-time and runtime settings
"""

import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path


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
class Config:
    """Complete configuration"""
    build: BuildConfig
    display: DisplayConfig


class ConfigLoader:
    """Loads and validates configuration from YAML"""
    
    def __init__(self):
        self.config_cache = {}
    
    def load_config(self, config_path: str = "config.yaml") -> Config:
        """Load configuration from YAML file"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Check cache
        if config_path in self.config_cache:
            return self.config_cache[config_path]
        
        try:
            with open(config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        
        # Validate and parse configuration
        config = self._parse_config(raw_config)
        
        # Cache the result
        self.config_cache[config_path] = config
        
        return config
    
    def _parse_config(self, raw_config: Dict[str, Any]) -> Config:
        """Parse raw config dictionary into structured objects"""
        try:
            # Parse build configuration
            build_raw = raw_config.get('build', {})
            program_raw = build_raw.get('program', {})
            branding_raw = build_raw.get('branding', {})
            
            program_config = ProgramConfig(
                name=program_raw.get('name', 'kubectl-ld'),
                monitor_name=program_raw.get('monitor_name', 'ldtop'),
                description=program_raw.get('description', 'Mock CLI tool'),
                class_prefix=program_raw.get('class_prefix', 'KubectlLD')
            )
            
            branding_config = BrandingConfig(
                emoji=branding_raw.get('emoji', '🚀'),
                tagline=branding_raw.get('tagline', 'CLI tool'),
                github_repo=branding_raw.get('github_repo', 'jeremyeder/kubectl-ld')
            )
            
            build_config = BuildConfig(
                program=program_config,
                branding=branding_config
            )
            
            # Parse display configuration
            display_raw = raw_config.get('display', {})
            columns_raw = display_raw.get('columns', [])
            
            columns = []
            for col_raw in columns_raw:
                # Parse color thresholds
                thresholds = []
                for threshold_raw in col_raw.get('color_thresholds', []):
                    thresholds.append(ColorThreshold(
                        color=threshold_raw.get('color', 'white'),
                        min=threshold_raw.get('min'),
                        max=threshold_raw.get('max')
                    ))
                
                column = ColumnConfig(
                    name=col_raw.get('name', ''),
                    field=col_raw.get('field', ''),
                    width=col_raw.get('width', 10),
                    justify=col_raw.get('justify', 'left'),
                    format=col_raw.get('format', 'string'),
                    color_thresholds=thresholds,
                    sortable=col_raw.get('sortable', False),
                    sort_key=col_raw.get('sort_key'),
                    enabled=col_raw.get('enabled', True),
                    truncate=col_raw.get('truncate')
                )
                columns.append(column)
            
            display_config = DisplayConfig(
                columns=columns,
                sorting=display_raw.get('sorting', {}),
                summary=display_raw.get('summary', {})
            )
            
            return Config(
                build=build_config,
                display=display_config
            )
            
        except KeyError as e:
            raise ValueError(f"Missing required configuration key: {e}")
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
    """Get default configuration for kubectl-ld compatibility"""
    # This maintains backward compatibility
    default_yaml = """
build:
  program:
    name: "kubectl-ld"
    monitor_name: "ldtop"
    description: "Mock CLI tool for debugging LLMInferenceService CRDs"
    class_prefix: "KubectlLD"
  branding:
    emoji: "🚀"
    tagline: "Mock CLI tool for debugging LLMInferenceService CRDs"
    github_repo: "jeremyeder/kubectl-ld"

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