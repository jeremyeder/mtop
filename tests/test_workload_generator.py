#!/usr/bin/env python3
"""
Test suite for workload pattern generator.
"""

import pytest
import time
from unittest.mock import Mock, patch

from mtop.workload_generator import (
    WorkloadGenerator, 
    LoadController,
    SpikePattern,
    DeploymentEvent,
    WorkloadEvent,
    EventType,
    WorkloadType
)
from config_loader import WorkloadConfig, SLOConfig


class TestSpikePattern:
    """Test spike pattern configuration."""
    
    def test_valid_spike_pattern(self):
        """Test valid spike pattern creation."""
        spike = SpikePattern(
            magnitude=3.5,
            ramp_time=30.0,
            duration=120.0,
            cooldown_time=60.0
        )
        
        assert spike.magnitude == 3.5
        assert spike.ramp_time == 30.0
        assert spike.duration == 120.0
        assert spike.cooldown_time == 60.0
        assert spike.jitter_factor == 0.1  # default
    
    def test_spike_pattern_validation(self):
        """Test spike pattern validation."""
        with pytest.raises(ValueError, match="Spike magnitude must be >= 1.0"):
            SpikePattern(magnitude=0.5, ramp_time=30.0, duration=120.0, cooldown_time=60.0)
        
        with pytest.raises(ValueError, match="Ramp time must be positive"):
            SpikePattern(magnitude=2.0, ramp_time=-10.0, duration=120.0, cooldown_time=60.0)
        
        with pytest.raises(ValueError, match="Duration must be positive"):
            SpikePattern(magnitude=2.0, ramp_time=30.0, duration=-120.0, cooldown_time=60.0)
        
        with pytest.raises(ValueError, match="Cooldown time must be positive"):
            SpikePattern(magnitude=2.0, ramp_time=30.0, duration=120.0, cooldown_time=-60.0)
        
        with pytest.raises(ValueError, match="Jitter factor must be 0-1"):
            SpikePattern(magnitude=2.0, ramp_time=30.0, duration=120.0, cooldown_time=60.0, jitter_factor=1.5)


class TestDeploymentEvent:
    """Test deployment event configuration."""
    
    def test_valid_deployment_event(self):
        """Test valid deployment event creation."""
        deployment = DeploymentEvent(
            model_name="gpt-4-optimized",
            deployment_time=180.0,
            traffic_shift_percentage=75.0,
            resource_overhead=0.3
        )
        
        assert deployment.model_name == "gpt-4-optimized"
        assert deployment.deployment_time == 180.0
        assert deployment.traffic_shift_percentage == 75.0
        assert deployment.resource_overhead == 0.3
        assert deployment.canary_percentage == 10.0  # default
    
    def test_deployment_event_validation(self):
        """Test deployment event validation."""
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            DeploymentEvent(
                model_name="",
                deployment_time=180.0,
                traffic_shift_percentage=75.0,
                resource_overhead=0.3
            )
        
        with pytest.raises(ValueError, match="Deployment time must be positive"):
            DeploymentEvent(
                model_name="test-model",
                deployment_time=-180.0,
                traffic_shift_percentage=75.0,
                resource_overhead=0.3
            )
        
        with pytest.raises(ValueError, match="Traffic shift must be 0-100%"):
            DeploymentEvent(
                model_name="test-model",
                deployment_time=180.0,
                traffic_shift_percentage=150.0,
                resource_overhead=0.3
            )
        
        with pytest.raises(ValueError, match="Resource overhead must be 0-1"):
            DeploymentEvent(
                model_name="test-model",
                deployment_time=180.0,
                traffic_shift_percentage=75.0,
                resource_overhead=1.5
            )


class TestWorkloadEvent:
    """Test workload event configuration."""
    
    def test_valid_workload_event(self):
        """Test valid workload event creation."""
        event = WorkloadEvent(
            event_type=EventType.TRAFFIC_SPIKE,
            start_time=time.time(),
            duration=120.0,
            magnitude=3.5,
            description="Test spike event"
        )
        
        assert event.event_type == EventType.TRAFFIC_SPIKE
        assert event.duration == 120.0
        assert event.magnitude == 3.5
        assert event.description == "Test spike event"
        assert event.metadata == {}
    
    def test_workload_event_validation(self):
        """Test workload event validation."""
        with pytest.raises(ValueError, match="Duration must be positive"):
            WorkloadEvent(
                event_type=EventType.TRAFFIC_SPIKE,
                start_time=time.time(),
                duration=-120.0,
                magnitude=3.5,
                description="Test spike event"
            )
        
        with pytest.raises(ValueError, match="Magnitude cannot be negative"):
            WorkloadEvent(
                event_type=EventType.TRAFFIC_SPIKE,
                start_time=time.time(),
                duration=120.0,
                magnitude=-3.5,
                description="Test spike event"
            )
        
        with pytest.raises(ValueError, match="Description cannot be empty"):
            WorkloadEvent(
                event_type=EventType.TRAFFIC_SPIKE,
                start_time=time.time(),
                duration=120.0,
                magnitude=3.5,
                description=""
            )


class TestWorkloadGenerator:
    """Test workload generator functionality."""
    
    @pytest.fixture
    def workload_config(self):
        """Create test workload configuration."""
        return WorkloadConfig(baseline_qps=100, spike_multiplier=2.0)
    
    @pytest.fixture
    def slo_config(self):
        """Create test SLO configuration."""
        return SLOConfig(ttft_p95_ms=500, error_rate_percent=0.1, tokens_per_second=1000)
    
    @pytest.fixture
    def workload_generator(self, workload_config, slo_config):
        """Create test workload generator."""
        return WorkloadGenerator(workload_config, slo_config)
    
    def test_workload_generator_initialization(self, workload_generator, workload_config):
        """Test workload generator initialization."""
        assert workload_generator.workload_config == workload_config
        assert workload_generator.current_qps == workload_config.baseline_qps
        assert workload_generator.active_events == []
        assert workload_generator.event_history == []
        assert workload_generator.default_spike.magnitude == 3.5
        assert workload_generator.default_spike.ramp_time == 30.0
        assert workload_generator.default_spike.duration == 120.0
        assert workload_generator.default_spike.cooldown_time == 60.0
    
    def test_baseline_qps(self, workload_generator):
        """Test baseline QPS generation."""
        # Without any events, should return baseline QPS with jitter
        qps = workload_generator.get_current_qps()
        assert 90 <= qps <= 110  # Allow for 10% jitter
    
    def test_traffic_spike_trigger(self, workload_generator):
        """Test traffic spike event triggering."""
        event = workload_generator.trigger_traffic_spike()
        
        assert event.event_type == EventType.TRAFFIC_SPIKE
        assert event.magnitude == 3.5
        assert event.description.startswith("Traffic spike: 3.5x")
        assert event in workload_generator.active_events
    
    def test_traffic_spike_calculation(self, workload_generator):
        """Test traffic spike QPS calculation."""
        # Trigger spike
        event = workload_generator.trigger_traffic_spike()
        
        # Immediately after trigger should be ramping up
        qps = workload_generator.get_current_qps()
        assert qps >= 95  # Should be at or above baseline (allowing for jitter)
        
        # Mock time to simulate peak
        with patch('time.time', return_value=event.start_time + 60):  # Peak time
            qps = workload_generator.get_current_qps()
            assert qps > 300  # Should be near peak (3.5x * 100)
    
    def test_model_deployment_trigger(self, workload_generator):
        """Test model deployment event triggering."""
        deployment = DeploymentEvent(
            model_name="test-model",
            deployment_time=180.0,
            traffic_shift_percentage=50.0,
            resource_overhead=0.3
        )
        
        event = workload_generator.trigger_model_deployment(deployment)
        
        assert event.event_type == EventType.MODEL_DEPLOYMENT
        assert event.magnitude == 0.3
        assert "test-model" in event.description
        assert event in workload_generator.active_events
    
    def test_scale_event_trigger(self, workload_generator):
        """Test scale event triggering."""
        event = workload_generator.trigger_scale_event(2.0, 120.0)
        
        assert event.event_type == EventType.SCALE_EVENT
        assert event.magnitude == 2.0
        assert event.duration == 120.0
        assert event in workload_generator.active_events
    
    def test_event_cleanup(self, workload_generator):
        """Test event cleanup after expiration."""
        # Trigger short event
        event = workload_generator.trigger_scale_event(2.0, 0.1)  # 0.1 second duration
        
        # Wait for event to expire
        time.sleep(0.2)
        
        # Check that event is cleaned up
        qps = workload_generator.get_current_qps()
        assert event not in workload_generator.active_events
        assert event in workload_generator.event_history
    
    def test_reset_functionality(self, workload_generator):
        """Test reset functionality."""
        # Add some events
        workload_generator.trigger_traffic_spike()
        workload_generator.trigger_scale_event(2.0, 60.0)
        
        # Reset
        workload_generator.reset()
        
        assert workload_generator.active_events == []
        assert workload_generator.event_history == []
        assert workload_generator.current_qps == 100  # baseline


class TestLoadController:
    """Test load controller functionality."""
    
    @pytest.fixture
    def workload_config(self):
        """Create test workload configuration."""
        return WorkloadConfig(baseline_qps=100, spike_multiplier=2.0)
    
    @pytest.fixture
    def workload_generator(self, workload_config):
        """Create test workload generator."""
        return WorkloadGenerator(workload_config)
    
    @pytest.fixture
    def load_controller(self, workload_generator):
        """Create test load controller."""
        return LoadController(workload_generator)
    
    def test_load_controller_initialization(self, load_controller):
        """Test load controller initialization."""
        assert load_controller.manual_multiplier == 1.0
        assert load_controller.get_manual_multiplier() == 1.0
    
    def test_manual_multiplier_setting(self, load_controller):
        """Test manual multiplier setting."""
        load_controller.set_manual_multiplier(2.5)
        assert load_controller.get_manual_multiplier() == 2.5
        
        with pytest.raises(ValueError, match="Manual multiplier cannot be negative"):
            load_controller.set_manual_multiplier(-1.0)
    
    def test_effective_qps_calculation(self, load_controller):
        """Test effective QPS calculation with manual multiplier."""
        load_controller.set_manual_multiplier(2.0)
        effective_qps = load_controller.get_effective_qps()
        
        # Should be approximately 2x baseline (allowing for jitter)
        assert 180 <= effective_qps <= 220
    
    def test_custom_spike_creation(self, load_controller):
        """Test custom spike pattern creation."""
        spike = load_controller.create_custom_spike(4.0, 240.0)
        
        assert spike.magnitude == 4.0
        assert spike.ramp_time == 30.0  # min(30.0, 240 * 0.25)
        assert spike.duration == 120.0  # 50% of 240
        assert spike.cooldown_time == 60.0  # min(60.0, 240 * 0.25)
    
    def test_deployment_scenario_creation(self, load_controller):
        """Test deployment scenario creation."""
        deployment = load_controller.create_deployment_scenario("test-model", 80.0)
        
        assert deployment.model_name == "test-model"
        assert deployment.deployment_time == 180.0
        assert deployment.traffic_shift_percentage == 80.0
        assert deployment.resource_overhead == 0.3
        assert deployment.canary_percentage == 10.0
    
    @patch('time.sleep')
    def test_realistic_load_simulation(self, mock_sleep, load_controller):
        """Test realistic load simulation."""
        events = load_controller.simulate_realistic_load(300.0)
        
        # Should create 3 events: small spike, deployment, major spike
        assert len(events) == 3
        
        # Check that sleep was called for timing
        assert mock_sleep.call_count >= 2


class TestIntegration:
    """Integration tests for workload generator system."""
    
    def test_workload_generator_integration(self):
        """Test complete workload generator integration."""
        # Create realistic configuration
        workload_config = WorkloadConfig(baseline_qps=100, spike_multiplier=2.0)
        slo_config = SLOConfig(ttft_p95_ms=500, error_rate_percent=0.1, tokens_per_second=1000)
        
        # Create generator and controller
        generator = WorkloadGenerator(workload_config, slo_config)
        controller = LoadController(generator)
        
        # Simulate realistic scenario
        controller.set_manual_multiplier(1.5)
        
        # Trigger traffic spike
        spike_event = generator.trigger_traffic_spike()
        
        # Get current load
        qps = controller.get_effective_qps()
        
        # Should be elevated due to manual multiplier and spike
        assert qps > 150  # Above baseline * multiplier
        
        # Verify event tracking
        assert len(generator.get_active_events()) == 1
        assert generator.get_active_events()[0] == spike_event
    
    def test_concurrent_events(self):
        """Test handling of concurrent workload events."""
        workload_config = WorkloadConfig(baseline_qps=100, spike_multiplier=2.0)
        generator = WorkloadGenerator(workload_config)
        
        # Trigger multiple concurrent events
        spike_event = generator.trigger_traffic_spike()
        scale_event = generator.trigger_scale_event(1.5, 60.0)
        
        # Should handle both events
        assert len(generator.get_active_events()) == 2
        
        # QPS should be affected by both events
        qps = generator.get_current_qps()
        assert qps > 150  # Should be above baseline due to combined effects (adjusted for realistic expectations)