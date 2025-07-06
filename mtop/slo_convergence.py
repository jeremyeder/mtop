#!/usr/bin/env python3
"""
Autonomous SLO convergence algorithm for cost and performance optimization.

This module implements the core autonomous convergence system that demonstrates
how llm-d optimizes for cost and performance targets while maintaining SLO compliance.
"""

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional

from config_loader import SLOConfig, TechnologyConfig, WorkloadConfig
from mtop.token_metrics import CostCalculator, TTFTCalculator, TokenMetrics
from mtop.gpu_heartbeat import CapacityScaler, UtilizationTracker, ScalingDecision
from mtop.workload_generator import WorkloadGenerator
from mtop.cost_optimizer import CostOptimizer


class ConvergenceState(Enum):
    """Current state of SLO convergence."""

    CONVERGING = "converging"
    CONVERGED = "converged"
    DIVERGING = "diverging"
    OSCILLATING = "oscillating"
    UNKNOWN = "unknown"


class OptimizationStrategy(Enum):
    """Optimization strategy being used."""

    COST_FIRST = "cost_first"
    PERFORMANCE_FIRST = "performance_first"
    BALANCED = "balanced"
    EMERGENCY = "emergency"


class ActionType(Enum):
    """Types of actions the convergence algorithm can take."""

    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    ADJUST_ALLOCATION = "adjust_allocation"
    REDISTRIBUTE_LOAD = "redistribute_load"
    CHANGE_STRATEGY = "change_strategy"
    NO_ACTION = "no_action"


@dataclass
class ConvergenceMetrics:
    """Current convergence metrics and SLO compliance status."""

    current_ttft_p95: Optional[float] = None  # Current P95 TTFT (ms)
    target_ttft_p95: float = 500.0  # Target P95 TTFT (ms)
    current_cost_per_million: Optional[float] = None  # Current cost per million tokens
    target_cost_per_million: float = 25.0  # Target cost per million tokens
    current_throughput: Optional[float] = None  # Current tokens per second
    target_throughput: float = 1000.0  # Target tokens per second

    ttft_compliance: Optional[bool] = None
    cost_compliance: Optional[bool] = None
    throughput_compliance: Optional[bool] = None

    convergence_score: float = 0.0  # Overall convergence score (0-1)
    stability_score: float = 0.0  # Stability score (0-1)

    def __post_init__(self):
        """Validate convergence metrics."""
        if self.target_ttft_p95 <= 0:
            raise ValueError(f"Target TTFT must be positive, got {self.target_ttft_p95}")
        if self.target_cost_per_million <= 0:
            raise ValueError(f"Target cost must be positive, got {self.target_cost_per_million}")
        if self.target_throughput <= 0:
            raise ValueError(f"Target throughput must be positive, got {self.target_throughput}")


@dataclass
class ConvergenceAction:
    """Represents an action taken by the convergence algorithm."""

    timestamp: float
    action_type: ActionType
    description: str
    reasoning: str
    expected_impact: str
    success: Optional[bool] = None
    actual_impact: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate convergence action."""
        if not self.description:
            raise ValueError("Description cannot be empty")
        if not self.reasoning:
            raise ValueError("Reasoning cannot be empty")
        if not self.expected_impact:
            raise ValueError("Expected impact cannot be empty")


class SLOConvergenceAlgorithm:
    """Core autonomous SLO convergence algorithm."""

    def __init__(
        self,
        slo_config: SLOConfig,
        technology_config: TechnologyConfig,
        workload_config: WorkloadConfig,
    ):
        """Initialize SLO convergence algorithm.

        Args:
            slo_config: SLO targets and constraints
            technology_config: GPU technology specifications
            workload_config: Workload pattern configuration
        """
        self.slo_config = slo_config
        self.technology_config = technology_config
        self.workload_config = workload_config

        # Core metrics and state
        self.current_metrics = ConvergenceMetrics(
            target_ttft_p95=slo_config.ttft_p95_ms, target_throughput=slo_config.tokens_per_second
        )
        self.convergence_state = ConvergenceState.UNKNOWN
        self.optimization_strategy = OptimizationStrategy.BALANCED

        # Action history and decision tracking
        self.action_history: deque = deque(maxlen=100)
        self.metrics_history: deque = deque(maxlen=1000)
        self.decision_lock = Lock()

        # Integration with existing systems
        self.ttft_calculator = TTFTCalculator(slo_config)
        self.cost_calculator = CostCalculator(technology_config)
        self.capacity_scaler = CapacityScaler()
        self.cost_optimizer = CostOptimizer(self.cost_calculator, slo_config, technology_config)

        # Convergence algorithm parameters
        self.convergence_tolerance = 0.05  # 5% tolerance for SLO targets
        self.stability_window = 30  # Measurements for stability analysis
        self.action_cooldown = 60.0  # Minimum seconds between actions
        self.last_action_time = 0.0

        # Adaptive parameters
        self.learning_rate = 0.1
        self.oscillation_damping = 0.8
        self.emergency_threshold = 2.0  # 2x SLO target triggers emergency mode

    def update_metrics(
        self, token_metrics: List[TokenMetrics], gpu_metrics: Dict[str, Any], workload_qps: float
    ) -> None:
        """Update current metrics from system measurements.

        Args:
            token_metrics: Current token generation metrics
            gpu_metrics: Current GPU utilization metrics
            workload_qps: Current workload queries per second
        """
        with self.decision_lock:
            # Update TTFT metrics
            for metrics in token_metrics:
                self.ttft_calculator.record_ttft_from_metrics(metrics)

            self.current_metrics.current_ttft_p95 = self.ttft_calculator.get_p95_latency()

            # Update cost metrics
            if token_metrics:
                total_tokens = sum(m.tokens_generated for m in token_metrics)
                if total_tokens > 0 and token_metrics[0].gpu_type:
                    # Calculate total inference time
                    total_time = sum(
                        (m.completion_time or time.time()) - m.start_time
                        for m in token_metrics
                        if m.completion_time
                    )
                    if total_time > 0:
                        total_cost = self.cost_calculator.calculate_token_cost(
                            total_tokens, token_metrics[0].gpu_type, total_time
                        )
                        self.current_metrics.current_cost_per_million = (
                            total_cost * 1_000_000 / total_tokens
                        )

            # Update throughput metrics
            if token_metrics:
                total_time = sum(
                    (m.completion_time or time.time()) - m.start_time
                    for m in token_metrics
                    if m.completion_time
                )
                total_tokens = sum(m.tokens_generated for m in token_metrics)
                if total_time > 0:
                    self.current_metrics.current_throughput = total_tokens / total_time

            # Update compliance status
            self._update_compliance_status()

            # Update convergence and stability scores
            self._update_convergence_scores()

            # Update cost optimizer with metrics
            self.cost_optimizer.record_cost_metrics(token_metrics, gpu_metrics, workload_qps)

            # Store metrics history
            self.metrics_history.append(
                {
                    "timestamp": time.time(),
                    "ttft_p95": self.current_metrics.current_ttft_p95,
                    "cost_per_million": self.current_metrics.current_cost_per_million,
                    "throughput": self.current_metrics.current_throughput,
                    "workload_qps": workload_qps,
                    "convergence_score": self.current_metrics.convergence_score,
                    "stability_score": self.current_metrics.stability_score,
                }
            )

    def _update_compliance_status(self) -> None:
        """Update SLO compliance status based on current metrics."""
        # TTFT compliance
        if self.current_metrics.current_ttft_p95 is not None:
            self.current_metrics.ttft_compliance = (
                self.current_metrics.current_ttft_p95 <= self.current_metrics.target_ttft_p95
            )

        # Cost compliance
        if self.current_metrics.current_cost_per_million is not None:
            self.current_metrics.cost_compliance = (
                self.current_metrics.current_cost_per_million
                <= self.current_metrics.target_cost_per_million
            )

        # Throughput compliance
        if self.current_metrics.current_throughput is not None:
            self.current_metrics.throughput_compliance = (
                self.current_metrics.current_throughput >= self.current_metrics.target_throughput
            )

    def _update_convergence_scores(self) -> None:
        """Update convergence and stability scores."""
        scores = []

        # TTFT score
        if self.current_metrics.current_ttft_p95 is not None:
            ttft_ratio = (
                self.current_metrics.current_ttft_p95 / self.current_metrics.target_ttft_p95
            )
            ttft_score = max(
                0, 1 - abs(ttft_ratio - 1)
            )  # Score decreases as we deviate from target
            scores.append(ttft_score)

        # Cost score
        if self.current_metrics.current_cost_per_million is not None:
            cost_ratio = (
                self.current_metrics.current_cost_per_million
                / self.current_metrics.target_cost_per_million
            )
            cost_score = max(0, 2 - cost_ratio)  # Better score for lower costs
            scores.append(min(1.0, cost_score))

        # Throughput score
        if self.current_metrics.current_throughput is not None:
            throughput_ratio = (
                self.current_metrics.current_throughput / self.current_metrics.target_throughput
            )
            throughput_score = min(1.0, throughput_ratio)  # Score increases with throughput
            scores.append(throughput_score)

        # Overall convergence score
        if scores:
            self.current_metrics.convergence_score = statistics.mean(scores)

        # Stability score based on recent variance
        self._calculate_stability_score()

    def _calculate_stability_score(self) -> None:
        """Calculate stability score based on recent metric variance."""
        if len(self.metrics_history) < self.stability_window:
            self.current_metrics.stability_score = 0.0
            return

        recent_metrics = list(self.metrics_history)[-self.stability_window :]
        convergence_scores = [
            m["convergence_score"] for m in recent_metrics if m["convergence_score"] > 0
        ]

        if len(convergence_scores) < 5:
            self.current_metrics.stability_score = 0.0
            return

        # Calculate coefficient of variation (lower is more stable)
        mean_score = statistics.mean(convergence_scores)
        if mean_score > 0:
            std_score = statistics.stdev(convergence_scores)
            cv = std_score / mean_score
            self.current_metrics.stability_score = max(0, 1 - cv)
        else:
            self.current_metrics.stability_score = 0.0

    def evaluate_convergence_state(self) -> ConvergenceState:
        """Evaluate current convergence state."""
        if len(self.metrics_history) < 10:
            return ConvergenceState.UNKNOWN

        recent_scores = [
            m["convergence_score"]
            for m in list(self.metrics_history)[-10:]
            if m["convergence_score"] > 0
        ]

        if len(recent_scores) < 5:
            return ConvergenceState.UNKNOWN

        mean_score = statistics.mean(recent_scores)
        std_score = statistics.stdev(recent_scores) if len(recent_scores) > 1 else 0

        # Check for convergence
        if mean_score > 0.9 and std_score < 0.05:
            self.convergence_state = ConvergenceState.CONVERGED
        elif std_score > 0.2:
            # High variance indicates oscillation or divergence
            if self._detect_oscillation():
                self.convergence_state = ConvergenceState.OSCILLATING
            else:
                self.convergence_state = ConvergenceState.DIVERGING
        elif mean_score > statistics.mean(recent_scores[:3]):  # Improving
            self.convergence_state = ConvergenceState.CONVERGING
        else:
            self.convergence_state = ConvergenceState.DIVERGING

        return self.convergence_state

    def _detect_oscillation(self) -> bool:
        """Detect if the system is oscillating around targets."""
        if len(self.metrics_history) < 20:
            return False

        recent_metrics = list(self.metrics_history)[-20:]
        scores = [m["convergence_score"] for m in recent_metrics if m["convergence_score"] > 0]

        if len(scores) < 10:
            return False

        # Look for regular patterns of ups and downs
        direction_changes = 0
        for i in range(1, len(scores) - 1):
            if (scores[i - 1] < scores[i] > scores[i + 1]) or (
                scores[i - 1] > scores[i] < scores[i + 1]
            ):
                direction_changes += 1

        # If more than 30% of points are direction changes, consider it oscillation
        return direction_changes / len(scores) > 0.3

    def decide_action(
        self, utilization_tracker: UtilizationTracker, workload_generator: WorkloadGenerator
    ) -> Optional[ConvergenceAction]:
        """Decide on the next action to take for convergence.

        Args:
            utilization_tracker: Current GPU utilization data
            workload_generator: Current workload pattern information

        Returns:
            Action to take, or None if no action needed
        """
        current_time = time.time()

        # Check cooldown period
        if current_time - self.last_action_time < self.action_cooldown:
            return None

        with self.decision_lock:
            # Update convergence state
            self.evaluate_convergence_state()

            # Determine optimization strategy
            self._adapt_strategy()

            # Decide action based on current state and strategy
            action = self._select_action(utilization_tracker, workload_generator)

            if action:
                self.action_history.append(action)
                self.last_action_time = current_time

            return action

    def _adapt_strategy(self) -> None:
        """Adapt optimization strategy based on current conditions."""
        # Check for emergency conditions
        if (
            self.current_metrics.current_ttft_p95
            and self.current_metrics.current_ttft_p95
            > self.current_metrics.target_ttft_p95 * self.emergency_threshold
        ):
            self.optimization_strategy = OptimizationStrategy.EMERGENCY
            return

        # Analyze recent performance
        if len(self.action_history) >= 3:
            recent_actions = list(self.action_history)[-3:]

            # If recent actions haven't improved convergence, try different strategy
            if all(not action.success for action in recent_actions if action.success is not None):
                if self.optimization_strategy == OptimizationStrategy.COST_FIRST:
                    self.optimization_strategy = OptimizationStrategy.PERFORMANCE_FIRST
                elif self.optimization_strategy == OptimizationStrategy.PERFORMANCE_FIRST:
                    self.optimization_strategy = OptimizationStrategy.BALANCED
                else:
                    self.optimization_strategy = OptimizationStrategy.COST_FIRST

        # Default to balanced strategy
        if self.optimization_strategy not in [OptimizationStrategy.EMERGENCY]:
            if self.convergence_state == ConvergenceState.OSCILLATING:
                self.optimization_strategy = OptimizationStrategy.BALANCED

    def _select_action(
        self, utilization_tracker: UtilizationTracker, workload_generator: WorkloadGenerator
    ) -> Optional[ConvergenceAction]:
        """Select the best action based on current conditions."""

        # Emergency mode: focus on performance
        if self.optimization_strategy == OptimizationStrategy.EMERGENCY:
            return self._emergency_action(utilization_tracker)

        # Get scaling recommendation
        scaling_decision, scaling_reason = self.capacity_scaler.evaluate_scaling_decision(
            utilization_tracker
        )

        # Analyze current compliance
        ttft_violation = self.current_metrics.ttft_compliance is False
        cost_violation = self.current_metrics.cost_compliance is False
        throughput_violation = self.current_metrics.throughput_compliance is False

        # Strategy-based action selection
        if self.optimization_strategy == OptimizationStrategy.PERFORMANCE_FIRST:
            if ttft_violation or throughput_violation:
                return self._performance_improvement_action(scaling_decision, scaling_reason)
            elif cost_violation:
                return self._cost_optimization_action(utilization_tracker)

        elif self.optimization_strategy == OptimizationStrategy.COST_FIRST:
            if cost_violation:
                return self._cost_optimization_action(utilization_tracker)
            elif ttft_violation or throughput_violation:
                return self._performance_improvement_action(scaling_decision, scaling_reason)

        else:  # BALANCED strategy
            # Prioritize based on severity of violations
            violations = []
            if ttft_violation:
                severity = (
                    self.current_metrics.current_ttft_p95 / self.current_metrics.target_ttft_p95
                )
                violations.append(("ttft", severity))
            if cost_violation:
                severity = (
                    self.current_metrics.current_cost_per_million
                    / self.current_metrics.target_cost_per_million
                )
                violations.append(("cost", severity))
            if throughput_violation:
                severity = (
                    self.current_metrics.target_throughput / self.current_metrics.current_throughput
                )
                violations.append(("throughput", severity))

            # Address most severe violation first
            if violations:
                violations.sort(key=lambda x: x[1], reverse=True)
                worst_violation = violations[0][0]

                if worst_violation in ["ttft", "throughput"]:
                    return self._performance_improvement_action(scaling_decision, scaling_reason)
                else:
                    return self._cost_optimization_action(utilization_tracker)

        # If all SLOs are met, optimize for efficiency
        if (
            self.current_metrics.ttft_compliance
            and self.current_metrics.cost_compliance
            and self.current_metrics.throughput_compliance
        ):
            return self._efficiency_optimization_action(utilization_tracker)

        return None

    def _emergency_action(self, utilization_tracker: UtilizationTracker) -> ConvergenceAction:
        """Create emergency action for severe SLO violations."""
        return ConvergenceAction(
            timestamp=time.time(),
            action_type=ActionType.SCALE_UP,
            description="Emergency scaling to address severe TTFT SLO violation",
            reasoning=f"TTFT ({self.current_metrics.current_ttft_p95}ms) exceeds emergency threshold ({self.current_metrics.target_ttft_p95 * self.emergency_threshold}ms)",
            expected_impact="Immediate capacity increase to reduce TTFT latency",
            metadata={
                "strategy": "emergency",
                "target_capacity_increase": 2.0,
                "max_cost_increase": "unlimited",
            },
        )

    def _performance_improvement_action(
        self, scaling_decision: ScalingDecision, reason: str
    ) -> ConvergenceAction:
        """Create action to improve performance metrics."""
        if scaling_decision == ScalingDecision.SCALE_UP:
            return ConvergenceAction(
                timestamp=time.time(),
                action_type=ActionType.SCALE_UP,
                description="Scale up capacity to improve performance",
                reasoning=f"Performance optimization: {reason}",
                expected_impact="Reduced TTFT latency and increased throughput",
                metadata={
                    "strategy": "performance_improvement",
                    "scaling_decision": scaling_decision.value,
                },
            )
        else:
            return ConvergenceAction(
                timestamp=time.time(),
                action_type=ActionType.ADJUST_ALLOCATION,
                description="Adjust resource allocation to improve performance",
                reasoning="Optimize GPU allocation for better performance",
                expected_impact="Improved resource utilization and reduced latency",
                metadata={
                    "strategy": "performance_improvement",
                    "allocation_adjustment": "performance_optimized",
                },
            )

    def _cost_optimization_action(
        self, utilization_tracker: UtilizationTracker
    ) -> ConvergenceAction:
        """Create action to optimize costs."""
        underutilized_gpus = utilization_tracker.get_underutilized_gpus()

        if underutilized_gpus:
            return ConvergenceAction(
                timestamp=time.time(),
                action_type=ActionType.SCALE_DOWN,
                description="Scale down underutilized capacity to reduce costs",
                reasoning=f"Cost optimization: {len(underutilized_gpus)} underutilized GPUs detected",
                expected_impact="Reduced operational costs while maintaining SLO compliance",
                metadata={
                    "strategy": "cost_optimization",
                    "underutilized_gpus": underutilized_gpus,
                    "expected_cost_savings": 0.3,
                },
            )
        else:
            return ConvergenceAction(
                timestamp=time.time(),
                action_type=ActionType.REDISTRIBUTE_LOAD,
                description="Redistribute load to optimize cost efficiency",
                reasoning="Load redistribution for better cost per token ratio",
                expected_impact="Improved cost efficiency through better resource utilization",
                metadata={"strategy": "cost_optimization", "redistribution_type": "cost_aware"},
            )

    def _efficiency_optimization_action(
        self, utilization_tracker: UtilizationTracker
    ) -> Optional[ConvergenceAction]:
        """Create action to optimize overall efficiency when SLOs are met."""
        avg_utilization = utilization_tracker.get_aggregate_utilization()

        if avg_utilization and avg_utilization < 60:
            return ConvergenceAction(
                timestamp=time.time(),
                action_type=ActionType.SCALE_DOWN,
                description="Optimize efficiency by right-sizing capacity",
                reasoning="All SLOs met, optimize for efficiency",
                expected_impact="Maintained SLO compliance with improved cost efficiency",
                metadata={
                    "strategy": "efficiency_optimization",
                    "current_utilization": avg_utilization,
                    "target_utilization": 75,
                },
            )

        return None

    def execute_action(self, action: ConvergenceAction) -> bool:
        """Execute a convergence action.

        Args:
            action: Action to execute

        Returns:
            True if action was executed successfully
        """
        try:
            # Log action execution
            print(f"Executing action: {action.description}")
            print(f"Reasoning: {action.reasoning}")

            # Simulate action execution based on type
            if action.action_type == ActionType.SCALE_UP:
                # In real implementation, this would trigger actual scaling
                print("Triggering scale up operation...")
                action.success = True
                action.actual_impact = "Capacity increased by 50%"

            elif action.action_type == ActionType.SCALE_DOWN:
                print("Triggering scale down operation...")
                action.success = True
                action.actual_impact = "Capacity reduced by 25%, cost savings 30%"

            elif action.action_type == ActionType.ADJUST_ALLOCATION:
                print("Adjusting resource allocation...")
                action.success = True
                action.actual_impact = "Resource allocation optimized"

            elif action.action_type == ActionType.REDISTRIBUTE_LOAD:
                print("Redistributing workload...")
                action.success = True
                action.actual_impact = "Load redistributed for better efficiency"

            elif action.action_type == ActionType.CHANGE_STRATEGY:
                print("Changing optimization strategy...")
                action.success = True
                action.actual_impact = f"Strategy changed to {self.optimization_strategy.value}"

            else:
                action.success = False
                action.actual_impact = "No action taken"

            return action.success

        except Exception as e:
            action.success = False
            action.actual_impact = f"Action failed: {str(e)}"
            return False

    def get_convergence_status(self) -> Dict[str, Any]:
        """Get current convergence status and metrics.

        Returns:
            Dictionary with convergence status information
        """
        return {
            "convergence_state": self.convergence_state.value,
            "optimization_strategy": self.optimization_strategy.value,
            "metrics": {
                "ttft_p95": self.current_metrics.current_ttft_p95,
                "cost_per_million": self.current_metrics.current_cost_per_million,
                "throughput": self.current_metrics.current_throughput,
                "convergence_score": self.current_metrics.convergence_score,
                "stability_score": self.current_metrics.stability_score,
            },
            "compliance": {
                "ttft": self.current_metrics.ttft_compliance,
                "cost": self.current_metrics.cost_compliance,
                "throughput": self.current_metrics.throughput_compliance,
            },
            "targets": {
                "ttft_p95": self.current_metrics.target_ttft_p95,
                "cost_per_million": self.current_metrics.target_cost_per_million,
                "throughput": self.current_metrics.target_throughput,
            },
            "recent_actions": len(self.action_history),
            "last_action": self.action_history[-1].description if self.action_history else None,
        }
