#!/usr/bin/env python3
"""
Workload pattern generator for SLO convergence demonstrations.

This module provides realistic workload simulation including traffic spikes,
model deployment events, and configurable load patterns for testing autonomous
SLO convergence capabilities.
"""

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional

from .config_loader import SLOConfig, WorkloadConfig


class WorkloadType(Enum):
    """Types of workload patterns."""

    BASELINE = "baseline"
    SPIKE = "spike"
    DEPLOYMENT = "deployment"
    RAMP_UP = "ramp_up"
    RAMP_DOWN = "ramp_down"
    SUSTAINED = "sustained"


class EventType(Enum):
    """Types of workload events."""

    TRAFFIC_SPIKE = "traffic_spike"
    MODEL_DEPLOYMENT = "model_deployment"
    SCALE_EVENT = "scale_event"
    MAINTENANCE = "maintenance"


@dataclass
class WorkloadEvent:
    """Represents a workload event that affects traffic patterns."""

    event_type: EventType
    start_time: float
    duration: float
    magnitude: float
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate workload event parameters."""
        if self.duration <= 0:
            raise ValueError(f"Duration must be positive, got {self.duration}")
        if self.magnitude < 0:
            raise ValueError(f"Magnitude cannot be negative, got {self.magnitude}")
        if not self.description:
            raise ValueError("Description cannot be empty")


@dataclass
class SpikePattern:
    """Traffic spike pattern configuration."""

    magnitude: float  # Multiplier for traffic increase (e.g., 3.5 = 3.5x traffic)
    ramp_time: float  # Time to reach peak magnitude (seconds)
    duration: float  # Duration at peak magnitude (seconds)
    cooldown_time: float  # Time to return to baseline (seconds)
    jitter_factor: float = 0.1  # Random variation factor (0-1)

    def __post_init__(self):
        """Validate spike pattern configuration."""
        if self.magnitude < 1.0:
            raise ValueError(f"Spike magnitude must be >= 1.0, got {self.magnitude}")
        if self.ramp_time <= 0:
            raise ValueError(f"Ramp time must be positive, got {self.ramp_time}")
        if self.duration <= 0:
            raise ValueError(f"Duration must be positive, got {self.duration}")
        if self.cooldown_time <= 0:
            raise ValueError(f"Cooldown time must be positive, got {self.cooldown_time}")
        if not 0 <= self.jitter_factor <= 1:
            raise ValueError(f"Jitter factor must be 0-1, got {self.jitter_factor}")


@dataclass
class DeploymentEvent:
    """Model deployment event configuration."""

    model_name: str
    deployment_time: float  # Time for deployment to complete (seconds)
    traffic_shift_percentage: float  # Percentage of traffic to shift (0-100)
    resource_overhead: float  # Additional resource usage during deployment (0-1)
    canary_percentage: float = 10.0  # Initial canary traffic percentage

    def __post_init__(self):
        """Validate deployment event configuration."""
        if not self.model_name:
            raise ValueError("Model name cannot be empty")
        if self.deployment_time <= 0:
            raise ValueError(f"Deployment time must be positive, got {self.deployment_time}")
        if not 0 <= self.traffic_shift_percentage <= 100:
            raise ValueError(f"Traffic shift must be 0-100%, got {self.traffic_shift_percentage}")
        if not 0 <= self.resource_overhead <= 1:
            raise ValueError(f"Resource overhead must be 0-1, got {self.resource_overhead}")
        if not 0 <= self.canary_percentage <= 100:
            raise ValueError(f"Canary percentage must be 0-100%, got {self.canary_percentage}")


class WorkloadGenerator:
    """Main workload pattern generation system."""

    def __init__(self, workload_config: WorkloadConfig, slo_config: Optional[SLOConfig] = None):
        """Initialize workload generator with configuration."""
        self.workload_config = workload_config
        self.slo_config = slo_config
        self.current_qps = workload_config.baseline_qps
        self.start_time = time.time()
        self.active_events: List[WorkloadEvent] = []
        self.event_history: List[WorkloadEvent] = []
        self._lock = Lock()

        # Default spike pattern based on requirements (3.5x, 30s ramp, 120s duration)
        self.default_spike = SpikePattern(
            magnitude=3.5, ramp_time=30.0, duration=120.0, cooldown_time=60.0, jitter_factor=0.1
        )

    def get_current_qps(self) -> float:
        """Get current queries per second based on active patterns."""
        with self._lock:
            current_time = time.time()
            base_qps = self.workload_config.baseline_qps
            total_multiplier = 1.0

            # Process active events
            for event in self.active_events[:]:  # Copy to avoid modification during iteration
                if current_time > event.start_time + event.duration:
                    # Event has ended
                    self.active_events.remove(event)
                    self.event_history.append(event)
                    continue

                # Calculate event contribution
                event_multiplier = self._calculate_event_multiplier(event, current_time)
                total_multiplier *= event_multiplier

            # Apply jitter for realism
            jitter = 1.0 + (random.random() - 0.5) * 0.1  # ±5% jitter
            self.current_qps = base_qps * total_multiplier * jitter

            return max(0, self.current_qps)

    def _calculate_event_multiplier(self, event: WorkloadEvent, current_time: float) -> float:
        """Calculate the multiplier effect of an event at the current time."""
        elapsed = current_time - event.start_time

        if event.event_type == EventType.TRAFFIC_SPIKE:
            return self._calculate_spike_multiplier(elapsed, event.magnitude, event.duration)
        elif event.event_type == EventType.MODEL_DEPLOYMENT:
            return self._calculate_deployment_multiplier(elapsed, event.duration, event.magnitude)
        elif event.event_type == EventType.SCALE_EVENT:
            return self._calculate_scale_multiplier(elapsed, event.magnitude, event.duration)

        return 1.0  # Default no effect

    def _calculate_spike_multiplier(
        self, elapsed: float, magnitude: float, duration: float
    ) -> float:
        """Calculate traffic spike multiplier based on elapsed time."""
        # Use default spike pattern timing
        ramp_time = self.default_spike.ramp_time
        cooldown_time = self.default_spike.cooldown_time
        peak_duration = duration - cooldown_time

        if elapsed <= ramp_time:
            # Ramp up phase - smooth curve
            progress = elapsed / ramp_time
            # Use sigmoid-like curve for smooth ramp
            smooth_progress = 0.5 * (1 + math.tanh(4 * (progress - 0.5)))
            return 1.0 + (magnitude - 1.0) * smooth_progress
        elif elapsed <= peak_duration:
            # Peak phase with minor variations
            jitter = 1.0 + (random.random() - 0.5) * self.default_spike.jitter_factor
            return magnitude * jitter
        elif elapsed <= duration:
            # Cooldown phase
            cooldown_progress = (elapsed - peak_duration) / cooldown_time
            # Smooth decay back to baseline
            decay_factor = 1.0 - 0.5 * (1 + math.tanh(4 * (cooldown_progress - 0.5)))
            return 1.0 + (magnitude - 1.0) * decay_factor

        return 1.0  # Back to baseline

    def _calculate_deployment_multiplier(
        self, elapsed: float, duration: float, overhead: float
    ) -> float:
        """Calculate deployment event multiplier."""
        if elapsed <= duration:
            # During deployment, there's resource overhead
            progress = elapsed / duration
            # Overhead decreases as deployment progresses
            current_overhead = overhead * (1.0 - progress)
            return 1.0 + current_overhead

        return 1.0  # Deployment complete

    def _calculate_scale_multiplier(
        self, elapsed: float, magnitude: float, duration: float
    ) -> float:
        """Calculate scaling event multiplier."""
        if elapsed <= duration:
            # Scaling events have immediate but temporary impact
            return magnitude

        return 1.0  # Scaling complete

    def trigger_traffic_spike(self, spike_pattern: Optional[SpikePattern] = None) -> WorkloadEvent:
        """Trigger a traffic spike event."""
        if spike_pattern is None:
            spike_pattern = self.default_spike

        event = WorkloadEvent(
            event_type=EventType.TRAFFIC_SPIKE,
            start_time=time.time(),
            duration=spike_pattern.ramp_time + spike_pattern.duration + spike_pattern.cooldown_time,
            magnitude=spike_pattern.magnitude,
            description=f"Traffic spike: {spike_pattern.magnitude}x for {spike_pattern.duration}s",
            metadata={
                "spike_pattern": spike_pattern,
                "baseline_qps": self.workload_config.baseline_qps,
            },
        )

        with self._lock:
            self.active_events.append(event)

        return event

    def trigger_model_deployment(self, deployment: DeploymentEvent) -> WorkloadEvent:
        """Trigger a model deployment event."""
        event = WorkloadEvent(
            event_type=EventType.MODEL_DEPLOYMENT,
            start_time=time.time(),
            duration=deployment.deployment_time,
            magnitude=deployment.resource_overhead,
            description=f"Model deployment: {deployment.model_name} ({deployment.traffic_shift_percentage}% traffic)",
            metadata={"deployment": deployment, "canary_started": time.time()},
        )

        with self._lock:
            self.active_events.append(event)

        return event

    def trigger_scale_event(self, scale_factor: float, duration: float = 60.0) -> WorkloadEvent:
        """Trigger a scaling event."""
        event = WorkloadEvent(
            event_type=EventType.SCALE_EVENT,
            start_time=time.time(),
            duration=duration,
            magnitude=scale_factor,
            description=f"Scale event: {scale_factor}x capacity for {duration}s",
            metadata={"scale_factor": scale_factor, "trigger_reason": "autonomous_slo_convergence"},
        )

        with self._lock:
            self.active_events.append(event)

        return event

    def get_active_events(self) -> List[WorkloadEvent]:
        """Get currently active workload events."""
        with self._lock:
            return self.active_events.copy()

    def get_event_history(self) -> List[WorkloadEvent]:
        """Get historical workload events."""
        with self._lock:
            return self.event_history.copy()

    def reset(self):
        """Reset workload generator to baseline state."""
        with self._lock:
            self.active_events.clear()
            self.event_history.clear()
            self.current_qps = self.workload_config.baseline_qps
            self.start_time = time.time()


class LoadController:
    """Interactive load control interface for workload adjustment."""

    def __init__(self, workload_generator: WorkloadGenerator):
        """Initialize load controller with workload generator."""
        self.workload_generator = workload_generator
        self.manual_multiplier = 1.0
        self._lock = Lock()

    def set_manual_multiplier(self, multiplier: float):
        """Set manual load multiplier."""
        if multiplier < 0:
            raise ValueError(f"Manual multiplier cannot be negative, got {multiplier}")

        with self._lock:
            self.manual_multiplier = multiplier

    def get_manual_multiplier(self) -> float:
        """Get current manual load multiplier."""
        with self._lock:
            return self.manual_multiplier

    def get_effective_qps(self) -> float:
        """Get effective QPS including manual adjustments."""
        base_qps = self.workload_generator.get_current_qps()
        with self._lock:
            return base_qps * self.manual_multiplier

    def create_custom_spike(self, magnitude: float, duration: float) -> SpikePattern:
        """Create custom spike pattern for interactive testing."""
        return SpikePattern(
            magnitude=magnitude,
            ramp_time=min(30.0, duration * 0.25),  # 25% of duration for ramp
            duration=duration * 0.5,  # 50% of duration at peak
            cooldown_time=min(60.0, duration * 0.25),  # 25% of duration for cooldown
            jitter_factor=0.1,
        )

    def create_deployment_scenario(
        self, model_name: str, traffic_percentage: float = 50.0
    ) -> DeploymentEvent:
        """Create deployment scenario for interactive testing."""
        return DeploymentEvent(
            model_name=model_name,
            deployment_time=180.0,  # 3 minutes deployment
            traffic_shift_percentage=traffic_percentage,
            resource_overhead=0.3,  # 30% overhead during deployment
            canary_percentage=10.0,
        )

    def simulate_realistic_load(self, duration: float = 300.0):
        """Simulate realistic load patterns over time."""
        # Create varied load pattern
        events = []

        # Initial small spike
        small_spike = self.create_custom_spike(1.5, 60.0)
        events.append(self.workload_generator.trigger_traffic_spike(small_spike))

        # Model deployment after 2 minutes
        deployment = self.create_deployment_scenario("gpt-4-optimized", 75.0)
        time.sleep(120)  # Wait 2 minutes
        events.append(self.workload_generator.trigger_model_deployment(deployment))

        # Major spike after deployment
        major_spike = self.create_custom_spike(3.5, 180.0)
        time.sleep(60)  # Wait 1 minute after deployment starts
        events.append(self.workload_generator.trigger_traffic_spike(major_spike))

        return events
