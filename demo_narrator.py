#!/usr/bin/env python3
"""
Split-screen demo narrator - top pane controller
Provides step-by-step narration and user interaction
"""

import argparse
import json
import signal
import sys
import time
from pathlib import Path
from typing import Dict, List

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.text import Text

try:
    from readchar import readkey
except ImportError:
    # Fallback for systems without readchar
    def readkey():
        return input("Press Enter to continue...") or " "


class DemoNarrator:
    def __init__(self, scenario: str = "basic", headless: bool = False):
        self.console = Console()
        self.scenario = scenario
        self.headless = headless
        self.step = 0
        self.running = True
        self.start_time = time.time()
        
        # Setup signal handler for clean exit
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Load scenario configuration
        self.config = self._load_scenario_config()
        
    def _signal_handler(self, signum, frame):
        """Handle signals for clean exit"""
        self.running = False
        self.console.print("\n[yellow]Demo terminated by user[/yellow]")
        sys.exit(0)
        
    def _load_scenario_config(self) -> Dict:
        """Load scenario configuration"""
        scenarios = {
            "basic": {
                "title": "Basic Rollout Demo",
                "description": "Simple 3-model canary deployment",
                "models": ["gpt2", "bert-base", "t5-base"],
                "steps": [
                    {
                        "title": "Initialize Models",
                        "description": "Setting up base models with current traffic distribution",
                        "action": "init",
                        "duration": 3
                    },
                    {
                        "title": "Start Canary Deployment", 
                        "description": "Begin rolling out new model version to 10% of traffic",
                        "action": "canary_start",
                        "duration": 5
                    },
                    {
                        "title": "Monitor Health",
                        "description": "Watching error rates and latency during canary phase",
                        "action": "monitor",
                        "duration": 4
                    },
                    {
                        "title": "Scale Canary",
                        "description": "Increasing canary traffic to 50% based on positive metrics",
                        "action": "canary_scale",
                        "duration": 5
                    },
                    {
                        "title": "Complete Rollout",
                        "description": "Promoting canary to 100% and retiring old version",
                        "action": "complete",
                        "duration": 3
                    }
                ]
            },
            "surge": {
                "title": "Traffic Surge Response",
                "description": "Black Friday surge across 20 models",
                "models": "all",  # Use all available models
                "steps": [
                    {
                        "title": "Baseline Traffic",
                        "description": "Normal evening traffic across all model endpoints",
                        "action": "baseline",
                        "duration": 3
                    },
                    {
                        "title": "Surge Detection",
                        "description": "🚨 Traffic spike detected! +340% increase in 60 seconds",
                        "action": "surge_start",
                        "duration": 4
                    },
                    {
                        "title": "Auto-Scaling Response",
                        "description": "Triggering horizontal pod autoscaler across high-demand models",
                        "action": "autoscale",
                        "duration": 6
                    },
                    {
                        "title": "Load Balancing",
                        "description": "Intelligent traffic distribution to prevent hotspots",
                        "action": "load_balance",
                        "duration": 5
                    },
                    {
                        "title": "Peak Management",
                        "description": "Maintaining performance during peak load",
                        "action": "peak_manage",
                        "duration": 4
                    },
                    {
                        "title": "Graceful Scale-Down",
                        "description": "Surge ending - scaling down to optimal capacity",
                        "action": "scale_down",
                        "duration": 3
                    }
                ]
            },
            "chaos": {
                "title": "Chaos Engineering",
                "description": "Failure injection and recovery testing",
                "models": ["gpt-4", "claude-2", "llama-2"],
                "steps": [
                    {
                        "title": "Healthy Baseline",
                        "description": "All systems operational - establishing baseline metrics",
                        "action": "healthy",
                        "duration": 3
                    },
                    {
                        "title": "Inject Node Failure",
                        "description": "💥 Simulating node failure in us-west-2a availability zone",
                        "action": "node_failure",
                        "duration": 5
                    },
                    {
                        "title": "Automatic Recovery",
                        "description": "Kubernetes detecting failure and rescheduling pods",
                        "action": "recovery",
                        "duration": 6
                    },
                    {
                        "title": "Network Partition",
                        "description": "🌐 Simulating network split between regions",
                        "action": "network_partition",
                        "duration": 4
                    },
                    {
                        "title": "Degraded Mode",
                        "description": "Operating with reduced capacity during partition",
                        "action": "degraded",
                        "duration": 3
                    },
                    {
                        "title": "Full Recovery",
                        "description": "✅ Network healed - returning to full capacity",
                        "action": "full_recovery",
                        "duration": 3
                    }
                ]
            },
            "multi": {
                "title": "Multi-Strategy Deployment",
                "description": "Multiple rollout strategies simultaneously",
                "models": ["gpt-4", "claude-2", "bert-large", "t5-xl"],
                "steps": [
                    {
                        "title": "Strategy Planning",
                        "description": "Planning different deployment strategies per model type",
                        "action": "plan",
                        "duration": 3
                    },
                    {
                        "title": "Blue/Green for GPT-4",
                        "description": "🟦🟩 Full environment swap for critical model",
                        "action": "bluegreen",
                        "duration": 5
                    },
                    {
                        "title": "Canary for Claude-2",
                        "description": "🕯️ Gradual rollout with traffic splitting",
                        "action": "canary",
                        "duration": 4
                    },
                    {
                        "title": "Shadow for BERT",
                        "description": "👻 Dark launch - testing without user impact",
                        "action": "shadow",
                        "duration": 4
                    },
                    {
                        "title": "Rolling for T5",
                        "description": "🔄 Progressive instance replacement",
                        "action": "rolling",
                        "duration": 5
                    },
                    {
                        "title": "Coordinated Completion",
                        "description": "All strategies completing successfully",
                        "action": "complete_all",
                        "duration": 3
                    }
                ]
            }
        }
        return scenarios.get(self.scenario, scenarios["basic"])
    
    def _wait_for_user(self, prompt: str = "Press any key to continue"):
        """Wait for user input or auto-advance in headless mode"""
        if self.headless:
            time.sleep(2)
            return
            
        self.console.print(f"\n[dim]{prompt}... (Q to quit)[/dim]")
        key = readkey().lower()
        if key in ['q', '\x03']:  # 'q' or Ctrl+C
            self.running = False
            raise KeyboardInterrupt()
    
    def _create_header(self) -> Panel:
        """Create the demo header"""
        title_text = Text(self.config["title"], style="bold blue")
        subtitle_text = Text(self.config["description"], style="dim")
        
        header_text = Text()
        header_text.append("🎬 kubectl-ld Split-Screen Demo\n", style="bold")
        header_text.append(title_text)
        header_text.append("\n")
        header_text.append(subtitle_text)
        
        return Panel(
            Align.center(header_text),
            border_style="blue",
            padding=(1, 2)
        )
    
    def _create_step_panel(self, step_info: Dict) -> Panel:
        """Create step information panel"""
        step_num = self.step + 1
        total_steps = len(self.config["steps"])
        
        # Progress bar
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        task = progress.add_task(
            f"Step {step_num}/{total_steps}",
            total=100,
            completed=(step_num - 1) * (100 / total_steps)
        )
        
        # Step content
        content = Text()
        content.append(f"🔸 Step {step_num}: {step_info['title']}\n\n", style="bold green")
        content.append(step_info["description"], style="white")
        content.append(f"\n\n⏱️ Duration: ~{step_info['duration']}s", style="dim")
        
        return Panel(
            content,
            title=f"📊 Demo Progress",
            border_style="green",
            padding=(1, 2)
        )
    
    def _create_controls_panel(self) -> Panel:
        """Create controls information panel"""
        if self.headless:
            controls_text = Text("🤖 Headless Mode - Auto-advancing", style="dim")
        else:
            controls_text = Text()
            controls_text.append("🎮 Controls:\n", style="bold yellow")
            controls_text.append("  [ENTER] ", style="bold")
            controls_text.append("Continue to next step\n")
            controls_text.append("  [Q] ", style="bold")
            controls_text.append("Quit demo\n")
            controls_text.append("  [Ctrl+B,D] ", style="bold")
            controls_text.append("Detach tmux session")
        
        return Panel(
            controls_text,
            title="🎯 Instructions",
            border_style="yellow",
            padding=(0, 2)
        )
    
    def run(self):
        """Run the narrator demo"""
        try:
            self.console.clear()
            
            # Show header
            self.console.print(self._create_header())
            self.console.print()
            
            if not self.headless:
                self._wait_for_user("Press any key to start the demo")
                
            # Run through all steps
            for step_info in self.config["steps"]:
                if not self.running:
                    break
                    
                self.console.clear()
                self.console.print(self._create_header())
                self.console.print()
                self.console.print(self._create_step_panel(step_info))
                self.console.print()
                self.console.print(self._create_controls_panel())
                
                # Signal to monitor what action to perform
                signal_file = Path("/tmp/kubectl_ld_demo_signal.json")
                signal_data = {
                    "action": step_info["action"],
                    "step": self.step,
                    "timestamp": time.time()
                }
                signal_file.write_text(json.dumps(signal_data))
                
                if not self.headless:
                    self._wait_for_user()
                else:
                    time.sleep(step_info["duration"])
                
                self.step += 1
            
            # Demo complete
            self.console.clear()
            self.console.print(Panel(
                Align.center(Text("✅ Demo Complete!\n\nThank you for watching the kubectl-ld demo", style="bold green")),
                border_style="green",
                padding=(2, 2)
            ))
            
            # Signal exit to monitor
            signal_file = Path("/tmp/kubectl_ld_demo_signal.json")
            exit_signal = {
                "action": "exit",
                "exit": True,
                "step": self.step,
                "timestamp": time.time()
            }
            signal_file.write_text(json.dumps(exit_signal))
            
            # Wait a moment for monitor to receive exit signal
            time.sleep(2)
            
            # Clean up signal file
            if signal_file.exists():
                signal_file.unlink()
                
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Demo interrupted by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
        finally:
            # Ensure signal file is cleaned up
            signal_file = Path("/tmp/kubectl_ld_demo_signal.json")
            if signal_file.exists():
                signal_file.unlink()


def main():
    parser = argparse.ArgumentParser(description="kubectl-ld Demo Narrator")
    parser.add_argument("--scenario", default="basic", 
                       choices=["basic", "surge", "chaos", "multi"],
                       help="Demo scenario to run")
    parser.add_argument("--headless", action="store_true",
                       help="Run in headless mode with automatic advancement")
    
    args = parser.parse_args()
    
    narrator = DemoNarrator(scenario=args.scenario, headless=args.headless)
    narrator.run()


if __name__ == "__main__":
    main()