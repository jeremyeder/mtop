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
from typing import Any, Dict, List, Optional

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
            batch_delay = 1.0 / target_tps * tokens_per_batch
            metrics.tokens_generated += tokens_per_batch
            metrics.tokens_consumed += int(tokens_per_batch * 1.2)  # Input tokens

            # Add realistic queue depth simulation
            metrics.queue_depth = max(0, random.randint(0, 5) - i // 2)

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
            elif model_name in self._metrics:
                del self._metrics[model_name]

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

            return {
                "total_models": len(self._metrics),
                "completed_models": len(completed_metrics),
                "total_tokens_generated": total_tokens_generated,
                "total_tokens_consumed": total_tokens_consumed,
                "total_queue_depth": total_queue_depth,
                "avg_tokens_per_second": avg_tps,
                "avg_ttft_ms": avg_ttft,
            }


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
