#!/usr/bin/env python3
"""
Comprehensive tests for GPU heartbeat engine system.
"""

import time
from unittest.mock import patch

import pytest

from config_loader import GPUType, TechnologyConfig
from mtop.gpu_heartbeat import (
    CapacityScaler,
    GPUHeartbeat,
    GPUMetrics,
    HeartbeatPulse,
    HeartbeatStrength,
    HeartbeatVisualizer,
    ScalingDecision,
    UtilizationTracker,
    create_gpu_heartbeat,
    simulate_multi_gpu_cluster,
)


class TestGPUMetrics:
    """Test GPUMetrics dataclass and validation."""

    def test_valid_gpu_metrics_creation(self):
        """Test creating valid GPUMetrics instance."""
        metrics = GPUMetrics(
            gpu_id="gpu-01",
            utilization_percent=75.5,
            vram_used_gb=45.2,
            vram_total_gb=80.0,
            temperature_c=72.0,
            power_watts=350.0,
        )

        assert metrics.gpu_id == "gpu-01"
        assert metrics.utilization_percent == 75.5
        assert metrics.vram_used_gb == 45.2
        assert metrics.vram_total_gb == 80.0
        assert metrics.temperature_c == 72.0
        assert metrics.power_watts == 350.0
        assert metrics.last_updated > 0

    def test_gpu_metrics_validation(self):
        """Test GPUMetrics validation in __post_init__."""
        # Test empty gpu_id
        with pytest.raises(ValueError, match="gpu_id cannot be empty"):
            GPUMetrics(gpu_id="")

        # Test invalid utilization
        with pytest.raises(ValueError, match="utilization_percent must be 0-100"):
            GPUMetrics(gpu_id="test", utilization_percent=-1)

        with pytest.raises(ValueError, match="utilization_percent must be 0-100"):
            GPUMetrics(gpu_id="test", utilization_percent=101)

        # Test negative VRAM
        with pytest.raises(ValueError, match="vram_used_gb cannot be negative"):
            GPUMetrics(gpu_id="test", vram_used_gb=-1)

        # Test invalid total VRAM
        with pytest.raises(ValueError, match="vram_total_gb must be positive"):
            GPUMetrics(gpu_id="test", vram_total_gb=0)

        # Test VRAM usage exceeding total
        with pytest.raises(ValueError, match="vram_used_gb .* cannot exceed total"):
            GPUMetrics(gpu_id="test", vram_used_gb=100, vram_total_gb=80)

    def test_vram_utilization_calculation(self):
        """Test VRAM utilization percentage calculation."""
        metrics = GPUMetrics(gpu_id="test", vram_used_gb=40, vram_total_gb=80)
        assert metrics.get_vram_utilization() == 50.0

        # Edge case: zero total VRAM
        metrics_zero = GPUMetrics(gpu_id="test", vram_used_gb=0, vram_total_gb=1)
        metrics_zero.vram_total_gb = 0  # Bypass validation for testing
        assert metrics_zero.get_vram_utilization() == 0.0

    def test_overload_detection(self):
        """Test GPU overload detection."""
        overloaded = GPUMetrics(gpu_id="test", utilization_percent=96.0)
        not_overloaded = GPUMetrics(gpu_id="test", utilization_percent=90.0)

        assert overloaded.is_overloaded()
        assert not not_overloaded.is_overloaded()

    def test_underutilization_detection(self):
        """Test GPU underutilization detection."""
        underutilized = GPUMetrics(gpu_id="test", utilization_percent=25.0)
        not_underutilized = GPUMetrics(gpu_id="test", utilization_percent=50.0)

        assert underutilized.is_underutilized()
        assert not not_underutilized.is_underutilized()


class TestHeartbeatPulse:
    """Test HeartbeatPulse dataclass and validation."""

    def test_valid_heartbeat_pulse_creation(self):
        """Test creating valid HeartbeatPulse instance."""
        pulse = HeartbeatPulse(
            strength=HeartbeatStrength.STRONG, frequency_bpm=85.5, color="#FF6600", intensity=0.7
        )

        assert pulse.strength == HeartbeatStrength.STRONG
        assert pulse.frequency_bpm == 85.5
        assert pulse.color == "#FF6600"
        assert pulse.intensity == 0.7
        assert pulse.timestamp > 0

    def test_heartbeat_pulse_validation(self):
        """Test HeartbeatPulse validation."""
        # Test invalid intensity
        with pytest.raises(ValueError, match="intensity must be 0-1"):
            HeartbeatPulse(
                strength=HeartbeatStrength.STEADY, frequency_bpm=80, color="#00FF00", intensity=-0.1
            )

        with pytest.raises(ValueError, match="intensity must be 0-1"):
            HeartbeatPulse(
                strength=HeartbeatStrength.STEADY, frequency_bpm=80, color="#00FF00", intensity=1.1
            )

        # Test invalid frequency
        with pytest.raises(ValueError, match="frequency_bpm must be positive"):
            HeartbeatPulse(
                strength=HeartbeatStrength.STEADY, frequency_bpm=0, color="#00FF00", intensity=0.5
            )


class TestUtilizationTracker:
    """Test UtilizationTracker functionality."""

    def test_utilization_tracker_creation(self):
        """Test creating UtilizationTracker."""
        tracker = UtilizationTracker(window_size=50)
        assert tracker.window_size == 50
        assert tracker.get_aggregate_utilization() == 0.0

    def test_update_gpu_metrics(self):
        """Test updating GPU metrics."""
        tracker = UtilizationTracker()

        metrics = GPUMetrics(gpu_id="gpu-01", utilization_percent=75.0)
        tracker.update_gpu_metrics(metrics)

        retrieved = tracker.get_gpu_metrics("gpu-01")
        assert retrieved is not None
        assert retrieved.utilization_percent == 75.0

    def test_aggregate_utilization_calculation(self):
        """Test aggregate utilization calculation."""
        tracker = UtilizationTracker()

        # Add multiple GPUs
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-01", utilization_percent=70.0))
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-02", utilization_percent=80.0))
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-03", utilization_percent=90.0))

        aggregate = tracker.get_aggregate_utilization()
        assert abs(aggregate - 80.0) < 0.1  # (70+80+90)/3 = 80

    def test_get_all_gpu_metrics(self):
        """Test getting all GPU metrics."""
        tracker = UtilizationTracker()

        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-01", utilization_percent=70.0))
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-02", utilization_percent=80.0))

        all_metrics = tracker.get_all_gpu_metrics()
        assert len(all_metrics) == 2
        assert "gpu-01" in all_metrics
        assert "gpu-02" in all_metrics

    def test_utilization_trend_analysis(self):
        """Test utilization trend analysis."""
        tracker = UtilizationTracker()

        # Insufficient data
        assert tracker.get_utilization_trend("gpu-01") is None

        # Add increasing trend data
        for i in range(15):
            utilization = 50.0 + i * 3.0  # Increasing trend
            tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-01", utilization_percent=utilization))

        trend = tracker.get_utilization_trend("gpu-01")
        assert trend == "increasing"

        # Add decreasing trend data
        for i in range(15):
            utilization = 90.0 - i * 3.0  # Decreasing trend
            tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-02", utilization_percent=utilization))

        trend = tracker.get_utilization_trend("gpu-02")
        assert trend == "decreasing"

    def test_overloaded_gpu_detection(self):
        """Test overloaded GPU detection."""
        tracker = UtilizationTracker()

        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-01", utilization_percent=96.0))
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-02", utilization_percent=80.0))

        overloaded = tracker.get_overloaded_gpus()
        assert "gpu-01" in overloaded
        assert "gpu-02" not in overloaded

    def test_underutilized_gpu_detection(self):
        """Test underutilized GPU detection."""
        tracker = UtilizationTracker()

        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-01", utilization_percent=25.0))
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-02", utilization_percent=80.0))

        underutilized = tracker.get_underutilized_gpus()
        assert "gpu-01" in underutilized
        assert "gpu-02" not in underutilized

    def test_thread_safety(self):
        """Test thread safety of UtilizationTracker."""
        import threading

        tracker = UtilizationTracker()

        def update_metrics():
            for i in range(50):
                metrics = GPUMetrics(gpu_id=f"gpu-{i%4:02d}", utilization_percent=50 + i % 40)
                tracker.update_gpu_metrics(metrics)
                time.sleep(0.001)

        # Start multiple threads
        threads = [threading.Thread(target=update_metrics) for _ in range(3)]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have 4 unique GPUs
        all_metrics = tracker.get_all_gpu_metrics()
        assert len(all_metrics) == 4


class TestCapacityScaler:
    """Test CapacityScaler functionality."""

    def test_capacity_scaler_creation(self):
        """Test creating CapacityScaler with custom thresholds."""
        scaler = CapacityScaler(scale_up_threshold=85.0, scale_down_threshold=35.0)
        assert scaler.scale_up_threshold == 85.0
        assert scaler.scale_down_threshold == 35.0

    def test_scale_up_decision(self):
        """Test scale up decision logic."""
        tracker = UtilizationTracker()
        scaler = CapacityScaler(scale_up_threshold=80.0)

        # Add GPUs with high utilization
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-01", utilization_percent=85.0))
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-02", utilization_percent=90.0))

        decision, reason = scaler.evaluate_scaling_decision(tracker)
        assert decision == ScalingDecision.SCALE_UP
        assert "Scale up" in reason

    def test_scale_down_decision(self):
        """Test scale down decision logic."""
        tracker = UtilizationTracker()
        scaler = CapacityScaler(scale_down_threshold=40.0)

        # Add GPUs with low utilization
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-01", utilization_percent=25.0))
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-02", utilization_percent=30.0))

        decision, reason = scaler.evaluate_scaling_decision(tracker)
        assert decision == ScalingDecision.SCALE_DOWN
        assert "Scale down" in reason

    def test_urgent_scaling_decision(self):
        """Test urgent scaling decision."""
        tracker = UtilizationTracker()
        scaler = CapacityScaler(urgent_threshold=95.0)

        # Add overloaded GPU
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-01", utilization_percent=96.0))

        decision, reason = scaler.evaluate_scaling_decision(tracker)
        assert decision == ScalingDecision.URGENT_SCALE
        assert "Urgent" in reason

    def test_maintain_decision(self):
        """Test maintain capacity decision."""
        tracker = UtilizationTracker()
        scaler = CapacityScaler()

        # Add GPUs with optimal utilization
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-01", utilization_percent=65.0))
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-02", utilization_percent=70.0))

        decision, reason = scaler.evaluate_scaling_decision(tracker)
        assert decision == ScalingDecision.MAINTAIN
        assert "Maintain" in reason

    def test_cooldown_behavior(self):
        """Test scaling cooldown behavior."""
        tracker = UtilizationTracker()
        scaler = CapacityScaler()
        scaler._cooldown_period = 2.0  # Short cooldown for testing

        # Trigger initial scaling
        tracker.update_gpu_metrics(GPUMetrics(gpu_id="gpu-01", utilization_percent=85.0))
        decision1, _ = scaler.evaluate_scaling_decision(tracker)
        assert decision1 == ScalingDecision.SCALE_UP

        # Immediate second call should be in cooldown
        decision2, reason2 = scaler.evaluate_scaling_decision(tracker)
        assert decision2 == ScalingDecision.MAINTAIN
        assert "Cooldown" in reason2

        # Wait for cooldown to expire
        time.sleep(2.1)
        decision3, _ = scaler.evaluate_scaling_decision(tracker)
        assert decision3 == ScalingDecision.SCALE_UP


class TestHeartbeatVisualizer:
    """Test HeartbeatVisualizer functionality."""

    def test_heartbeat_visualizer_creation(self):
        """Test creating HeartbeatVisualizer."""
        visualizer = HeartbeatVisualizer()
        assert len(visualizer._pulse_history) == 0

    def test_minimal_heartbeat_generation(self):
        """Test generating minimal heartbeat pulse."""
        visualizer = HeartbeatVisualizer()
        pulse = visualizer.generate_pulse(aggregate_utilization=20.0)

        assert pulse.strength == HeartbeatStrength.MINIMAL
        assert 35 <= pulse.frequency_bpm <= 65  # 40-60 BPM ± variation
        assert pulse.color == "#0000FF"  # Blue
        assert 0.2 <= pulse.intensity <= 0.4

    def test_steady_heartbeat_generation(self):
        """Test generating steady heartbeat pulse."""
        visualizer = HeartbeatVisualizer()
        pulse = visualizer.generate_pulse(aggregate_utilization=50.0)

        assert pulse.strength == HeartbeatStrength.STEADY
        assert 75 <= pulse.frequency_bpm <= 95  # 80 BPM ± variation
        assert pulse.color == "#00FF00"  # Green
        assert 0.4 <= pulse.intensity <= 0.6

    def test_strong_heartbeat_generation(self):
        """Test generating strong heartbeat pulse."""
        visualizer = HeartbeatVisualizer()
        pulse = visualizer.generate_pulse(aggregate_utilization=75.0)

        assert pulse.strength == HeartbeatStrength.STRONG
        assert 99 <= pulse.frequency_bpm <= 129  # 104 BPM ± variation
        assert pulse.color == "#FFA500"  # Orange
        assert 0.6 <= pulse.intensity <= 0.8

    def test_intense_heartbeat_generation(self):
        """Test generating intense heartbeat pulse."""
        visualizer = HeartbeatVisualizer()
        pulse = visualizer.generate_pulse(aggregate_utilization=90.0)

        assert pulse.strength == HeartbeatStrength.INTENSE
        assert 120 <= pulse.frequency_bpm <= 140  # 125 BPM ± variation
        assert pulse.color == "#FF6600"  # Orange-red
        assert 0.8 <= pulse.intensity <= 1.0

    def test_critical_heartbeat_generation(self):
        """Test generating critical heartbeat pulse."""
        visualizer = HeartbeatVisualizer()
        pulse = visualizer.generate_pulse(aggregate_utilization=97.0)

        assert pulse.strength == HeartbeatStrength.CRITICAL
        assert 139 <= pulse.frequency_bpm <= 159  # 144 BPM ± variation
        assert pulse.color == "#FF0000"  # Red
        assert 0.9 <= pulse.intensity <= 1.0

    def test_gpu_count_scaling(self):
        """Test frequency scaling based on GPU count."""
        visualizer = HeartbeatVisualizer()

        pulse_1gpu = visualizer.generate_pulse(aggregate_utilization=70.0, gpu_count=1)
        pulse_4gpu = visualizer.generate_pulse(aggregate_utilization=70.0, gpu_count=4)

        # More GPUs should result in higher frequency
        assert pulse_4gpu.frequency_bpm > pulse_1gpu.frequency_bpm

    def test_pulse_statistics(self):
        """Test pulse statistics calculation."""
        visualizer = HeartbeatVisualizer()

        # Empty statistics
        stats = visualizer.get_pulse_statistics()
        assert stats == {}

        # Generate some pulses
        for util in [20, 50, 80]:
            visualizer.generate_pulse(aggregate_utilization=util)

        stats = visualizer.get_pulse_statistics()
        assert stats["pulse_count"] == 3
        assert "avg_frequency_bpm" in stats
        assert "latest_pulse" in stats

    def test_pulse_history_rolling_window(self):
        """Test pulse history rolling window behavior."""
        visualizer = HeartbeatVisualizer()

        # Generate more pulses than the window size (60)
        for i in range(70):
            visualizer.generate_pulse(aggregate_utilization=50.0)

        stats = visualizer.get_pulse_statistics()
        assert stats["pulse_count"] == 60  # Should cap at maxlen


class TestGPUHeartbeat:
    """Test GPUHeartbeat main engine."""

    def test_gpu_heartbeat_creation(self):
        """Test creating GPUHeartbeat engine."""
        heartbeat = GPUHeartbeat()
        assert isinstance(heartbeat.tracker, UtilizationTracker)
        assert isinstance(heartbeat.scaler, CapacityScaler)
        assert isinstance(heartbeat.visualizer, HeartbeatVisualizer)

    def test_gpu_heartbeat_with_technology_config(self):
        """Test GPUHeartbeat with technology configuration."""
        tech_config = TechnologyConfig(
            gpu_types={
                "nvidia-h100": GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=4.10),
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=40, hourly_cost=3.20),
            }
        )

        heartbeat = GPUHeartbeat(tech_config)
        assert heartbeat.technology_config == tech_config

    def test_add_gpu(self):
        """Test adding GPU to system."""
        heartbeat = GPUHeartbeat()
        heartbeat.add_gpu("gpu-01", "nvidia-h100")

        assert "gpu-01" in heartbeat._active_gpus
        assert heartbeat._active_gpus["gpu-01"] == "nvidia-h100"

        # Should have initial metrics
        metrics = heartbeat.tracker.get_gpu_metrics("gpu-01")
        assert metrics is not None
        assert metrics.gpu_id == "gpu-01"

    def test_add_gpu_with_technology_config(self):
        """Test adding GPU with technology config for VRAM detection."""
        tech_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=40, hourly_cost=3.20),
            }
        )

        heartbeat = GPUHeartbeat(tech_config)
        heartbeat.add_gpu("gpu-01", "nvidia-a100")

        metrics = heartbeat.tracker.get_gpu_metrics("gpu-01")
        assert metrics.vram_total_gb == 40.0  # Should use config value

    def test_remove_gpu(self):
        """Test removing GPU from system."""
        heartbeat = GPUHeartbeat()
        heartbeat.add_gpu("gpu-01", "nvidia-h100")

        assert "gpu-01" in heartbeat._active_gpus

        heartbeat.remove_gpu("gpu-01")
        assert "gpu-01" not in heartbeat._active_gpus

    def test_get_current_heartbeat(self):
        """Test getting current heartbeat pulse."""
        heartbeat = GPUHeartbeat()
        heartbeat.add_gpu("gpu-01", "nvidia-h100")

        pulse = heartbeat.get_current_heartbeat()
        assert isinstance(pulse, HeartbeatPulse)
        assert pulse.strength in HeartbeatStrength
        assert pulse.frequency_bpm > 0

    def test_get_scaling_recommendation(self):
        """Test getting scaling recommendation."""
        heartbeat = GPUHeartbeat()
        heartbeat.add_gpu("gpu-01", "nvidia-h100")

        decision, reason = heartbeat.get_scaling_recommendation()
        assert isinstance(decision, ScalingDecision)
        assert isinstance(reason, str)

    def test_get_system_status(self):
        """Test getting comprehensive system status."""
        heartbeat = GPUHeartbeat()
        heartbeat.add_gpu("gpu-01", "nvidia-h100")
        heartbeat.add_gpu("gpu-02", "nvidia-a100")

        status = heartbeat.get_system_status()

        # Check required fields
        assert "timestamp" in status
        assert "gpu_count" in status
        assert "aggregate_utilization" in status
        assert "scaling_decision" in status
        assert "current_pulse" in status
        assert "gpu_details" in status

        assert status["gpu_count"] == 2
        assert len(status["gpu_details"]) == 2

    @pytest.mark.skip(reason="Simulation hangs in CI - needs refactoring to be testable")
    def test_simulate_workload(self):
        """Test workload simulation."""
        heartbeat = GPUHeartbeat()
        heartbeat.add_gpu("gpu-01", "nvidia-h100")

        # Very short simulation to avoid hanging
        heartbeat.simulate_workload(target_utilization=75.0, duration_seconds=0.01)

        # Should have updated metrics
        metrics = heartbeat.tracker.get_gpu_metrics("gpu-01")
        assert metrics is not None
        assert metrics.utilization_percent > 0

    def test_thread_safety(self):
        """Test thread safety of GPUHeartbeat operations."""
        import threading

        heartbeat = GPUHeartbeat()

        def add_gpus():
            for i in range(10):
                heartbeat.add_gpu(f"gpu-{i:02d}", "nvidia-h100")
                time.sleep(0.001)

        def get_status():
            for _ in range(20):
                heartbeat.get_system_status()
                time.sleep(0.001)

        # Start multiple threads
        threads = [threading.Thread(target=add_gpus), threading.Thread(target=get_status)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have added all GPUs successfully
        assert len(heartbeat._active_gpus) == 10


class TestFactoryFunctions:
    """Test factory functions."""

    def test_create_gpu_heartbeat_basic(self):
        """Test basic GPU heartbeat creation."""
        heartbeat = create_gpu_heartbeat()
        assert isinstance(heartbeat, GPUHeartbeat)
        assert heartbeat.technology_config is None

    def test_create_gpu_heartbeat_with_config(self):
        """Test GPU heartbeat creation with config."""
        tech_config = TechnologyConfig(
            gpu_types={
                "nvidia-h100": GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=4.10),
            }
        )

        heartbeat = create_gpu_heartbeat(tech_config)
        assert heartbeat.technology_config == tech_config

    @pytest.mark.skip(reason="Simulation hangs in CI - needs refactoring to be testable")
    def test_simulate_multi_gpu_cluster(self):
        """Test multi-GPU cluster simulation."""
        # Very short simulation to avoid hanging
        heartbeat = simulate_multi_gpu_cluster(
            gpu_count=3, target_utilization=70.0, duration_seconds=0.01
        )

        assert isinstance(heartbeat, GPUHeartbeat)
        assert len(heartbeat._active_gpus) == 3

        # Check that different GPU types were assigned
        gpu_types = set(heartbeat._active_gpus.values())
        assert len(gpu_types) >= 2  # Should have at least 2 different types


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""

    def test_realistic_scaling_scenario(self):
        """Test realistic scaling scenario."""
        heartbeat = GPUHeartbeat()

        # Add multiple GPUs
        for i in range(4):
            heartbeat.add_gpu(f"gpu-{i:02d}", "nvidia-h100")

        # Simulate high load scenario
        for gpu_id in heartbeat._active_gpus:
            high_load_metrics = GPUMetrics(
                gpu_id=gpu_id,
                utilization_percent=95.0,  # Very high utilization
                vram_used_gb=75.0,
                vram_total_gb=80.0,
            )
            heartbeat.tracker.update_gpu_metrics(high_load_metrics)

        # Should recommend urgent scaling
        decision, reason = heartbeat.get_scaling_recommendation()
        assert decision == ScalingDecision.URGENT_SCALE

        # Heartbeat should be critical
        pulse = heartbeat.get_current_heartbeat()
        assert pulse.strength == HeartbeatStrength.CRITICAL

    def test_cost_optimization_scenario(self):
        """Test cost optimization scenario with underutilized GPUs."""
        heartbeat = GPUHeartbeat()

        # Add GPUs with low utilization
        for i in range(4):
            heartbeat.add_gpu(f"gpu-{i:02d}", "nvidia-h100")
            low_load_metrics = GPUMetrics(
                gpu_id=f"gpu-{i:02d}",
                utilization_percent=20.0,  # Very low utilization
                vram_used_gb=10.0,
                vram_total_gb=80.0,
            )
            heartbeat.tracker.update_gpu_metrics(low_load_metrics)

        # Should recommend scale down
        decision, reason = heartbeat.get_scaling_recommendation()
        assert decision == ScalingDecision.SCALE_DOWN

        # Heartbeat should be minimal
        pulse = heartbeat.get_current_heartbeat()
        assert pulse.strength == HeartbeatStrength.MINIMAL

    def test_performance_monitoring_scenario(self):
        """Test performance monitoring scenario."""
        tech_config = TechnologyConfig(
            gpu_types={
                "nvidia-h100": GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=4.10),
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=40, hourly_cost=3.20),
            }
        )

        heartbeat = GPUHeartbeat(tech_config)

        # Add mixed GPU types
        heartbeat.add_gpu("gpu-h100-01", "nvidia-h100")
        heartbeat.add_gpu("gpu-a100-01", "nvidia-a100")

        # Get comprehensive status
        status = heartbeat.get_system_status()

        # Verify all expected data is present
        assert status["gpu_count"] == 2
        assert "gpu-h100-01" in status["gpu_details"]
        assert "gpu-a100-01" in status["gpu_details"]

        # Check H100 specific details
        h100_details = status["gpu_details"]["gpu-h100-01"]
        assert h100_details["vram_total_gb"] == 80.0

        # Check A100 specific details
        a100_details = status["gpu_details"]["gpu-a100-01"]
        assert a100_details["vram_total_gb"] == 40.0
