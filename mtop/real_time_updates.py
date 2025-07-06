#!/usr/bin/env python3
"""
Real-time metrics streaming and update coordination system.

This module provides live updating capabilities for all visualization components,
with efficient data streaming, synchronized updates, and performance optimization.
"""

import asyncio
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from threading import Event, Lock
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from rich.console import Console
from rich.live import Live

from mtop.executive_view import ExecutiveViewDashboard
from mtop.gpu_heartbeat import GPUHeartbeat
from mtop.heartbeat_visualizer import HeartbeatAnimator
from mtop.slo_convergence import ConvergenceMetrics
from mtop.slo_dashboard import SLODashboard


class UpdateFrequency(Enum):
    """Update frequency levels for different components."""

    REALTIME = 0.1  # 10 Hz - Real-time animations
    HIGH = 0.5  # 2 Hz - Active monitoring
    MEDIUM = 1.0  # 1 Hz - Standard dashboards
    LOW = 5.0  # 0.2 Hz - Executive summaries


class ComponentType(Enum):
    """Types of visualization components."""

    HEARTBEAT_ANIMATOR = "heartbeat_animator"
    SLO_DASHBOARD = "slo_dashboard"
    EXECUTIVE_VIEW = "executive_view"
    CUSTOM = "custom"


@dataclass
class MetricsSnapshot:
    """Complete snapshot of system metrics at a point in time."""

    timestamp: float
    gpu_heartbeat_status: Dict[str, Any]
    convergence_metrics: Optional[ConvergenceMetrics]
    gpu_count: int
    aggregate_utilization: float
    scaling_decision: str
    business_impact_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateConfig:
    """Configuration for component update behavior."""

    component_id: str
    component_type: ComponentType
    update_frequency: UpdateFrequency
    enabled: bool = True
    last_update_time: float = 0.0
    update_count: int = 0
    performance_budget_ms: float = 50.0  # Max 50ms per update


class MetricsStreamer:
    """Streams real-time metrics from GPU heartbeat and convergence systems."""

    def __init__(self, buffer_size: int = 1000):
        """Initialize metrics streamer.

        Args:
            buffer_size: Size of metrics buffer for historical data
        """
        self.buffer_size = buffer_size
        self._metrics_buffer: deque = deque(maxlen=buffer_size)
        self._subscribers: Set[Callable[[MetricsSnapshot], None]] = set()
        self._lock = Lock()
        self._running = False
        self._stream_thread: Optional[threading.Thread] = None

    def subscribe(self, callback: Callable[[MetricsSnapshot], None]) -> None:
        """Subscribe to metrics updates.

        Args:
            callback: Function to call with new metrics snapshots
        """
        with self._lock:
            self._subscribers.add(callback)

    def unsubscribe(self, callback: Callable[[MetricsSnapshot], None]) -> None:
        """Unsubscribe from metrics updates.

        Args:
            callback: Function to remove from subscribers
        """
        with self._lock:
            self._subscribers.discard(callback)

    def start_streaming(
        self, gpu_heartbeat: GPUHeartbeat, convergence_metrics: Optional[ConvergenceMetrics] = None
    ) -> None:
        """Start streaming metrics from sources.

        Args:
            gpu_heartbeat: GPU heartbeat engine to stream from
            convergence_metrics: Optional convergence metrics
        """
        if self._running:
            return

        self._running = True
        self._stream_thread = threading.Thread(
            target=self._stream_loop, args=(gpu_heartbeat, convergence_metrics), daemon=True
        )
        self._stream_thread.start()

    def stop_streaming(self) -> None:
        """Stop metrics streaming."""
        self._running = False
        if self._stream_thread:
            self._stream_thread.join(timeout=1.0)

    def _stream_loop(
        self, gpu_heartbeat: GPUHeartbeat, convergence_metrics: Optional[ConvergenceMetrics]
    ) -> None:
        """Main streaming loop.

        Args:
            gpu_heartbeat: GPU heartbeat engine
            convergence_metrics: Optional convergence metrics
        """
        while self._running:
            try:
                # Capture current metrics snapshot
                snapshot = self._capture_snapshot(gpu_heartbeat, convergence_metrics)

                # Add to buffer
                with self._lock:
                    self._metrics_buffer.append(snapshot)

                    # Notify all subscribers
                    for (
                        callback
                    ) in self._subscribers.copy():  # Copy to avoid modification during iteration
                        try:
                            callback(snapshot)
                        except Exception as e:
                            print(f"Error in metrics callback: {e}")

                # Sleep briefly to avoid overwhelming the system
                time.sleep(0.1)  # 10 Hz update rate

            except Exception as e:
                print(f"Error in metrics streaming: {e}")
                time.sleep(1.0)  # Back off on errors

    def _capture_snapshot(
        self, gpu_heartbeat: GPUHeartbeat, convergence_metrics: Optional[ConvergenceMetrics]
    ) -> MetricsSnapshot:
        """Capture current metrics snapshot.

        Args:
            gpu_heartbeat: GPU heartbeat engine
            convergence_metrics: Optional convergence metrics

        Returns:
            Complete metrics snapshot
        """
        system_status = gpu_heartbeat.get_system_status()
        scaling_decision, _ = gpu_heartbeat.get_scaling_recommendation()

        return MetricsSnapshot(
            timestamp=time.time(),
            gpu_heartbeat_status=system_status,
            convergence_metrics=convergence_metrics,
            gpu_count=system_status["gpu_count"],
            aggregate_utilization=system_status["aggregate_utilization"],
            scaling_decision=scaling_decision.value,
            metadata={"source": "gpu_heartbeat", "version": "1.0"},
        )

    def get_latest_snapshot(self) -> Optional[MetricsSnapshot]:
        """Get the most recent metrics snapshot.

        Returns:
            Latest metrics snapshot or None if no data
        """
        with self._lock:
            return self._metrics_buffer[-1] if self._metrics_buffer else None

    def get_metrics_history(self, count: int = 60) -> List[MetricsSnapshot]:
        """Get recent metrics history.

        Args:
            count: Number of recent snapshots to return

        Returns:
            List of recent metrics snapshots
        """
        with self._lock:
            return list(self._metrics_buffer)[-count:]


class UpdateCoordinator:
    """Coordinates synchronized updates across all visualization components."""

    def __init__(self, performance_monitor: bool = True):
        """Initialize update coordinator.

        Args:
            performance_monitor: Enable performance monitoring
        """
        self._components: Dict[str, UpdateConfig] = {}
        self._performance_monitor = performance_monitor
        self._performance_history: deque = deque(maxlen=100)
        self._lock = Lock()
        self._shutdown_event = Event()

    def register_component(
        self,
        component_id: str,
        component_type: ComponentType,
        update_frequency: UpdateFrequency,
        performance_budget_ms: float = 50.0,
    ) -> None:
        """Register a component for coordinated updates.

        Args:
            component_id: Unique identifier for the component
            component_type: Type of component
            update_frequency: How often to update this component
            performance_budget_ms: Maximum time allowed per update
        """
        with self._lock:
            self._components[component_id] = UpdateConfig(
                component_id=component_id,
                component_type=component_type,
                update_frequency=update_frequency,
                performance_budget_ms=performance_budget_ms,
            )

    def unregister_component(self, component_id: str) -> None:
        """Unregister a component.

        Args:
            component_id: Component identifier to remove
        """
        with self._lock:
            self._components.pop(component_id, None)

    def should_update_component(self, component_id: str) -> bool:
        """Check if a component should be updated now.

        Args:
            component_id: Component identifier

        Returns:
            True if component should be updated
        """
        with self._lock:
            config = self._components.get(component_id)
            if not config or not config.enabled:
                return False

            current_time = time.time()
            time_since_last = current_time - config.last_update_time
            return time_since_last >= config.update_frequency.value

    def mark_component_updated(self, component_id: str, update_duration_ms: float = 0.0) -> None:
        """Mark a component as having been updated.

        Args:
            component_id: Component identifier
            update_duration_ms: How long the update took in milliseconds
        """
        with self._lock:
            config = self._components.get(component_id)
            if config:
                config.last_update_time = time.time()
                config.update_count += 1

                # Track performance if monitoring enabled
                if self._performance_monitor:
                    self._performance_history.append(
                        {
                            "timestamp": time.time(),
                            "component_id": component_id,
                            "duration_ms": update_duration_ms,
                            "budget_ms": config.performance_budget_ms,
                            "over_budget": update_duration_ms > config.performance_budget_ms,
                        }
                    )

    def get_component_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all registered components.

        Returns:
            Dictionary with component statistics
        """
        with self._lock:
            stats = {}
            for component_id, config in self._components.items():
                current_time = time.time()
                time_since_last = current_time - config.last_update_time

                stats[component_id] = {
                    "component_type": config.component_type.value,
                    "update_frequency_hz": 1.0 / config.update_frequency.value,
                    "enabled": config.enabled,
                    "update_count": config.update_count,
                    "last_update_ago_s": time_since_last,
                    "next_update_in_s": max(0, config.update_frequency.value - time_since_last),
                    "performance_budget_ms": config.performance_budget_ms,
                }

            return stats

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance monitoring summary.

        Returns:
            Performance statistics summary
        """
        if not self._performance_monitor or not self._performance_history:
            return {"monitoring_enabled": False}

        recent_updates = list(self._performance_history)[-50:]  # Last 50 updates
        durations = [update["duration_ms"] for update in recent_updates]
        over_budget_count = sum(1 for update in recent_updates if update["over_budget"])

        return {
            "monitoring_enabled": True,
            "total_updates": len(self._performance_history),
            "recent_updates": len(recent_updates),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "over_budget_percentage": (
                (over_budget_count / len(recent_updates)) * 100 if recent_updates else 0
            ),
        }


class RealTimeVisualizationManager:
    """High-level manager for real-time visualization updates."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize real-time visualization manager.

        Args:
            console: Rich console for output (optional)
        """
        self.console = console or Console()
        self.metrics_streamer = MetricsStreamer()
        self.update_coordinator = UpdateCoordinator()

        # Component instances
        self.heartbeat_animator: Optional[HeartbeatAnimator] = None
        self.slo_dashboard: Optional[SLODashboard] = None
        self.executive_view: Optional[ExecutiveViewDashboard] = None

        # Control flags
        self._running = False
        self._update_thread: Optional[threading.Thread] = None

    def setup_components(
        self,
        gpu_heartbeat: GPUHeartbeat,
        slo_config: Optional[Any] = None,
        baseline_cost: float = 50000.0,
    ) -> None:
        """Set up all visualization components.

        Args:
            gpu_heartbeat: GPU heartbeat engine
            slo_config: SLO configuration (optional)
            baseline_cost: Baseline monthly cost for executive view
        """
        # Initialize components
        self.heartbeat_animator = HeartbeatAnimator(self.console)
        self.slo_dashboard = SLODashboard(slo_config, self.console)
        self.executive_view = ExecutiveViewDashboard(
            baseline_monthly_cost=baseline_cost, console=self.console
        )

        # Register components with coordinator
        self.update_coordinator.register_component(
            "heartbeat_animator", ComponentType.HEARTBEAT_ANIMATOR, UpdateFrequency.REALTIME
        )
        self.update_coordinator.register_component(
            "slo_dashboard", ComponentType.SLO_DASHBOARD, UpdateFrequency.HIGH
        )
        self.update_coordinator.register_component(
            "executive_view", ComponentType.EXECUTIVE_VIEW, UpdateFrequency.MEDIUM
        )

        # Subscribe to metrics updates
        self.metrics_streamer.subscribe(self._on_metrics_update)

    def start_real_time_updates(
        self, gpu_heartbeat: GPUHeartbeat, convergence_metrics: Optional[ConvergenceMetrics] = None
    ) -> None:
        """Start real-time updates for all components.

        Args:
            gpu_heartbeat: GPU heartbeat engine
            convergence_metrics: Optional convergence metrics
        """
        if self._running:
            return

        self._running = True

        # Start metrics streaming
        self.metrics_streamer.start_streaming(gpu_heartbeat, convergence_metrics)

        # Start update coordination thread
        self._update_thread = threading.Thread(
            target=self._update_loop, args=(gpu_heartbeat,), daemon=True
        )
        self._update_thread.start()

    def stop_real_time_updates(self) -> None:
        """Stop real-time updates."""
        self._running = False

        # Stop metrics streaming
        self.metrics_streamer.stop_streaming()

        # Wait for update thread to finish
        if self._update_thread:
            self._update_thread.join(timeout=2.0)

    def _on_metrics_update(self, snapshot: MetricsSnapshot) -> None:
        """Handle new metrics snapshot.

        Args:
            snapshot: New metrics snapshot
        """
        # Update SLO dashboard if it has convergence metrics
        if self.slo_dashboard and snapshot.convergence_metrics:
            self.slo_dashboard.update_metrics(snapshot.convergence_metrics, snapshot.gpu_count)

    def _update_loop(self, gpu_heartbeat: GPUHeartbeat) -> None:
        """Main update coordination loop.

        Args:
            gpu_heartbeat: GPU heartbeat engine
        """
        while self._running:
            try:
                current_snapshot = self.metrics_streamer.get_latest_snapshot()
                if not current_snapshot:
                    time.sleep(0.1)
                    continue

                # Check each component for updates
                self._check_heartbeat_updates(gpu_heartbeat, current_snapshot)
                self._check_slo_updates(current_snapshot)
                self._check_executive_updates(gpu_heartbeat, current_snapshot)

                time.sleep(0.05)  # 20 Hz coordination loop

            except Exception as e:
                print(f"Error in update loop: {e}")
                time.sleep(1.0)

    def _check_heartbeat_updates(
        self, gpu_heartbeat: GPUHeartbeat, snapshot: MetricsSnapshot
    ) -> None:
        """Check and perform heartbeat animator updates.

        Args:
            gpu_heartbeat: GPU heartbeat engine
            snapshot: Current metrics snapshot
        """
        if not self.heartbeat_animator:
            return

        if self.update_coordinator.should_update_component("heartbeat_animator"):
            start_time = time.time()

            try:
                # Update heartbeat visualization
                # (Note: Actual rendering would be handled by Live context)
                cluster_viz = self.heartbeat_animator.create_cluster_visualization(gpu_heartbeat)

                duration_ms = (time.time() - start_time) * 1000
                self.update_coordinator.mark_component_updated("heartbeat_animator", duration_ms)

            except Exception as e:
                print(f"Error updating heartbeat animator: {e}")

    def _check_slo_updates(self, snapshot: MetricsSnapshot) -> None:
        """Check and perform SLO dashboard updates.

        Args:
            snapshot: Current metrics snapshot
        """
        if not self.slo_dashboard or not snapshot.convergence_metrics:
            return

        if self.update_coordinator.should_update_component("slo_dashboard"):
            start_time = time.time()

            try:
                # SLO dashboard updates are handled in _on_metrics_update
                # This just marks the update timing
                duration_ms = (time.time() - start_time) * 1000
                self.update_coordinator.mark_component_updated("slo_dashboard", duration_ms)

            except Exception as e:
                print(f"Error updating SLO dashboard: {e}")

    def _check_executive_updates(
        self, gpu_heartbeat: GPUHeartbeat, snapshot: MetricsSnapshot
    ) -> None:
        """Check and perform executive view updates.

        Args:
            gpu_heartbeat: GPU heartbeat engine
            snapshot: Current metrics snapshot
        """
        if not self.executive_view:
            return

        if self.update_coordinator.should_update_component("executive_view"):
            start_time = time.time()

            try:
                # Generate updated executive summary
                summary = self.executive_view.generate_executive_summary(
                    gpu_heartbeat, snapshot.convergence_metrics
                )

                duration_ms = (time.time() - start_time) * 1000
                self.update_coordinator.mark_component_updated("executive_view", duration_ms)

            except Exception as e:
                print(f"Error updating executive view: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get complete real-time system status.

        Returns:
            Dictionary with system status information
        """
        latest_snapshot = self.metrics_streamer.get_latest_snapshot()
        component_stats = self.update_coordinator.get_component_stats()
        performance_summary = self.update_coordinator.get_performance_summary()

        return {
            "timestamp": time.time(),
            "streaming_active": self.metrics_streamer._running,
            "updates_active": self._running,
            "latest_metrics": latest_snapshot.__dict__ if latest_snapshot else None,
            "component_stats": component_stats,
            "performance_summary": performance_summary,
            "metrics_buffer_size": len(self.metrics_streamer._metrics_buffer),
        }


def create_demo_real_time_system() -> Tuple[RealTimeVisualizationManager, Any]:
    """Create a demo real-time visualization system.

    Returns:
        Tuple of (visualization_manager, gpu_heartbeat_engine)
    """
    from mtop.gpu_heartbeat import create_gpu_heartbeat

    # Create GPU heartbeat engine
    heartbeat = create_gpu_heartbeat()

    # Add demo GPUs
    heartbeat.add_gpu("gpu-00", "nvidia-h100")
    heartbeat.add_gpu("gpu-01", "nvidia-a100")
    heartbeat.add_gpu("gpu-02", "nvidia-v100")

    # Create visualization manager
    viz_manager = RealTimeVisualizationManager()

    # Set up components
    viz_manager.setup_components(heartbeat, baseline_cost=75000.0)

    return viz_manager, heartbeat


def main():
    """Demo the real-time visualization system."""
    console = Console()

    console.print("[bold]⚡ Real-Time Visualization Demo[/bold]", style="cyan")
    console.print("Starting real-time metrics streaming and coordinated updates...\n")

    # Create demo system
    viz_manager, heartbeat = create_demo_real_time_system()

    # Start background workload simulation
    import threading

    simulation_thread = threading.Thread(
        target=heartbeat.simulate_workload,
        args=(70.0, 30.0),  # 70% utilization for 30 seconds
        daemon=True,
    )
    simulation_thread.start()

    # Start real-time updates
    viz_manager.start_real_time_updates(heartbeat)

    try:
        # Monitor system for demo duration
        start_time = time.time()
        while time.time() - start_time < 30.0:
            # Display system status periodically
            if int(time.time()) % 5 == 0:  # Every 5 seconds
                status = viz_manager.get_system_status()
                console.print(
                    f"[dim]System Status: {status['streaming_active']} streaming, "
                    f"{len(status['component_stats'])} components active[/dim]"
                )

            time.sleep(1.0)

    except KeyboardInterrupt:
        console.print("\n[yellow]Demo stopped by user[/yellow]")
    finally:
        viz_manager.stop_real_time_updates()

    console.print("\n[green]✅ Real-time visualization demo complete![/green]")


if __name__ == "__main__":
    main()
