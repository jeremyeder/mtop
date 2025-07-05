#!/usr/bin/env python3
"""
Token metrics tracking system for LLM inference monitoring.

This module provides core token generation and consumption tracking with support
for time-to-first-token (TTFT), cost calculations, and queue depth monitoring.
"""

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, Optional

from config_loader import SLOConfig, TechnologyConfig


@dataclass
class TokenMetrics:
    """Core token metrics tracking for LLM inference operations.

    Tracks token generation, consumption, timing metrics, and resource utilization
    for LLM inference services. Thread-safe for concurrent access.
    """

    model_name: str
    tokens_generated: int = 0
    tokens_consumed: int = 0
    start_time: float = field(default_factory=time.time)
    first_token_time: Optional[float] = None
    completion_time: Optional[float] = None
    queue_depth: int = 0
    gpu_type: str = ""

    def __post_init__(self):
        """Validate token metrics configuration."""
        if not self.model_name or not isinstance(self.model_name, str):
            raise ValueError("model_name must be a non-empty string")

        if self.tokens_generated < 0:
            raise ValueError(f"tokens_generated cannot be negative, got {self.tokens_generated}")

        if self.tokens_consumed < 0:
            raise ValueError(f"tokens_consumed cannot be negative, got {self.tokens_consumed}")

        if self.start_time <= 0:
            raise ValueError(f"start_time must be positive, got {self.start_time}")

        if self.first_token_time is not None and self.first_token_time < self.start_time:
            raise ValueError("first_token_time cannot be before start_time")

        if self.completion_time is not None and self.completion_time < self.start_time:
            raise ValueError("completion_time cannot be before start_time")

        if self.queue_depth < 0:
            raise ValueError(f"queue_depth cannot be negative, got {self.queue_depth}")

    def get_ttft_ms(self) -> Optional[float]:
        """Calculate time to first token in milliseconds."""
        if self.first_token_time is None:
            return None
        return (self.first_token_time - self.start_time) * 1000

    def get_total_time_ms(self) -> Optional[float]:
        """Calculate total completion time in milliseconds."""
        if self.completion_time is None:
            return None
        return (self.completion_time - self.start_time) * 1000

    def get_tokens_per_second(self) -> float:
        """Calculate current tokens per second throughput."""
        if self.completion_time is None:
            # Use current time if not completed
            elapsed = time.time() - self.start_time
        else:
            elapsed = self.completion_time - self.start_time

        if elapsed <= 0:
            return 0.0

        return self.tokens_generated / elapsed

    def is_completed(self) -> bool:
        """Check if the token generation is completed."""
        return self.completion_time is not None


@dataclass
class TTFTCalculator:
    """Time-to-first-token (TTFT) calculator with SLO validation and statistical analysis.

    Tracks TTFT measurements, calculates percentiles, and validates against SLO targets.
    Thread-safe for concurrent access across multiple token generation operations.
    """

    slo_config: SLOConfig
    measurements: deque = field(default_factory=lambda: deque(maxlen=1000))  # Rolling window
    _lock: Lock = field(default_factory=Lock)

    def __post_init__(self):
        """Validate TTFT calculator configuration."""
        if not isinstance(self.slo_config, SLOConfig):
            raise ValueError("slo_config must be a valid SLOConfig instance")

    def record_ttft(self, start_time: float, first_token_time: float) -> float:
        """Record a TTFT measurement.

        Args:
            start_time: Request start timestamp
            first_token_time: First token generation timestamp

        Returns:
            TTFT measurement in milliseconds

        Raises:
            ValueError: If timestamps are invalid
        """
        if first_token_time < start_time:
            raise ValueError("first_token_time cannot be before start_time")

        ttft_ms = (first_token_time - start_time) * 1000

        with self._lock:
            self.measurements.append(ttft_ms)

        return ttft_ms

    def record_ttft_from_metrics(self, metrics: TokenMetrics) -> Optional[float]:
        """Record TTFT from TokenMetrics instance.

        Args:
            metrics: TokenMetrics with timing information

        Returns:
            TTFT measurement in milliseconds, or None if not available
        """
        if metrics.first_token_time is None:
            return None

        return self.record_ttft(metrics.start_time, metrics.first_token_time)

    def get_p95_latency(self) -> Optional[float]:
        """Calculate P95 TTFT latency from measurements.

        Returns:
            P95 latency in milliseconds, or None if insufficient data
        """
        with self._lock:
            if len(self.measurements) < 20:  # Need sufficient data for P95
                return None

            return statistics.quantiles(list(self.measurements), n=20)[18]  # 95th percentile

    def get_p99_latency(self) -> Optional[float]:
        """Calculate P99 TTFT latency from measurements.

        Returns:
            P99 latency in milliseconds, or None if insufficient data
        """
        with self._lock:
            if len(self.measurements) < 100:  # Need more data for P99
                return None

            return statistics.quantiles(list(self.measurements), n=100)[98]  # 99th percentile

    def get_mean_latency(self) -> Optional[float]:
        """Calculate mean TTFT latency from measurements.

        Returns:
            Mean latency in milliseconds, or None if no data
        """
        with self._lock:
            if not self.measurements:
                return None

            return statistics.mean(self.measurements)

    def get_median_latency(self) -> Optional[float]:
        """Calculate median TTFT latency from measurements.

        Returns:
            Median latency in milliseconds, or None if no data
        """
        with self._lock:
            if not self.measurements:
                return None

            return statistics.median(self.measurements)

    def check_slo_compliance(self) -> Optional[bool]:
        """Check if current P95 latency meets SLO target.

        Returns:
            True if compliant, False if not, None if insufficient data
        """
        p95_latency = self.get_p95_latency()
        if p95_latency is None:
            return None

        return p95_latency <= self.slo_config.ttft_p95_ms

    def get_slo_target(self) -> int:
        """Get SLO target for TTFT P95 latency.

        Returns:
            SLO target in milliseconds
        """
        return self.slo_config.ttft_p95_ms

    def get_slo_variance(self) -> Optional[float]:
        """Calculate variance from SLO target as percentage.

        Returns:
            Variance percentage (positive = over target, negative = under target),
            or None if insufficient data
        """
        p95_latency = self.get_p95_latency()
        if p95_latency is None:
            return None

        target = self.slo_config.ttft_p95_ms
        return ((p95_latency - target) / target) * 100

    def get_measurement_count(self) -> int:
        """Get total number of measurements recorded.

        Returns:
            Number of measurements in rolling window
        """
        with self._lock:
            return len(self.measurements)

    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get comprehensive statistics summary.

        Returns:
            Dictionary with all available statistics
        """
        with self._lock:
            if not self.measurements:
                return {
                    "measurement_count": 0,
                    "slo_target_ms": self.slo_config.ttft_p95_ms,
                    "slo_compliant": None,
                }

            measurements_list = list(self.measurements)

            result = {
                "measurement_count": len(measurements_list),
                "slo_target_ms": self.slo_config.ttft_p95_ms,
                "mean_ms": statistics.mean(measurements_list),
                "median_ms": statistics.median(measurements_list),
                "min_ms": min(measurements_list),
                "max_ms": max(measurements_list),
            }

            # Add percentiles if we have enough data
            if len(measurements_list) >= 20:
                result["p95_ms"] = statistics.quantiles(measurements_list, n=20)[18]
                result["slo_compliant"] = result["p95_ms"] <= self.slo_config.ttft_p95_ms
                result["slo_variance_percent"] = (
                    (result["p95_ms"] - self.slo_config.ttft_p95_ms) / self.slo_config.ttft_p95_ms
                ) * 100
            else:
                result["slo_compliant"] = None

            if len(measurements_list) >= 100:
                result["p99_ms"] = statistics.quantiles(measurements_list, n=100)[98]

            return result

    def reset_measurements(self) -> None:
        """Reset all measurements.

        Clears the rolling window of measurements while preserving SLO configuration.
        """
        with self._lock:
            self.measurements.clear()


@dataclass
class CostCalculator:
    """Cost calculation for LLM inference operations using GPU pricing.

    Provides cost-per-million-tokens calculations, real-time cost tracking,
    and cost efficiency metrics based on TechnologyConfig GPU pricing.
    """

    technology_config: TechnologyConfig

    def __post_init__(self):
        """Validate cost calculator configuration."""
        if not isinstance(self.technology_config, TechnologyConfig):
            raise ValueError("technology_config must be a valid TechnologyConfig instance")

    def calculate_token_cost(self, tokens: int, gpu_type: str, duration_seconds: float) -> float:
        """Calculate the cost for generating tokens on a specific GPU type.

        Args:
            tokens: Number of tokens generated
            gpu_type: GPU type used for inference
            duration_seconds: Duration of token generation in seconds

        Returns:
            Cost in dollars for the token generation

        Raises:
            ValueError: If GPU type is not found or invalid parameters
        """
        if tokens < 0:
            raise ValueError(f"tokens cannot be negative, got {tokens}")

        if duration_seconds < 0:
            raise ValueError(f"duration_seconds cannot be negative, got {duration_seconds}")

        if not gpu_type or gpu_type not in self.technology_config.gpu_types:
            raise ValueError(f"gpu_type '{gpu_type}' not found in technology config")

        # Get GPU hourly cost
        gpu_info = self.technology_config.gpu_types[gpu_type]
        hourly_cost = gpu_info.hourly_cost

        # Calculate cost: (duration in hours) * hourly_cost
        duration_hours = duration_seconds / 3600
        total_cost = duration_hours * hourly_cost

        return total_cost

    def get_cost_per_million_tokens(self, gpu_type: str, tokens_per_second: int) -> float:
        """Calculate cost per million tokens for a given GPU type and throughput.

        Args:
            gpu_type: GPU type used for inference
            tokens_per_second: Throughput in tokens per second

        Returns:
            Cost per million tokens in dollars

        Raises:
            ValueError: If GPU type is not found or invalid parameters
        """
        if tokens_per_second <= 0:
            raise ValueError(f"tokens_per_second must be positive, got {tokens_per_second}")

        if not gpu_type or gpu_type not in self.technology_config.gpu_types:
            raise ValueError(f"gpu_type '{gpu_type}' not found in technology config")

        # Get GPU hourly cost
        gpu_info = self.technology_config.gpu_types[gpu_type]
        hourly_cost = gpu_info.hourly_cost

        # Calculate time to generate 1 million tokens
        million_tokens = 1_000_000
        seconds_for_million_tokens = million_tokens / tokens_per_second
        hours_for_million_tokens = seconds_for_million_tokens / 3600

        # Calculate cost for 1 million tokens
        cost_per_million = hours_for_million_tokens * hourly_cost

        return cost_per_million

    def calculate_efficiency_ratio(self, actual_cost: float, target_cost: float) -> float:
        """Calculate cost efficiency ratio compared to target.

        Args:
            actual_cost: Actual cost incurred
            target_cost: Target cost for comparison

        Returns:
            Efficiency ratio (1.0 = target, <1.0 = better than target, >1.0 = worse)

        Raises:
            ValueError: If target_cost is not positive
        """
        if target_cost <= 0:
            raise ValueError(f"target_cost must be positive, got {target_cost}")

        if actual_cost < 0:
            raise ValueError(f"actual_cost cannot be negative, got {actual_cost}")

        return actual_cost / target_cost

    def calculate_cost_from_metrics(self, metrics: TokenMetrics) -> Optional[float]:
        """Calculate cost from TokenMetrics instance.

        Args:
            metrics: TokenMetrics with timing and token information

        Returns:
            Cost in dollars, or None if metrics are incomplete

        Raises:
            ValueError: If GPU type is not found
        """
        if not metrics.is_completed():
            return None

        if not metrics.gpu_type:
            return None

        duration_seconds = metrics.completion_time - metrics.start_time
        return self.calculate_token_cost(
            metrics.tokens_generated, metrics.gpu_type, duration_seconds
        )

    def get_gpu_cost_comparison(self) -> Dict[str, float]:
        """Get cost comparison across all available GPU types.

        Returns:
            Dictionary mapping GPU type to hourly cost
        """
        return {
            gpu_type: gpu_info.hourly_cost
            for gpu_type, gpu_info in self.technology_config.gpu_types.items()
        }

    def get_cheapest_gpu(self) -> Optional[str]:
        """Get the cheapest GPU type available.

        Returns:
            GPU type name with lowest hourly cost, or None if no GPUs available
        """
        if not self.technology_config.gpu_types:
            return None

        return min(
            self.technology_config.gpu_types.keys(),
            key=lambda gpu_type: self.technology_config.gpu_types[gpu_type].hourly_cost,
        )

    def get_most_expensive_gpu(self) -> Optional[str]:
        """Get the most expensive GPU type available.

        Returns:
            GPU type name with highest hourly cost, or None if no GPUs available
        """
        if not self.technology_config.gpu_types:
            return None

        return max(
            self.technology_config.gpu_types.keys(),
            key=lambda gpu_type: self.technology_config.gpu_types[gpu_type].hourly_cost,
        )

    def calculate_cost_savings(self, from_gpu: str, to_gpu: str, duration_seconds: float) -> float:
        """Calculate cost savings when switching GPU types.

        Args:
            from_gpu: Current GPU type
            to_gpu: Target GPU type
            duration_seconds: Duration of inference in seconds

        Returns:
            Cost savings in dollars (positive = savings, negative = additional cost)

        Raises:
            ValueError: If GPU types are not found
        """
        if from_gpu not in self.technology_config.gpu_types:
            raise ValueError(f"from_gpu '{from_gpu}' not found in technology config")

        if to_gpu not in self.technology_config.gpu_types:
            raise ValueError(f"to_gpu '{to_gpu}' not found in technology config")

        if duration_seconds < 0:
            raise ValueError(f"duration_seconds cannot be negative, got {duration_seconds}")

        from_cost = self.technology_config.gpu_types[from_gpu].hourly_cost
        to_cost = self.technology_config.gpu_types[to_gpu].hourly_cost

        duration_hours = duration_seconds / 3600
        cost_difference = (from_cost - to_cost) * duration_hours

        return cost_difference

    def get_cost_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cost statistics for all GPU types.

        Returns:
            Dictionary with cost statistics and comparisons
        """
        if not self.technology_config.gpu_types:
            return {}

        costs = [gpu_info.hourly_cost for gpu_info in self.technology_config.gpu_types.values()]
        gpu_names = list(self.technology_config.gpu_types.keys())

        return {
            "total_gpu_types": len(self.technology_config.gpu_types),
            "cheapest_gpu": self.get_cheapest_gpu(),
            "most_expensive_gpu": self.get_most_expensive_gpu(),
            "min_hourly_cost": min(costs),
            "max_hourly_cost": max(costs),
            "avg_hourly_cost": sum(costs) / len(costs),
            "gpu_types": gpu_names,
            "cost_comparison": self.get_gpu_cost_comparison(),
        }


class TokenTracker:
    """Thread-safe token metrics tracking and simulation system.

    Manages token generation simulation, metrics collection, and provides
    integration with technology and SLO configurations.
    """

    def __init__(
        self,
        technology_config: Optional[TechnologyConfig] = None,
        slo_config: Optional[SLOConfig] = None,
    ):
        """Initialize token tracker with optional configuration.

        Args:
            technology_config: GPU types and capabilities configuration
            slo_config: Service level objectives for performance targets
        """
        self.technology_config = technology_config
        self.slo_config = slo_config
        self._metrics: Dict[str, TokenMetrics] = {}
        self._queue_metrics: Dict[str, "QueueMetrics"] = {}
        self._lock = Lock()

    def create_metrics(self, model_name: str, gpu_type: str = "") -> TokenMetrics:
        """Create new token metrics for a model.

        Args:
            model_name: Name of the LLM model
            gpu_type: GPU type being used for inference

        Returns:
            TokenMetrics instance for tracking
        """
        with self._lock:
            metrics = TokenMetrics(model_name=model_name, gpu_type=gpu_type, start_time=time.time())
            self._metrics[model_name] = metrics
            # Create corresponding queue metrics
            self._queue_metrics[model_name] = QueueMetrics()
            return metrics

    def update_tokens_generated(self, model_name: str, tokens: int) -> None:
        """Update token generation count for a model.

        Args:
            model_name: Name of the model
            tokens: Number of tokens generated
        """
        with self._lock:
            if model_name in self._metrics:
                self._metrics[model_name].tokens_generated += tokens

                # Set first token time if this is the first token
                if (
                    self._metrics[model_name].first_token_time is None
                    and self._metrics[model_name].tokens_generated > 0
                ):
                    self._metrics[model_name].first_token_time = time.time()

    def update_tokens_consumed(self, model_name: str, tokens: int) -> None:
        """Update token consumption count for a model.

        Args:
            model_name: Name of the model
            tokens: Number of tokens consumed
        """
        with self._lock:
            if model_name in self._metrics:
                self._metrics[model_name].tokens_consumed += tokens

    def update_queue_depth(self, model_name: str, depth: int) -> None:
        """Update queue depth for a model.

        Args:
            model_name: Name of the model
            depth: Current queue depth
        """
        with self._lock:
            if model_name in self._metrics:
                self._metrics[model_name].queue_depth = depth
                # Update queue metrics as well
                if model_name in self._queue_metrics:
                    self._queue_metrics[model_name].update_queue_depth(depth)

    def complete_generation(self, model_name: str) -> None:
        """Mark token generation as completed for a model.

        Args:
            model_name: Name of the model
        """
        with self._lock:
            if model_name in self._metrics:
                self._metrics[model_name].completion_time = time.time()

    def get_metrics(self, model_name: str) -> Optional[TokenMetrics]:
        """Get current metrics for a model.

        Args:
            model_name: Name of the model

        Returns:
            TokenMetrics instance or None if not found
        """
        with self._lock:
            return self._metrics.get(model_name)

    def get_all_metrics(self) -> Dict[str, TokenMetrics]:
        """Get all current metrics.

        Returns:
            Dictionary mapping model names to TokenMetrics
        """
        with self._lock:
            return self._metrics.copy()

    def get_queue_metrics(self, model_name: str) -> Optional["QueueMetrics"]:
        """Get queue metrics for a model.

        Args:
            model_name: Name of the model

        Returns:
            QueueMetrics instance or None if not found
        """
        with self._lock:
            return self._queue_metrics.get(model_name)

    def get_all_queue_metrics(self) -> Dict[str, "QueueMetrics"]:
        """Get all current queue metrics.

        Returns:
            Dictionary mapping model names to QueueMetrics
        """
        with self._lock:
            return self._queue_metrics.copy()

    def simulate_token_generation(
        self, model_name: str, target_tokens: int = 100, target_tps: Optional[int] = None
    ) -> TokenMetrics:
        """Simulate token generation for a model based on configuration.

        Args:
            model_name: Name of the model
            target_tokens: Target number of tokens to generate
            target_tps: Target tokens per second (uses SLO config if not provided)

        Returns:
            TokenMetrics with simulated data
        """
        # Use SLO config for target TPS if available
        if target_tps is None and self.slo_config:
            target_tps = self.slo_config.tokens_per_second

        if target_tps is None:
            target_tps = 100  # Default fallback

        # Determine GPU type
        gpu_type = ""
        if self.technology_config and self.technology_config.gpu_types:
            # Use first available GPU type as default
            gpu_type = list(self.technology_config.gpu_types.keys())[0]

        # Create metrics
        metrics = self.create_metrics(model_name, gpu_type)

        # Simulate TTFT (time to first token)
        # Realistic TTFT is usually 50-500ms depending on model size
        import random

        ttft_base = 100  # Base 100ms
        if self.slo_config:
            # Use SLO target as baseline with some variance
            ttft_base = self.slo_config.ttft_p95_ms * 0.7  # 70% of P95 for average

        simulated_ttft = ttft_base + random.uniform(-20, 50)  # Add realistic variance
        metrics.first_token_time = metrics.start_time + (simulated_ttft / 1000)

        # Simulate token generation
        tokens_per_batch = min(10, target_tokens)  # Generate in batches
        batches = target_tokens // tokens_per_batch

        for i in range(batches):
            # Add some realistic delay between batches
            # _batch_delay = 1.0 / target_tps * tokens_per_batch  # Currently unused
            metrics.tokens_generated += tokens_per_batch
            metrics.tokens_consumed += int(tokens_per_batch * 1.2)  # Input tokens

            # Add realistic queue depth simulation
            queue_depth = max(0, random.randint(0, 5) - i // 2)
            metrics.queue_depth = queue_depth
            
            # Update queue metrics with realistic depth progression
            if model_name in self._queue_metrics:
                self._queue_metrics[model_name].update_queue_depth(queue_depth)

        # Complete generation
        total_time = target_tokens / target_tps
        metrics.completion_time = metrics.start_time + total_time

        return metrics

    def reset_metrics(self, model_name: Optional[str] = None) -> None:
        """Reset metrics for a specific model or all models.

        Args:
            model_name: Name of model to reset, or None to reset all
        """
        with self._lock:
            if model_name is None:
                self._metrics.clear()
                self._queue_metrics.clear()
            elif model_name in self._metrics:
                del self._metrics[model_name]
                if model_name in self._queue_metrics:
                    del self._queue_metrics[model_name]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics across all tracked models.

        Returns:
            Dictionary with aggregated statistics
        """
        with self._lock:
            if not self._metrics:
                return {}

            metrics_list = list(self._metrics.values())
            completed_metrics = [m for m in metrics_list if m.is_completed()]

            total_tokens_generated = sum(m.tokens_generated for m in metrics_list)
            total_tokens_consumed = sum(m.tokens_consumed for m in metrics_list)
            total_queue_depth = sum(m.queue_depth for m in metrics_list)

            avg_tps = 0.0
            avg_ttft = 0.0

            if completed_metrics:
                avg_tps = sum(m.get_tokens_per_second() for m in completed_metrics) / len(
                    completed_metrics
                )
                ttft_values = [
                    m.get_ttft_ms() for m in completed_metrics if m.get_ttft_ms() is not None
                ]
                if ttft_values:
                    avg_ttft = sum(ttft_values) / len(ttft_values)

            # Calculate queue metrics statistics
            queue_stats = {}
            if self._queue_metrics:
                all_queue_depths = []
                total_queue_utilization = 0.0
                
                for queue_metric in self._queue_metrics.values():
                    queue_stats_data = queue_metric.get_depth_statistics()
                    if queue_stats_data.get("history_count", 0) > 0:
                        all_queue_depths.append(queue_stats_data["average_depth"])
                        total_queue_utilization += queue_metric.get_queue_utilization()
                
                if all_queue_depths:
                    queue_stats = {
                        "avg_queue_depth": sum(all_queue_depths) / len(all_queue_depths),
                        "avg_queue_utilization_percent": total_queue_utilization / len(self._queue_metrics),
                    }

            result = {
                "total_models": len(self._metrics),
                "completed_models": len(completed_metrics),
                "total_tokens_generated": total_tokens_generated,
                "total_tokens_consumed": total_tokens_consumed,
                "total_queue_depth": total_queue_depth,
                "avg_tokens_per_second": avg_tps,
                "avg_ttft_ms": avg_ttft,
            }
            
            # Add queue statistics if available
            result.update(queue_stats)
            
            return result


def create_token_tracker(
    technology_config: Optional[TechnologyConfig] = None, slo_config: Optional[SLOConfig] = None
) -> TokenTracker:
    """Factory function to create a configured TokenTracker.

    Args:
        technology_config: GPU types and capabilities configuration
        slo_config: Service level objectives for performance targets

    Returns:
        Configured TokenTracker instance
    """
    return TokenTracker(technology_config, slo_config)


def create_ttft_calculator(slo_config: SLOConfig) -> TTFTCalculator:
    """Factory function to create a configured TTFTCalculator.

    Args:
        slo_config: Service level objectives with TTFT targets

    Returns:
        Configured TTFTCalculator instance

    Raises:
        ValueError: If slo_config is None or invalid
    """
    if slo_config is None:
        raise ValueError("slo_config is required for TTFTCalculator")

    return TTFTCalculator(slo_config=slo_config)


def create_cost_calculator(technology_config: TechnologyConfig) -> CostCalculator:
    """Factory function to create a configured CostCalculator.

    Args:
        technology_config: GPU types and pricing configuration

    Returns:
        Configured CostCalculator instance

    Raises:
        ValueError: If technology_config is None or invalid
    """
    if technology_config is None:
        raise ValueError("technology_config is required for CostCalculator")

    return CostCalculator(technology_config=technology_config)


def create_queue_metrics(max_queue_depth: int = 100) -> "QueueMetrics":
    """Factory function to create a configured QueueMetrics.

    Args:
        max_queue_depth: Maximum queue depth for capacity planning

    Returns:
        Configured QueueMetrics instance

    Raises:
        ValueError: If max_queue_depth is not positive
    """
    if max_queue_depth <= 0:
        raise ValueError("max_queue_depth must be positive")

    return QueueMetrics(max_queue_depth=max_queue_depth)


@dataclass
class QueueMetrics:
    """Queue depth tracking and performance impact analysis for LLM inference.
    
    Tracks queue depth over time and analyzes its impact on time-to-first-token (TTFT)
    and overall throughput. Thread-safe for concurrent access.
    """
    
    max_queue_depth: int = 100
    current_depth: int = 0
    depth_history: deque = field(default_factory=lambda: deque(maxlen=1000))  # Rolling window
    _lock: Lock = field(default_factory=Lock)
    
    def __post_init__(self):
        """Validate queue metrics configuration."""
        if self.max_queue_depth <= 0:
            raise ValueError(f"max_queue_depth must be positive, got {self.max_queue_depth}")
        
        if self.current_depth < 0:
            raise ValueError(f"current_depth cannot be negative, got {self.current_depth}")
    
    def update_queue_depth(self, depth: int) -> None:
        """Update current queue depth and add to history.
        
        Args:
            depth: Current queue depth
            
        Raises:
            ValueError: If depth is negative
        """
        if depth < 0:
            raise ValueError(f"depth cannot be negative, got {depth}")
        
        with self._lock:
            self.current_depth = depth
            self.depth_history.append(depth)
    
    def get_current_depth(self) -> int:
        """Get current queue depth.
        
        Returns:
            Current queue depth
        """
        with self._lock:
            return self.current_depth
    
    def get_average_depth(self) -> float:
        """Calculate average queue depth from history.
        
        Returns:
            Average queue depth, or 0.0 if no history
        """
        with self._lock:
            if not self.depth_history:
                return 0.0
            
            return sum(self.depth_history) / len(self.depth_history)
    
    def get_max_depth(self) -> int:
        """Get maximum queue depth from history.
        
        Returns:
            Maximum queue depth, or 0 if no history
        """
        with self._lock:
            if not self.depth_history:
                return 0
            
            return max(self.depth_history)
    
    def get_min_depth(self) -> int:
        """Get minimum queue depth from history.
        
        Returns:
            Minimum queue depth, or 0 if no history
        """
        with self._lock:
            if not self.depth_history:
                return 0
            
            return min(self.depth_history)
    
    def get_depth_impact_on_ttft(self) -> float:
        """Calculate estimated impact of queue depth on TTFT.
        
        Uses a simplified model where deeper queues increase TTFT linearly.
        Real-world impact depends on model size, hardware, and batching strategies.
        
        Returns:
            Estimated TTFT impact in milliseconds based on current depth
        """
        with self._lock:
            if self.current_depth == 0:
                return 0.0
            
            # Simplified impact model: each request in queue adds ~10ms TTFT
            # This is a rough approximation for demo purposes
            base_impact_per_request = 10.0  # ms
            return self.current_depth * base_impact_per_request
    
    def get_depth_percentile(self, percentile: int) -> Optional[float]:
        """Calculate queue depth percentile from history.
        
        Args:
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Queue depth at specified percentile, or None if insufficient data
            
        Raises:
            ValueError: If percentile is not between 0 and 100
        """
        if not 0 <= percentile <= 100:
            raise ValueError(f"percentile must be between 0 and 100, got {percentile}")
        
        with self._lock:
            if len(self.depth_history) < 10:  # Need sufficient data
                return None
            
            depths = sorted(self.depth_history)
            if percentile == 0:
                return float(depths[0])
            elif percentile == 100:
                return float(depths[-1])
            else:
                # Calculate percentile index
                index = (percentile / 100.0) * (len(depths) - 1)
                lower_index = int(index)
                upper_index = min(lower_index + 1, len(depths) - 1)
                
                if lower_index == upper_index:
                    return float(depths[lower_index])
                else:
                    # Linear interpolation
                    weight = index - lower_index
                    return depths[lower_index] * (1 - weight) + depths[upper_index] * weight
    
    def get_depth_statistics(self) -> Dict[str, Any]:
        """Get comprehensive queue depth statistics.
        
        Returns:
            Dictionary with queue depth statistics
        """
        with self._lock:
            if not self.depth_history:
                return {
                    "current_depth": self.current_depth,
                    "max_queue_depth": self.max_queue_depth,
                    "history_count": 0,
                    "estimated_ttft_impact_ms": self.get_depth_impact_on_ttft(),
                }
            
            depths = list(self.depth_history)
            
            result = {
                "current_depth": self.current_depth,
                "max_queue_depth": self.max_queue_depth,
                "history_count": len(depths),
                "average_depth": sum(depths) / len(depths),
                "min_depth": min(depths),
                "max_depth": max(depths),
                "estimated_ttft_impact_ms": self.get_depth_impact_on_ttft(),
            }
            
            # Add percentiles if we have enough data
            if len(depths) >= 10:
                result["p50_depth"] = self.get_depth_percentile(50)
                result["p95_depth"] = self.get_depth_percentile(95)
                result["p99_depth"] = self.get_depth_percentile(99)
            
            return result
    
    def reset_history(self) -> None:
        """Reset queue depth history while preserving current depth.
        
        Clears the rolling window of depth measurements while keeping
        current state and configuration.
        """
        with self._lock:
            self.depth_history.clear()
    
    def is_queue_full(self) -> bool:
        """Check if queue is at maximum capacity.
        
        Returns:
            True if current depth equals max depth
        """
        with self._lock:
            return self.current_depth >= self.max_queue_depth
    
    def get_queue_utilization(self) -> float:
        """Calculate queue utilization as percentage.
        
        Returns:
            Queue utilization percentage (0.0 to 100.0)
        """
        with self._lock:
            if self.max_queue_depth == 0:
                return 0.0
            
            return (self.current_depth / self.max_queue_depth) * 100.0
