#!/usr/bin/env python3
"""
Comprehensive tests for CostCalculator functionality.
"""

import pytest

from config_loader import GPUType, TechnologyConfig
from mtop.token_metrics import CostCalculator, TokenMetrics, TokenTracker, create_cost_calculator


class TestCostCalculator:
    """Test CostCalculator for GPU cost calculations."""

    def test_cost_calculator_creation(self):
        """Test basic CostCalculator creation."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.2),
                "nvidia-h100": GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=4.1),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        assert calculator.technology_config == technology_config

    def test_cost_calculator_validation(self):
        """Test CostCalculator validation."""
        with pytest.raises(ValueError, match="technology_config must be a valid TechnologyConfig"):
            CostCalculator(technology_config="invalid")  # type: ignore

    def test_calculate_token_cost_basic(self):
        """Test basic token cost calculation."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),  # $3.60/hour
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        # Calculate cost for 1 hour of inference
        cost = calculator.calculate_token_cost(
            tokens=1000, gpu_type="nvidia-a100", duration_seconds=3600
        )

        assert cost == 3.60  # Should be exactly $3.60 for 1 hour

    def test_calculate_token_cost_partial_hour(self):
        """Test token cost calculation for partial hours."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        # Calculate cost for 30 minutes (0.5 hours)
        cost = calculator.calculate_token_cost(
            tokens=500, gpu_type="nvidia-a100", duration_seconds=1800
        )

        assert cost == 1.80  # Should be $1.80 for 0.5 hours

    def test_calculate_token_cost_validation(self):
        """Test token cost calculation validation."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        # Test negative tokens
        with pytest.raises(ValueError, match="tokens cannot be negative"):
            calculator.calculate_token_cost(-100, "nvidia-a100", 3600)

        # Test negative duration
        with pytest.raises(ValueError, match="duration_seconds cannot be negative"):
            calculator.calculate_token_cost(100, "nvidia-a100", -3600)

        # Test invalid GPU type
        with pytest.raises(ValueError, match="gpu_type 'invalid' not found"):
            calculator.calculate_token_cost(100, "invalid", 3600)

    def test_get_cost_per_million_tokens(self):
        """Test cost per million tokens calculation."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        # If we can generate 1000 tokens per second, 1M tokens takes 1000 seconds
        # 1000 seconds = 1000/3600 = 0.2778 hours
        # Cost = 0.2778 * 3.60 = 1.0 dollar
        cost_per_million = calculator.get_cost_per_million_tokens("nvidia-a100", 1000)

        assert abs(cost_per_million - 1.0) < 0.01  # Should be approximately $1.00

    def test_get_cost_per_million_tokens_validation(self):
        """Test cost per million tokens validation."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        # Test zero tokens per second
        with pytest.raises(ValueError, match="tokens_per_second must be positive"):
            calculator.get_cost_per_million_tokens("nvidia-a100", 0)

        # Test negative tokens per second
        with pytest.raises(ValueError, match="tokens_per_second must be positive"):
            calculator.get_cost_per_million_tokens("nvidia-a100", -100)

        # Test invalid GPU type
        with pytest.raises(ValueError, match="gpu_type 'invalid' not found"):
            calculator.get_cost_per_million_tokens("invalid", 1000)

    def test_calculate_efficiency_ratio(self):
        """Test efficiency ratio calculation."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        # Test exactly on target
        ratio = calculator.calculate_efficiency_ratio(actual_cost=2.0, target_cost=2.0)
        assert ratio == 1.0

        # Test better than target (lower cost)
        ratio = calculator.calculate_efficiency_ratio(actual_cost=1.0, target_cost=2.0)
        assert ratio == 0.5

        # Test worse than target (higher cost)
        ratio = calculator.calculate_efficiency_ratio(actual_cost=3.0, target_cost=2.0)
        assert ratio == 1.5

    def test_calculate_efficiency_ratio_validation(self):
        """Test efficiency ratio validation."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        # Test negative target cost
        with pytest.raises(ValueError, match="target_cost must be positive"):
            calculator.calculate_efficiency_ratio(2.0, -1.0)

        # Test zero target cost
        with pytest.raises(ValueError, match="target_cost must be positive"):
            calculator.calculate_efficiency_ratio(2.0, 0.0)

        # Test negative actual cost
        with pytest.raises(ValueError, match="actual_cost cannot be negative"):
            calculator.calculate_efficiency_ratio(-1.0, 2.0)

    def test_calculate_cost_from_metrics(self):
        """Test cost calculation from TokenMetrics."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        # Create completed metrics
        metrics = TokenMetrics(
            model_name="test-model",
            tokens_generated=1000,
            gpu_type="nvidia-a100",
            start_time=1000.0,
            completion_time=1001.0,  # 1 second duration
        )

        cost = calculator.calculate_cost_from_metrics(metrics)
        expected_cost = 3.60 / 3600  # 1 second of $3.60/hour
        assert cost is not None
        assert abs(cost - expected_cost) < 0.001

    def test_calculate_cost_from_metrics_incomplete(self):
        """Test cost calculation from incomplete metrics."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        # Create incomplete metrics (no completion_time)
        metrics = TokenMetrics(
            model_name="test-model",
            tokens_generated=1000,
            gpu_type="nvidia-a100",
            start_time=1000.0,
        )

        cost = calculator.calculate_cost_from_metrics(metrics)
        assert cost is None

    def test_calculate_cost_from_metrics_no_gpu_type(self):
        """Test cost calculation from metrics without GPU type."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        # Create metrics without GPU type
        metrics = TokenMetrics(
            model_name="test-model",
            tokens_generated=1000,
            start_time=1000.0,
            completion_time=1001.0,
        )

        cost = calculator.calculate_cost_from_metrics(metrics)
        assert cost is None

    def test_get_gpu_cost_comparison(self):
        """Test GPU cost comparison."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
                "nvidia-h100": GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=4.10),
                "nvidia-v100": GPUType(name="nvidia-v100", memory_gb=32, hourly_cost=2.50),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        comparison = calculator.get_gpu_cost_comparison()

        expected = {
            "nvidia-a100": 3.60,
            "nvidia-h100": 4.10,
            "nvidia-v100": 2.50,
        }
        assert comparison == expected

    def test_get_cheapest_gpu(self):
        """Test finding cheapest GPU."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
                "nvidia-h100": GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=4.10),
                "nvidia-v100": GPUType(name="nvidia-v100", memory_gb=32, hourly_cost=2.50),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        cheapest = calculator.get_cheapest_gpu()
        assert cheapest == "nvidia-v100"

    def test_get_cheapest_gpu_empty(self):
        """Test finding cheapest GPU with empty config."""
        technology_config = TechnologyConfig(gpu_types={})
        calculator = CostCalculator(technology_config=technology_config)

        cheapest = calculator.get_cheapest_gpu()
        assert cheapest is None

    def test_get_most_expensive_gpu(self):
        """Test finding most expensive GPU."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
                "nvidia-h100": GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=4.10),
                "nvidia-v100": GPUType(name="nvidia-v100", memory_gb=32, hourly_cost=2.50),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        most_expensive = calculator.get_most_expensive_gpu()
        assert most_expensive == "nvidia-h100"

    def test_get_most_expensive_gpu_empty(self):
        """Test finding most expensive GPU with empty config."""
        technology_config = TechnologyConfig(gpu_types={})
        calculator = CostCalculator(technology_config=technology_config)

        most_expensive = calculator.get_most_expensive_gpu()
        assert most_expensive is None

    def test_calculate_cost_savings(self):
        """Test cost savings calculation."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
                "nvidia-v100": GPUType(name="nvidia-v100", memory_gb=32, hourly_cost=2.50),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        # Switch from A100 to V100 for 1 hour
        savings = calculator.calculate_cost_savings("nvidia-a100", "nvidia-v100", 3600)
        expected_savings = 3.60 - 2.50  # $1.10 savings per hour
        assert abs(savings - expected_savings) < 0.001

        # Switch from V100 to A100 (negative savings = additional cost)
        additional_cost = calculator.calculate_cost_savings("nvidia-v100", "nvidia-a100", 3600)
        expected_additional_cost = 2.50 - 3.60  # -$1.10 (additional cost)
        assert abs(additional_cost - expected_additional_cost) < 0.001

    def test_calculate_cost_savings_validation(self):
        """Test cost savings calculation validation."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        # Test invalid from_gpu
        with pytest.raises(ValueError, match="from_gpu 'invalid' not found"):
            calculator.calculate_cost_savings("invalid", "nvidia-a100", 3600)

        # Test invalid to_gpu
        with pytest.raises(ValueError, match="to_gpu 'invalid' not found"):
            calculator.calculate_cost_savings("nvidia-a100", "invalid", 3600)

        # Test negative duration
        with pytest.raises(ValueError, match="duration_seconds cannot be negative"):
            calculator.calculate_cost_savings("nvidia-a100", "nvidia-a100", -3600)

    def test_get_cost_statistics(self):
        """Test comprehensive cost statistics."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
                "nvidia-h100": GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=4.10),
                "nvidia-v100": GPUType(name="nvidia-v100", memory_gb=32, hourly_cost=2.50),
            }
        )
        calculator = CostCalculator(technology_config=technology_config)

        stats = calculator.get_cost_statistics()

        assert stats["total_gpu_types"] == 3
        assert stats["cheapest_gpu"] == "nvidia-v100"
        assert stats["most_expensive_gpu"] == "nvidia-h100"
        assert stats["min_hourly_cost"] == 2.50
        assert stats["max_hourly_cost"] == 4.10
        assert abs(stats["avg_hourly_cost"] - 3.40) < 0.01  # (3.60 + 4.10 + 2.50) / 3
        assert set(stats["gpu_types"]) == {"nvidia-a100", "nvidia-h100", "nvidia-v100"}
        assert "cost_comparison" in stats

    def test_get_cost_statistics_empty(self):
        """Test cost statistics with empty config."""
        technology_config = TechnologyConfig(gpu_types={})
        calculator = CostCalculator(technology_config=technology_config)

        stats = calculator.get_cost_statistics()
        assert stats == {}


class TestCostCalculatorFactory:
    """Test factory function for creating CostCalculator."""

    def test_create_cost_calculator_basic(self):
        """Test basic cost calculator creation."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
            }
        )
        calculator = create_cost_calculator(technology_config)

        assert isinstance(calculator, CostCalculator)
        assert calculator.technology_config == technology_config

    def test_create_cost_calculator_none_config(self):
        """Test cost calculator creation with None config."""
        with pytest.raises(ValueError, match="technology_config is required for CostCalculator"):
            create_cost_calculator(None)  # type: ignore


class TestCostCalculatorIntegration:
    """Test CostCalculator integration with other components."""

    def test_integration_with_token_tracker(self):
        """Test CostCalculator integration with TokenTracker."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
                "nvidia-v100": GPUType(name="nvidia-v100", memory_gb=32, hourly_cost=2.50),
            }
        )

        tracker = TokenTracker(technology_config=technology_config)
        calculator = CostCalculator(technology_config=technology_config)

        # Simulate token generation
        metrics = tracker.simulate_token_generation("test-model", target_tokens=1000)

        # Calculate cost from simulated metrics
        cost = calculator.calculate_cost_from_metrics(metrics)

        assert cost is not None
        assert cost > 0  # Should have some cost

        # Cost should be reasonable for short simulation
        assert cost < 1.0  # Should be less than $1 for quick simulation

    def test_cost_comparison_across_gpus(self):
        """Test cost comparison for the same workload across different GPUs."""
        technology_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=80, hourly_cost=3.60),
                "nvidia-v100": GPUType(name="nvidia-v100", memory_gb=32, hourly_cost=2.50),
                "nvidia-h100": GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=4.10),
            }
        )

        calculator = CostCalculator(technology_config=technology_config)

        # Calculate cost per million tokens for each GPU at 1000 TPS
        costs = {}
        for gpu_type in technology_config.gpu_types.keys():
            costs[gpu_type] = calculator.get_cost_per_million_tokens(gpu_type, 1000)

        # V100 should be cheapest, H100 should be most expensive
        assert costs["nvidia-v100"] < costs["nvidia-a100"] < costs["nvidia-h100"]

        # Verify the cheapest/most expensive detection works
        assert calculator.get_cheapest_gpu() == "nvidia-v100"
        assert calculator.get_most_expensive_gpu() == "nvidia-h100"