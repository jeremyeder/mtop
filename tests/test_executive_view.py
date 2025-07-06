#!/usr/bin/env python3
"""
Tests for the executive view dashboard system.
"""

import time
import unittest
from unittest.mock import Mock, patch

from mtop.executive_view import (
    BusinessMetricType,
    CostOptimizationMetrics,
    EfficiencyMetrics,
    ExecutiveSummary,
    ExecutiveViewDashboard,
    SLOComplianceMetrics,
    create_demo_executive_view,
)
from mtop.gpu_heartbeat import GPUMetrics
from mtop.slo_convergence import ConvergenceMetrics


class TestCostOptimizationMetrics(unittest.TestCase):
    """Test cost optimization metrics dataclass."""

    def test_cost_metrics_creation(self):
        """Test creating valid cost metrics."""
        metrics = CostOptimizationMetrics(
            baseline_monthly_cost=50000.0,
            current_monthly_cost=35000.0,
            monthly_savings=15000.0,
            savings_percentage=30.0,
            annual_projected_savings=180000.0,
            roi_percentage=180.0,
            payback_period_months=6.7,
        )

        self.assertEqual(metrics.baseline_monthly_cost, 50000.0)
        self.assertEqual(metrics.monthly_savings, 15000.0)
        self.assertEqual(metrics.savings_percentage, 30.0)

    def test_cost_metrics_validation(self):
        """Test cost metrics validation."""
        # Test invalid baseline cost
        with self.assertRaises(ValueError):
            CostOptimizationMetrics(
                baseline_monthly_cost=-1000.0,  # Invalid negative
                current_monthly_cost=35000.0,
                monthly_savings=15000.0,
                savings_percentage=30.0,
                annual_projected_savings=180000.0,
                roi_percentage=180.0,
                payback_period_months=6.7,
            )

        # Test invalid current cost
        with self.assertRaises(ValueError):
            CostOptimizationMetrics(
                baseline_monthly_cost=50000.0,
                current_monthly_cost=-5000.0,  # Invalid negative
                monthly_savings=15000.0,
                savings_percentage=30.0,
                annual_projected_savings=180000.0,
                roi_percentage=180.0,
                payback_period_months=6.7,
            )


class TestEfficiencyMetrics(unittest.TestCase):
    """Test efficiency metrics dataclass."""

    def test_efficiency_metrics_creation(self):
        """Test creating valid efficiency metrics."""
        metrics = EfficiencyMetrics(
            average_gpu_utilization=75.5,
            peak_efficiency_achieved=85.0,
            free_gpu_capacity_utilized=60.0,
            elastic_scaling_effectiveness=80.0,
            resource_waste_reduction=90.0,
        )

        self.assertEqual(metrics.average_gpu_utilization, 75.5)
        self.assertEqual(metrics.peak_efficiency_achieved, 85.0)

    def test_efficiency_metrics_validation(self):
        """Test efficiency metrics validation."""
        # Test invalid utilization (> 100%)
        with self.assertRaises(ValueError):
            EfficiencyMetrics(
                average_gpu_utilization=150.0,  # Invalid > 100
                peak_efficiency_achieved=85.0,
                free_gpu_capacity_utilized=60.0,
                elastic_scaling_effectiveness=80.0,
                resource_waste_reduction=90.0,
            )

        # Test invalid negative value
        with self.assertRaises(ValueError):
            EfficiencyMetrics(
                average_gpu_utilization=75.0,
                peak_efficiency_achieved=-10.0,  # Invalid negative
                free_gpu_capacity_utilized=60.0,
                elastic_scaling_effectiveness=80.0,
                resource_waste_reduction=90.0,
            )


class TestSLOComplianceMetrics(unittest.TestCase):
    """Test SLO compliance metrics dataclass."""

    def test_slo_metrics_creation(self):
        """Test creating valid SLO compliance metrics."""
        metrics = SLOComplianceMetrics(
            ttft_compliance_percentage=95.5,
            cost_compliance_percentage=92.0,
            overall_slo_compliance=93.75,
            availability_percentage=99.9,
            performance_consistency=88.0,
        )

        self.assertEqual(metrics.ttft_compliance_percentage, 95.5)
        self.assertEqual(metrics.overall_slo_compliance, 93.75)

    def test_slo_metrics_validation(self):
        """Test SLO metrics validation."""
        # Test invalid percentage > 100
        with self.assertRaises(ValueError):
            SLOComplianceMetrics(
                ttft_compliance_percentage=105.0,  # Invalid > 100
                cost_compliance_percentage=92.0,
                overall_slo_compliance=93.75,
                availability_percentage=99.9,
                performance_consistency=88.0,
            )


class TestExecutiveViewDashboard(unittest.TestCase):
    """Test executive view dashboard functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.dashboard = ExecutiveViewDashboard(baseline_monthly_cost=50000.0)

    def test_dashboard_initialization(self):
        """Test dashboard initializes correctly."""
        self.assertIsNotNone(self.dashboard.console)
        self.assertEqual(self.dashboard.baseline_monthly_cost, 50000.0)
        self.assertEqual(len(self.dashboard.summary_history), 0)

    def test_cost_metrics_calculation(self):
        """Test cost metrics calculation."""
        # Test with 10 GPUs at $2.50/hour
        cost_metrics = self.dashboard.calculate_cost_metrics(
            current_gpu_count=10, gpu_hourly_rate=2.50
        )

        # Expected monthly cost: 24 * 30 * 10 * 2.50 = $18,000
        expected_monthly_cost = 24 * 30 * 10 * 2.50
        self.assertEqual(cost_metrics.current_monthly_cost, expected_monthly_cost)

        # Expected savings: $50,000 - $18,000 = $32,000
        expected_savings = 50000.0 - expected_monthly_cost
        self.assertEqual(cost_metrics.monthly_savings, expected_savings)

        # Expected savings percentage: (32000 / 50000) * 100 = 64%
        expected_percentage = (expected_savings / 50000.0) * 100
        self.assertEqual(cost_metrics.savings_percentage, expected_percentage)

        # Check other fields are calculated
        self.assertIsInstance(cost_metrics.annual_projected_savings, float)
        self.assertIsInstance(cost_metrics.roi_percentage, float)
        self.assertIsInstance(cost_metrics.payback_period_months, float)

    def test_cost_metrics_no_savings(self):
        """Test cost metrics when current cost exceeds baseline."""
        # Test with 30 GPUs (expensive scenario)
        cost_metrics = self.dashboard.calculate_cost_metrics(
            current_gpu_count=30, gpu_hourly_rate=3.00
        )

        # Current cost should exceed baseline
        expected_monthly_cost = 24 * 30 * 30 * 3.00  # $64,800
        self.assertEqual(cost_metrics.current_monthly_cost, expected_monthly_cost)

        # Savings should be 0 (no negative savings)
        self.assertEqual(cost_metrics.monthly_savings, 0.0)
        self.assertEqual(cost_metrics.savings_percentage, 0.0)

    def test_efficiency_metrics_calculation(self):
        """Test efficiency metrics calculation."""
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        # Create heartbeat with test data
        heartbeat = create_gpu_heartbeat()
        heartbeat.add_gpu("gpu-00", "nvidia-h100")
        heartbeat.add_gpu("gpu-01", "nvidia-a100")

        # Update with test metrics
        test_metrics_1 = GPUMetrics(
            gpu_id="gpu-00", utilization_percent=75.0, vram_used_gb=60.0, vram_total_gb=80.0
        )
        test_metrics_2 = GPUMetrics(
            gpu_id="gpu-01", utilization_percent=80.0, vram_used_gb=70.0, vram_total_gb=80.0
        )

        heartbeat.tracker.update_gpu_metrics(test_metrics_1)
        heartbeat.tracker.update_gpu_metrics(test_metrics_2)

        # Calculate efficiency metrics
        efficiency_metrics = self.dashboard.calculate_efficiency_metrics(heartbeat)

        # Average utilization should be (75 + 80) / 2 = 77.5%
        self.assertAlmostEqual(efficiency_metrics.average_gpu_utilization, 77.5, places=1)

        # All metrics should be within valid range
        self.assertGreaterEqual(efficiency_metrics.peak_efficiency_achieved, 0.0)
        self.assertLessEqual(efficiency_metrics.peak_efficiency_achieved, 100.0)
        self.assertGreaterEqual(efficiency_metrics.elastic_scaling_effectiveness, 0.0)
        self.assertLessEqual(efficiency_metrics.elastic_scaling_effectiveness, 100.0)

    def test_efficiency_metrics_no_data(self):
        """Test efficiency metrics with no GPU data."""
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        # Create empty heartbeat
        heartbeat = create_gpu_heartbeat()

        efficiency_metrics = self.dashboard.calculate_efficiency_metrics(heartbeat)

        # All metrics should be 0 when no data
        self.assertEqual(efficiency_metrics.average_gpu_utilization, 0.0)
        self.assertEqual(efficiency_metrics.peak_efficiency_achieved, 0.0)
        self.assertEqual(efficiency_metrics.free_gpu_capacity_utilized, 0.0)
        self.assertEqual(efficiency_metrics.elastic_scaling_effectiveness, 0.0)
        self.assertEqual(efficiency_metrics.resource_waste_reduction, 0.0)

    def test_slo_compliance_calculation_no_data(self):
        """Test SLO compliance calculation with no historical data."""
        slo_metrics = self.dashboard.calculate_slo_compliance_metrics()

        # Should return baseline values when no data
        self.assertEqual(slo_metrics.ttft_compliance_percentage, 95.0)
        self.assertEqual(slo_metrics.cost_compliance_percentage, 90.0)
        self.assertEqual(slo_metrics.overall_slo_compliance, 92.5)
        self.assertEqual(slo_metrics.availability_percentage, 99.5)

    def test_slo_compliance_calculation_with_convergence(self):
        """Test SLO compliance calculation with convergence metrics."""
        # Create test convergence metrics
        convergence_metrics = ConvergenceMetrics(
            current_ttft_p95=200.0,
            target_ttft_p95=250.0,
            current_cost_per_million=0.20,
            target_cost_per_million=0.25,
            convergence_score=0.85,
            stability_score=0.90,
        )

        # Add some mock SLO history
        self.dashboard.slo_history.extend(
            [
                {"ttft_compliance": True, "cost_compliance": True},
                {"ttft_compliance": True, "cost_compliance": False},
                {"ttft_compliance": False, "cost_compliance": True},
                {"ttft_compliance": True, "cost_compliance": True},
            ]
        )

        slo_metrics = self.dashboard.calculate_slo_compliance_metrics(convergence_metrics)

        # TTFT compliance: 3/4 = 75%
        self.assertEqual(slo_metrics.ttft_compliance_percentage, 75.0)
        # Cost compliance: 3/4 = 75%
        self.assertEqual(slo_metrics.cost_compliance_percentage, 75.0)
        # Overall: (75 + 75) / 2 = 75%
        self.assertEqual(slo_metrics.overall_slo_compliance, 75.0)
        # Performance consistency based on stability score: 90%
        self.assertEqual(slo_metrics.performance_consistency, 90.0)

    def test_executive_summary_generation(self):
        """Test complete executive summary generation."""
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        # Create test scenario
        heartbeat = create_gpu_heartbeat()
        heartbeat.add_gpu("gpu-00", "nvidia-h100")
        heartbeat.add_gpu("gpu-01", "nvidia-a100")

        # Generate summary
        summary = self.dashboard.generate_executive_summary(heartbeat)

        # Validate summary structure
        self.assertIsInstance(summary, ExecutiveSummary)
        self.assertIsInstance(summary.cost_metrics, CostOptimizationMetrics)
        self.assertIsInstance(summary.efficiency_metrics, EfficiencyMetrics)
        self.assertIsInstance(summary.slo_metrics, SLOComplianceMetrics)

        # Business impact score should be 0-100
        self.assertGreaterEqual(summary.business_impact_score, 0.0)
        self.assertLessEqual(summary.business_impact_score, 100.0)

        # Should have recommendation
        self.assertIsInstance(summary.recommendation, str)
        self.assertGreater(len(summary.recommendation), 0)

        # Should be added to history
        self.assertEqual(len(self.dashboard.summary_history), 1)

    def test_panel_creation_methods(self):
        """Test Rich panel creation methods."""
        # Create test metrics
        cost_metrics = CostOptimizationMetrics(
            baseline_monthly_cost=50000.0,
            current_monthly_cost=30000.0,
            monthly_savings=20000.0,
            savings_percentage=40.0,
            annual_projected_savings=240000.0,
            roi_percentage=240.0,
            payback_period_months=5.0,
        )

        efficiency_metrics = EfficiencyMetrics(
            average_gpu_utilization=75.0,
            peak_efficiency_achieved=85.0,
            free_gpu_capacity_utilized=60.0,
            elastic_scaling_effectiveness=80.0,
            resource_waste_reduction=90.0,
        )

        slo_metrics = SLOComplianceMetrics(
            ttft_compliance_percentage=95.0,
            cost_compliance_percentage=92.0,
            overall_slo_compliance=93.5,
            availability_percentage=99.8,
            performance_consistency=88.0,
        )

        summary = ExecutiveSummary(
            timestamp=time.time(),
            cost_metrics=cost_metrics,
            efficiency_metrics=efficiency_metrics,
            slo_metrics=slo_metrics,
            business_impact_score=85.0,
            recommendation="Excellent performance",
            key_achievements=["$20k monthly savings", "75% GPU utilization"],
            risk_factors=[],
        )

        # Test panel creation (should not raise exceptions)
        cost_panel = self.dashboard.create_cost_savings_panel(cost_metrics)
        efficiency_panel = self.dashboard.create_efficiency_panel(efficiency_metrics)
        slo_panel = self.dashboard.create_slo_compliance_panel(slo_metrics)
        impact_panel = self.dashboard.create_business_impact_panel(summary)
        dashboard = self.dashboard.create_executive_dashboard(summary)

        # All should be Rich objects
        self.assertIsNotNone(cost_panel)
        self.assertIsNotNone(efficiency_panel)
        self.assertIsNotNone(slo_panel)
        self.assertIsNotNone(impact_panel)
        self.assertIsNotNone(dashboard)

    @patch("mtop.executive_view.Live")
    def test_live_dashboard_setup(self, mock_live):
        """Test live dashboard setup (without actually running)."""
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        # Create test heartbeat
        heartbeat = create_gpu_heartbeat()
        heartbeat.add_gpu("gpu-00", "nvidia-h100")

        # Mock Live context manager
        mock_live_instance = Mock()
        mock_live.return_value.__enter__ = Mock(return_value=mock_live_instance)
        mock_live.return_value.__exit__ = Mock(return_value=None)

        # Run very short duration
        with patch("time.sleep"), patch("time.time", side_effect=[0, 0.1, 0.2]):
            self.dashboard.run_live_dashboard(heartbeat, duration_seconds=0.1, refresh_rate=10.0)

        # Verify Live was called
        mock_live.assert_called_once()


class TestDemoScenario(unittest.TestCase):
    """Test demo scenario creation."""

    def test_demo_executive_view_creation(self):
        """Test creating demo executive view."""
        dashboard, heartbeat = create_demo_executive_view()

        # Check dashboard is configured
        self.assertIsInstance(dashboard, ExecutiveViewDashboard)
        self.assertEqual(dashboard.baseline_monthly_cost, 75000.0)

        # Check heartbeat has GPUs
        all_metrics = heartbeat.tracker.get_all_gpu_metrics()
        self.assertIn("gpu-00", all_metrics)
        self.assertIn("gpu-01", all_metrics)
        self.assertIn("gpu-02", all_metrics)


class TestIntegration(unittest.TestCase):
    """Integration tests for executive view."""

    def test_end_to_end_summary_generation(self):
        """Test complete end-to-end summary generation."""
        # Create demo scenario
        dashboard, heartbeat = create_demo_executive_view()

        # Simulate brief workload
        heartbeat.simulate_workload(target_utilization=70.0, duration_seconds=1.0)

        # Generate summary
        summary = dashboard.generate_executive_summary(heartbeat)

        # Should produce valid summary
        self.assertIsNotNone(summary)
        self.assertGreater(summary.business_impact_score, 0.0)
        self.assertIsInstance(summary.recommendation, str)

    def test_cost_calculation_realistic_scenarios(self):
        """Test cost calculations with realistic scenarios."""
        dashboard = ExecutiveViewDashboard(baseline_monthly_cost=100000.0)

        # Scenario 1: Small efficient cluster (5 GPUs)
        cost_metrics_small = dashboard.calculate_cost_metrics(5, 2.00)
        expected_cost_small = 24 * 30 * 5 * 2.00  # $7,200
        self.assertEqual(cost_metrics_small.current_monthly_cost, expected_cost_small)
        self.assertGreater(cost_metrics_small.savings_percentage, 90)  # >90% savings

        # Scenario 2: Large cluster (40 GPUs)
        cost_metrics_large = dashboard.calculate_cost_metrics(40, 3.00)
        expected_cost_large = 24 * 30 * 40 * 3.00  # $86,400
        self.assertEqual(cost_metrics_large.current_monthly_cost, expected_cost_large)
        self.assertGreater(cost_metrics_large.savings_percentage, 10)  # Some savings

    def test_business_impact_scoring(self):
        """Test business impact score calculation."""
        dashboard = ExecutiveViewDashboard()

        # Create scenarios with different impact levels
        from mtop.gpu_heartbeat import create_gpu_heartbeat

        heartbeat = create_gpu_heartbeat()
        heartbeat.add_gpu("gpu-00", "nvidia-h100")

        # Generate summary and check impact score is reasonable
        summary = dashboard.generate_executive_summary(heartbeat)

        # Impact score should be in valid range
        self.assertGreaterEqual(summary.business_impact_score, 0.0)
        self.assertLessEqual(summary.business_impact_score, 100.0)

        # Should have some form of recommendation
        self.assertIn("performance", summary.recommendation.lower())


if __name__ == "__main__":
    unittest.main()
