#!/usr/bin/env python3
"""
SLO dashboard with visual gauges for TTFT and cost metrics.

This module provides a comprehensive dashboard for monitoring SLO compliance
with twin gauges showing TTFT and cost-per-million-tokens metrics, along with
convergence trajectory and decision history visualization.
"""

import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from rich.align import Align
from rich.box import ROUNDED
from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from mtop.slo_convergence import ConvergenceAction, ConvergenceMetrics, ConvergenceState

from .config_loader import SLOConfig


@dataclass
class GaugeConfig:
    """Configuration for a gauge display."""

    title: str
    current_value: Optional[float]
    target_value: float
    critical_value: float
    unit: str
    is_lower_better: bool = True  # True for metrics where lower is better (TTFT, cost)
    format_string: str = "{:.1f}"
    # Enhanced visualization options
    enable_animated_needle: bool = True
    enable_gradient_fill: bool = True
    enable_sparkline: bool = True
    enable_predictive_indicator: bool = True
    enable_pulse_on_critical: bool = True


@dataclass
class PredictiveIndicator:
    """Predictive indicator for gauge metrics."""

    predicted_value: float
    time_to_violation: Optional[float]  # seconds until SLO breach
    confidence: float  # 0.0 to 1.0
    trend_direction: str  # "improving", "degrading", "stable"


class SLODashboard:
    """Visual dashboard for SLO monitoring with gauges and history."""

    def __init__(self, slo_config: SLOConfig, console: Optional[Console] = None):
        """Initialize SLO dashboard.

        Args:
            slo_config: SLO configuration with targets
            console: Rich console for output (optional)
        """
        self.slo_config = slo_config
        self.console = console or Console()

        # History tracking
        self.metrics_history: deque = deque(maxlen=60)  # 60 data points for trending
        self.action_history: deque = deque(maxlen=10)  # Last 10 actions

        # Enhanced tracking for visualizations
        self.ttft_sparkline_data: deque = deque(maxlen=30)  # 30 points for sparkline
        self.cost_sparkline_data: deque = deque(maxlen=30)  # 30 points for sparkline
        self.last_needle_position: Dict[str, float] = {}  # For needle animation
        self.animation_frame = 0  # For pulse effects

        # Gauge configurations based on SLO targets
        self.ttft_gauge_config = GaugeConfig(
            title="TTFT (P95)",
            current_value=None,
            target_value=250.0,  # Target: 250ms
            critical_value=500.0,  # Critical: 500ms
            unit="ms",
            is_lower_better=True,
            format_string="{:.0f}",
        )

        self.cost_gauge_config = GaugeConfig(
            title="Cost per Million Tokens",
            current_value=None,
            target_value=0.25,  # Target: $0.25/M
            critical_value=0.40,  # Max: $0.40/M
            unit="$/M",
            is_lower_better=True,
            format_string="${:.2f}",
        )

    def update_metrics(self, metrics: ConvergenceMetrics, gpu_count: Optional[int] = None) -> None:
        """Update dashboard with new metrics.

        Args:
            metrics: Current convergence metrics
            gpu_count: Current number of active GPUs (optional)
        """
        # Update gauge values
        self.ttft_gauge_config.current_value = metrics.current_ttft_p95
        self.cost_gauge_config.current_value = metrics.current_cost_per_million

        # Update sparkline data
        if metrics.current_ttft_p95 is not None:
            self.ttft_sparkline_data.append(metrics.current_ttft_p95)
        if metrics.current_cost_per_million is not None:
            self.cost_sparkline_data.append(metrics.current_cost_per_million)

        # Increment animation frame for effects
        self.animation_frame += 1

        # Add to history
        self.metrics_history.append(
            {
                "timestamp": time.time(),
                "ttft": metrics.current_ttft_p95,
                "cost": metrics.current_cost_per_million,
                "convergence_score": metrics.convergence_score,
                "stability_score": metrics.stability_score,
                "ttft_compliance": metrics.ttft_compliance,
                "cost_compliance": metrics.cost_compliance,
                "gpu_count": gpu_count,
            }
        )

    def add_action(self, action: ConvergenceAction) -> None:
        """Add an action to the history.

        Args:
            action: Convergence action taken
        """
        self.action_history.append(action)

    def calculate_predictive_indicator(
        self, config: GaugeConfig, sparkline_data: deque
    ) -> Optional[PredictiveIndicator]:
        """Calculate predictive indicator for a metric.

        Args:
            config: Gauge configuration
            sparkline_data: Historical data for the metric

        Returns:
            PredictiveIndicator or None if insufficient data
        """
        if len(sparkline_data) < 5:  # Need at least 5 data points
            return None

        data_points = list(sparkline_data)

        # Simple linear regression for trend prediction
        n = len(data_points)
        x_values = list(range(n))

        # Calculate trend line
        sum_x = sum(x_values)
        sum_y = sum(data_points)
        sum_xy = sum(x * y for x, y in zip(x_values, data_points))
        sum_x2 = sum(x * x for x in x_values)

        if n * sum_x2 - sum_x * sum_x == 0:  # Avoid division by zero
            return None

        # Linear regression coefficients
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n

        # Predict next value (30 seconds ahead)
        predicted_value = slope * (n + 30) + intercept

        # Determine trend direction
        if abs(slope) < 0.01:  # Threshold for "stable"
            trend_direction = "stable"
        elif slope > 0:
            if config.is_lower_better:
                trend_direction = "degrading"
            else:
                trend_direction = "improving"
        else:
            if config.is_lower_better:
                trend_direction = "improving"
            else:
                trend_direction = "degrading"

        # Calculate time to violation
        time_to_violation = None
        if trend_direction == "degrading":
            violation_threshold = (
                config.critical_value if config.is_lower_better else config.target_value
            )
            current_value = data_points[-1]

            if slope != 0:
                steps_to_violation = (violation_threshold - current_value) / slope
                if steps_to_violation > 0:
                    time_to_violation = steps_to_violation  # In data points (seconds)

        # Calculate confidence based on data variance
        variance = (
            sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, data_points)) / n
        )
        confidence = max(0.1, min(1.0, 1.0 / (1.0 + variance)))

        return PredictiveIndicator(
            predicted_value=predicted_value,
            time_to_violation=time_to_violation,
            confidence=confidence,
            trend_direction=trend_direction,
        )

    def create_sparkline(self, data: deque, width: int = 20) -> str:
        """Create ASCII sparkline from data.

        Args:
            data: Historical data points
            width: Width of sparkline in characters

        Returns:
            ASCII sparkline string
        """
        if not data or len(data) < 2:
            return "─" * width

        data_points = list(data)[-width:]  # Take last 'width' points

        # Normalize data to 0-7 range for block characters
        min_val = min(data_points)
        max_val = max(data_points)

        if max_val == min_val:
            return "─" * len(data_points)

        # Unicode block characters for sparkline
        blocks = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

        sparkline = ""
        for value in data_points:
            normalized = (value - min_val) / (max_val - min_val)
            block_index = int(normalized * (len(blocks) - 1))
            sparkline += blocks[block_index]

        # Pad to width if needed
        while len(sparkline) < width:
            sparkline += " "

        return sparkline

    def create_animated_needle(self, config: GaugeConfig, position: float) -> str:
        """Create animated needle visualization.

        Args:
            config: Gauge configuration
            position: Current position (0-100%)

        Returns:
            Needle visualization string
        """
        gauge_width = 40

        # Smooth needle animation
        gauge_key = config.title
        last_pos = self.last_needle_position.get(gauge_key, position)

        # Animate towards target position
        smoothing_factor = 0.3
        animated_pos = last_pos + (position - last_pos) * smoothing_factor
        self.last_needle_position[gauge_key] = animated_pos

        # Create needle visualization
        needle_pos = int((animated_pos / 100) * gauge_width)

        # Build gauge with needle
        gauge = "│" + "─" * (gauge_width - 2) + "│"

        # Insert needle
        if 0 <= needle_pos < len(gauge):
            gauge = gauge[:needle_pos] + "▲" + gauge[needle_pos + 1 :]

        return gauge

    def get_gradient_color(
        self, position: float, is_critical: bool = False, status_color: str = "green"
    ) -> str:
        """Get gradient color based on position and state.

        Args:
            position: Position on gauge (0-100%)
            is_critical: Whether in critical state
            status_color: Base status color from gauge logic

        Returns:
            Rich color string
        """
        if is_critical and self.animation_frame % 4 < 2:  # Pulse effect
            return "red"
        else:
            return status_color  # Use the calculated status color

    def create_gauge(self, config: GaugeConfig) -> Panel:
        """Create an enhanced visual gauge for a metric.

        Args:
            config: Gauge configuration

        Returns:
            Panel containing the enhanced gauge visualization
        """
        if config.current_value is None:
            # No data yet
            content = Text("No data", style="dim italic")
            return Panel(
                Align.center(content, vertical="middle"),
                title=config.title,
                border_style="dim",
                height=12,  # Increased height for enhanced features
            )

        # Calculate position on scale (0-100%)
        if config.is_lower_better:
            # For metrics where lower is better
            if config.current_value <= config.target_value:
                # In target zone (0-50% of gauge)
                position = (config.current_value / config.target_value) * 50
                status_color = "green"
                status_text = "✓ GOOD"
                is_critical = False
            elif config.current_value <= config.critical_value:
                # In warning zone (50-100% of gauge)
                position = (
                    50
                    + (
                        (config.current_value - config.target_value)
                        / (config.critical_value - config.target_value)
                    )
                    * 50
                )
                status_color = "yellow"
                status_text = "⚠ WARNING"
                is_critical = False
            else:
                # Beyond critical
                position = 100
                status_color = "red"
                status_text = "✗ CRITICAL"
                is_critical = True
        else:
            # For metrics where higher is better
            if config.current_value >= config.target_value:
                position = 100
                status_color = "green"
                status_text = "✓ GOOD"
                is_critical = False
            elif config.current_value >= config.critical_value:
                position = (config.current_value / config.critical_value) * 100
                status_color = "yellow"
                status_text = "⚠ WARNING"
                is_critical = False
            else:
                position = (config.current_value / config.critical_value) * 50
                status_color = "red"
                status_text = "✗ CRITICAL"
                is_critical = True

        # Get gradient color with pulse effect
        display_color = self.get_gradient_color(
            position, is_critical and config.enable_pulse_on_critical, status_color
        )

        # Build enhanced gauge content
        content_elements = []

        # Main value display
        value_text = Text(
            config.format_string.format(config.current_value) + config.unit,
            style=f"bold {display_color}",
        )
        content_elements.append(Align.center(value_text))

        # Enhanced needle gauge (if enabled)
        if config.enable_animated_needle:
            needle_gauge = self.create_animated_needle(config, position)
            content_elements.append(Align.center(Text(needle_gauge, style=display_color)))
        else:
            # Fallback to progress bar
            progress = Progress(
                BarColumn(bar_width=40),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                expand=False,
            )
            task_id = progress.add_task("", total=100, completed=position)
            content_elements.append(Align.center(progress))

        # Sparkline (if enabled and data available)
        if config.enable_sparkline:
            sparkline_data = (
                self.ttft_sparkline_data if "TTFT" in config.title else self.cost_sparkline_data
            )
            if sparkline_data:
                sparkline = self.create_sparkline(sparkline_data, width=30)
                sparkline_text = Text(f"Trend: {sparkline}", style="cyan")
                content_elements.append(Align.center(sparkline_text))

        # Predictive indicator (if enabled)
        if config.enable_predictive_indicator:
            sparkline_data = (
                self.ttft_sparkline_data if "TTFT" in config.title else self.cost_sparkline_data
            )
            prediction = self.calculate_predictive_indicator(config, sparkline_data)
            if prediction:
                trend_icon = {"improving": "📈", "degrading": "📉", "stable": "➡️"}.get(
                    prediction.trend_direction, "➡️"
                )

                prediction_text = f"{trend_icon} {prediction.trend_direction.title()}"

                if prediction.time_to_violation:
                    minutes = int(prediction.time_to_violation / 60)
                    if minutes < 60:
                        prediction_text += f" (SLO breach in ~{minutes}m)"
                    else:
                        hours = minutes // 60
                        prediction_text += f" (SLO breach in ~{hours}h)"

                pred_color = {"improving": "green", "degrading": "red", "stable": "yellow"}.get(
                    prediction.trend_direction, "white"
                )

                content_elements.append(Align.center(Text(prediction_text, style=f"{pred_color}")))

        # Target and critical reference
        ref_text = (
            f"Target: {config.format_string.format(config.target_value)}{config.unit} | "
            f"Critical: {config.format_string.format(config.critical_value)}{config.unit}"
        )
        content_elements.append(Align.center(Text(ref_text, style="dim")))

        # Status line
        status_line = Text(status_text, style=f"bold {display_color}")
        content_elements.append(Align.center(status_line))

        return Panel(
            Group(*content_elements),
            title=config.title,
            border_style=display_color,
            height=12,  # Increased height for enhanced features
        )

    def create_convergence_trajectory(self) -> Panel:
        """Create convergence trajectory visualization.

        Returns:
            Panel containing trajectory chart
        """
        if len(self.metrics_history) < 2:
            return Panel(
                Text("Collecting data...", style="dim italic"),
                title="Convergence Trajectory",
                border_style="blue",
                height=10,
            )

        # Create simple ASCII chart
        chart_width = 50
        chart_height = 8

        # Get recent history
        recent_history = list(self.metrics_history)[-chart_width:]

        # Create chart lines
        lines = []

        # Header
        lines.append(Text("Score", style="bold"))

        # Chart area
        for row in range(chart_height):
            line_text = ""
            threshold = 1.0 - (row / chart_height)

            for point in recent_history:
                score = point.get("convergence_score", 0)
                if score >= threshold:
                    line_text += "█"
                else:
                    line_text += " "

            # Add axis
            line_text = f"{threshold:3.1f} |{line_text}"
            lines.append(Text(line_text, style="cyan" if threshold > 0.9 else "white"))

        # Add time axis
        lines.append(Text("    +" + "-" * len(recent_history), style="dim"))
        lines.append(Text("     Past" + " " * (len(recent_history) - 10) + "Now", style="dim"))

        # Add current state
        latest = self.metrics_history[-1]
        state_text = Text(
            f"\nConvergence: {latest['convergence_score']:.1%} | Stability: {latest['stability_score']:.1%}",
            style="bold",
        )
        lines.append(state_text)

        return Panel(
            Group(*lines),
            title="Convergence Trajectory",
            border_style="blue",
            height=12,
        )

    def create_decision_history(self) -> Panel:
        """Create decision history table.

        Returns:
            Panel containing decision history
        """
        if not self.action_history:
            return Panel(
                Text("No actions taken yet", style="dim italic"),
                title="Decision History",
                border_style="magenta",
                height=10,
            )

        table = Table(box=ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Time", style="dim", width=12)
        table.add_column("Action", style="cyan")
        table.add_column("Reason", style="white")
        table.add_column("Impact", style="yellow")

        # Add recent actions
        for action in list(self.action_history)[-5:]:  # Show last 5 actions
            time_str = time.strftime("%H:%M:%S", time.localtime(action.timestamp))

            # Determine action style based on success
            action_style = (
                "green" if action.success else "red" if action.success is False else "yellow"
            )

            # Enhance impact text to show GPU scaling
            impact_text = action.actual_impact or "Pending"
            if action.success and "GPU" not in impact_text and impact_text != "Pending":
                # Add GPU scaling context to existing impact
                gpu_context = action.metadata.get("gpu_scaling_info", "")
                if gpu_context:
                    impact_text = f"{impact_text[:20]}... {gpu_context}"

            table.add_row(
                time_str,
                Text(action.action_type.value, style=action_style),
                Text(
                    action.reasoning[:40] + "..."
                    if len(action.reasoning) > 40
                    else action.reasoning
                ),
                Text(
                    impact_text,
                    style="italic" if impact_text == "Pending" else "normal",
                ),
            )

        return Panel(
            table,
            title="Decision History",
            border_style="magenta",
            height=10,
        )

    def create_slo_summary(self) -> Panel:
        """Create SLO compliance summary.

        Returns:
            Panel containing SLO summary
        """
        if not self.metrics_history:
            return Panel(
                Text("No data", style="dim italic"),
                title="SLO Compliance",
                border_style="white",
                height=8,
            )

        latest = self.metrics_history[-1]

        # Build summary text
        summary_parts = []

        # TTFT compliance
        ttft_status = "✓" if latest.get("ttft_compliance") else "✗"
        ttft_color = "green" if latest.get("ttft_compliance") else "red"
        summary_parts.append(Text(f"TTFT: {ttft_status}", style=f"bold {ttft_color}"))

        # Cost compliance
        cost_status = "✓" if latest.get("cost_compliance") else "✗"
        cost_color = "green" if latest.get("cost_compliance") else "red"
        summary_parts.append(Text(f"Cost: {cost_status}", style=f"bold {cost_color}"))

        # GPU capacity indicator
        gpu_count = latest.get("gpu_count")
        if gpu_count is not None:
            # Determine scaling status and color
            if len(self.metrics_history) >= 2:
                prev_gpu_count = self.metrics_history[-2].get("gpu_count", gpu_count)
                if gpu_count > prev_gpu_count:
                    gpu_indicator = f"Active GPUs: {gpu_count} ↑"
                    gpu_color = "yellow"
                elif gpu_count < prev_gpu_count:
                    gpu_indicator = f"Active GPUs: {gpu_count} ↓"
                    gpu_color = "cyan"
                else:
                    gpu_indicator = f"Active GPUs: {gpu_count}"
                    gpu_color = "green"
            else:
                gpu_indicator = f"Active GPUs: {gpu_count}"
                gpu_color = "green"

            summary_parts.append(Text(f"{gpu_indicator}", style=f"bold {gpu_color}"))

        # Overall status
        all_compliant = latest.get("ttft_compliance") and latest.get("cost_compliance")
        overall_status = "All SLOs Met" if all_compliant else "SLO Violations"
        overall_color = "green" if all_compliant else "red"
        summary_parts.append(Text(f"\n{overall_status}", style=f"bold {overall_color}"))

        return Panel(
            Align.center(Group(*summary_parts), vertical="middle"),
            title="SLO Compliance",
            border_style="white",
            height=8,
        )

    def render(self) -> Group:
        """Render the complete dashboard.

        Returns:
            Group containing all dashboard components
        """
        # Top row: Gauges
        gauges = Columns(
            [
                self.create_gauge(self.ttft_gauge_config),
                self.create_gauge(self.cost_gauge_config),
            ],
            equal=True,
            expand=True,
        )

        # Middle row: Convergence and Summary
        middle_row = Columns(
            [
                self.create_convergence_trajectory(),
                self.create_slo_summary(),
            ],
            equal=False,
            expand=True,
        )

        # Bottom row: Decision History
        history = self.create_decision_history()

        # Combine all elements
        return Group(
            Panel(
                Group(gauges, middle_row, history),
                title="[bold blue]SLO Dashboard[/bold blue]",
                subtitle="[dim]Real-time SLO Monitoring[/dim]",
                border_style="blue",
            )
        )

    def live_update(self, update_callback, refresh_rate: float = 1.0) -> None:
        """Run dashboard with live updates.

        Args:
            update_callback: Function that returns new ConvergenceMetrics
            refresh_rate: Seconds between updates
        """
        with Live(self.render(), console=self.console, refresh_per_second=1 / refresh_rate) as live:
            while True:
                try:
                    # Get new metrics
                    metrics = update_callback()
                    if metrics:
                        # Check if GPU count is attached to metrics
                        gpu_count = getattr(metrics, "_gpu_count", None)
                        self.update_metrics(metrics, gpu_count)

                    # Update display
                    live.update(self.render())

                    time.sleep(refresh_rate)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.console.print(f"[red]Error updating dashboard: {e}[/red]")
                    time.sleep(refresh_rate)


def demo_dashboard():
    """Run a demo of the SLO dashboard."""
    console = Console()

    # Create demo SLO config
    slo_config = SLOConfig(
        ttft_p95_ms=250.0,
        tokens_per_second=1000.0,
        error_rate_percent=1.0,
    )

    # Create dashboard
    dashboard = SLODashboard(slo_config, console)

    # Add some demo data
    import random

    def generate_demo_metrics():
        """Generate demo metrics with GPU scaling simulation."""
        # Simulate convergence over time with GPU scaling
        time_step = len(dashboard.metrics_history)

        # GPU scaling pattern: start low, scale up during convergence, then optimize down
        if time_step < 10:
            gpu_count = 2  # Start with minimal capacity
        elif time_step < 20:
            gpu_count = min(6, 2 + (time_step - 10) // 2)  # Scale up to 6 GPUs
        elif time_step < 40:
            gpu_count = 6  # Maintain during convergence
        else:
            gpu_count = max(4, 6 - (time_step - 40) // 10)  # Scale down to optimal 4

        # TTFT improves with more GPUs, cost increases with GPU count
        base_ttft = 500 - (gpu_count * 50) + random.uniform(-30, 30)
        base_cost = 0.15 + (gpu_count * 0.03) + random.uniform(-0.02, 0.02)

        metrics = ConvergenceMetrics(
            current_ttft_p95=max(150, base_ttft),
            target_ttft_p95=250.0,
            current_cost_per_million=max(0.18, base_cost),
            target_cost_per_million=0.25,
            current_throughput=300 + (gpu_count * 120) + random.uniform(-50, 50),
            target_throughput=1000.0,
        )

        # Update compliance
        metrics.ttft_compliance = metrics.current_ttft_p95 <= metrics.target_ttft_p95
        metrics.cost_compliance = (
            metrics.current_cost_per_million <= metrics.target_cost_per_million
        )
        metrics.throughput_compliance = metrics.current_throughput >= metrics.target_throughput

        # Calculate scores based on convergence progress
        target_score = 0.3 + min(0.6, time_step * 0.015)
        metrics.convergence_score = min(1.0, target_score + random.uniform(-0.1, 0.1))
        metrics.stability_score = min(1.0, 0.4 + (time_step * 0.01) + random.uniform(-0.1, 0.1))

        # Store GPU count for dashboard update
        metrics._gpu_count = gpu_count  # Temporarily store for live_update callback

        return metrics

    # Add some demo actions
    from mtop.slo_convergence import ActionType

    # Create realistic GPU scaling actions
    actions = [
        ConvergenceAction(
            timestamp=time.time() - 240,
            action_type=ActionType.SCALE_UP,
            description="Scale up to meet TTFT SLO",
            reasoning="TTFT 450ms > target 250ms",
            expected_impact="Reduce TTFT by 40%",
            success=True,
            actual_impact="TTFT reduced to 280ms",
            metadata={"gpu_scaling_info": "2→4 GPUs, +$120/hr"},
        ),
        ConvergenceAction(
            timestamp=time.time() - 150,
            action_type=ActionType.SCALE_UP,
            description="Additional scaling for convergence",
            reasoning="Still above TTFT target",
            expected_impact="Achieve TTFT compliance",
            success=True,
            actual_impact="TTFT now 220ms, SLO met",
            metadata={"gpu_scaling_info": "4→6 GPUs, +$60/hr"},
        ),
        ConvergenceAction(
            timestamp=time.time() - 60,
            action_type=ActionType.SCALE_DOWN,
            description="Right-size for cost optimization",
            reasoning="SLOs stable, optimize costs",
            expected_impact="Maintain SLOs, reduce cost 25%",
            success=None,
            actual_impact=None,
            metadata={"gpu_scaling_info": "6→4 GPUs, -$120/hr"},
        ),
    ]

    for action in actions:
        dashboard.add_action(action)

    # Run live demo
    console.print("[bold green]Starting SLO Dashboard Demo...[/bold green]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")

    try:
        dashboard.live_update(generate_demo_metrics, refresh_rate=1.0)
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo stopped[/yellow]")


if __name__ == "__main__":
    demo_dashboard()
