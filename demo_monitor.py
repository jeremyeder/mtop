#!/usr/bin/env python3
"""
Split-screen demo monitor - bottom pane display
Shows real-time multi-model monitoring and metrics
"""

import argparse
import json
import random
import signal
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text


class ModelMetrics:
    """Represents metrics for a single model"""
    def __init__(self, name: str, base_rps: int = 100):
        self.name = name
        self.base_rps = base_rps
        self.current_rps = base_rps
        self.target_rps = base_rps
        self.cpu_percent = random.randint(20, 40)
        self.memory_percent = random.randint(30, 50)
        self.error_rate = 0.1
        self.latency_p95 = random.randint(80, 150)
        self.status = "Ready"
        self.replicas = 3
        self.traffic_percent = 100
        self.deployment_progress = 100
        
    def update(self, action: str = "normal"):
        """Update metrics based on action"""
        if action == "surge_start":
            self.target_rps = self.base_rps * random.uniform(2.5, 4.0)
        elif action == "autoscale":
            if self.current_rps > self.base_rps * 2:
                self.replicas = min(self.replicas + 2, 12)
                self.cpu_percent = max(self.cpu_percent - 10, 20)
        elif action == "node_failure":
            if random.random() < 0.3:  # 30% chance this model is affected
                self.status = "Degraded"
                self.error_rate = 5.0
                self.current_rps = self.current_rps * 0.7
        elif action == "recovery":
            if self.status == "Degraded":
                self.status = "Recovering"
                self.error_rate = max(self.error_rate - 1.0, 0.1)
        elif action == "full_recovery":
            self.status = "Ready"
            self.error_rate = 0.1
            
        # Smooth transitions
        if self.current_rps < self.target_rps:
            self.current_rps = min(self.current_rps * 1.1, self.target_rps)
        elif self.current_rps > self.target_rps:
            self.current_rps = max(self.current_rps * 0.95, self.target_rps)
            
        # Add some randomness
        self.current_rps += random.uniform(-10, 10)
        self.cpu_percent += random.randint(-2, 2)
        self.cpu_percent = max(10, min(95, self.cpu_percent))


class DemoMonitor:
    def __init__(self, scenario: str = "basic", headless: bool = False):
        self.console = Console()
        self.scenario = scenario
        self.headless = headless
        self.running = True
        self.current_action = "init"
        self.view_mode = "overview"  # overview, traffic, health, deployments
        self.start_time = time.time()
        self.max_runtime = 30 if headless else 3600  # 30 sec for headless, 1 hour for interactive
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize models based on scenario
        self.models = self._initialize_models()
        
    def _signal_handler(self, signum, frame):
        """Handle signals for clean exit"""
        self.running = False
        sys.exit(0)
        
    def _initialize_models(self) -> Dict[str, ModelMetrics]:
        """Initialize models based on scenario"""
        models = {}
        
        if self.scenario == "basic":
            model_names = ["gpt2", "bert-base", "t5-base"]
            base_rps_values = [500, 300, 200]
        elif self.scenario == "surge":
            # Use many models for surge scenario
            model_names = [
                "gpt-4", "gpt-3.5-turbo", "claude-2", "llama-2-70b",
                "bert-large", "t5-xl", "roberta-base", "distilbert",
                "whisper-base", "stable-diffusion", "codex", "davinci",
                "curie", "babbage", "ada", "bloom-176b", "opt-175b",
                "palm-540b", "chinchilla", "gopher"
            ]
            base_rps_values = [1000, 800, 600, 400] + [random.randint(50, 300) for _ in range(16)]
        elif self.scenario == "chaos":
            model_names = ["gpt-4", "claude-2", "llama-2-70b", "palm-540b"]
            base_rps_values = [800, 600, 400, 300]
        else:  # multi
            model_names = ["gpt-4", "claude-2", "bert-large", "t5-xl"]
            base_rps_values = [600, 500, 300, 250]
            
        for name, base_rps in zip(model_names, base_rps_values):
            models[name] = ModelMetrics(name, base_rps)
            
        return models
        
    def _read_signal(self) -> Optional[Dict]:
        """Read signal from narrator"""
        signal_file = Path("/tmp/kubectl_ld_demo_signal.json")
        if signal_file.exists():
            try:
                signal_data = json.loads(signal_file.read_text())
                return signal_data
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return None
        
    def _create_traffic_table(self) -> Table:
        """Create traffic monitoring table"""
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Model", width=20)
        table.add_column("Status", width=12, justify="center")
        table.add_column("RPS", width=10, justify="right")
        table.add_column("Traffic %", width=10, justify="center")
        table.add_column("Replicas", width=8, justify="center")
        table.add_column("CPU", width=8, justify="center")
        table.add_column("Errors", width=8, justify="center")
        
        # Sort models by RPS for better visualization
        sorted_models = sorted(self.models.items(), key=lambda x: x[1].current_rps, reverse=True)
        
        for name, metrics in sorted_models:
            # Status emoji
            if metrics.status == "Ready":
                status_emoji = "🟢"
            elif metrics.status == "Degraded":
                status_emoji = "🔴"
            elif metrics.status == "Recovering":
                status_emoji = "🟡"
            else:
                status_emoji = "⚪"
                
            # Traffic direction indicator
            rps_trend = "→"
            if metrics.current_rps > metrics.target_rps * 1.05:
                rps_trend = "↗️"
            elif metrics.current_rps < metrics.target_rps * 0.95:
                rps_trend = "↘️"
                
            # Error rate color
            error_style = "green" if metrics.error_rate < 1 else "yellow" if metrics.error_rate < 3 else "red"
            
            table.add_row(
                name[:18] + ("..." if len(name) > 18 else ""),
                f"{status_emoji} {metrics.status}",
                f"{int(metrics.current_rps):,} {rps_trend}",
                f"{metrics.traffic_percent}%",
                str(metrics.replicas),
                f"{metrics.cpu_percent}%",
                f"[{error_style}]{metrics.error_rate:.1f}%[/{error_style}]"
            )
            
        return table
        
    def _create_summary_panel(self) -> Panel:
        """Create summary statistics panel"""
        total_rps = sum(m.current_rps for m in self.models.values())
        total_replicas = sum(m.replicas for m in self.models.values())
        avg_cpu = sum(m.cpu_percent for m in self.models.values()) / len(self.models)
        avg_error = sum(m.error_rate for m in self.models.values()) / len(self.models)
        
        healthy_models = sum(1 for m in self.models.values() if m.status == "Ready")
        total_models = len(self.models)
        
        summary_text = Text()
        summary_text.append(f"📊 Cluster Overview\n", style="bold cyan")
        summary_text.append(f"Total RPS: {int(total_rps):,} ", style="white")
        summary_text.append(f"• Models: {healthy_models}/{total_models} healthy ", style="green" if healthy_models == total_models else "yellow")
        summary_text.append(f"• Replicas: {total_replicas}\n", style="white")
        summary_text.append(f"Avg CPU: {avg_cpu:.1f}% ", style="white")
        summary_text.append(f"• Avg Errors: {avg_error:.2f}% ", style="green" if avg_error < 1 else "red")
        summary_text.append(f"• Action: {self.current_action}", style="dim")
        
        return Panel(summary_text, border_style="cyan")
        
    def _create_deployment_progress(self) -> Panel:
        """Create deployment progress panel"""
        if self.scenario != "multi":
            return Panel("No active deployments", border_style="dim")
            
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        
        # Simulate different deployment strategies
        strategies = {
            "gpt-4": ("Blue/Green", 85),
            "claude-2": ("Canary", 45),
            "bert-large": ("Shadow", 30),
            "t5-xl": ("Rolling", 70)
        }
        
        for model, (strategy, percent) in strategies.items():
            progress.add_task(f"{model} ({strategy})", completed=percent, total=100)
            
        return Panel(progress, title="🚀 Active Deployments", border_style="blue")
        
    def _create_layout(self) -> Layout:
        """Create the monitor layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="summary", size=4),
            Layout(name="main"),
            Layout(name="deployments", size=8)
        )
        
        layout["summary"].update(self._create_summary_panel())
        layout["main"].update(Panel(self._create_traffic_table(), title="🔥 Live Traffic Monitor", border_style="green"))
        layout["deployments"].update(self._create_deployment_progress())
        
        return layout
        
    def run(self):
        """Run the monitor display"""
        try:
            with Live(self._create_layout(), refresh_per_second=2) as live:
                while self.running:
                    # Check for timeout in headless mode
                    if self.headless and (time.time() - self.start_time) > self.max_runtime:
                        self.console.print("[yellow]Demo timeout reached, exiting...[/yellow]")
                        break
                        
                    # Check for signals from narrator
                    signal_data = self._read_signal()
                    if signal_data:
                        self.current_action = signal_data.get("action", "normal")
                        # Check for exit signal
                        if signal_data.get("exit", False):
                            break
                        
                    # Update all models
                    for model in self.models.values():
                        model.update(self.current_action)
                        
                    # Update display
                    live.update(self._create_layout())
                    
                    time.sleep(0.5)
                    
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.console.print(f"[red]Monitor error: {e}[/red]")


def main():
    parser = argparse.ArgumentParser(description="kubectl-ld Demo Monitor")
    parser.add_argument("--scenario", default="basic",
                       choices=["basic", "surge", "chaos", "multi"],
                       help="Demo scenario to monitor")
    parser.add_argument("--headless", action="store_true",
                       help="Run in headless mode")
    
    args = parser.parse_args()
    
    monitor = DemoMonitor(scenario=args.scenario, headless=args.headless)
    monitor.run()


if __name__ == "__main__":
    main()