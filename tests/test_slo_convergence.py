#!/usr/bin/env python3
"""
Test suite for SLO convergence algorithm.
"""

import time
from unittest.mock import MagicMock, Mock

import pytest

from config_loader import GPUType, SLOConfig, TechnologyConfig, WorkloadConfig
from mtop.gpu_heartbeat import GPUMetrics, ScalingDecision, UtilizationTracker
from mtop.slo_convergence import (
    ActionType,
    ConvergenceAction,
    ConvergenceMetrics,
    ConvergenceState,
    OptimizationStrategy,
    SLOConvergenceAlgorithm,
)
from mtop.token_metrics import TokenMetrics
from mtop.workload_generator import WorkloadGenerator


class TestConvergenceMetrics:
    """Test convergence metrics functionality."""

    def test_valid_convergence_metrics(self):
        """Test valid convergence metrics creation."""
        metrics = ConvergenceMetrics(
            current_ttft_p95=450.0,
            target_ttft_p95=500.0,
            current_cost_per_million=22.0,
            target_cost_per_million=25.0,
            current_throughput=1200.0,
            target_throughput=1000.0,
        )

        assert metrics.current_ttft_p95 == 450.0
        assert metrics.target_ttft_p95 == 500.0
        assert metrics.current_cost_per_million == 22.0
        assert metrics.target_cost_per_million == 25.0
        assert metrics.current_throughput == 1200.0
        assert metrics.target_throughput == 1000.0

    def test_convergence_metrics_validation(self):
        """Test convergence metrics validation."""
        with pytest.raises(ValueError, match="Target TTFT must be positive"):
            ConvergenceMetrics(target_ttft_p95=-100.0)

        with pytest.raises(ValueError, match="Target cost must be positive"):
            ConvergenceMetrics(target_cost_per_million=-10.0)

        with pytest.raises(ValueError, match="Target throughput must be positive"):
            ConvergenceMetrics(target_throughput=-1000.0)


class TestConvergenceAction:
    """Test convergence action functionality."""

    def test_valid_convergence_action(self):
        """Test valid convergence action creation."""
        action = ConvergenceAction(
            timestamp=time.time(),
            action_type=ActionType.SCALE_UP,
            description="Scale up for performance",
            reasoning="TTFT exceeds target",
            expected_impact="Reduced latency",
        )

        assert action.action_type == ActionType.SCALE_UP
        assert action.description == "Scale up for performance"
        assert action.reasoning == "TTFT exceeds target"
        assert action.expected_impact == "Reduced latency"
        assert action.success is None
        assert action.metadata == {}

    def test_convergence_action_validation(self):
        """Test convergence action validation."""
        with pytest.raises(ValueError, match="Description cannot be empty"):
            ConvergenceAction(
                timestamp=time.time(),
                action_type=ActionType.SCALE_UP,
                description="",
                reasoning="Test reason",
                expected_impact="Test impact",
            )

        with pytest.raises(ValueError, match="Reasoning cannot be empty"):
            ConvergenceAction(
                timestamp=time.time(),
                action_type=ActionType.SCALE_UP,
                description="Test description",
                reasoning="",
                expected_impact="Test impact",
            )

        with pytest.raises(ValueError, match="Expected impact cannot be empty"):
            ConvergenceAction(
                timestamp=time.time(),
                action_type=ActionType.SCALE_UP,
                description="Test description",
                reasoning="Test reason",
                expected_impact="",
            )


class TestSLOConvergenceAlgorithm:
    """Test SLO convergence algorithm functionality."""

    @pytest.fixture
    def slo_config(self):
        """Create test SLO configuration."""
        return SLOConfig(ttft_p95_ms=500, error_rate_percent=0.1, tokens_per_second=1000)

    @pytest.fixture
    def technology_config(self):
        """Create test technology configuration."""
        return TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType("nvidia-a100", 80, 3.00),
                "nvidia-h100": GPUType("nvidia-h100", 80, 5.00),
            }
        )

    @pytest.fixture
    def workload_config(self):
        """Create test workload configuration."""
        return WorkloadConfig(baseline_qps=100, spike_multiplier=2.0)

    @pytest.fixture
    def convergence_algorithm(self, slo_config, technology_config, workload_config):
        """Create test convergence algorithm."""
        return SLOConvergenceAlgorithm(slo_config, technology_config, workload_config)

    def test_algorithm_initialization(self, convergence_algorithm, slo_config):
        """Test algorithm initialization."""
        assert convergence_algorithm.slo_config == slo_config
        assert convergence_algorithm.current_metrics.target_ttft_p95 == 500
        assert convergence_algorithm.current_metrics.target_throughput == 1000
        assert convergence_algorithm.convergence_state == ConvergenceState.UNKNOWN
        assert convergence_algorithm.optimization_strategy == OptimizationStrategy.BALANCED
        assert len(convergence_algorithm.action_history) == 0
        assert len(convergence_algorithm.metrics_history) == 0

    def test_metrics_update(self, convergence_algorithm):
        """Test metrics update functionality."""
        # Create multiple test token metrics to get P95 calculation
        base_time = time.time()
        token_metrics = []

        # Generate 25 token metrics to ensure P95 calculation works
        for i in range(25):
            token_metrics.append(
                TokenMetrics(
                    model_name="test-model",
                    tokens_generated=1000,
                    start_time=base_time - 1.0 + (i * 0.01),
                    first_token_time=base_time - 0.5 + (i * 0.01),
                    completion_time=base_time + (i * 0.01),
                    gpu_type="nvidia-a100",
                )
            )

        gpu_metrics = {"gpu-0": {"utilization": 75.0, "memory_used": 40.0}}

        workload_qps = 150.0

        convergence_algorithm.update_metrics(token_metrics, gpu_metrics, workload_qps)

        # Check that metrics were updated (P95 should be available with 25+ measurements)
        assert convergence_algorithm.current_metrics.current_ttft_p95 is not None
        assert len(convergence_algorithm.metrics_history) == 1

        # Check metrics history
        history_entry = convergence_algorithm.metrics_history[0]
        assert history_entry["workload_qps"] == 150.0
        assert "timestamp" in history_entry
        assert "convergence_score" in history_entry

    def test_compliance_status_update(self, convergence_algorithm):
        """Test compliance status update."""
        # Set current metrics
        convergence_algorithm.current_metrics.current_ttft_p95 = 450.0  # Under target
        convergence_algorithm.current_metrics.current_cost_per_million = 30.0  # Over target
        convergence_algorithm.current_metrics.current_throughput = 1200.0  # Over target

        convergence_algorithm._update_compliance_status()

        assert convergence_algorithm.current_metrics.ttft_compliance is True
        assert convergence_algorithm.current_metrics.cost_compliance is False
        assert convergence_algorithm.current_metrics.throughput_compliance is True

    def test_convergence_score_calculation(self, convergence_algorithm):
        """Test convergence score calculation."""
        # Set current metrics for scoring
        convergence_algorithm.current_metrics.current_ttft_p95 = 500.0  # Exactly at target
        convergence_algorithm.current_metrics.current_cost_per_million = 20.0  # Under target (good)
        convergence_algorithm.current_metrics.current_throughput = 1000.0  # At target

        convergence_algorithm._update_convergence_scores()

        # Should have high convergence score
        assert convergence_algorithm.current_metrics.convergence_score > 0.8

    def test_convergence_state_evaluation(self, convergence_algorithm):
        """Test convergence state evaluation."""
        # Add metrics history with converged pattern
        for i in range(15):
            convergence_algorithm.metrics_history.append(
                {
                    "timestamp": time.time() + i,
                    "convergence_score": 0.95 + (i % 3) * 0.01,  # Stable high scores
                    "ttft_p95": 490 + (i % 3) * 5,
                    "cost_per_million": 22.0,
                    "throughput": 1050,
                }
            )

        state = convergence_algorithm.evaluate_convergence_state()
        assert state == ConvergenceState.CONVERGED

    def test_oscillation_detection(self, convergence_algorithm):
        """Test oscillation detection."""
        # Add metrics history with oscillating pattern
        for i in range(20):
            score = 0.7 + 0.2 * (i % 2)  # Oscillating between 0.7 and 0.9
            convergence_algorithm.metrics_history.append(
                {
                    "timestamp": time.time() + i,
                    "convergence_score": score,
                    "ttft_p95": 500 + 50 * (i % 2),
                    "cost_per_million": 25.0,
                    "throughput": 1000,
                }
            )

        is_oscillating = convergence_algorithm._detect_oscillation()
        assert is_oscillating is True

    def test_strategy_adaptation(self, convergence_algorithm):
        """Test strategy adaptation."""
        # Set emergency condition
        convergence_algorithm.current_metrics.current_ttft_p95 = 1200.0  # 2.4x target
        convergence_algorithm._adapt_strategy()

        assert convergence_algorithm.optimization_strategy == OptimizationStrategy.EMERGENCY

    def test_emergency_action_creation(self, convergence_algorithm):
        """Test emergency action creation."""
        # Create mock utilization tracker
        mock_tracker = Mock(spec=UtilizationTracker)

        # Set emergency condition
        convergence_algorithm.current_metrics.current_ttft_p95 = 1200.0
        convergence_algorithm.optimization_strategy = OptimizationStrategy.EMERGENCY

        action = convergence_algorithm._emergency_action(mock_tracker)

        assert action.action_type == ActionType.SCALE_UP
        assert "emergency" in action.description.lower()
        assert "emergency" in action.metadata["strategy"]

    def test_performance_improvement_action(self, convergence_algorithm):
        """Test performance improvement action creation."""
        action = convergence_algorithm._performance_improvement_action(
            ScalingDecision.SCALE_UP, "High utilization detected"
        )

        assert action.action_type == ActionType.SCALE_UP
        assert "performance" in action.description.lower()
        assert action.metadata["scaling_decision"] == "scale_up"

    def test_cost_optimization_action(self, convergence_algorithm):
        """Test cost optimization action creation."""
        # Create mock utilization tracker with underutilized GPUs
        mock_tracker = Mock(spec=UtilizationTracker)
        mock_tracker.get_underutilized_gpus.return_value = ["gpu-1", "gpu-2"]

        action = convergence_algorithm._cost_optimization_action(mock_tracker)

        assert action.action_type == ActionType.SCALE_DOWN
        assert "cost" in action.description.lower()
        assert len(action.metadata["underutilized_gpus"]) == 2

    def test_action_execution(self, convergence_algorithm):
        """Test action execution."""
        action = ConvergenceAction(
            timestamp=time.time(),
            action_type=ActionType.SCALE_UP,
            description="Test scale up",
            reasoning="Test reasoning",
            expected_impact="Test impact",
        )

        success = convergence_algorithm.execute_action(action)

        assert success is True
        assert action.success is True
        assert action.actual_impact is not None

    def test_convergence_status_reporting(self, convergence_algorithm):
        """Test convergence status reporting."""
        # Set some metrics
        convergence_algorithm.current_metrics.current_ttft_p95 = 480.0
        convergence_algorithm.current_metrics.current_cost_per_million = 23.0
        convergence_algorithm.current_metrics.current_throughput = 1100.0
        convergence_algorithm.current_metrics.convergence_score = 0.85
        convergence_algorithm.current_metrics.stability_score = 0.92

        status = convergence_algorithm.get_convergence_status()

        assert "convergence_state" in status
        assert "optimization_strategy" in status
        assert "metrics" in status
        assert "compliance" in status
        assert "targets" in status

        assert status["metrics"]["ttft_p95"] == 480.0
        assert status["metrics"]["cost_per_million"] == 23.0
        assert status["metrics"]["convergence_score"] == 0.85


class TestActionDecisionLogic:
    """Test action decision logic."""

    @pytest.fixture
    def convergence_algorithm(self):
        """Create test convergence algorithm."""
        slo_config = SLOConfig(ttft_p95_ms=500, error_rate_percent=0.1, tokens_per_second=1000)
        technology_config = TechnologyConfig(
            gpu_types={"nvidia-a100": GPUType("nvidia-a100", 80, 3.00)}
        )
        workload_config = WorkloadConfig(baseline_qps=100, spike_multiplier=2.0)
        return SLOConvergenceAlgorithm(slo_config, technology_config, workload_config)

    @pytest.fixture
    def mock_utilization_tracker(self):
        """Create mock utilization tracker."""
        tracker = Mock(spec=UtilizationTracker)
        tracker.get_aggregate_utilization.return_value = 75.0
        tracker.get_underutilized_gpus.return_value = []
        tracker.get_overloaded_gpus.return_value = []
        return tracker

    @pytest.fixture
    def mock_workload_generator(self):
        """Create mock workload generator."""
        generator = Mock(spec=WorkloadGenerator)
        generator.get_current_qps.return_value = 150.0
        return generator

    def test_no_action_during_cooldown(
        self, convergence_algorithm, mock_utilization_tracker, mock_workload_generator
    ):
        """Test that no action is taken during cooldown period."""
        # Set recent action time
        convergence_algorithm.last_action_time = time.time() - 30  # 30 seconds ago
        convergence_algorithm.action_cooldown = 60.0  # 60 second cooldown

        action = convergence_algorithm.decide_action(
            mock_utilization_tracker, mock_workload_generator
        )

        assert action is None

    def test_action_selection_after_cooldown(
        self, convergence_algorithm, mock_utilization_tracker, mock_workload_generator
    ):
        """Test action selection after cooldown period."""
        # Set old action time
        convergence_algorithm.last_action_time = time.time() - 120  # 2 minutes ago

        # Set SLO violation
        convergence_algorithm.current_metrics.current_ttft_p95 = 600.0  # Exceeds target
        convergence_algorithm.current_metrics.ttft_compliance = False

        # Mock capacity scaler decision
        convergence_algorithm.capacity_scaler.evaluate_scaling_decision = Mock(
            return_value=(ScalingDecision.SCALE_UP, "High latency detected")
        )

        action = convergence_algorithm.decide_action(
            mock_utilization_tracker, mock_workload_generator
        )

        assert action is not None
        assert action.action_type in [ActionType.SCALE_UP, ActionType.ADJUST_ALLOCATION]

    def test_balanced_strategy_prioritization(
        self, convergence_algorithm, mock_utilization_tracker, mock_workload_generator
    ):
        """Test balanced strategy prioritization of violations."""
        convergence_algorithm.optimization_strategy = OptimizationStrategy.BALANCED
        convergence_algorithm.last_action_time = 0  # No cooldown

        # Set multiple violations with cost being most severe
        convergence_algorithm.current_metrics.current_ttft_p95 = 550.0  # 1.1x target
        convergence_algorithm.current_metrics.current_cost_per_million = 50.0  # 2.0x target
        convergence_algorithm.current_metrics.ttft_compliance = False
        convergence_algorithm.current_metrics.cost_compliance = False

        mock_utilization_tracker.get_underutilized_gpus.return_value = ["gpu-1"]

        # Mock capacity scaler to avoid real method calls
        convergence_algorithm.capacity_scaler.evaluate_scaling_decision = Mock(
            return_value=(ScalingDecision.SCALE_DOWN, "Cost optimization")
        )

        action = convergence_algorithm.decide_action(
            mock_utilization_tracker, mock_workload_generator
        )

        # Should prioritize cost optimization due to higher severity
        assert action is not None
        assert action.action_type == ActionType.SCALE_DOWN


class TestIntegration:
    """Integration tests for SLO convergence system."""

    def test_full_convergence_cycle(self):
        """Test complete convergence cycle."""
        # Create configuration
        slo_config = SLOConfig(ttft_p95_ms=500, error_rate_percent=0.1, tokens_per_second=1000)
        technology_config = TechnologyConfig(
            gpu_types={"nvidia-a100": GPUType("nvidia-a100", 80, 3.00)}
        )
        workload_config = WorkloadConfig(baseline_qps=100, spike_multiplier=2.0)

        # Create algorithm
        algorithm = SLOConvergenceAlgorithm(slo_config, technology_config, workload_config)

        # Create test metrics showing SLO violation (need 25+ for P95 calculation)
        base_time = time.time()
        token_metrics = []
        for i in range(25):
            token_metrics.append(
                TokenMetrics(
                    model_name="test-model",
                    tokens_generated=1000,
                    start_time=base_time - 1.0 + (i * 0.01),
                    first_token_time=base_time
                    - 0.4
                    + (i * 0.01),  # 600ms TTFT (violates 500ms target)
                    completion_time=base_time + (i * 0.01),
                    gpu_type="nvidia-a100",
                )
            )

        gpu_metrics = {"gpu-0": {"utilization": 95.0}}

        # Update metrics
        algorithm.update_metrics(token_metrics, gpu_metrics, 200.0)

        # Create mock dependencies
        mock_tracker = Mock(spec=UtilizationTracker)
        mock_tracker.get_aggregate_utilization.return_value = 95.0
        mock_tracker.get_underutilized_gpus.return_value = []

        algorithm.capacity_scaler.evaluate_scaling_decision = Mock(
            return_value=(ScalingDecision.SCALE_UP, "High utilization")
        )

        mock_workload_generator = Mock(spec=WorkloadGenerator)
        mock_workload_generator.get_current_qps.return_value = 200.0

        # Decide action
        action = algorithm.decide_action(mock_tracker, mock_workload_generator)

        # Should recommend scaling up due to TTFT violation
        assert action is not None
        assert action.action_type == ActionType.SCALE_UP

        # Execute action
        success = algorithm.execute_action(action)
        assert success is True

        # Check that action was recorded
        assert len(algorithm.action_history) == 1
        assert algorithm.action_history[0] == action

        # Get status
        status = algorithm.get_convergence_status()
        assert status["recent_actions"] == 1
        assert status["last_action"] == action.description
