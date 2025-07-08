#!/usr/bin/env python3
"""
GPU capacity heartbeat engine for LLM inference monitoring.

This module simulates GPU capacity scaling with heartbeat visualization,
providing realistic GPU utilization patterns and capacity management.
"""

import math
import random
import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

from .config_loader import TechnologyConfig


class HeartbeatStrength(Enum):
    """Heartbeat strength levels based on GPU load."""

    MINIMAL = "minimal"  # <30% utilization
    STEADY = "steady"  # 30-60% utilization
    STRONG = "strong"  # 60-85% utilization
    INTENSE = "intense"  # >85% utilization
    CRITICAL = "critical"  # >95% utilization


class ScalingDecision(Enum):
    """Capacity scaling decisions."""

    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"
    SCALE_UP = "scale_up"
    URGENT_SCALE = "urgent_scale"


@dataclass
class GPUMetrics:
    """Real-time GPU utilization and capacity metrics."""

    gpu_id: str
    utilization_percent: float = 0.0
    vram_used_gb: float = 0.0
    vram_total_gb: float = 80.0
    temperature_c: float = 65.0
    power_watts: float = 300.0
    last_updated: float = field(default_factory=time.time)

    def __post_init__(self):
        """Validate GPU metrics."""
        if not self.gpu_id:
            raise ValueError("gpu_id cannot be empty")

        if not 0 <= self.utilization_percent <= 100:
            raise ValueError(f"utilization_percent must be 0-100, got {self.utilization_percent}")

        if self.vram_used_gb < 0:
            raise ValueError(f"vram_used_gb cannot be negative, got {self.vram_used_gb}")

        if self.vram_total_gb <= 0:
            raise ValueError(f"vram_total_gb must be positive, got {self.vram_total_gb}")

        if self.vram_used_gb > self.vram_total_gb:
            raise ValueError(
                f"vram_used_gb ({self.vram_used_gb}) cannot exceed total ({self.vram_total_gb})"
            )

    def get_vram_utilization(self) -> float:
        """Calculate VRAM utilization percentage."""
        if self.vram_total_gb == 0:
            return 0.0
        return (self.vram_used_gb / self.vram_total_gb) * 100.0

    def is_overloaded(self) -> bool:
        """Check if GPU is overloaded (>95% utilization)."""
        return self.utilization_percent > 95.0

    def is_underutilized(self) -> bool:
        """Check if GPU is underutilized (<30% utilization)."""
        return self.utilization_percent < 30.0


@dataclass
class HeartbeatPulse:
    """Individual heartbeat pulse characteristics."""

    strength: HeartbeatStrength
    frequency_bpm: float  # Beats per minute
    color: str  # Hex color code
    intensity: float  # 0.0 to 1.0
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        """Validate pulse characteristics."""
        if not 0 <= self.intensity <= 1.0:
            raise ValueError(f"intensity must be 0-1, got {self.intensity}")

        if self.frequency_bpm <= 0:
            raise ValueError(f"frequency_bpm must be positive, got {self.frequency_bpm}")


class UtilizationTracker:
    """Tracks GPU utilization patterns and calculates aggregated metrics."""

    def __init__(self, window_size: int = 100):
        """Initialize utilization tracker.

        Args:
            window_size: Number of measurements to keep in rolling window
        """
        self.window_size = window_size
        self._metrics: Dict[str, GPUMetrics] = {}
        self._utilization_history: Dict[str, deque] = {}
        self._lock = Lock()

    def update_gpu_metrics(self, gpu_metrics: GPUMetrics) -> None:
        """Update metrics for a specific GPU.

        Args:
            gpu_metrics: Current GPU metrics
        """
        with self._lock:
            gpu_id = gpu_metrics.gpu_id
            self._metrics[gpu_id] = gpu_metrics

            # Update utilization history
            if gpu_id not in self._utilization_history:
                self._utilization_history[gpu_id] = deque(maxlen=self.window_size)

            self._utilization_history[gpu_id].append(gpu_metrics.utilization_percent)

    def get_aggregate_utilization(self) -> float:
        """Calculate average utilization across all GPUs.

        Returns:
            Average utilization percentage across all GPUs
        """
        with self._lock:
            if not self._metrics:
                return 0.0

            total_util = sum(gpu.utilization_percent for gpu in self._metrics.values())
            return total_util / len(self._metrics)

    def get_gpu_metrics(self, gpu_id: str) -> Optional[GPUMetrics]:
        """Get current metrics for specific GPU.

        Args:
            gpu_id: GPU identifier

        Returns:
            GPU metrics or None if not found
        """
        with self._lock:
            return self._metrics.get(gpu_id)

    def get_all_gpu_metrics(self) -> Dict[str, GPUMetrics]:
        """Get all current GPU metrics.

        Returns:
            Dictionary mapping GPU IDs to metrics
        """
        with self._lock:
            return self._metrics.copy()

    def get_utilization_trend(self, gpu_id: str) -> Optional[str]:
        """Analyze utilization trend for specific GPU.

        Args:
            gpu_id: GPU identifier

        Returns:
            Trend direction: "increasing", "decreasing", "stable", or None
        """
        with self._lock:
            if gpu_id not in self._utilization_history:
                return None

            history = list(self._utilization_history[gpu_id])
            if len(history) < 10:  # Need sufficient data
                return None

            # Calculate trend using linear regression slope
            x_values = list(range(len(history)))
            y_values = history

            n = len(history)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)

            # Calculate slope
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

            # Determine trend based on slope
            if slope > 2.0:  # Increasing more than 2% per measurement
                return "increasing"
            elif slope < -2.0:  # Decreasing more than 2% per measurement
                return "decreasing"
            else:
                return "stable"

    def get_overloaded_gpus(self) -> List[str]:
        """Get list of GPUs that are overloaded.

        Returns:
            List of GPU IDs with >95% utilization
        """
        with self._lock:
            return [gpu_id for gpu_id, metrics in self._metrics.items() if metrics.is_overloaded()]

    def get_underutilized_gpus(self) -> List[str]:
        """Get list of GPUs that are underutilized.

        Returns:
            List of GPU IDs with <30% utilization
        """
        with self._lock:
            return [
                gpu_id for gpu_id, metrics in self._metrics.items() if metrics.is_underutilized()
            ]


class CapacityScaler:
    """Makes capacity scaling decisions based on GPU utilization patterns."""

    def __init__(
        self,
        scale_up_threshold: float = 80.0,
        scale_down_threshold: float = 40.0,
        urgent_threshold: float = 95.0,
    ):
        """Initialize capacity scaler.

        Args:
            scale_up_threshold: Utilization % to trigger scale up
            scale_down_threshold: Utilization % to trigger scale down
            urgent_threshold: Utilization % to trigger urgent scaling
        """
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.urgent_threshold = urgent_threshold
        self._last_scaling_time = 0.0
        self._cooldown_period = 300.0  # 5 minutes between scaling actions

    def evaluate_scaling_decision(self, tracker: UtilizationTracker) -> Tuple[ScalingDecision, str]:
        """Evaluate whether to scale capacity up or down.

        Args:
            tracker: UtilizationTracker with current GPU metrics

        Returns:
            Tuple of (scaling_decision, reasoning)
        """
        current_time = time.time()
        aggregate_util = tracker.get_aggregate_utilization()
        overloaded_gpus = tracker.get_overloaded_gpus()
        underutilized_gpus = tracker.get_underutilized_gpus()

        # Check for urgent scaling (override cooldown)
        if aggregate_util >= self.urgent_threshold or len(overloaded_gpus) > 0:
            self._last_scaling_time = current_time
            return (
                ScalingDecision.URGENT_SCALE,
                f"Urgent: {len(overloaded_gpus)} GPUs overloaded, avg util {aggregate_util:.1f}%",
            )

        # Check cooldown period
        if current_time - self._last_scaling_time < self._cooldown_period:
            return (
                ScalingDecision.MAINTAIN,
                f"Cooldown active ({self._cooldown_period - (current_time - self._last_scaling_time):.0f}s remaining)",
            )

        # Normal scaling decisions
        if aggregate_util >= self.scale_up_threshold:
            self._last_scaling_time = current_time
            return (
                ScalingDecision.SCALE_UP,
                f"Scale up: avg utilization {aggregate_util:.1f}% > {self.scale_up_threshold}%",
            )

        elif aggregate_util <= self.scale_down_threshold and len(underutilized_gpus) > 1:
            self._last_scaling_time = current_time
            return (
                ScalingDecision.SCALE_DOWN,
                f"Scale down: avg utilization {aggregate_util:.1f}% < {self.scale_down_threshold}%",
            )

        else:
            return (
                ScalingDecision.MAINTAIN,
                f"Maintain: utilization {aggregate_util:.1f}% within optimal range",
            )


class HeartbeatVisualizer:
    """Generates heartbeat pulse characteristics based on GPU load."""

    def __init__(self):
        """Initialize heartbeat visualizer."""
        self._pulse_history: deque = deque(maxlen=60)  # Last 60 pulses
        self._lock = Lock()

    def generate_pulse(self, aggregate_utilization: float, gpu_count: int = 1) -> HeartbeatPulse:
        """Generate heartbeat pulse based on current utilization.

        Args:
            aggregate_utilization: Average utilization across GPUs
            gpu_count: Number of GPUs in cluster

        Returns:
            HeartbeatPulse with appropriate characteristics
        """
        # Determine heartbeat strength
        if aggregate_utilization >= 95.0:
            strength = HeartbeatStrength.CRITICAL
            frequency = 140 + (aggregate_utilization - 95) * 2  # 140-150 BPM
            color = "#FF0000"  # Red
            intensity = 1.0
        elif aggregate_utilization >= 85.0:
            strength = HeartbeatStrength.INTENSE
            frequency = 120 + (aggregate_utilization - 85)  # 120-130 BPM
            color = "#FF6600"  # Orange-red
            intensity = 0.9
        elif aggregate_utilization >= 60.0:
            strength = HeartbeatStrength.STRONG
            frequency = 80 + (aggregate_utilization - 60) * 1.6  # 80-120 BPM
            color = "#FFA500"  # Orange
            intensity = 0.7
        elif aggregate_utilization >= 30.0:
            strength = HeartbeatStrength.STEADY
            frequency = 60 + (aggregate_utilization - 30)  # 60-90 BPM
            color = "#00FF00"  # Green
            intensity = 0.5
        else:
            strength = HeartbeatStrength.MINIMAL
            frequency = 40 + aggregate_utilization * 0.67  # 40-60 BPM
            color = "#0000FF"  # Blue
            intensity = 0.3

        # Add some realistic variation
        frequency += random.uniform(-5, 5)
        intensity += random.uniform(-0.1, 0.1)
        intensity = max(0.1, min(1.0, intensity))

        # Scale frequency based on GPU count (more GPUs = faster heartbeat)
        frequency *= 1.0 + (gpu_count - 1) * 0.1

        pulse = HeartbeatPulse(
            strength=strength, frequency_bpm=frequency, color=color, intensity=intensity
        )

        with self._lock:
            self._pulse_history.append(pulse)

        return pulse

    def get_pulse_statistics(self) -> Dict[str, Any]:
        """Get statistics about recent heartbeat pulses.

        Returns:
            Dictionary with pulse statistics
        """
        with self._lock:
            if not self._pulse_history:
                return {}

            frequencies = [pulse.frequency_bpm for pulse in self._pulse_history]
            intensities = [pulse.intensity for pulse in self._pulse_history]

            return {
                "pulse_count": len(self._pulse_history),
                "avg_frequency_bpm": statistics.mean(frequencies),
                "min_frequency_bpm": min(frequencies),
                "max_frequency_bpm": max(frequencies),
                "avg_intensity": statistics.mean(intensities),
                "latest_pulse": {
                    "strength": self._pulse_history[-1].strength.value,
                    "frequency_bpm": self._pulse_history[-1].frequency_bpm,
                    "color": self._pulse_history[-1].color,
                    "intensity": self._pulse_history[-1].intensity,
                },
            }


class GPUHeartbeat:
    """Main GPU heartbeat engine coordinating all components."""

    def __init__(self, technology_config: Optional[TechnologyConfig] = None):
        """Initialize GPU heartbeat engine.

        Args:
            technology_config: Technology configuration for GPU types
        """
        self.technology_config = technology_config
        self.tracker = UtilizationTracker()
        self.scaler = CapacityScaler()
        self.visualizer = HeartbeatVisualizer()
        self._active_gpus: Dict[str, str] = {}  # gpu_id -> gpu_type
        self._lock = Lock()

    def add_gpu(self, gpu_id: str, gpu_type: str, vram_total_gb: Optional[float] = None) -> None:
        """Add GPU to monitoring system.

        Args:
            gpu_id: Unique GPU identifier
            gpu_type: GPU type (e.g., 'nvidia-h100')
            vram_total_gb: Total VRAM in GB (auto-detected if None)
        """
        with self._lock:
            self._active_gpus[gpu_id] = gpu_type

            # Auto-detect VRAM if not provided
            if vram_total_gb is None and self.technology_config:
                if gpu_type in self.technology_config.gpu_types:
                    # Use memory_gb from technology config
                    vram_total_gb = self.technology_config.gpu_types[gpu_type].memory_gb
                else:
                    vram_total_gb = 80.0  # Default fallback
            elif vram_total_gb is None:
                vram_total_gb = 80.0  # Default fallback

            # Initialize with baseline metrics
            initial_metrics = GPUMetrics(
                gpu_id=gpu_id,
                utilization_percent=random.uniform(20, 40),  # Realistic idle baseline
                vram_used_gb=random.uniform(5, 15),  # Some baseline usage
                vram_total_gb=vram_total_gb,
                temperature_c=random.uniform(60, 70),
                power_watts=random.uniform(200, 350),
            )

            self.tracker.update_gpu_metrics(initial_metrics)

    def remove_gpu(self, gpu_id: str) -> None:
        """Remove GPU from monitoring system.

        Args:
            gpu_id: GPU identifier to remove
        """
        with self._lock:
            if gpu_id in self._active_gpus:
                del self._active_gpus[gpu_id]

    def simulate_workload(
        self, target_utilization: float = 70.0, duration_seconds: float = 60.0
    ) -> None:
        """Simulate GPU workload with realistic utilization patterns.

        Args:
            target_utilization: Target average utilization percentage
            duration_seconds: Duration of simulation in seconds
        """
        start_time = time.time()
        update_interval = 2.0  # Update every 2 seconds

        max_iterations = int(duration_seconds / 0.1) + 100  # Safety valve
        iteration = 0

        while time.time() - start_time < duration_seconds and iteration < max_iterations:
            current_time = time.time()
            elapsed = current_time - start_time
            iteration += 1

            # Create realistic utilization wave pattern
            base_utilization = target_utilization
            wave_amplitude = 15.0  # ±15% variation
            wave_frequency = 0.1  # Slow wave

            for gpu_id in list(self._active_gpus.keys()):
                # Add individual GPU variation
                gpu_variation = random.uniform(-10, 10)
                wave_offset = random.uniform(0, 2 * math.pi)

                utilization = (
                    base_utilization
                    + wave_amplitude
                    * math.sin(2 * math.pi * wave_frequency * elapsed + wave_offset)
                    + gpu_variation
                )

                # Keep within reasonable bounds
                utilization = max(10.0, min(98.0, utilization))

                # Simulate memory usage that correlates with utilization
                max_vram = 80.0  # Default to H100
                if (
                    self.technology_config
                    and self._active_gpus[gpu_id] in self.technology_config.gpu_types
                ):
                    max_vram = self.technology_config.gpu_types[self._active_gpus[gpu_id]].memory_gb

                vram_used = (utilization / 100.0) * max_vram * random.uniform(0.6, 0.9)

                # Create updated metrics
                updated_metrics = GPUMetrics(
                    gpu_id=gpu_id,
                    utilization_percent=utilization,
                    vram_used_gb=vram_used,
                    vram_total_gb=max_vram,
                    temperature_c=65
                    + (utilization - 50) * 0.5,  # Temperature correlates with usage
                    power_watts=200 + utilization * 3.0,  # Power correlates with usage
                )

                self.tracker.update_gpu_metrics(updated_metrics)

            time.sleep(update_interval)

    def get_current_heartbeat(self) -> HeartbeatPulse:
        """Get current heartbeat pulse based on GPU state.

        Returns:
            Current heartbeat pulse characteristics
        """
        aggregate_util = self.tracker.get_aggregate_utilization()
        gpu_count = len(self._active_gpus)

        return self.visualizer.generate_pulse(aggregate_util, gpu_count)

    def get_scaling_recommendation(self) -> Tuple[ScalingDecision, str]:
        """Get current capacity scaling recommendation.

        Returns:
            Tuple of (scaling_decision, reasoning)
        """
        return self.scaler.evaluate_scaling_decision(self.tracker)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status.

        Returns:
            Dictionary with complete system status
        """
        all_metrics = self.tracker.get_all_gpu_metrics()
        scaling_decision, scaling_reason = self.get_scaling_recommendation()
        current_pulse = self.get_current_heartbeat()
        pulse_stats = self.visualizer.get_pulse_statistics()

        return {
            "timestamp": time.time(),
            "gpu_count": len(self._active_gpus),
            "aggregate_utilization": self.tracker.get_aggregate_utilization(),
            "overloaded_gpus": self.tracker.get_overloaded_gpus(),
            "underutilized_gpus": self.tracker.get_underutilized_gpus(),
            "scaling_decision": scaling_decision.value,
            "scaling_reason": scaling_reason,
            "current_pulse": {
                "strength": current_pulse.strength.value,
                "frequency_bpm": current_pulse.frequency_bpm,
                "color": current_pulse.color,
                "intensity": current_pulse.intensity,
            },
            "pulse_statistics": pulse_stats,
            "gpu_details": {
                gpu_id: {
                    "utilization_percent": metrics.utilization_percent,
                    "vram_used_gb": metrics.vram_used_gb,
                    "vram_total_gb": metrics.vram_total_gb,
                    "vram_utilization": metrics.get_vram_utilization(),
                    "temperature_c": metrics.temperature_c,
                    "power_watts": metrics.power_watts,
                    "trend": self.tracker.get_utilization_trend(gpu_id),
                    "overloaded": metrics.is_overloaded(),
                    "underutilized": metrics.is_underutilized(),
                }
                for gpu_id, metrics in all_metrics.items()
            },
        }


def create_gpu_heartbeat(technology_config: Optional[TechnologyConfig] = None) -> GPUHeartbeat:
    """Factory function to create a configured GPUHeartbeat engine.

    Args:
        technology_config: Technology configuration for GPU types

    Returns:
        Configured GPUHeartbeat instance
    """
    return GPUHeartbeat(technology_config)


def simulate_multi_gpu_cluster(
    gpu_count: int = 4,
    target_utilization: float = 70.0,
    duration_seconds: float = 30.0,
    technology_config: Optional[TechnologyConfig] = None,
) -> GPUHeartbeat:
    """Create and simulate a multi-GPU cluster for demonstration.

    Args:
        gpu_count: Number of GPUs to simulate
        target_utilization: Target average utilization
        duration_seconds: Simulation duration
        technology_config: Technology configuration

    Returns:
        GPUHeartbeat engine with simulated cluster
    """
    heartbeat = create_gpu_heartbeat(technology_config)

    # Add GPUs with different types
    gpu_types = ["nvidia-h100", "nvidia-a100", "nvidia-v100"]
    for i in range(gpu_count):
        gpu_type = gpu_types[i % len(gpu_types)]
        heartbeat.add_gpu(f"gpu-{i:02d}", gpu_type)

    # Run simulation
    heartbeat.simulate_workload(target_utilization, duration_seconds)

    return heartbeat
