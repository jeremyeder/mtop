#!/usr/bin/env python3
"""
Tests for the real-time updates system.
"""

import threading
import time
import unittest
from unittest.mock import Mock, patch

from mtop.real_time_updates import (
    ComponentType,
    MetricsSnapshot,
    MetricsStreamer,
    RealTimeVisualizationManager,
    UpdateConfig,
    UpdateCoordinator,
    UpdateFrequency,
    create_demo_real_time_system,
)
from mtop.slo_convergence import ConvergenceMetrics


class TestMetricsSnapshot(unittest.TestCase):
    """Test metrics snapshot dataclass."""

    def test_metrics_snapshot_creation(self):
        """Test creating metrics snapshot."""
        snapshot = MetricsSnapshot(
            timestamp=time.time(),
            gpu_heartbeat_status={"gpu_count": 3, "aggregate_utilization": 75.0},
            convergence_metrics=None,
            gpu_count=3,
            aggregate_utilization=75.0,
            scaling_decision="maintain",
            business_impact_score=85.0,
        )

        self.assertEqual(snapshot.gpu_count, 3)
        self.assertEqual(snapshot.aggregate_utilization, 75.0)
        self.assertEqual(snapshot.scaling_decision, "maintain")
        self.assertEqual(snapshot.business_impact_score, 85.0)


class TestUpdateConfig(unittest.TestCase):
    """Test update configuration."""

    def test_update_config_creation(self):
        """Test creating update configuration."""
        config = UpdateConfig(
            component_id="test_component",
            component_type=ComponentType.HEARTBEAT_ANIMATOR,
            update_frequency=UpdateFrequency.HIGH,
            performance_budget_ms=25.0,
        )

        self.assertEqual(config.component_id, "test_component")
        self.assertEqual(config.component_type, ComponentType.HEARTBEAT_ANIMATOR)
        self.assertEqual(config.update_frequency, UpdateFrequency.HIGH)
        self.assertEqual(config.performance_budget_ms, 25.0)
        self.assertTrue(config.enabled)
        self.assertEqual(config.update_count, 0)


class TestMetricsStreamer(unittest.TestCase):
    """Test metrics streaming functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.streamer = MetricsStreamer(buffer_size=10)

    def tearDown(self):
        """Clean up after tests."""
        self.streamer.stop_streaming()

    def test_streamer_initialization(self):
        """Test streamer initializes correctly."""
        self.assertEqual(self.streamer.buffer_size, 10)
        self.assertEqual(len(self.streamer._subscribers), 0)
        self.assertFalse(self.streamer._running)

    def test_subscriber_management(self):
        """Test subscribing and unsubscribing to metrics."""

        def dummy_callback(snapshot):
            pass

        # Subscribe
        self.streamer.subscribe(dummy_callback)
        self.assertEqual(len(self.streamer._subscribers), 1)
        self.assertIn(dummy_callback, self.streamer._subscribers)

        # Unsubscribe
        self.streamer.unsubscribe(dummy_callback)
        self.assertEqual(len(self.streamer._subscribers), 0)
        self.assertNotIn(dummy_callback, self.streamer._subscribers)

    def test_snapshot_capture(self):
        """Test metrics snapshot capture."""
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        # Create test heartbeat
        heartbeat = create_gpu_heartbeat()
        heartbeat.add_gpu("gpu-00", "nvidia-h100")

        # Create test convergence metrics
        convergence_metrics = ConvergenceMetrics(
            current_ttft_p95=200.0,
            target_ttft_p95=250.0,
            current_cost_per_million=0.20,
            target_cost_per_million=0.25,
        )

        # Capture snapshot
        snapshot = self.streamer._capture_snapshot(heartbeat, convergence_metrics)

        # Validate snapshot
        self.assertIsInstance(snapshot, MetricsSnapshot)
        self.assertEqual(snapshot.gpu_count, 1)
        self.assertIsInstance(snapshot.aggregate_utilization, float)
        self.assertEqual(snapshot.convergence_metrics, convergence_metrics)
        self.assertIn("source", snapshot.metadata)

    def test_streaming_lifecycle(self):
        """Test starting and stopping streaming."""
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        heartbeat = create_gpu_heartbeat()
        heartbeat.add_gpu("gpu-00", "nvidia-h100")

        # Start streaming
        self.streamer.start_streaming(heartbeat)
        self.assertTrue(self.streamer._running)
        self.assertIsNotNone(self.streamer._stream_thread)

        # Brief wait to let some data accumulate
        time.sleep(0.2)

        # Should have some metrics
        latest = self.streamer.get_latest_snapshot()
        self.assertIsNotNone(latest)

        # Stop streaming
        self.streamer.stop_streaming()
        self.assertFalse(self.streamer._running)

    def test_callback_notification(self):
        """Test that subscribers get notified of updates."""
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        received_snapshots = []

        def test_callback(snapshot):
            received_snapshots.append(snapshot)

        # Subscribe callback
        self.streamer.subscribe(test_callback)

        # Start streaming
        heartbeat = create_gpu_heartbeat()
        heartbeat.add_gpu("gpu-00", "nvidia-h100")
        self.streamer.start_streaming(heartbeat)

        # Wait briefly for callbacks
        time.sleep(0.3)

        # Stop streaming
        self.streamer.stop_streaming()

        # Should have received some snapshots
        self.assertGreater(len(received_snapshots), 0)
        self.assertIsInstance(received_snapshots[0], MetricsSnapshot)

    def test_metrics_history(self):
        """Test metrics history retrieval."""
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        heartbeat = create_gpu_heartbeat()
        heartbeat.add_gpu("gpu-00", "nvidia-h100")

        # Start streaming briefly
        self.streamer.start_streaming(heartbeat)
        time.sleep(0.2)
        self.streamer.stop_streaming()

        # Get history
        history = self.streamer.get_metrics_history(count=5)
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)

        # Get latest
        latest = self.streamer.get_latest_snapshot()
        self.assertIsNotNone(latest)


class TestUpdateCoordinator(unittest.TestCase):
    """Test update coordination functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.coordinator = UpdateCoordinator()

    def test_coordinator_initialization(self):
        """Test coordinator initializes correctly."""
        self.assertEqual(len(self.coordinator._components), 0)
        self.assertTrue(self.coordinator._performance_monitor)

    def test_component_registration(self):
        """Test component registration and management."""
        # Register component
        self.coordinator.register_component(
            "test_comp", ComponentType.SLO_DASHBOARD, UpdateFrequency.HIGH, 30.0
        )

        self.assertEqual(len(self.coordinator._components), 1)
        self.assertIn("test_comp", self.coordinator._components)

        config = self.coordinator._components["test_comp"]
        self.assertEqual(config.component_id, "test_comp")
        self.assertEqual(config.component_type, ComponentType.SLO_DASHBOARD)
        self.assertEqual(config.update_frequency, UpdateFrequency.HIGH)
        self.assertEqual(config.performance_budget_ms, 30.0)

        # Unregister component
        self.coordinator.unregister_component("test_comp")
        self.assertEqual(len(self.coordinator._components), 0)

    def test_update_timing(self):
        """Test update timing logic."""
        # Register component with fast updates
        self.coordinator.register_component(
            "fast_comp", ComponentType.HEARTBEAT_ANIMATOR, UpdateFrequency.REALTIME
        )

        # Should need update initially
        self.assertTrue(self.coordinator.should_update_component("fast_comp"))

        # Mark as updated
        self.coordinator.mark_component_updated("fast_comp", 5.0)

        # Should not need update immediately
        self.assertFalse(self.coordinator.should_update_component("fast_comp"))

        # Wait for update interval
        time.sleep(UpdateFrequency.REALTIME.value + 0.01)

        # Should need update again
        self.assertTrue(self.coordinator.should_update_component("fast_comp"))

    def test_component_stats(self):
        """Test component statistics retrieval."""
        # Register multiple components
        self.coordinator.register_component(
            "comp1", ComponentType.HEARTBEAT_ANIMATOR, UpdateFrequency.REALTIME
        )
        self.coordinator.register_component(
            "comp2", ComponentType.SLO_DASHBOARD, UpdateFrequency.HIGH
        )

        # Mark some updates
        self.coordinator.mark_component_updated("comp1", 15.0)
        self.coordinator.mark_component_updated("comp2", 25.0)

        # Get stats
        stats = self.coordinator.get_component_stats()

        self.assertEqual(len(stats), 2)
        self.assertIn("comp1", stats)
        self.assertIn("comp2", stats)

        comp1_stats = stats["comp1"]
        self.assertEqual(comp1_stats["component_type"], ComponentType.HEARTBEAT_ANIMATOR.value)
        self.assertEqual(comp1_stats["update_count"], 1)
        self.assertTrue(comp1_stats["enabled"])

    def test_performance_monitoring(self):
        """Test performance monitoring functionality."""
        # Register component
        self.coordinator.register_component(
            "perf_comp", ComponentType.EXECUTIVE_VIEW, UpdateFrequency.MEDIUM, 20.0
        )

        # Mark updates with different performance
        self.coordinator.mark_component_updated("perf_comp", 15.0)  # Under budget
        self.coordinator.mark_component_updated("perf_comp", 25.0)  # Over budget

        # Get performance summary
        summary = self.coordinator.get_performance_summary()

        self.assertTrue(summary["monitoring_enabled"])
        self.assertEqual(summary["total_updates"], 2)
        self.assertGreater(summary["avg_duration_ms"], 0)
        self.assertEqual(summary["max_duration_ms"], 25.0)
        self.assertEqual(summary["over_budget_percentage"], 50.0)  # 1 of 2 over budget


class TestRealTimeVisualizationManager(unittest.TestCase):
    """Test real-time visualization manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = RealTimeVisualizationManager()

    def tearDown(self):
        """Clean up after tests."""
        self.manager.stop_real_time_updates()

    def test_manager_initialization(self):
        """Test manager initializes correctly."""
        self.assertIsNotNone(self.manager.console)
        self.assertIsNotNone(self.manager.metrics_streamer)
        self.assertIsNotNone(self.manager.update_coordinator)
        self.assertFalse(self.manager._running)

    def test_component_setup(self):
        """Test setting up visualization components."""
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        heartbeat = create_gpu_heartbeat()
        heartbeat.add_gpu("gpu-00", "nvidia-h100")

        # Set up components
        self.manager.setup_components(heartbeat, baseline_cost=60000.0)

        # Check components are initialized
        self.assertIsNotNone(self.manager.heartbeat_animator)
        self.assertIsNotNone(self.manager.slo_dashboard)
        self.assertIsNotNone(self.manager.executive_view)

        # Check components are registered
        stats = self.manager.update_coordinator.get_component_stats()
        self.assertEqual(len(stats), 3)
        self.assertIn("heartbeat_animator", stats)
        self.assertIn("slo_dashboard", stats)
        self.assertIn("executive_view", stats)

    @patch("time.sleep")  # Speed up the test
    def test_real_time_updates_lifecycle(self, mock_sleep):
        """Test starting and stopping real-time updates."""
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        heartbeat = create_gpu_heartbeat()
        heartbeat.add_gpu("gpu-00", "nvidia-h100")

        # Set up components
        self.manager.setup_components(heartbeat)

        # Start updates
        self.manager.start_real_time_updates(heartbeat)
        self.assertTrue(self.manager._running)
        self.assertTrue(self.manager.metrics_streamer._running)

        # Brief wait
        time.sleep(0.1)

        # Stop updates
        self.manager.stop_real_time_updates()
        self.assertFalse(self.manager._running)
        self.assertFalse(self.manager.metrics_streamer._running)

    def test_system_status(self):
        """Test system status reporting."""
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        heartbeat = create_gpu_heartbeat()
        heartbeat.add_gpu("gpu-00", "nvidia-h100")

        # Set up components
        self.manager.setup_components(heartbeat)

        # Get status
        status = self.manager.get_system_status()

        self.assertIn("timestamp", status)
        self.assertIn("streaming_active", status)
        self.assertIn("updates_active", status)
        self.assertIn("component_stats", status)
        self.assertIn("performance_summary", status)
        self.assertIn("metrics_buffer_size", status)

        # Should have 3 registered components
        self.assertEqual(len(status["component_stats"]), 3)


class TestDemoScenario(unittest.TestCase):
    """Test demo scenario creation."""

    def test_demo_real_time_system_creation(self):
        """Test creating demo real-time system."""
        viz_manager, heartbeat = create_demo_real_time_system()

        # Check manager is configured
        self.assertIsInstance(viz_manager, RealTimeVisualizationManager)

        # Check heartbeat has GPUs
        all_metrics = heartbeat.tracker.get_all_gpu_metrics()
        self.assertIn("gpu-00", all_metrics)
        self.assertIn("gpu-01", all_metrics)
        self.assertIn("gpu-02", all_metrics)

        # Check components are set up
        self.assertIsNotNone(viz_manager.heartbeat_animator)
        self.assertIsNotNone(viz_manager.slo_dashboard)
        self.assertIsNotNone(viz_manager.executive_view)


class TestIntegration(unittest.TestCase):
    """Integration tests for real-time updates."""

    def test_end_to_end_streaming(self):
        """Test complete end-to-end streaming pipeline."""
        viz_manager, heartbeat = create_demo_real_time_system()

        received_updates = []

        def capture_updates(snapshot):
            received_updates.append(snapshot)

        # Subscribe to updates
        viz_manager.metrics_streamer.subscribe(capture_updates)

        try:
            # Start system
            viz_manager.start_real_time_updates(heartbeat)

            # Let it run briefly
            time.sleep(0.3)

            # Should have received updates
            self.assertGreater(len(received_updates), 0)

            # Check update quality
            latest_update = received_updates[-1]
            self.assertIsInstance(latest_update, MetricsSnapshot)
            self.assertEqual(latest_update.gpu_count, 3)
            self.assertIsInstance(latest_update.aggregate_utilization, float)

        finally:
            viz_manager.stop_real_time_updates()

    def test_performance_under_load(self):
        """Test system performance under simulated load."""
        viz_manager, heartbeat = create_demo_real_time_system()

        try:
            # Start system
            viz_manager.start_real_time_updates(heartbeat)

            # Simulate workload
            heartbeat.simulate_workload(target_utilization=80.0, duration_seconds=0.5)

            # Let updates run
            time.sleep(0.6)

            # Check performance
            performance = viz_manager.update_coordinator.get_performance_summary()
            if performance["monitoring_enabled"] and performance["total_updates"] > 0:
                # Most updates should be within reasonable time
                self.assertLess(performance["avg_duration_ms"], 100.0)  # Under 100ms average

        finally:
            viz_manager.stop_real_time_updates()

    def test_component_coordination(self):
        """Test that components are properly coordinated."""
        viz_manager, heartbeat = create_demo_real_time_system()

        try:
            # Start system
            viz_manager.start_real_time_updates(heartbeat)

            # Let it run briefly
            time.sleep(0.2)

            # Check component stats
            stats = viz_manager.update_coordinator.get_component_stats()

            # All components should be registered
            self.assertEqual(len(stats), 3)

            # Check that components have different update frequencies
            heartbeat_freq = stats["heartbeat_animator"]["update_frequency_hz"]
            executive_freq = stats["executive_view"]["update_frequency_hz"]

            # Heartbeat should update faster than executive view
            self.assertGreater(heartbeat_freq, executive_freq)

        finally:
            viz_manager.stop_real_time_updates()


if __name__ == "__main__":
    unittest.main()
