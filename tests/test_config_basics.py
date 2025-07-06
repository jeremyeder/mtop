"""Basic configuration tests to ensure config loading works."""


def test_default_config_loads():
    """Default config.yaml loads without errors."""
    from config_loader import load_config

    config = load_config()
    assert config is not None
    assert hasattr(config, "technology")
    assert hasattr(config, "slo")
    assert hasattr(config, "workload")


def test_config_structure():
    """Config has expected structure."""
    from config_loader import load_config

    config = load_config()
    assert config.technology.gpu_types is not None
    assert len(config.technology.gpu_types) > 0
    assert config.slo is not None
    assert config.workload is not None
