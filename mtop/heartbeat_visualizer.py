#!/usr/bin/env python3
"""
Heartbeat animation system for GPU capacity visualization.

This module provides animated pulsing GPU capacity bars with technology-specific
characteristics, smooth transitions, and professional Rich-based animations.
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from rich.align import Align
from rich.bar import Bar
from rich.box import ROUNDED
from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from mtop.gpu_heartbeat import GPUHeartbeat, GPUMetrics, HeartbeatPulse, HeartbeatStrength

from .config_loader import TechnologyConfig


class TechnologyType(Enum):
    """Technology types with specific visual characteristics."""

    DRA = "dra"  # Dynamic Resource Allocation
    TRADITIONAL = "traditional"  # Traditional GPU allocation
    MULTI_INSTANCE = "multi_instance"  # MIG (Multi-Instance GPU)


@dataclass
class TechnologyCharacteristics:
    """Visual characteristics for a technology type."""

    color: str  # Primary color for the technology
    secondary_color: str  # Secondary/accent color
    pulse_frequency_hz: float  # Base pulse frequency in Hz
    pulse_strength: float  # Base pulse strength (0.0 - 1.0)
    animation_style: str  # Animation style identifier
    description: str  # Human-readable description


@dataclass
class AnimationFrame:
    """Single frame of heartbeat animation."""

    timestamp: float
    gpu_id: str
    utilization: float
    capacity_bar_width: int
    pulse_intensity: float  # 0.0 - 1.0
    color: str
    pulse_color: str  # Color during pulse peak
    bar_text: str

    def __post_init__(self):
        """Validate animation frame values."""
        if not 0 <= self.utilization <= 100:
            raise ValueError(f"utilization must be 0-100, got {self.utilization}")
        if not 0 <= self.pulse_intensity <= 1.0:
            raise ValueError(f"pulse_intensity must be 0-1, got {self.pulse_intensity}")


class HeartbeatAnimator:
    """Manages heartbeat animations for GPU capacity bars."""

    # Technology-specific characteristics
    TECHNOLOGY_CONFIGS = {
        TechnologyType.DRA: TechnologyCharacteristics(
            color="#00FFFF",  # Cyan
            secondary_color="#00CCCC",
            pulse_frequency_hz=2.0,  # 2.0 Hz as specified
            pulse_strength=0.8,  # Strong pulse
            animation_style="smooth_wave",
            description="Dynamic Resource Allocation",
        ),
        TechnologyType.TRADITIONAL: TechnologyCharacteristics(
            color="#00FF00",  # Green
            secondary_color="#00CC00",
            pulse_frequency_hz=1.0,
            pulse_strength=0.6,
            animation_style="stepped",
            description="Traditional GPU Allocation",
        ),
        TechnologyType.MULTI_INSTANCE: TechnologyCharacteristics(
            color="#FF6600",  # Orange
            secondary_color="#CC5500",
            pulse_frequency_hz=1.5,
            pulse_strength=0.7,
            animation_style="segmented",
            description="Multi-Instance GPU",
        ),
    }

    def __init__(self, console: Optional[Console] = None):
        """Initialize heartbeat animator.

        Args:
            console: Rich console for output (optional)
        """
        self.console = console or Console()
        self._start_time = time.time()
        self._gpu_technologies: Dict[str, TechnologyType] = {}

    def set_gpu_technology(self, gpu_id: str, technology: TechnologyType) -> None:
        """Set technology type for a specific GPU.

        Args:
            gpu_id: GPU identifier
            technology: Technology type for this GPU
        """
        self._gpu_technologies[gpu_id] = technology

    def get_gpu_technology(self, gpu_id: str) -> TechnologyType:
        """Get technology type for a GPU (default to TRADITIONAL).

        Args:
            gpu_id: GPU identifier

        Returns:
            Technology type for the GPU
        """
        return self._gpu_technologies.get(gpu_id, TechnologyType.TRADITIONAL)

    def calculate_pulse_intensity(
        self, gpu_id: str, base_utilization: float, heartbeat_pulse: HeartbeatPulse
    ) -> float:
        """Calculate current pulse intensity for a GPU.

        Args:
            gpu_id: GPU identifier
            base_utilization: Base GPU utilization (0-100)
            heartbeat_pulse: Current heartbeat pulse characteristics

        Returns:
            Pulse intensity (0.0 - 1.0)
        """
        current_time = time.time()
        elapsed = current_time - self._start_time

        technology = self.get_gpu_technology(gpu_id)
        tech_config = self.TECHNOLOGY_CONFIGS[technology]

        # Calculate base pulse from technology frequency
        tech_pulse_radians = 2 * math.pi * tech_config.pulse_frequency_hz * elapsed
        tech_pulse = (math.sin(tech_pulse_radians) + 1) / 2  # Normalize to 0-1

        # Blend with heartbeat engine pulse
        heartbeat_factor = heartbeat_pulse.intensity
        utilization_factor = base_utilization / 100.0

        # Combine factors with technology-specific strength
        combined_intensity = (
            tech_pulse * tech_config.pulse_strength * 0.6  # Technology rhythm
            + heartbeat_factor * 0.3  # Engine heartbeat
            + utilization_factor * 0.1  # Base utilization
        )

        # Apply smooth easing
        eased_intensity = self._ease_in_out_cubic(combined_intensity)

        return max(0.0, min(1.0, eased_intensity))

    def _ease_in_out_cubic(self, t: float) -> float:
        """Cubic easing function for smooth animations.

        Args:
            t: Input value (0-1)

        Returns:
            Eased value (0-1)
        """
        if t < 0.5:
            return 4 * t * t * t
        else:
            p = 2 * t - 2
            return 1 + p * p * p / 2

    def create_gpu_bar(
        self, gpu_metrics: GPUMetrics, heartbeat_pulse: HeartbeatPulse, bar_width: int = 40
    ) -> AnimationFrame:
        """Create animated GPU capacity bar for a single GPU.

        Args:
            gpu_metrics: Current GPU metrics
            heartbeat_pulse: Current heartbeat pulse
            bar_width: Width of the capacity bar

        Returns:
            Animation frame for this GPU
        """
        gpu_id = gpu_metrics.gpu_id
        utilization = gpu_metrics.utilization_percent

        technology = self.get_gpu_technology(gpu_id)
        tech_config = self.TECHNOLOGY_CONFIGS[technology]

        # Calculate pulse intensity
        pulse_intensity = self.calculate_pulse_intensity(gpu_id, utilization, heartbeat_pulse)

        # Determine colors based on pulse intensity
        base_color = tech_config.color
        pulse_color = tech_config.secondary_color

        # Create bar text with GPU ID and utilization
        bar_text = f"{gpu_id}: {utilization:.1f}% ({tech_config.description})"

        return AnimationFrame(
            timestamp=time.time(),
            gpu_id=gpu_id,
            utilization=utilization,
            capacity_bar_width=bar_width,
            pulse_intensity=pulse_intensity,
            color=base_color,
            pulse_color=pulse_color,
            bar_text=bar_text,
        )

    def render_animated_bar(self, frame: AnimationFrame) -> Panel:
        """Render a single animated GPU capacity bar.

        Args:
            frame: Animation frame data

        Returns:
            Rich Panel with animated bar
        """
        # Calculate effective color based on pulse
        if frame.pulse_intensity > 0.7:
            # High pulse - use pulse color
            bar_color = frame.pulse_color
            border_style = f"bold {frame.pulse_color}"
        elif frame.pulse_intensity > 0.3:
            # Medium pulse - blend colors
            bar_color = frame.color
            border_style = frame.color
        else:
            # Low pulse - use base color
            bar_color = frame.color
            border_style = "dim"

        # Create progress bar
        progress = Progress(
            TextColumn("{task.description}"),
            BarColumn(bar_width=frame.capacity_bar_width),
            TextColumn("{task.percentage:>3.0f}%"),
            expand=False,
        )

        # Add task with current utilization
        task_id = progress.add_task(
            description=f"[bold]{frame.gpu_id}[/bold]", total=100, completed=frame.utilization
        )

        # Create panel with pulsing border
        panel_title = f"GPU {frame.gpu_id}"
        if frame.pulse_intensity > 0.5:
            panel_title = f"[bold]{panel_title}[/bold]"

        return Panel(
            Group(
                progress,
                Text(f"Tech: {self.get_gpu_technology(frame.gpu_id).value.upper()}", style="dim"),
                Text(f"Pulse: {frame.pulse_intensity:.2f}", style="dim"),
            ),
            title=panel_title,
            border_style=border_style,
            box=ROUNDED,
        )

    def create_cluster_visualization(
        self, gpu_heartbeat: GPUHeartbeat, bar_width: int = 30
    ) -> Group:
        """Create animated visualization for entire GPU cluster.

        Args:
            gpu_heartbeat: GPU heartbeat engine with current state
            bar_width: Width of individual GPU bars

        Returns:
            Rich Group with animated cluster visualization
        """
        current_pulse = gpu_heartbeat.get_current_heartbeat()
        all_metrics = gpu_heartbeat.tracker.get_all_gpu_metrics()

        # Create animation frames for all GPUs
        gpu_bars = []
        for gpu_id, metrics in all_metrics.items():
            frame = self.create_gpu_bar(metrics, current_pulse, bar_width)
            animated_bar = self.render_animated_bar(frame)
            gpu_bars.append(animated_bar)

        # Create cluster summary
        aggregate_util = gpu_heartbeat.tracker.get_aggregate_utilization()
        scaling_decision, scaling_reason = gpu_heartbeat.get_scaling_recommendation()

        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Metric", style="bold")
        summary_table.add_column("Value")

        summary_table.add_row("Cluster Utilization", f"{aggregate_util:.1f}%")
        summary_table.add_row("Scaling Decision", scaling_decision.value.replace("_", " ").title())
        summary_table.add_row("Heartbeat", f"{current_pulse.frequency_bpm:.1f} BPM")
        summary_table.add_row("Pulse Strength", current_pulse.strength.value.title())

        summary_panel = Panel(
            summary_table, title="[bold]Cluster Status[/bold]", border_style="blue"
        )

        # Arrange in columns if multiple GPUs
        if len(gpu_bars) <= 2:
            gpu_layout = Group(*gpu_bars)
        else:
            # Split into columns for better layout
            mid_point = len(gpu_bars) // 2
            left_column = Group(*gpu_bars[:mid_point])
            right_column = Group(*gpu_bars[mid_point:])
            gpu_layout = Columns([left_column, right_column], equal=True)

        return Group(summary_panel, "", gpu_layout)

    def run_live_animation(
        self,
        gpu_heartbeat: GPUHeartbeat,
        duration_seconds: float = 60.0,
        refresh_rate: float = 10.0,
    ) -> None:
        """Run live heartbeat animation.

        Args:
            gpu_heartbeat: GPU heartbeat engine
            duration_seconds: How long to run animation
            refresh_rate: Refresh rate in Hz
        """
        refresh_interval = 1.0 / refresh_rate

        with Live(console=self.console, refresh_per_second=refresh_rate) as live:
            start_time = time.time()

            while time.time() - start_time < duration_seconds:
                # Create current visualization
                cluster_viz = self.create_cluster_visualization(gpu_heartbeat)

                # Update live display
                live.update(
                    Panel(
                        cluster_viz,
                        title="[bold]🔥 GPU Heartbeat Monitor[/bold]",
                        border_style="red",
                    )
                )

                time.sleep(refresh_interval)


def create_demo_scenario() -> Tuple[HeartbeatAnimator, GPUHeartbeat]:
    """Create a demo scenario with animated heartbeat visualization.

    Returns:
        Tuple of (animator, gpu_heartbeat_engine)
    """
    from mtop.gpu_heartbeat import create_gpu_heartbeat

    # Create heartbeat engine
    heartbeat = create_gpu_heartbeat()

    # Add GPUs with different technologies
    heartbeat.add_gpu("gpu-00", "nvidia-h100")
    heartbeat.add_gpu("gpu-01", "nvidia-a100")
    heartbeat.add_gpu("gpu-02", "nvidia-v100")

    # Create animator
    animator = HeartbeatAnimator()

    # Set technology types for demonstration
    animator.set_gpu_technology("gpu-00", TechnologyType.DRA)  # DRA = cyan, 2.0Hz
    animator.set_gpu_technology("gpu-01", TechnologyType.TRADITIONAL)
    animator.set_gpu_technology("gpu-02", TechnologyType.MULTI_INSTANCE)

    return animator, heartbeat


def main():
    """Demo the heartbeat animation system."""
    console = Console()

    console.print("[bold]🔥 GPU Heartbeat Animation Demo[/bold]", style="red")
    console.print("Creating animated GPU cluster with technology-specific characteristics...\n")

    # Create demo scenario
    animator, heartbeat = create_demo_scenario()

    # Start workload simulation in background
    import threading

    simulation_thread = threading.Thread(
        target=heartbeat.simulate_workload,
        args=(70.0, 30.0),  # 70% target utilization for 30 seconds
        daemon=True,
    )
    simulation_thread.start()

    # Run live animation
    try:
        animator.run_live_animation(heartbeat, duration_seconds=30.0, refresh_rate=5.0)
    except KeyboardInterrupt:
        console.print("\n[yellow]Animation stopped by user[/yellow]")

    console.print("\n[green]✅ Heartbeat animation demo complete![/green]")


if __name__ == "__main__":
    main()
