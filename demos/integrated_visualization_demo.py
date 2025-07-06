#!/usr/bin/env python3
"""
Integrated Visualization Demo - Showcase all Phase 3 components.

This demo script orchestrates all visualization components in a cohesive presentation
suitable for executives and technical audiences.
"""

import threading
import time
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from mtop.executive_view import create_demo_executive_view
from mtop.gpu_heartbeat import create_gpu_heartbeat
from mtop.heartbeat_visualizer import create_demo_scenario
from mtop.real_time_updates import create_demo_real_time_system
from mtop.slo_convergence import ConvergenceMetrics
from mtop.slo_dashboard import SLODashboard


class VisualizationExcellenceDemo:
    """Complete demonstration of visualization excellence."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize the integrated demo.

        Args:
            console: Rich console for output (optional)
        """
        self.console = console or Console()

    def show_title_screen(self) -> None:
        """Display the demo title screen."""
        title = Text("🎬 VISUALIZATION EXCELLENCE", style="bold white on blue", justify="center")
        subtitle = Text(
            "GPU Infrastructure Monitoring with Real-time Analytics", style="cyan", justify="center"
        )
        description = Text(
            "Showcasing: Heartbeat Animation • SLO Dashboard • Executive View • Real-time Updates",
            style="dim",
            justify="center",
        )

        content = f"{title}\n\n{subtitle}\n\n{description}"

        panel = Panel(
            content,
            title="[bold]🚀 llm-d Visualization Framework[/bold]",
            border_style="blue",
            padding=(2, 4),
        )

        self.console.print(panel)
        self.console.print("\n[dim]Starting demonstration in 3 seconds...[/dim]")
        time.sleep(3)

    def demo_heartbeat_animation(self) -> None:
        """Demonstrate the GPU heartbeat animation system."""
        self.console.clear()
        self.console.print(
            "\n[bold blue]🔥 PHASE 1: GPU Heartbeat Animation[/bold blue]", justify="center"
        )
        self.console.print(
            "[cyan]Real-time GPU capacity with technology-specific characteristics[/cyan]\n",
            justify="center",
        )

        # Create heartbeat demo
        animator, heartbeat = create_demo_scenario()

        # Start background workload simulation
        sim_thread = threading.Thread(
            target=heartbeat.simulate_workload, args=(75.0, 15.0), daemon=True
        )
        sim_thread.start()

        self.console.print(
            "[green]✨ Starting GPU heartbeat animation with DRA technology...[/green]"
        )
        time.sleep(1)

        try:
            # Run heartbeat animation for 12 seconds
            animator.run_live_animation(heartbeat, duration_seconds=12.0, refresh_rate=8.0)
        except KeyboardInterrupt:
            pass

        self.console.print("\n[green]✅ Heartbeat animation complete![/green]")
        time.sleep(2)

    def demo_slo_dashboard(self) -> None:
        """Demonstrate the SLO compliance dashboard."""
        self.console.clear()
        self.console.print(
            "\n[bold yellow]📊 PHASE 2: SLO Compliance Dashboard[/bold yellow]", justify="center"
        )
        self.console.print(
            "[cyan]Twin gauges with TTFT and cost metrics convergence[/cyan]\n", justify="center"
        )

        # Create SLO dashboard
        dashboard = SLODashboard(None, self.console)

        self.console.print("[green]📈 Launching SLO dashboard with convergence metrics...[/green]")
        time.sleep(1)

        # Simulate convergence progression over 15 updates
        for i in range(15):
            # Simulate improving metrics over time
            ttft = 250 - i * 8  # Improving from 250ms to 138ms
            cost = 0.30 - i * 0.01  # Improving from $0.30 to $0.16 per million

            metrics = ConvergenceMetrics(
                current_ttft_p95=ttft,
                target_ttft_p95=200.0,
                current_cost_per_million=cost,
                target_cost_per_million=0.20,
                convergence_score=min(1.0, 0.3 + i * 0.05),
                stability_score=min(1.0, 0.4 + i * 0.04),
            )

            dashboard.update_metrics(metrics, gpu_count=4)

            # Create and display dashboard
            gauge_display = dashboard.create_twin_gauges()
            convergence_display = dashboard.create_convergence_display()

            with Live(console=self.console, refresh_per_second=4):
                live_panel = Panel(
                    f"{gauge_display}\n\n{convergence_display}",
                    title=f"[bold]SLO Dashboard - Update {i+1}/15[/bold]",
                    border_style="yellow",
                )
                self.console.print(live_panel)

            self.console.print(
                f"[dim]📊 SLO Update {i+1}/15: TTFT={ttft:.0f}ms, Cost=${cost:.2f}/M[/dim]"
            )
            time.sleep(0.8)

        self.console.print("\n[green]✅ SLO dashboard demonstration complete![/green]")
        time.sleep(2)

    def demo_executive_view(self) -> None:
        """Demonstrate the executive summary dashboard."""
        self.console.clear()
        self.console.print(
            "\n[bold green]🏢 PHASE 3: Executive Dashboard[/bold green]", justify="center"
        )
        self.console.print(
            "[cyan]Business value metrics: cost savings, ROI, SLO compliance[/cyan]\n",
            justify="center",
        )

        # Create executive demo
        dashboard, heartbeat = create_demo_executive_view()

        # Start background workload simulation
        sim_thread = threading.Thread(
            target=heartbeat.simulate_workload, args=(65.0, 10.0), daemon=True
        )
        sim_thread.start()

        self.console.print(
            "[green]💰 Launching executive dashboard with business metrics...[/green]"
        )
        time.sleep(1)

        try:
            # Run executive dashboard for 10 seconds
            dashboard.run_live_dashboard(heartbeat, duration_seconds=10.0, refresh_rate=3.0)
        except KeyboardInterrupt:
            pass

        self.console.print("\n[green]✅ Executive dashboard complete![/green]")
        time.sleep(2)

    def demo_real_time_integration(self) -> None:
        """Demonstrate the integrated real-time system."""
        self.console.clear()
        self.console.print(
            "\n[bold red]⚡ FINALE: Real-time Integration[/bold red]", justify="center"
        )
        self.console.print(
            "[cyan]All components with synchronized real-time updates[/cyan]\n", justify="center"
        )

        # Create integrated system
        viz_manager, heartbeat = create_demo_real_time_system()

        # Start background workload simulation
        sim_thread = threading.Thread(
            target=heartbeat.simulate_workload, args=(80.0, 8.0), daemon=True
        )
        sim_thread.start()

        self.console.print(
            "[green]🚀 Launching integrated real-time visualization system...[/green]"
        )
        time.sleep(1)

        try:
            # Start real-time updates
            viz_manager.start_real_time_updates(heartbeat)

            # Monitor for 6 seconds with status updates
            start_time = time.time()
            while time.time() - start_time < 6.0:
                status = viz_manager.get_system_status()
                self.console.print(
                    f"[dim]⚡ System Status: {status['streaming_active']} streaming, "
                    f"{len(status['component_stats'])} components active[/dim]"
                )
                time.sleep(1.5)

        except KeyboardInterrupt:
            pass
        finally:
            viz_manager.stop_real_time_updates()

        self.console.print("\n[green]✅ Real-time integration complete![/green]")
        time.sleep(2)

    def show_finale(self) -> None:
        """Show the demo finale with summary."""
        self.console.clear()

        title = Text(
            "🎯 VISUALIZATION EXCELLENCE ACHIEVED", style="bold white on green", justify="center"
        )

        achievements = [
            "🔥 GPU Heartbeat Animation: Technology-specific pulsing with DRA (cyan, 2.0Hz)",
            "📊 SLO Dashboard: Twin gauges with TTFT and cost convergence tracking",
            "🏢 Executive View: Business metrics with ROI and cost optimization",
            "⚡ Real-time Updates: Synchronized streaming across all components",
        ]

        achievements_text = "\n".join(achievements)

        footer = Text(
            "💡 llm-d: Autonomous GPU infrastructure optimization",
            style="bold cyan",
            justify="center",
        )
        call_to_action = Text(
            "🚀 Ready for production deployment!", style="bold white", justify="center"
        )

        content = f"{title}\n\n{achievements_text}\n\n{footer}\n{call_to_action}"

        panel = Panel(
            content,
            title="[bold]🎬 Demo Complete[/bold]",
            border_style="green",
            padding=(2, 4),
        )

        self.console.print(panel)

    def run_complete_demo(self) -> None:
        """Run the complete visualization excellence demonstration."""
        try:
            # Title screen
            self.show_title_screen()

            # Phase 1: Heartbeat Animation
            self.demo_heartbeat_animation()

            # Phase 2: SLO Dashboard
            self.demo_slo_dashboard()

            # Phase 3: Executive View
            self.demo_executive_view()

            # Finale: Real-time Integration
            self.demo_real_time_integration()

            # Show finale
            self.show_finale()

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Demo interrupted by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Demo error: {e}[/red]")


def main():
    """Run the integrated visualization excellence demo."""
    console = Console()

    # Create and run the demo
    demo = VisualizationExcellenceDemo(console)
    demo.run_complete_demo()


if __name__ == "__main__":
    main()
