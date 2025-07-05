#!/usr/bin/env python3
import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict

from readchar import readkey
from rich.console import Console
from rich.table import Table


def render_step(state: Dict[str, Any], step_idx: int, total_steps: int, topology: str) -> None:
    console = Console()
    console.clear()
    step_info = f"🔁 Rollout: {topology.capitalize()} (Step {step_idx + 1}/{total_steps})   [press 'n'=next, 'q'=quit]"
    console.rule(step_info)

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Model", width=30)
    table.add_column("Status", justify="center")
    table.add_column("Traffic %", justify="center")

    for model, status_info in state["status"].items():
        traffic = state["traffic"].get(model, 0)
        status = status_info["status"]
        if status == "Ready":
            emoji = "🟢"
        elif status == "Pending":
            emoji = "🟡"
        elif status == "Failed":
            emoji = "🔴"
        elif status == "Terminated":
            emoji = "❌"
        elif status == "Shadow":
            emoji = "👻"
        else:
            emoji = "⚪️"
        table.add_row(model, f"{emoji} {status}", f"{traffic}%")

    console.print(table)


def main() -> None:
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--topology", default="canary", help="Name of rollout topology")
        parser.add_argument(
            "--autoplay", action="store_true", help="Automatically advance rollout steps"
        )
        parser.add_argument(
            "--delay", type=int, default=2, help="Seconds between steps in autoplay mode"
        )
        args = parser.parse_args()

        state_dir = Path(f"mocks/states/rollout/{args.topology}")
        steps = sorted(state_dir.glob("step*.json"))
        if not steps:
            print(f"No steps found for topology '{args.topology}'")
            return

        for idx, step_path in enumerate(steps):
            with open(step_path) as f:
                state = json.load(f)
            render_step(state, idx, len(steps), args.topology)
            if args.autoplay:
                time.sleep(args.delay)
            else:
                while True:
                    key = readkey()
                    if key.lower() == "n":
                        break
                    elif key.lower() == "q":
                        return

    except KeyboardInterrupt:
        print("\n👋 Rollout viewer exited.")


if __name__ == "__main__":
    main()
