#!/usr/bin/env python3
"""
Cost optimization logic for autonomous SLO convergence.

This module extends the existing cost calculation systems with intelligent
cost optimization and trade-off analysis for maintaining SLO compliance
while minimizing operational costs.
"""

import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Dict, List

from config_loader import SLOConfig, TechnologyConfig
from mtop.gpu_heartbeat import GPUMetrics
from mtop.token_metrics import CostCalculator, TokenMetrics


class OptimizationObjective(Enum):
    """Cost optimization objectives."""

    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_PERFORMANCE = "maximize_performance"
    BALANCED = "balanced"
    MAINTAIN_SLO = "maintain_slo"


class CostEfficiencyStrategy(Enum):
    """Cost efficiency strategies."""

    RIGHT_SIZE_CAPACITY = "right_size_capacity"
    WORKLOAD_CONSOLIDATION = "workload_consolidation"
    GPU_TYPE_OPTIMIZATION = "gpu_type_optimization"
    DYNAMIC_SCALING = "dynamic_scaling"
    IDLE_RESOURCE_REDUCTION = "idle_resource_reduction"


@dataclass
class CostOptimization:
    """Represents a cost optimization opportunity."""

    strategy: CostEfficiencyStrategy
    estimated_savings: float  # Annual savings in dollars
    confidence_score: float  # Confidence in savings estimate (0-1)
    implementation_effort: str  # "low", "medium", "high"
    risk_level: str  # "low", "medium", "high"
    description: str
    prerequisites: List[str] = field(default_factory=list)
    estimated_impact_time: float = 300.0  # Seconds to see impact

    def __post_init__(self):
        """Validate cost optimization."""
        if self.estimated_savings < 0:
            raise ValueError(f"Estimated savings cannot be negative, got {self.estimated_savings}")
        if not 0 <= self.confidence_score <= 1:
            raise ValueError(f"Confidence score must be 0-1, got {self.confidence_score}")
        if self.implementation_effort not in ["low", "medium", "high"]:
            raise ValueError(
                f"Implementation effort must be low/medium/high, got {self.implementation_effort}"
            )
        if self.risk_level not in ["low", "medium", "high"]:
            raise ValueError(f"Risk level must be low/medium/high, got {self.risk_level}")


@dataclass
class CostTradeoffAnalysis:
    """Analysis of cost vs performance trade-offs."""

    current_cost_per_million: float
    target_cost_per_million: float
    current_performance_score: float  # 0-1, higher is better
    projected_performance_impact: float  # Change in performance score
    cost_reduction_percentage: float
    slo_compliance_risk: float  # 0-1, higher is more risky
    recommendation: str

    def __post_init__(self):
        """Validate trade-off analysis."""
        if self.current_cost_per_million < 0:
            raise ValueError("Current cost cannot be negative")
        if self.target_cost_per_million < 0:
            raise ValueError("Target cost cannot be negative")
        if not 0 <= self.current_performance_score <= 1:
            raise ValueError("Performance score must be 0-1")
        if not 0 <= self.slo_compliance_risk <= 1:
            raise ValueError("SLO compliance risk must be 0-1")


class CostOptimizer:
    """Advanced cost optimization system with SLO-aware decision making."""

    def __init__(
        self,
        cost_calculator: CostCalculator,
        slo_config: SLOConfig,
        technology_config: TechnologyConfig,
    ):
        """Initialize cost optimizer.

        Args:
            cost_calculator: Existing cost calculation system
            slo_config: SLO targets and constraints
            technology_config: GPU technology specifications
        """
        self.cost_calculator = cost_calculator
        self.slo_config = slo_config
        self.technology_config = technology_config

        # Cost tracking and optimization state
        self.cost_history: deque = deque(maxlen=1000)
        self.optimization_history: deque = deque(maxlen=100)
        self.active_optimizations: List[CostOptimization] = []
        self._lock = Lock()

        # Optimization parameters
        self.cost_target_margin = 0.1  # 10% margin below target
        self.min_confidence_threshold = 0.7  # Minimum confidence for recommendations
        self.max_slo_risk_tolerance = 0.2  # Maximum acceptable SLO risk

        # Cost efficiency tracking
        self.gpu_cost_efficiency: Dict[str, float] = {}
        self.workload_cost_patterns: Dict[str, List[float]] = defaultdict(list)

        # Current state
        self.current_objective = OptimizationObjective.BALANCED
        self.total_annual_savings = 0.0
        self.optimization_opportunities: List[CostOptimization] = []

    def record_cost_metrics(
        self,
        token_metrics: List[TokenMetrics],
        gpu_metrics: Dict[str, GPUMetrics],
        workload_qps: float,
    ) -> None:
        """Record cost metrics for optimization analysis.

        Args:
            token_metrics: Current token generation metrics
            gpu_metrics: Current GPU utilization metrics
            workload_qps: Current workload queries per second
        """
        current_time = time.time()

        with self._lock:
            # Calculate current costs
            total_cost = 0.0
            total_tokens = 0

            for metrics in token_metrics:
                if metrics.gpu_type and metrics.completion_time:
                    duration = metrics.completion_time - metrics.start_time
                    cost = self.cost_calculator.calculate_token_cost(
                        metrics.tokens_generated, metrics.gpu_type, duration
                    )
                    total_cost += cost
                    total_tokens += metrics.tokens_generated

            # Calculate cost per million tokens
            cost_per_million = 0.0
            if total_tokens > 0:
                cost_per_million = (total_cost * 1_000_000) / total_tokens

            # Calculate GPU efficiency metrics
            self._update_gpu_efficiency(gpu_metrics, total_cost, workload_qps)

            # Record historical data
            gpu_utilization = {}
            for gpu_id, metrics in gpu_metrics.items():
                # Handle both GPUMetrics objects and dict representations
                if hasattr(metrics, "utilization_percent"):
                    gpu_utilization[gpu_id] = metrics.utilization_percent
                elif isinstance(metrics, dict) and "utilization" in metrics:
                    gpu_utilization[gpu_id] = metrics["utilization"]
                elif isinstance(metrics, dict) and "utilization_percent" in metrics:
                    gpu_utilization[gpu_id] = metrics["utilization_percent"]
                else:
                    gpu_utilization[gpu_id] = 0.0

            cost_record = {
                "timestamp": current_time,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "cost_per_million": cost_per_million,
                "workload_qps": workload_qps,
                "gpu_utilization": gpu_utilization,
            }

            self.cost_history.append(cost_record)

            # Update workload cost patterns
            workload_pattern = self._classify_workload_pattern(workload_qps)
            self.workload_cost_patterns[workload_pattern].append(cost_per_million)

    def _update_gpu_efficiency(
        self, gpu_metrics: Dict[str, Any], total_cost: float, workload_qps: float
    ) -> None:
        """Update GPU cost efficiency metrics."""
        if not gpu_metrics or total_cost == 0:
            return

        # Calculate cost efficiency per GPU
        for gpu_id, metrics in gpu_metrics.items():
            # Handle both GPUMetrics objects and dict representations
            if hasattr(metrics, "utilization_percent"):
                utilization = metrics.utilization_percent
            elif isinstance(metrics, dict) and "utilization" in metrics:
                utilization = metrics["utilization"]
            elif isinstance(metrics, dict) and "utilization_percent" in metrics:
                utilization = metrics["utilization_percent"]
            else:
                continue  # Skip if we can't get utilization

            if utilization > 0:
                # Efficiency = (utilization * throughput) / cost_contribution
                cost_contribution = total_cost / len(gpu_metrics)  # Simple allocation
                efficiency = (utilization * workload_qps) / (cost_contribution * 100)
                self.gpu_cost_efficiency[gpu_id] = efficiency

    def _classify_workload_pattern(self, workload_qps: float) -> str:
        """Classify current workload pattern for cost analysis."""
        if len(self.cost_history) < 5:
            return "baseline"

        recent_qps = [record["workload_qps"] for record in list(self.cost_history)[-5:]]
        avg_qps = statistics.mean(recent_qps)
        std_qps = statistics.stdev(recent_qps) if len(recent_qps) > 1 else 0

        # Classify based on variance and magnitude
        if std_qps / avg_qps > 0.3:  # High variance
            return "spike_pattern"
        elif workload_qps > avg_qps * 1.5:
            return "high_load"
        elif workload_qps < avg_qps * 0.7:
            return "low_load"
        else:
            return "baseline"

    def analyze_cost_optimization_opportunities(self) -> List[CostOptimization]:
        """Analyze current system for cost optimization opportunities.

        Returns:
            List of cost optimization opportunities ranked by potential savings
        """
        opportunities = []

        if len(self.cost_history) < 10:
            return opportunities

        with self._lock:
            # Analyze recent cost trends
            recent_costs = list(self.cost_history)[-20:]

            # Check for right-sizing opportunities
            opportunities.extend(self._analyze_right_sizing_opportunities(recent_costs))

            # Check for GPU type optimization
            opportunities.extend(self._analyze_gpu_type_optimization())

            # Check for idle resource reduction
            opportunities.extend(self._analyze_idle_resource_opportunities(recent_costs))

            # Check for workload consolidation
            opportunities.extend(self._analyze_workload_consolidation_opportunities())

            # Sort by estimated savings (descending)
            opportunities.sort(key=lambda x: x.estimated_savings, reverse=True)

            self.optimization_opportunities = opportunities

        return opportunities

    def _analyze_right_sizing_opportunities(
        self, recent_costs: List[Dict]
    ) -> List[CostOptimization]:
        """Analyze right-sizing opportunities based on utilization patterns."""
        opportunities = []

        if not recent_costs:
            return opportunities

        # Calculate average utilization
        total_utilization = 0.0
        total_gpus = 0

        for record in recent_costs:
            gpu_utils = record.get("gpu_utilization", {})
            if gpu_utils:
                total_utilization += sum(gpu_utils.values())
                total_gpus += len(gpu_utils)

        if total_gpus == 0:
            return opportunities

        avg_utilization = total_utilization / total_gpus

        # Check for over-provisioning
        if avg_utilization < 60:
            potential_reduction = (60 - avg_utilization) / 100  # Percentage reduction
            avg_cost = statistics.mean(
                [r["cost_per_million"] for r in recent_costs if r["cost_per_million"] > 0]
            )

            if avg_cost > 0:
                annual_savings = avg_cost * potential_reduction * 365 * 24  # Rough calculation

                opportunities.append(
                    CostOptimization(
                        strategy=CostEfficiencyStrategy.RIGHT_SIZE_CAPACITY,
                        estimated_savings=annual_savings,
                        confidence_score=0.8,
                        implementation_effort="medium",
                        risk_level="low",
                        description=f"Reduce capacity by {potential_reduction*100:.1f}% based on {avg_utilization:.1f}% average utilization",
                        prerequisites=["Load balancing verification", "Peak traffic analysis"],
                        estimated_impact_time=600.0,
                    )
                )

        return opportunities

    def _analyze_gpu_type_optimization(self) -> List[CostOptimization]:
        """Analyze GPU type optimization opportunities."""
        opportunities = []

        # Compare cost efficiency across GPU types
        current_gpu_type = None

        # Get current GPU types from technology config
        for gpu_type_name, gpu_info in self.technology_config.gpu_types.items():
            if current_gpu_type is None:
                current_gpu_type = gpu_type_name

            # Check if switching would be beneficial
            if (
                gpu_info.hourly_cost
                < self.technology_config.gpu_types[current_gpu_type].hourly_cost
            ):
                cost_difference = (
                    self.technology_config.gpu_types[current_gpu_type].hourly_cost
                    - gpu_info.hourly_cost
                )
                annual_savings = cost_difference * 24 * 365

                opportunities.append(
                    CostOptimization(
                        strategy=CostEfficiencyStrategy.GPU_TYPE_OPTIMIZATION,
                        estimated_savings=annual_savings,
                        confidence_score=0.6,
                        implementation_effort="high",
                        risk_level="medium",
                        description=f"Switch from {current_gpu_type} to {gpu_type_name} for ${cost_difference:.2f}/hour savings",
                        prerequisites=["Performance validation", "Migration planning"],
                        estimated_impact_time=1800.0,
                    )
                )

        return opportunities

    def _analyze_idle_resource_opportunities(
        self, recent_costs: List[Dict]
    ) -> List[CostOptimization]:
        """Analyze opportunities to reduce idle resources."""
        opportunities = []

        # Look for periods of low utilization
        idle_periods = []
        for record in recent_costs:
            gpu_utils = record.get("gpu_utilization", {})
            if gpu_utils:
                avg_util = statistics.mean(gpu_utils.values())
                if avg_util < 20:  # Consider < 20% as idle
                    idle_periods.append(record)

        if len(idle_periods) > len(recent_costs) * 0.3:  # More than 30% idle time
            avg_cost_during_idle = statistics.mean(
                [r["cost_per_million"] for r in idle_periods if r["cost_per_million"] > 0]
            )

            if avg_cost_during_idle > 0:
                # Estimate savings from automatic scaling down during idle
                potential_savings = (
                    avg_cost_during_idle * 0.7 * (len(idle_periods) / len(recent_costs))
                )
                annual_savings = potential_savings * 365 * 24

                opportunities.append(
                    CostOptimization(
                        strategy=CostEfficiencyStrategy.IDLE_RESOURCE_REDUCTION,
                        estimated_savings=annual_savings,
                        confidence_score=0.9,
                        implementation_effort="low",
                        risk_level="low",
                        description=f"Implement auto-scaling to reduce resources during {len(idle_periods)} idle periods detected",
                        prerequisites=["Auto-scaling configuration"],
                        estimated_impact_time=300.0,
                    )
                )

        return opportunities

    def _analyze_workload_consolidation_opportunities(self) -> List[CostOptimization]:
        """Analyze workload consolidation opportunities."""
        opportunities = []

        # Check if multiple workload patterns could be consolidated
        pattern_costs = {}
        for pattern, costs in self.workload_cost_patterns.items():
            if costs:
                pattern_costs[pattern] = statistics.mean(costs)

        if len(pattern_costs) > 2:
            # Look for patterns with similar costs that could be consolidated
            sorted_patterns = sorted(pattern_costs.items(), key=lambda x: x[1])

            if len(sorted_patterns) >= 2:
                pattern1, cost1 = sorted_patterns[0]
                pattern2, cost2 = sorted_patterns[1]

                if abs(cost1 - cost2) / max(cost1, cost2) < 0.2:  # Within 20% cost difference
                    estimated_savings = min(cost1, cost2) * 0.15 * 365 * 24  # 15% efficiency gain

                    opportunities.append(
                        CostOptimization(
                            strategy=CostEfficiencyStrategy.WORKLOAD_CONSOLIDATION,
                            estimated_savings=estimated_savings,
                            confidence_score=0.7,
                            implementation_effort="medium",
                            risk_level="medium",
                            description=f"Consolidate {pattern1} and {pattern2} workload patterns for efficiency",
                            prerequisites=["Resource isolation analysis", "Performance testing"],
                            estimated_impact_time=900.0,
                        )
                    )

        return opportunities

    def perform_cost_tradeoff_analysis(
        self, target_cost_reduction: float, current_performance_metrics: Dict[str, float]
    ) -> CostTradeoffAnalysis:
        """Perform detailed cost vs performance trade-off analysis.

        Args:
            target_cost_reduction: Desired cost reduction percentage (0-1)
            current_performance_metrics: Current performance metrics

        Returns:
            Cost trade-off analysis with recommendations
        """
        if not self.cost_history:
            raise ValueError("Insufficient cost history for analysis")

        recent_cost = self.cost_history[-1]["cost_per_million"]
        target_cost = recent_cost * (1 - target_cost_reduction)

        # Calculate current performance score
        current_performance_score = self._calculate_performance_score(current_performance_metrics)

        # Estimate performance impact based on cost reduction
        performance_impact = self._estimate_performance_impact(target_cost_reduction)

        # Calculate SLO compliance risk
        slo_risk = self._calculate_slo_compliance_risk(
            target_cost_reduction, current_performance_metrics
        )

        # Generate recommendation
        recommendation = self._generate_tradeoff_recommendation(
            target_cost_reduction, performance_impact, slo_risk
        )

        return CostTradeoffAnalysis(
            current_cost_per_million=recent_cost,
            target_cost_per_million=target_cost,
            current_performance_score=current_performance_score,
            projected_performance_impact=performance_impact,
            cost_reduction_percentage=target_cost_reduction * 100,
            slo_compliance_risk=slo_risk,
            recommendation=recommendation,
        )

    def _calculate_performance_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall performance score from metrics."""
        score = 0.0
        weight_sum = 0.0

        # TTFT component (lower is better)
        if "ttft_p95" in metrics:
            ttft_score = max(0, 1 - (metrics["ttft_p95"] / self.slo_config.ttft_p95_ms))
            score += ttft_score * 0.4  # 40% weight
            weight_sum += 0.4

        # Throughput component (higher is better)
        if "throughput" in metrics:
            throughput_score = min(1, metrics["throughput"] / self.slo_config.tokens_per_second)
            score += throughput_score * 0.4  # 40% weight
            weight_sum += 0.4

        # Error rate component (lower is better)
        if "error_rate" in metrics:
            error_score = max(0, 1 - (metrics["error_rate"] / self.slo_config.error_rate_percent))
            score += error_score * 0.2  # 20% weight
            weight_sum += 0.2

        return score / weight_sum if weight_sum > 0 else 0.0

    def _estimate_performance_impact(self, cost_reduction: float) -> float:
        """Estimate performance impact from cost reduction."""
        # Generally, cost reduction leads to some performance degradation
        # This is a simplified model - in reality this would be more sophisticated
        base_impact = cost_reduction * 0.5  # 50% of cost reduction affects performance

        # Factor in diminishing returns
        impact_factor = 1.0 + (cost_reduction**1.5)

        return -base_impact * impact_factor  # Negative because performance decreases

    def _calculate_slo_compliance_risk(
        self, cost_reduction: float, current_metrics: Dict[str, float]
    ) -> float:
        """Calculate risk of SLO non-compliance from cost reduction."""
        risk = 0.0

        # TTFT risk
        if "ttft_p95" in current_metrics:
            current_ttft_margin = (
                self.slo_config.ttft_p95_ms - current_metrics["ttft_p95"]
            ) / self.slo_config.ttft_p95_ms
            ttft_risk = max(0, cost_reduction - current_ttft_margin)
            risk += ttft_risk * 0.5

        # Throughput risk
        if "throughput" in current_metrics:
            current_throughput_margin = (
                current_metrics["throughput"] - self.slo_config.tokens_per_second
            ) / self.slo_config.tokens_per_second
            throughput_risk = max(0, cost_reduction - current_throughput_margin)
            risk += throughput_risk * 0.3

        # General risk factor based on aggressive cost reduction
        if cost_reduction > 0.3:  # More than 30% reduction is inherently risky
            risk += (cost_reduction - 0.3) * 0.5

        return min(1.0, risk)  # Cap at 100% risk

    def _generate_tradeoff_recommendation(
        self, cost_reduction: float, performance_impact: float, slo_risk: float
    ) -> str:
        """Generate recommendation based on trade-off analysis."""
        if slo_risk > self.max_slo_risk_tolerance:
            return f"HIGH RISK: {cost_reduction*100:.1f}% cost reduction has {slo_risk*100:.1f}% SLO risk. Consider smaller reduction."

        if abs(performance_impact) > 0.2:
            return f"MODERATE RISK: {cost_reduction*100:.1f}% cost reduction may reduce performance by {abs(performance_impact)*100:.1f}%. Monitor closely."

        if cost_reduction > 0.15:
            return f"PROCEED WITH CAUTION: {cost_reduction*100:.1f}% cost reduction appears feasible with {slo_risk*100:.1f}% SLO risk."

        return f"RECOMMENDED: {cost_reduction*100:.1f}% cost reduction is low-risk with minimal performance impact."

    def get_cost_optimization_status(self) -> Dict[str, Any]:
        """Get current cost optimization status and metrics.

        Returns:
            Dictionary with cost optimization status
        """
        with self._lock:
            recent_costs = list(self.cost_history)[-10:] if self.cost_history else []

            current_cost_per_million = 0.0
            avg_cost_per_million = 0.0

            if recent_costs:
                costs = [r["cost_per_million"] for r in recent_costs if r["cost_per_million"] > 0]
                if costs:
                    current_cost_per_million = costs[-1]
                    avg_cost_per_million = statistics.mean(costs)

            return {
                "current_cost_per_million": current_cost_per_million,
                "average_cost_per_million": avg_cost_per_million,
                "target_cost_per_million": 25.0,  # From SLO config
                "cost_compliance": (
                    current_cost_per_million <= 25.0 if current_cost_per_million > 0 else None
                ),
                "optimization_opportunities": len(self.optimization_opportunities),
                "total_potential_savings": sum(
                    opt.estimated_savings for opt in self.optimization_opportunities
                ),
                "active_optimizations": len(self.active_optimizations),
                "optimization_objective": self.current_objective.value,
                "gpu_efficiency_scores": dict(self.gpu_cost_efficiency),
                "workload_patterns": {
                    pattern: len(costs) for pattern, costs in self.workload_cost_patterns.items()
                },
                "historical_data_points": len(self.cost_history),
            }

    def implement_optimization(self, optimization: CostOptimization) -> bool:
        """Implement a cost optimization.

        Args:
            optimization: Cost optimization to implement

        Returns:
            True if implementation started successfully
        """
        try:
            print(f"Implementing cost optimization: {optimization.description}")
            print(f"Strategy: {optimization.strategy.value}")
            print(f"Estimated annual savings: ${optimization.estimated_savings:.2f}")
            print(f"Implementation effort: {optimization.implementation_effort}")
            print(f"Risk level: {optimization.risk_level}")

            # Add to active optimizations
            with self._lock:
                self.active_optimizations.append(optimization)

                # Record in optimization history
                self.optimization_history.append(
                    {
                        "timestamp": time.time(),
                        "strategy": optimization.strategy.value,
                        "estimated_savings": optimization.estimated_savings,
                        "confidence_score": optimization.confidence_score,
                        "implementation_status": "started",
                    }
                )

            return True

        except Exception as e:
            print(f"Failed to implement optimization: {str(e)}")
            return False
