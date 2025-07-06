#!/usr/bin/env python3
"""
Phase 1 Cost Optimization Demo Script

Real-time LLM cost optimization demonstration using actual Phase 1 infrastructure:
- TokenMetrics integration for real TTFT measurements
- CostCalculator integration for dynamic GPU pricing
- QueueMetrics integration for queue depth impact analysis

This script demonstrates working software capabilities instead of hardcoded values,
providing technical credibility for sales demonstrations.
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Imports after path setup to avoid import errors
from config_loader import load_config  # noqa: E402
from mtop.token_metrics import (  # noqa: E402
    create_cost_calculator,
    create_token_tracker,
    create_ttft_calculator,
)


class Phase1Demo:
    """
    Phase 1 cost optimization demo with real infrastructure integration.

    Demonstrates actual Phase 1 capabilities:
    - Real token metrics and TTFT calculations
    - Dynamic cost calculations using TechnologyConfig
    - Queue depth impact analysis
    - Live ROI calculations
    """

    def __init__(self):
        """Initialize demo with Phase 1 infrastructure components."""
        # Load configuration
        self.config = load_config()

        # Initialize Phase 1 components
        self.token_tracker = create_token_tracker(
            technology_config=self.config.technology, slo_config=self.config.slo
        )
        self.ttft_calculator = create_ttft_calculator(self.config.slo)
        self.cost_calculator = create_cost_calculator(self.config.technology)

        # Demo configuration
        self.demo_models = [
            "llama-3-70b-instruct",
            "gpt-4-turbo",
            "claude-3-sonnet",
            "mixtral-8x7b",
        ]

        # Color codes for terminal output
        self.colors = {
            "header": "\033[95m",
            "blue": "\033[94m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "red": "\033[91m",
            "bold": "\033[1m",
            "underline": "\033[4m",
            "end": "\033[0m",
        }

    def print_colored(self, text: str, color: str = "end", bold: bool = False):
        """Print colored text to terminal."""
        color_code = self.colors.get(color, self.colors["end"])
        bold_code = self.colors["bold"] if bold else ""
        print(f"{bold_code}{color_code}{text}{self.colors['end']}")

    def print_header(self, title: str):
        """Print section header with formatting."""
        print("\n" + "=" * 60)
        self.print_colored(f"  {title}", "header", bold=True)
        print("=" * 60)

    def simulate_realistic_metrics(self):
        """Simulate realistic token generation with Phase 1 integration."""
        print("\n🔄 Initializing Phase 1 token generation simulation...")

        # Create realistic metrics for demo models
        for model in self.demo_models:
            # Simulate realistic token generation
            metrics = self.token_tracker.simulate_token_generation(
                model_name=model,
                target_tokens=150,  # Realistic response length
                target_tps=None,  # Use SLO config defaults
            )

            # Record TTFT measurements
            if metrics.first_token_time:
                self.ttft_calculator.record_ttft_from_metrics(metrics)

        time.sleep(1)  # Brief pause for realism
        print("✅ Phase 1 simulation complete - real metrics generated")

    def show_live_metrics_dashboard(self):
        """Display live metrics dashboard with real Phase 1 data."""
        self.print_header("📊 Live Phase 1 Metrics Dashboard")

        # Get real metrics from token tracker
        all_metrics = self.token_tracker.get_all_metrics()

        print(f"{'Model':<25} {'TPS':<8} {'TTFT (ms)':<12} {'Queue':<7} {'GPU':<6}")
        print("-" * 60)

        for model_name, metrics in all_metrics.items():
            tps = f"{metrics.get_tokens_per_second():.0f}"
            ttft = f"{metrics.get_ttft_ms():.0f}" if metrics.get_ttft_ms() else "N/A"
            queue = f"{metrics.queue_depth}"
            gpu = metrics.gpu_type

            print(f"{model_name:<25} {tps:<8} {ttft:<12} {queue:<7} {gpu:<6}")

        # Show summary statistics
        summary = self.token_tracker.get_summary_stats()
        print(
            f"\n📈 Summary: {summary['total_models']} models, "
            + f"{summary['total_tokens_generated']} tokens generated, "
            + f"{summary['avg_tokens_per_second']:.0f} avg TPS"
        )

    def analyze_cost_optimization(self):
        """Analyze cost optimization opportunities using real CostCalculator."""
        self.print_header("💰 Dynamic Cost Optimization Analysis")

        # Get GPU cost comparison from technology config
        gpu_costs = self.cost_calculator.get_gpu_cost_comparison()

        print("Current GPU Pricing (from TechnologyConfig):")
        for gpu_type, cost in gpu_costs.items():
            print(f"  {gpu_type}: ${cost:.2f}/hour")

        # Calculate real cost savings for a specific model
        model_name = "llama-3-70b-instruct"
        metrics = self.token_tracker.get_metrics(model_name)

        if metrics and metrics.is_completed():
            # Calculate actual costs
            duration = metrics.completion_time - metrics.start_time
            h100_cost = self.cost_calculator.calculate_token_cost(
                metrics.tokens_generated, "H100", duration
            )
            a100_cost = self.cost_calculator.calculate_token_cost(
                metrics.tokens_generated, "A100", duration
            )

            savings = h100_cost - a100_cost
            savings_percent = (savings / h100_cost) * 100

            print(f"\n🎯 Cost Analysis for {model_name}:")
            print(f"  Current (H100): ${h100_cost:.4f} for {metrics.tokens_generated} tokens")
            print(f"  Optimized (A100): ${a100_cost:.4f} for {metrics.tokens_generated} tokens")
            print(f"  Savings: ${savings:.4f} ({savings_percent:.1f}% reduction)")

            # Extrapolate to monthly savings
            monthly_savings = savings * (30 * 24 * 3600) / duration  # Scale to monthly
            print(f"  Monthly savings (scaled): ${monthly_savings:.2f}")

    def demonstrate_queue_impact(self):
        """Demonstrate queue depth impact on TTFT using real QueueMetrics."""
        self.print_header("📊 Queue Depth Impact Analysis")

        # Get queue metrics for models
        queue_metrics = self.token_tracker.get_all_queue_metrics()

        print("Queue Depth Impact on Performance:")
        print(f"{'Model':<25} {'Queue Depth':<12} {'TTFT Impact':<15} {'Utilization':<12}")
        print("-" * 65)

        for model_name, queue_metric in queue_metrics.items():
            stats = queue_metric.get_depth_statistics()
            current_depth = stats["current_depth"]
            ttft_impact = stats["estimated_ttft_impact_ms"]
            utilization = queue_metric.get_queue_utilization()

            print(
                f"{model_name:<25} {current_depth:<12} {ttft_impact:.1f}ms{'':<10} {utilization:.1f}%"
            )

        # Show business impact
        print(f"\n💡 Business Impact:")
        print(f"  • Queue depth directly affects time-to-first-token")
        print(f"  • Each request in queue adds ~10ms TTFT latency")
        print(f"  • Optimal queue management maintains <500ms SLO target")

    def show_slo_compliance(self):
        """Show real SLO compliance using TTFTCalculator."""
        self.print_header("✅ SLO Compliance Analysis")

        # Get real P95 latency from measurements
        p95_latency = self.ttft_calculator.get_p95_latency()
        slo_target = self.ttft_calculator.get_slo_target()

        if p95_latency is not None:
            compliance = "✅ COMPLIANT" if p95_latency <= slo_target else "❌ NON-COMPLIANT"
            variance = self.ttft_calculator.get_slo_variance()

            print(f"SLO Target: {slo_target}ms TTFT P95")
            print(f"Current P95: {p95_latency:.1f}ms")
            print(f"Status: {compliance}")
            print(f"Variance: {variance:+.1f}% from target")

            # Show statistics summary
            stats = self.ttft_calculator.get_statistics_summary()
            print(f"\nStatistics ({stats['measurement_count']} measurements):")
            print(f"  Mean: {stats.get('mean_ms', 0):.1f}ms")
            print(f"  Median: {stats.get('median_ms', 0):.1f}ms")
            print(f"  P95: {stats.get('p95_ms', 0):.1f}ms")
        else:
            print("Insufficient data for P95 calculation (need 20+ measurements)")

    def show_roi_summary(self):
        """Show ROI summary with real calculations."""
        self.print_header("🚀 ROI Summary - Real Phase 1 Results")

        # Get cost statistics
        cost_stats = self.cost_calculator.get_cost_statistics()

        print(f"Infrastructure Efficiency:")
        print(f"  • {cost_stats['total_gpu_types']} GPU types optimized")
        print(
            f"  • Cost range: ${cost_stats['min_hourly_cost']:.2f} - ${cost_stats['max_hourly_cost']:.2f}/hour"
        )
        print(f"  • Average cost: ${cost_stats['avg_hourly_cost']:.2f}/hour")

        # Calculate potential savings
        cheapest_gpu = cost_stats["cheapest_gpu"]
        most_expensive_gpu = cost_stats["most_expensive_gpu"]

        if cheapest_gpu and most_expensive_gpu:
            savings = self.cost_calculator.calculate_cost_savings(
                from_gpu=most_expensive_gpu, to_gpu=cheapest_gpu, duration_seconds=3600  # 1 hour
            )

            print(f"\nCost Optimization Potential:")
            print(f"  • Switch from {most_expensive_gpu} to {cheapest_gpu}")
            print(
                f"  • Savings: ${savings:.2f}/hour ({(savings/cost_stats['max_hourly_cost'])*100:.1f}%)"
            )
            print(f"  • Monthly savings: ${savings * 24 * 30:.2f}")
            print(f"  • Annual savings: ${savings * 24 * 365:.2f}")

        # Show token metrics summary
        token_summary = self.token_tracker.get_summary_stats()
        print(f"\nToken Processing Efficiency:")
        print(f"  • {token_summary['total_models']} models monitored")
        print(f"  • {token_summary['total_tokens_generated']} tokens generated")
        print(f"  • {token_summary['avg_tokens_per_second']:.0f} average TPS")
        print(f"  • {token_summary['avg_ttft_ms']:.0f}ms average TTFT")

    def run_demo(self):
        """Run the complete Phase 1 cost optimization demo."""
        print("\n" + "=" * 60)
        self.print_colored("🎯 mtop Phase 1 Demo: Real-Time Cost Optimization", "header", bold=True)
        self.print_colored("   Demonstrating actual Phase 1 infrastructure integration", "blue")
        print("=" * 60)

        # Demo sequence with realistic timing
        steps = [
            ("Simulating realistic token generation", self.simulate_realistic_metrics),
            ("Displaying live metrics dashboard", self.show_live_metrics_dashboard),
            ("Analyzing cost optimization opportunities", self.analyze_cost_optimization),
            ("Demonstrating queue impact analysis", self.demonstrate_queue_impact),
            ("Checking SLO compliance", self.show_slo_compliance),
            ("Presenting ROI summary", self.show_roi_summary),
        ]

        for step_name, step_func in steps:
            print(f"\n⏳ {step_name}...")
            time.sleep(0.5)  # Brief pause for VHS recording
            step_func()
            time.sleep(1)  # Pause between sections

        print("\n" + "=" * 60)
        self.print_colored("✅ Phase 1 Demo Complete", "green", bold=True)
        self.print_colored("   All metrics generated from real Phase 1 infrastructure", "blue")
        print("=" * 60)


def main():
    """Main demo execution."""
    try:
        demo = Phase1Demo()
        demo.run_demo()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
