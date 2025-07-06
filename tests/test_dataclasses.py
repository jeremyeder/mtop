"""Basic dataclass tests to ensure data structures work."""


def test_token_metrics_creation():
    """TokenMetrics can be created with valid data."""
    from mtop.token_metrics import TokenMetrics

    metrics = TokenMetrics(
        model_name="test", gpu_type="nvidia-h100", start_time=1000.0, first_token_time=1001.0
    )
    assert metrics.model_name == "test"
    assert metrics.gpu_type == "nvidia-h100"
    assert metrics.start_time == 1000.0
    assert metrics.first_token_time == 1001.0


def test_gpu_type_creation():
    """GPUType dataclass works."""
    from config_loader import GPUType

    gpu = GPUType(name="test-gpu", memory_gb=16, hourly_cost=1.0)
    assert gpu.name == "test-gpu"
    assert gpu.memory_gb == 16
    assert gpu.hourly_cost == 1.0
