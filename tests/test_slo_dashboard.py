#!/usr/bin/env python3
"""Tests for SLO dashboard visualization."""

import time
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from mtop.config_loader import SLOConfig
from mtop.slo_convergence import ActionType, ConvergenceAction, ConvergenceMetrics
from mtop.slo_dashboard import GaugeConfig, SLODashboard


@pytest.fixture
def slo_config():
    """Create test SLO configuration."""
    return SLOConfig(
        ttft_p95_ms=250.0,
        tokens_per_second=1000.0,
        error_rate_percent=1.0,
    )


@pytest.fixture
def dashboard(slo_config):
    """Create test dashboard."""
    console = Console(force_terminal=True, width=120)
    return SLODashboard(slo_config, console)


@pytest.fixture
def sample_metrics():
    """Create sample convergence metrics."""
    metrics = ConvergenceMetrics(
        current_ttft_p95=300.0,
        target_ttft_p95=250.0,
        current_cost_per_million=0.30,
        target_cost_per_million=0.25,
        current_throughput=900.0,
        target_throughput=1000.0,
    )
    metrics.ttft_compliance = False
    metrics.cost_compliance = False
    metrics.throughput_compliance = False
    metrics.convergence_score = 0.75
    metrics.stability_score = 0.8
    return metrics


@pytest.fixture
def sample_action():
    """Create sample convergence action."""
    return ConvergenceAction(
        timestamp=time.time(),
        action_type=ActionType.SCALE_UP,
        description="Scale up for performance",
        reasoning="TTFT exceeds target",
        expected_impact="Reduce TTFT by 20%",
        success=True,
        actual_impact="TTFT reduced by 25%",
    )


class TestGaugeConfig:
    """Test GaugeConfig dataclass."""

    def test_gauge_config_creation(self):
        """Test creating gauge configuration."""
        config = GaugeConfig(
            title="Test Gauge",
            current_value=100.0,
            target_value=200.0,
            critical_value=300.0,
            unit="ms",
            is_lower_better=True,
            format_string="{:.1f}",
        )
        assert config.title == "Test Gauge"
        assert config.current_value == 100.0
        assert config.target_value == 200.0
        assert config.critical_value == 300.0
        assert config.unit == "ms"
        assert config.is_lower_better is True
        assert config.format_string == "{:.1f}"

    def test_gauge_config_defaults(self):
        """Test gauge config default values."""
        config = GaugeConfig(
            title="Test",
            current_value=None,
            target_value=100.0,
            critical_value=200.0,
            unit="units",
        )
        assert config.is_lower_better is True
        assert config.format_string == "{:.1f}"


class TestSLODashboard:
    """Test SLODashboard class."""

    def test_dashboard_initialization(self, slo_config):
        """Test dashboard initialization."""
        dashboard = SLODashboard(slo_config)

        # Check gauge configurations
        assert dashboard.ttft_gauge_config.target_value == 250.0
        assert dashboard.ttft_gauge_config.critical_value == 500.0
        assert dashboard.cost_gauge_config.target_value == 0.25
        assert dashboard.cost_gauge_config.critical_value == 0.40

        # Check history initialization
        assert len(dashboard.metrics_history) == 0
        assert len(dashboard.action_history) == 0

    def test_update_metrics(self, dashboard, sample_metrics):
        """Test updating dashboard metrics."""
        dashboard.update_metrics(sample_metrics)

        # Check gauge values updated
        assert dashboard.ttft_gauge_config.current_value == 300.0
        assert dashboard.cost_gauge_config.current_value == 0.30

        # Check history updated
        assert len(dashboard.metrics_history) == 1
        history_entry = dashboard.metrics_history[0]
        assert history_entry["ttft"] == 300.0
        assert history_entry["cost"] == 0.30
        assert history_entry["convergence_score"] == 0.75
        assert history_entry["stability_score"] == 0.8

    def test_add_action(self, dashboard, sample_action):
        """Test adding action to history."""
        dashboard.add_action(sample_action)

        assert len(dashboard.action_history) == 1
        assert dashboard.action_history[0] == sample_action

    def test_create_gauge_no_data(self, dashboard):
        """Test gauge creation with no data."""
        config = GaugeConfig(
            title="Test Gauge",
            current_value=None,
            target_value=100.0,
            critical_value=200.0,
            unit="units",
        )

        panel = dashboard.create_gauge(config)
        assert panel is not None
        assert panel.title == "Test Gauge"

    def test_create_gauge_in_target_zone(self, dashboard):
        """Test gauge creation when value is in target zone."""
        config = GaugeConfig(
            title="TTFT",
            current_value=200.0,  # Below target of 250
            target_value=250.0,
            critical_value=500.0,
            unit="ms",
            is_lower_better=True,
        )

        panel = dashboard.create_gauge(config)
        assert panel is not None
        # Panel should have green border for good status
        assert "green" in str(panel.border_style)

    def test_create_gauge_in_warning_zone(self, dashboard):
        """Test gauge creation when value is in warning zone."""
        config = GaugeConfig(
            title="TTFT",
            current_value=400.0,  # Between target (250) and critical (500)
            target_value=250.0,
            critical_value=500.0,
            unit="ms",
            is_lower_better=True,
        )

        panel = dashboard.create_gauge(config)
        assert panel is not None
        # Panel should have yellow border for warning status
        assert "yellow" in str(panel.border_style)

    def test_create_gauge_critical(self, dashboard):
        """Test gauge creation when value is critical."""
        config = GaugeConfig(
            title="TTFT",
            current_value=600.0,  # Above critical (500)
            target_value=250.0,
            critical_value=500.0,
            unit="ms",
            is_lower_better=True,
        )

        panel = dashboard.create_gauge(config)
        assert panel is not None
        # Panel should have red border for critical status
        assert "red" in str(panel.border_style)

    def test_create_gauge_higher_better(self, dashboard):
        """Test gauge for metrics where higher is better."""
        config = GaugeConfig(
            title="Throughput",
            current_value=1200.0,  # Above target
            target_value=1000.0,
            critical_value=500.0,
            unit="tok/s",
            is_lower_better=False,
        )

        panel = dashboard.create_gauge(config)
        assert panel is not None
        # Should be green when above target for higher-is-better metrics
        assert "green" in str(panel.border_style)

    def test_create_convergence_trajectory_no_data(self, dashboard):
        """Test convergence trajectory with no data."""
        panel = dashboard.create_convergence_trajectory()
        assert panel is not None
        assert panel.title == "Convergence Trajectory"

    def test_create_convergence_trajectory_with_data(self, dashboard, sample_metrics):
        """Test convergence trajectory with data."""
        # Add multiple data points
        for i in range(5):
            metrics = ConvergenceMetrics(
                current_ttft_p95=300.0 - i * 10,
                target_ttft_p95=250.0,
                current_cost_per_million=0.30 - i * 0.01,
                target_cost_per_million=0.25,
            )
            metrics.convergence_score = 0.7 + i * 0.05
            metrics.stability_score = 0.8
            dashboard.update_metrics(metrics)

        panel = dashboard.create_convergence_trajectory()
        assert panel is not None
        assert panel.title == "Convergence Trajectory"

    def test_create_decision_history_no_data(self, dashboard):
        """Test decision history with no data."""
        panel = dashboard.create_decision_history()
        assert panel is not None
        assert panel.title == "Decision History"

    def test_create_decision_history_with_data(self, dashboard, sample_action):
        """Test decision history with actions."""
        # Add multiple actions
        for i in range(3):
            action = ConvergenceAction(
                timestamp=time.time() - i * 60,
                action_type=ActionType.SCALE_UP if i % 2 == 0 else ActionType.SCALE_DOWN,
                description=f"Action {i}",
                reasoning=f"Reason {i}",
                expected_impact=f"Impact {i}",
                success=i < 2,
                actual_impact=f"Actual impact {i}" if i < 2 else None,
            )
            dashboard.add_action(action)

        panel = dashboard.create_decision_history()
        assert panel is not None
        assert panel.title == "Decision History"

    def test_create_slo_summary_no_data(self, dashboard):
        """Test SLO summary with no data."""
        panel = dashboard.create_slo_summary()
        assert panel is not None
        assert panel.title == "SLO Compliance"

    def test_create_slo_summary_all_compliant(self, dashboard):
        """Test SLO summary when all SLOs are met."""
        metrics = ConvergenceMetrics(
            current_ttft_p95=200.0,
            target_ttft_p95=250.0,
            current_cost_per_million=0.20,
            target_cost_per_million=0.25,
        )
        metrics.ttft_compliance = True
        metrics.cost_compliance = True
        dashboard.update_metrics(metrics)

        panel = dashboard.create_slo_summary()
        assert panel is not None

    def test_create_slo_summary_violations(self, dashboard, sample_metrics):
        """Test SLO summary with violations."""
        dashboard.update_metrics(sample_metrics)

        panel = dashboard.create_slo_summary()
        assert panel is not None

    def test_render_complete_dashboard(self, dashboard, sample_metrics, sample_action):
        """Test rendering complete dashboard."""
        dashboard.update_metrics(sample_metrics)
        dashboard.add_action(sample_action)

        group = dashboard.render()
        assert group is not None

    def test_metrics_history_max_length(self, dashboard):
        """Test that metrics history respects max length."""
        # Add more than maxlen entries
        for i in range(70):
            metrics = ConvergenceMetrics(
                current_ttft_p95=250.0,
                target_ttft_p95=250.0,
                current_cost_per_million=0.25,
                target_cost_per_million=0.25,
            )
            dashboard.update_metrics(metrics)

        # Should only keep last 60 entries
        assert len(dashboard.metrics_history) == 60

    def test_action_history_max_length(self, dashboard):
        """Test that action history respects max length."""
        # Add more than maxlen entries
        for i in range(15):
            action = ConvergenceAction(
                timestamp=time.time(),
                action_type=ActionType.NO_ACTION,
                description=f"Action {i}",
                reasoning="Test",
                expected_impact="None",
            )
            dashboard.add_action(action)

        # Should only keep last 10 entries
        assert len(dashboard.action_history) == 10

    @patch("time.sleep")
    def test_live_update_keyboard_interrupt(self, mock_sleep, dashboard):
        """Test live update handling keyboard interrupt."""
        mock_callback = MagicMock()
        mock_callback.side_effect = KeyboardInterrupt()

        # Should exit gracefully
        dashboard.live_update(mock_callback, refresh_rate=1.0)

    @patch("time.sleep")
    def test_live_update_error_handling(self, mock_sleep, dashboard):
        """Test live update error handling."""
        mock_callback = MagicMock()
        # First call raises error, second raises KeyboardInterrupt to exit
        mock_callback.side_effect = [Exception("Test error"), KeyboardInterrupt()]

        # Should handle error and continue
        dashboard.live_update(mock_callback, refresh_rate=1.0)

        # Should have called callback twice
        assert mock_callback.call_count == 2


class TestDemoFunction:
    """Test the demo function."""

    @patch("mtop.slo_dashboard.Console")
    @patch("time.sleep")
    def test_demo_dashboard(self, mock_sleep, mock_console):
        """Test demo dashboard function."""
        # Make it exit after a few iterations
        mock_sleep.side_effect = [None, None, KeyboardInterrupt()]

        from mtop.slo_dashboard import demo_dashboard

        # Should run without errors
        demo_dashboard()

        # Console should have been used
        assert mock_console.called
