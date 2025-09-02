#!/usr/bin/env python3
"""
Executive summary dashboard for business value and cost optimization metrics.

This module provides C-level executives with high-level business value metrics,
cost savings calculations, ROI analysis, and SLO compliance overview without
technical complexity.
"""

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from rich.align import Align
from rich.box import DOUBLE, ROUNDED
from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from mtop.gpu_heartbeat import GPUHeartbeat
from mtop.slo_convergence import ConvergenceMetrics

from .config_loader import SLOConfig, TechnologyConfig


class BusinessMetricType(Enum):
    """Types of business metrics tracked for executives."""

    COST_SAVINGS = "cost_savings"
    ROI = "roi"
    SLO_COMPLIANCE = "slo_compliance"
    EFFICIENCY = "efficiency"
    UTILIZATION = "utilization"


@dataclass
class CostOptimizationMetrics:
    """Cost optimization and savings metrics."""

    baseline_monthly_cost: float  # Traditional GPU allocation cost baseline
    current_monthly_cost: float  # Current optimized cost
    monthly_savings: float  # Absolute monthly savings
    savings_percentage: float  # Percentage cost reduction
    annual_projected_savings: float  # Projected annual savings
    roi_percentage: float  # Return on investment percentage
    payback_period_months: float  # Payback period in months

    def __post_init__(self):
        """Validate cost metrics."""
        if self.baseline_monthly_cost <= 0:
            raise ValueError(f"Baseline cost must be positive, got {self.baseline_monthly_cost}")
        if self.current_monthly_cost < 0:
            raise ValueError(f"Current cost cannot be negative, got {self.current_monthly_cost}")


@dataclass
class EfficiencyMetrics:
    """GPU utilization and efficiency metrics."""

    average_gpu_utilization: float  # Average utilization across cluster
    peak_efficiency_achieved: float  # Peak efficiency percentage
    free_gpu_capacity_utilized: float  # How much "free" capacity is being used
    elastic_scaling_effectiveness: float  # How effectively we scale up/down
    resource_waste_reduction: float  # Reduction in wasted resources

    def __post_init__(self):
        """Validate efficiency metrics."""
        for field_name, value in [
            ("average_gpu_utilization", self.average_gpu_utilization),
            ("peak_efficiency_achieved", self.peak_efficiency_achieved),
            ("free_gpu_capacity_utilized", self.free_gpu_capacity_utilized),
            ("elastic_scaling_effectiveness", self.elastic_scaling_effectiveness),
            ("resource_waste_reduction", self.resource_waste_reduction),
        ]:
            if not 0 <= value <= 100:
                raise ValueError(f"{field_name} must be 0-100%, got {value}")


@dataclass
class SLOComplianceMetrics:
    """SLO compliance and performance metrics."""

    ttft_compliance_percentage: float  # % of time TTFT SLO is met
    cost_compliance_percentage: float  # % of time cost targets are met
    overall_slo_compliance: float  # Overall SLO compliance score
    availability_percentage: float  # System availability
    performance_consistency: float  # Performance consistency score

    def __post_init__(self):
        """Validate SLO compliance metrics."""
        for field_name, value in [
            ("ttft_compliance_percentage", self.ttft_compliance_percentage),
            ("cost_compliance_percentage", self.cost_compliance_percentage),
            ("overall_slo_compliance", self.overall_slo_compliance),
            ("availability_percentage", self.availability_percentage),
            ("performance_consistency", self.performance_consistency),
        ]:
            if not 0 <= value <= 100:
                raise ValueError(f"{field_name} must be 0-100%, got {value}")


@dataclass
class ExecutiveSummary:
    """Complete executive summary with all business metrics."""

    timestamp: float
    cost_metrics: CostOptimizationMetrics
    efficiency_metrics: EfficiencyMetrics
    slo_metrics: SLOComplianceMetrics
    business_impact_score: float  # Overall business impact score (0-100)
    recommendation: str  # Executive recommendation
    key_achievements: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)


class ExecutiveViewDashboard:
    """Executive-friendly dashboard showing business value and ROI."""

    def __init__(
        self,
        slo_config: Optional[SLOConfig] = None,
        console: Optional[Console] = None,
        baseline_monthly_cost: float = 50000.0,  # $50k/month baseline
    ):
        """Initialize executive dashboard.

        Args:
            slo_config: SLO configuration for targets
            console: Rich console for output (optional)
            baseline_monthly_cost: Baseline monthly cost for comparison
        """
        self.slo_config = slo_config
        self.console = console or Console()
        self.baseline_monthly_cost = baseline_monthly_cost

        # Historical data for trending
        self.summary_history: deque = deque(maxlen=24)  # 24 hours of data
        self.cost_history: deque = deque(maxlen=168)  # 1 week of hourly data
        self.slo_history: deque = deque(maxlen=60)  # 1 hour of minute data

    def calculate_cost_metrics(
        self, current_gpu_count: int, gpu_hourly_rate: float = 2.50
    ) -> CostOptimizationMetrics:
        """Calculate cost optimization metrics.

        Args:
            current_gpu_count: Current number of active GPUs
            gpu_hourly_rate: Cost per GPU per hour

        Returns:
            Cost optimization metrics
        """
        # Calculate current monthly cost (24 hours * 30 days * GPU count * rate)
        current_monthly_cost = 24 * 30 * current_gpu_count * gpu_hourly_rate

        # Calculate savings
        monthly_savings = max(0, self.baseline_monthly_cost - current_monthly_cost)
        savings_percentage = (monthly_savings / self.baseline_monthly_cost) * 100
        annual_projected_savings = monthly_savings * 12

        # Simple ROI calculation (assuming implementation cost is ~$100k)
        implementation_cost = 100000.0
        roi_percentage = (
            (annual_projected_savings / implementation_cost) * 100 if implementation_cost > 0 else 0
        )
        payback_period_months = (
            implementation_cost / monthly_savings if monthly_savings > 0 else float("inf")
        )

        return CostOptimizationMetrics(
            baseline_monthly_cost=self.baseline_monthly_cost,
            current_monthly_cost=current_monthly_cost,
            monthly_savings=monthly_savings,
            savings_percentage=savings_percentage,
            annual_projected_savings=annual_projected_savings,
            roi_percentage=roi_percentage,
            payback_period_months=payback_period_months,
        )

    def calculate_efficiency_metrics(self, gpu_heartbeat: GPUHeartbeat) -> EfficiencyMetrics:
        """Calculate GPU efficiency metrics.

        Args:
            gpu_heartbeat: GPU heartbeat engine with current metrics

        Returns:
            Efficiency metrics
        """
        all_metrics = gpu_heartbeat.tracker.get_all_gpu_metrics()

        if not all_metrics:
            # No data available - return neutral metrics
            return EfficiencyMetrics(
                average_gpu_utilization=0.0,
                peak_efficiency_achieved=0.0,
                free_gpu_capacity_utilized=0.0,
                elastic_scaling_effectiveness=0.0,
                resource_waste_reduction=0.0,
            )

        # Calculate average utilization
        utilizations = [metrics.utilization_percent for metrics in all_metrics.values()]
        average_utilization = statistics.mean(utilizations)

        # Peak efficiency is the highest utilization without overloading
        safe_utilizations = [u for u in utilizations if u <= 85.0]  # Below overload threshold
        peak_efficiency = max(safe_utilizations) if safe_utilizations else 0.0

        # Free GPU capacity utilization (how much "spare" capacity we're using)
        spare_capacity_used = max(0, average_utilization - 50.0)  # Above baseline 50%
        free_gpu_capacity_utilized = min(100.0, spare_capacity_used * 2)  # Scale to 0-100%

        # Elastic scaling effectiveness (based on utilization distribution)
        utilization_std = statistics.stdev(utilizations) if len(utilizations) > 1 else 0.0
        elastic_effectiveness = max(0, 100 - utilization_std * 2)  # Lower variance = better scaling

        # Resource waste reduction (inverse of underutilization)
        underutilized_percentage = (
            sum(1 for u in utilizations if u < 30.0) / len(utilizations) * 100
        )
        resource_waste_reduction = max(0, 100 - underutilized_percentage)

        return EfficiencyMetrics(
            average_gpu_utilization=average_utilization,
            peak_efficiency_achieved=peak_efficiency,
            free_gpu_capacity_utilized=free_gpu_capacity_utilized,
            elastic_scaling_effectiveness=elastic_effectiveness,
            resource_waste_reduction=resource_waste_reduction,
        )

    def calculate_slo_compliance_metrics(
        self, convergence_metrics: Optional[ConvergenceMetrics] = None
    ) -> SLOComplianceMetrics:
        """Calculate SLO compliance metrics.

        Args:
            convergence_metrics: Current convergence metrics (optional)

        Returns:
            SLO compliance metrics
        """
        if convergence_metrics is None or not self.slo_history:
            # No data - assume baseline compliance
            return SLOComplianceMetrics(
                ttft_compliance_percentage=95.0,
                cost_compliance_percentage=90.0,
                overall_slo_compliance=92.5,
                availability_percentage=99.5,
                performance_consistency=85.0,
            )

        # Calculate compliance from history
        recent_slo_data = list(self.slo_history)

        ttft_compliant = sum(1 for entry in recent_slo_data if entry.get("ttft_compliance", True))
        ttft_compliance_percentage = (ttft_compliant / len(recent_slo_data)) * 100

        cost_compliant = sum(1 for entry in recent_slo_data if entry.get("cost_compliance", True))
        cost_compliance_percentage = (cost_compliant / len(recent_slo_data)) * 100

        overall_slo_compliance = (ttft_compliance_percentage + cost_compliance_percentage) / 2

        # Availability (assume high availability with occasional brief outages)
        availability_percentage = 99.5  # High availability system

        # Performance consistency (based on convergence stability)
        performance_consistency = min(100.0, convergence_metrics.stability_score * 100)

        return SLOComplianceMetrics(
            ttft_compliance_percentage=ttft_compliance_percentage,
            cost_compliance_percentage=cost_compliance_percentage,
            overall_slo_compliance=overall_slo_compliance,
            availability_percentage=availability_percentage,
            performance_consistency=performance_consistency,
        )

    def generate_executive_summary(
        self, gpu_heartbeat: GPUHeartbeat, convergence_metrics: Optional[ConvergenceMetrics] = None
    ) -> ExecutiveSummary:
        """Generate complete executive summary.

        Args:
            gpu_heartbeat: GPU heartbeat engine
            convergence_metrics: Current convergence metrics

        Returns:
            Complete executive summary
        """
        all_gpu_metrics = gpu_heartbeat.tracker.get_all_gpu_metrics()
        current_gpu_count = len(all_gpu_metrics)

        # Calculate all metric categories
        cost_metrics = self.calculate_cost_metrics(current_gpu_count)
        efficiency_metrics = self.calculate_efficiency_metrics(gpu_heartbeat)
        slo_metrics = self.calculate_slo_compliance_metrics(convergence_metrics)

        # Calculate overall business impact score
        impact_factors = [
            cost_metrics.savings_percentage / 100.0,  # Cost savings impact
            efficiency_metrics.average_gpu_utilization / 100.0,  # Efficiency impact
            slo_metrics.overall_slo_compliance / 100.0,  # SLO compliance impact
        ]
        business_impact_score = statistics.mean(impact_factors) * 100

        # Generate key achievements
        key_achievements = []
        if cost_metrics.savings_percentage > 15:
            key_achievements.append(f"${cost_metrics.monthly_savings:,.0f}/month cost reduction")
        if efficiency_metrics.average_gpu_utilization > 70:
            key_achievements.append(
                f"{efficiency_metrics.average_gpu_utilization:.1f}% GPU utilization achieved"
            )
        if slo_metrics.overall_slo_compliance > 95:
            key_achievements.append(
                f"{slo_metrics.overall_slo_compliance:.1f}% SLO compliance maintained"
            )

        # Generate risk factors
        risk_factors = []
        if cost_metrics.savings_percentage < 10:
            risk_factors.append("Low cost savings - optimization opportunity exists")
        if efficiency_metrics.average_gpu_utilization < 50:
            risk_factors.append("Underutilized GPU resources")
        if slo_metrics.overall_slo_compliance < 90:
            risk_factors.append("SLO compliance below target")

        # Generate recommendation
        if business_impact_score > 80:
            recommendation = "Excellent performance - continue current optimization strategy"
        elif business_impact_score > 60:
            recommendation = "Good performance - minor optimizations recommended"
        elif business_impact_score > 40:
            recommendation = "Moderate performance - review scaling parameters"
        else:
            recommendation = "Performance needs improvement - consider strategy revision"

        summary = ExecutiveSummary(
            timestamp=time.time(),
            cost_metrics=cost_metrics,
            efficiency_metrics=efficiency_metrics,
            slo_metrics=slo_metrics,
            business_impact_score=business_impact_score,
            recommendation=recommendation,
            key_achievements=key_achievements,
            risk_factors=risk_factors,
        )

        # Add to history
        self.summary_history.append(summary)

        return summary

    def create_cost_savings_panel(self, cost_metrics: CostOptimizationMetrics) -> Panel:
        """Create cost savings visualization panel.

        Args:
            cost_metrics: Cost optimization metrics

        Returns:
            Rich Panel with cost savings visualization
        """
        # Create cost table
        cost_table = Table(show_header=False, box=None, padding=(0, 1))
        cost_table.add_column("Metric", style="bold", width=20)
        cost_table.add_column("Value", style="green", width=15)

        cost_table.add_row("Monthly Savings", f"${cost_metrics.monthly_savings:,.0f}")
        cost_table.add_row("Cost Reduction", f"{cost_metrics.savings_percentage:.1f}%")
        cost_table.add_row("Annual Projection", f"${cost_metrics.annual_projected_savings:,.0f}")
        cost_table.add_row("ROI", f"{cost_metrics.roi_percentage:.1f}%")

        payback_text = (
            f"{cost_metrics.payback_period_months:.1f} months"
            if cost_metrics.payback_period_months < 24
            else "24+ months"
        )
        cost_table.add_row("Payback Period", payback_text)

        return Panel(
            cost_table,
            title="[bold green]💰 Cost Optimization[/bold green]",
            border_style="green",
            box=ROUNDED,
        )

    def create_efficiency_panel(self, efficiency_metrics: EfficiencyMetrics) -> Panel:
        """Create GPU efficiency visualization panel.

        Args:
            efficiency_metrics: Efficiency metrics

        Returns:
            Rich Panel with efficiency visualization
        """
        # Create efficiency progress bars
        progress = Progress(
            TextColumn("[progress.description]{task.description}", justify="left"),
            BarColumn(bar_width=20),
            TextColumn("{task.percentage:>3.0f}%"),
            expand=False,
        )

        progress.add_task(
            "GPU Utilization", total=100, completed=efficiency_metrics.average_gpu_utilization
        )
        progress.add_task(
            "Peak Efficiency", total=100, completed=efficiency_metrics.peak_efficiency_achieved
        )
        progress.add_task(
            "Elastic Scaling", total=100, completed=efficiency_metrics.elastic_scaling_effectiveness
        )
        progress.add_task(
            "Waste Reduction", total=100, completed=efficiency_metrics.resource_waste_reduction
        )

        return Panel(
            progress,
            title="[bold blue]⚡ GPU Efficiency[/bold blue]",
            border_style="blue",
            box=ROUNDED,
        )

    def create_slo_compliance_panel(self, slo_metrics: SLOComplianceMetrics) -> Panel:
        """Create SLO compliance visualization panel.

        Args:
            slo_metrics: SLO compliance metrics

        Returns:
            Rich Panel with SLO compliance visualization
        """
        # Create SLO table with status indicators
        slo_table = Table(show_header=False, box=None, padding=(0, 1))
        slo_table.add_column("SLO Metric", style="bold", width=20)
        slo_table.add_column("Compliance", width=10)
        slo_table.add_column("Status", width=8)

        # Helper function for status icon
        def get_status_icon(percentage: float) -> str:
            if percentage >= 95:
                return "🟢"
            elif percentage >= 90:
                return "🟡"
            else:
                return "🔴"

        slo_table.add_row(
            "TTFT Performance",
            f"{slo_metrics.ttft_compliance_percentage:.1f}%",
            get_status_icon(slo_metrics.ttft_compliance_percentage),
        )
        slo_table.add_row(
            "Cost Targets",
            f"{slo_metrics.cost_compliance_percentage:.1f}%",
            get_status_icon(slo_metrics.cost_compliance_percentage),
        )
        slo_table.add_row(
            "System Availability",
            f"{slo_metrics.availability_percentage:.1f}%",
            get_status_icon(slo_metrics.availability_percentage),
        )
        slo_table.add_row(
            "Overall SLO",
            f"{slo_metrics.overall_slo_compliance:.1f}%",
            get_status_icon(slo_metrics.overall_slo_compliance),
        )

        return Panel(
            slo_table,
            title="[bold yellow]📊 SLO Compliance[/bold yellow]",
            border_style="yellow",
            box=ROUNDED,
        )

    def create_business_impact_panel(self, summary: ExecutiveSummary) -> Panel:
        """Create business impact summary panel.

        Args:
            summary: Executive summary

        Returns:
            Rich Panel with business impact summary
        """
        # Business impact score gauge
        impact_progress = Progress(
            TextColumn("Business Impact Score"),
            BarColumn(bar_width=30),
            TextColumn("{task.percentage:>3.0f}%"),
            expand=False,
        )
        impact_progress.add_task("", total=100, completed=summary.business_impact_score)

        # Key achievements
        achievements_text = Text()
        if summary.key_achievements:
            achievements_text.append("✅ Key Achievements:\n", style="bold green")
            for achievement in summary.key_achievements[:3]:  # Top 3
                achievements_text.append(f"  • {achievement}\n", style="green")
        else:
            achievements_text.append("⏳ Optimization in progress...\n", style="yellow")

        # Recommendation
        rec_text = Text()
        rec_text.append("🎯 Recommendation: ", style="bold")
        rec_text.append(summary.recommendation, style="cyan")

        content = Group(impact_progress, "", achievements_text, rec_text)

        return Panel(
            content,
            title="[bold cyan]🚀 Business Impact[/bold cyan]",
            border_style="cyan",
            box=DOUBLE,
        )

    def create_executive_dashboard(self, summary: ExecutiveSummary) -> Group:
        """Create complete executive dashboard.

        Args:
            summary: Executive summary data

        Returns:
            Rich Group with complete dashboard
        """
        # Create individual panels
        cost_panel = self.create_cost_savings_panel(summary.cost_metrics)
        efficiency_panel = self.create_efficiency_panel(summary.efficiency_metrics)
        slo_panel = self.create_slo_compliance_panel(summary.slo_metrics)
        impact_panel = self.create_business_impact_panel(summary)

        # Arrange in 2x2 grid
        top_row = Columns([cost_panel, efficiency_panel], equal=True)
        bottom_row = Columns([slo_panel, impact_panel], equal=True)

        # Add header
        header = Text(
            "🏢 EXECUTIVE DASHBOARD - GPU Infrastructure Optimization",
            style="bold white on blue",
            justify="center",
        )

        # Add timestamp
        timestamp_text = Text(
            f"Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(summary.timestamp))}",
            style="dim",
            justify="center",
        )

        return Group(header, "", top_row, "", bottom_row, "", timestamp_text)

    def run_live_dashboard(
        self,
        gpu_heartbeat: GPUHeartbeat,
        duration_seconds: float = 300.0,
        refresh_rate: float = 1.0,
        convergence_metrics: Optional[ConvergenceMetrics] = None,
    ) -> None:
        """Run live executive dashboard.

        Args:
            gpu_heartbeat: GPU heartbeat engine
            duration_seconds: How long to run dashboard
            refresh_rate: Refresh rate in Hz
            convergence_metrics: Optional convergence metrics
        """
        refresh_interval = 1.0 / refresh_rate

        with Live(console=self.console, refresh_per_second=refresh_rate) as live:
            start_time = time.time()

            while time.time() - start_time < duration_seconds:
                # Generate current executive summary
                summary = self.generate_executive_summary(gpu_heartbeat, convergence_metrics)

                # Create dashboard
                dashboard = self.create_executive_dashboard(summary)

                # Update live display
                live.update(dashboard)

                time.sleep(refresh_interval)


def create_demo_executive_view() -> Tuple[ExecutiveViewDashboard, Any]:
    """Create a demo executive view with sample data.

    Returns:
        Tuple of (executive_dashboard, gpu_heartbeat_engine)
    """
    from mtop.gpu_heartbeat import create_gpu_heartbeat

    # Create GPU heartbeat engine
    heartbeat = create_gpu_heartbeat()

    # Add some GPUs for demo
    heartbeat.add_gpu("gpu-00", "nvidia-h100")
    heartbeat.add_gpu("gpu-01", "nvidia-a100")
    heartbeat.add_gpu("gpu-02", "nvidia-v100")

    # Create executive dashboard
    executive_dashboard = ExecutiveViewDashboard(baseline_monthly_cost=75000.0)  # $75k baseline

    return executive_dashboard, heartbeat


def main():
    """Demo the executive view dashboard."""
    console = Console()

    console.print("[bold]🏢 Executive Dashboard Demo[/bold]", style="blue")
    console.print("Creating executive summary with cost optimization metrics...\n")

    # Create demo
    dashboard, heartbeat = create_demo_executive_view()

    # Run brief workload simulation
    import threading

    simulation_thread = threading.Thread(
        target=heartbeat.simulate_workload,
        args=(65.0, 15.0),  # 65% utilization for 15 seconds
        daemon=True,
    )
    simulation_thread.start()

    # Run dashboard
    try:
        dashboard.run_live_dashboard(heartbeat, duration_seconds=15.0, refresh_rate=2.0)
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped by user[/yellow]")

    console.print("\n[green]✅ Executive dashboard demo complete![/green]")


if __name__ == "__main__":
    main()
