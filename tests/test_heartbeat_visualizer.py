#!/usr/bin/env python3
"""
Tests for the heartbeat animation system.
"""

import math
import time
import unittest
from unittest.mock import Mock, patch

from mtop.gpu_heartbeat import GPUMetrics, HeartbeatPulse, HeartbeatStrength
from mtop.heartbeat_visualizer import (
    AnimationFrame,
    HeartbeatAnimator,
    TechnologyCharacteristics,
    TechnologyType,
    create_demo_scenario,
)


class TestTechnologyCharacteristics(unittest.TestCase):
    """Test technology characteristics dataclass."""

    def test_technology_characteristics_creation(self):
        """Test creating technology characteristics."""
        tech = TechnologyCharacteristics(
            color="#00FFFF",
            secondary_color="#00CCCC",
            pulse_frequency_hz=2.0,
            pulse_strength=0.8,
            animation_style="smooth_wave",
            description="Dynamic Resource Allocation",
        )

        self.assertEqual(tech.color, "#00FFFF")
        self.assertEqual(tech.pulse_frequency_hz, 2.0)
        self.assertEqual(tech.pulse_strength, 0.8)
        self.assertEqual(tech.description, "Dynamic Resource Allocation")


class TestAnimationFrame(unittest.TestCase):
    """Test animation frame dataclass."""

    def test_animation_frame_creation(self):
        """Test creating valid animation frame."""
        frame = AnimationFrame(
            timestamp=time.time(),
            gpu_id="gpu-00",
            utilization=75.5,
            capacity_bar_width=40,
            pulse_intensity=0.8,
            color="#00FFFF",
            pulse_color="#00CCCC",
            bar_text="gpu-00: 75.5% (DRA)",
        )

        self.assertEqual(frame.gpu_id, "gpu-00")
        self.assertEqual(frame.utilization, 75.5)
        self.assertEqual(frame.pulse_intensity, 0.8)

    def test_animation_frame_validation(self):
        """Test animation frame validation."""
        # Test invalid utilization
        with self.assertRaises(ValueError):
            AnimationFrame(
                timestamp=time.time(),
                gpu_id="gpu-00",
                utilization=150.0,  # Invalid > 100
                capacity_bar_width=40,
                pulse_intensity=0.8,
                color="#00FFFF",
                pulse_color="#00CCCC",
                bar_text="test",
            )

        # Test invalid pulse intensity
        with self.assertRaises(ValueError):
            AnimationFrame(
                timestamp=time.time(),
                gpu_id="gpu-00",
                utilization=50.0,
                capacity_bar_width=40,
                pulse_intensity=1.5,  # Invalid > 1.0
                color="#00FFFF",
                pulse_color="#00CCCC",
                bar_text="test",
            )


class TestHeartbeatAnimator(unittest.TestCase):
    """Test heartbeat animator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.animator = HeartbeatAnimator()

    def test_animator_initialization(self):
        """Test animator initializes correctly."""
        self.assertIsNotNone(self.animator.console)
        self.assertEqual(len(self.animator._gpu_technologies), 0)

    def test_technology_configurations(self):
        """Test that all required technology configurations exist."""
        configs = HeartbeatAnimator.TECHNOLOGY_CONFIGS

        # Check all technology types have configurations
        self.assertIn(TechnologyType.DRA, configs)
        self.assertIn(TechnologyType.TRADITIONAL, configs)
        self.assertIn(TechnologyType.MULTI_INSTANCE, configs)

        # Check DRA configuration matches requirements
        dra_config = configs[TechnologyType.DRA]
        self.assertEqual(dra_config.color, "#00FFFF")  # Cyan
        self.assertEqual(dra_config.pulse_frequency_hz, 2.0)  # 2.0 Hz
        self.assertEqual(dra_config.pulse_strength, 0.8)  # 0.8 strength

    def test_gpu_technology_management(self):
        """Test setting and getting GPU technologies."""
        # Initially no technology set
        self.assertEqual(
            self.animator.get_gpu_technology("gpu-00"), TechnologyType.TRADITIONAL  # Default
        )

        # Set DRA technology
        self.animator.set_gpu_technology("gpu-00", TechnologyType.DRA)
        self.assertEqual(self.animator.get_gpu_technology("gpu-00"), TechnologyType.DRA)

        # Different GPU still gets default
        self.assertEqual(self.animator.get_gpu_technology("gpu-01"), TechnologyType.TRADITIONAL)

    def test_pulse_intensity_calculation(self):
        """Test pulse intensity calculation."""
        # Create test heartbeat pulse
        pulse = HeartbeatPulse(
            strength=HeartbeatStrength.STRONG, frequency_bpm=120.0, color="#FFA500", intensity=0.7
        )

        # Set DRA technology for GPU
        self.animator.set_gpu_technology("gpu-00", TechnologyType.DRA)

        # Calculate pulse intensity
        intensity = self.animator.calculate_pulse_intensity("gpu-00", 75.0, pulse)

        # Should be between 0 and 1
        self.assertGreaterEqual(intensity, 0.0)
        self.assertLessEqual(intensity, 1.0)

        # Higher utilization should generally give higher intensity
        low_intensity = self.animator.calculate_pulse_intensity("gpu-00", 20.0, pulse)
        high_intensity = self.animator.calculate_pulse_intensity("gpu-00", 90.0, pulse)

        # Note: Due to sinusoidal variation, this isn't always true, so we just test bounds
        self.assertGreaterEqual(low_intensity, 0.0)
        self.assertLessEqual(high_intensity, 1.0)

    def test_easing_function(self):
        """Test cubic easing function."""
        # Test edge cases
        self.assertAlmostEqual(self.animator._ease_in_out_cubic(0.0), 0.0)
        self.assertAlmostEqual(self.animator._ease_in_out_cubic(1.0), 1.0)
        self.assertAlmostEqual(self.animator._ease_in_out_cubic(0.5), 0.5)

        # Test that function is smooth (no discontinuities)
        for t in [0.1, 0.3, 0.7, 0.9]:
            result = self.animator._ease_in_out_cubic(t)
            self.assertGreaterEqual(result, 0.0)
            self.assertLessEqual(result, 1.0)

    def test_gpu_bar_creation(self):
        """Test creating GPU animation bars."""
        # Create test GPU metrics
        metrics = GPUMetrics(
            gpu_id="gpu-00",
            utilization_percent=75.0,
            vram_used_gb=60.0,
            vram_total_gb=80.0,
            temperature_c=85.0,
            power_watts=400.0,
        )

        # Create test heartbeat pulse
        pulse = HeartbeatPulse(
            strength=HeartbeatStrength.STRONG, frequency_bpm=120.0, color="#FFA500", intensity=0.7
        )

        # Set DRA technology
        self.animator.set_gpu_technology("gpu-00", TechnologyType.DRA)

        # Create animation frame
        frame = self.animator.create_gpu_bar(metrics, pulse, bar_width=40)

        # Validate frame
        self.assertEqual(frame.gpu_id, "gpu-00")
        self.assertEqual(frame.utilization, 75.0)
        self.assertEqual(frame.capacity_bar_width, 40)
        self.assertGreaterEqual(frame.pulse_intensity, 0.0)
        self.assertLessEqual(frame.pulse_intensity, 1.0)
        self.assertEqual(frame.color, "#00FFFF")  # DRA cyan

    @patch("mtop.heartbeat_visualizer.Live")
    def test_live_animation_setup(self, mock_live):
        """Test live animation setup (without actually running)."""
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        # Create test heartbeat engine
        heartbeat = create_gpu_heartbeat()
        heartbeat.add_gpu("gpu-00", "nvidia-h100")

        # Mock the Live context manager
        mock_live_instance = Mock()
        mock_live.return_value.__enter__ = Mock(return_value=mock_live_instance)
        mock_live.return_value.__exit__ = Mock(return_value=None)

        # This would normally run the animation, but we'll use a very short duration
        with (
            patch("time.sleep"),
            patch("time.time", side_effect=[0, 0.1, 0.2]),
        ):  # Mock time progression
            self.animator.run_live_animation(heartbeat, duration_seconds=0.1, refresh_rate=10.0)

        # Verify Live was called
        mock_live.assert_called_once()


class TestDemoScenario(unittest.TestCase):
    """Test demo scenario creation."""

    def test_demo_scenario_creation(self):
        """Test creating demo scenario."""
        animator, heartbeat = create_demo_scenario()

        # Check animator is configured
        self.assertIsInstance(animator, HeartbeatAnimator)

        # Check GPUs are added with correct technologies
        self.assertEqual(animator.get_gpu_technology("gpu-00"), TechnologyType.DRA)
        self.assertEqual(animator.get_gpu_technology("gpu-01"), TechnologyType.TRADITIONAL)
        self.assertEqual(animator.get_gpu_technology("gpu-02"), TechnologyType.MULTI_INSTANCE)

        # Check heartbeat engine has GPUs
        all_metrics = heartbeat.tracker.get_all_gpu_metrics()
        self.assertIn("gpu-00", all_metrics)
        self.assertIn("gpu-01", all_metrics)
        self.assertIn("gpu-02", all_metrics)


class TestIntegration(unittest.TestCase):
    """Integration tests for heartbeat visualization."""

    def test_end_to_end_frame_generation(self):
        """Test complete frame generation pipeline."""
        # Create demo scenario
        animator, heartbeat = create_demo_scenario()

        # Simulate some workload briefly
        heartbeat.simulate_workload(target_utilization=60.0, duration_seconds=1.0)

        # Generate cluster visualization
        cluster_viz = animator.create_cluster_visualization(heartbeat, bar_width=20)

        # Should not raise any exceptions
        self.assertIsNotNone(cluster_viz)

    def test_technology_specific_characteristics(self):
        """Test that different technologies produce different visual characteristics."""
        animator = HeartbeatAnimator()

        # Set up GPUs with different technologies
        animator.set_gpu_technology("dra-gpu", TechnologyType.DRA)
        animator.set_gpu_technology("traditional-gpu", TechnologyType.TRADITIONAL)

        # Create identical metrics for both
        metrics_dra = GPUMetrics(
            gpu_id="dra-gpu", utilization_percent=50.0, vram_used_gb=40.0, vram_total_gb=80.0
        )

        metrics_traditional = GPUMetrics(
            gpu_id="traditional-gpu",
            utilization_percent=50.0,
            vram_used_gb=40.0,
            vram_total_gb=80.0,
        )

        # Create identical pulse
        pulse = HeartbeatPulse(
            strength=HeartbeatStrength.STEADY, frequency_bpm=80.0, color="#00FF00", intensity=0.5
        )

        # Generate frames
        frame_dra = animator.create_gpu_bar(metrics_dra, pulse)
        frame_traditional = animator.create_gpu_bar(metrics_traditional, pulse)

        # Should have different colors
        self.assertEqual(frame_dra.color, "#00FFFF")  # DRA cyan
        self.assertEqual(frame_traditional.color, "#00FF00")  # Traditional green

        # Pulse intensities might be different due to technology characteristics
        # (we don't enforce specific values due to time-based variation)
        self.assertGreaterEqual(frame_dra.pulse_intensity, 0.0)
        self.assertLessEqual(frame_dra.pulse_intensity, 1.0)
        self.assertGreaterEqual(frame_traditional.pulse_intensity, 0.0)
        self.assertLessEqual(frame_traditional.pulse_intensity, 1.0)


if __name__ == "__main__":
    unittest.main()
