#!/usr/bin/env python3
"""
Simple Demo Command Wrapper for mtop

Makes it super easy to run different demo scenarios:
  ./scripts/demo.py startup
  ./scripts/demo.py enterprise
  ./scripts/demo.py canary-failure
  ./scripts/demo.py cost-optimization
  ./scripts/demo.py research-lab

Like having a magic wand for demos! 🪄
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class DemoRunner:
    """The demo magic happens here! ✨"""

    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.recipes_dir = self.repo_root / "demos" / "recipes"
        self.mtop_cmd = self.repo_root / "mtop-main"

    def list_recipes(self) -> List[str]:
        """Show all available demo recipes"""
        if not self.recipes_dir.exists():
            return []

        recipes = []
        for recipe_file in self.recipes_dir.glob("*.yaml"):
            recipes.append(recipe_file.stem)
        return sorted(recipes)

    def load_recipe(self, recipe_name: str) -> Dict[str, Any]:
        """Load a demo recipe configuration"""
        recipe_path = self.recipes_dir / f"{recipe_name}.yaml"

        if not recipe_path.exists():
            available = ", ".join(self.list_recipes())
            raise FileNotFoundError(
                f"Recipe '{recipe_name}' not found. Available recipes: {available}"
            )

        with open(recipe_path, "r") as f:
            return yaml.safe_load(f)

    def set_environment(self, recipe: Dict[str, Any]) -> Dict[str, str]:
        """Set up environment variables for the demo"""
        env = os.environ.copy()

        # Set basic environment from recipe
        env_config = recipe.get("environment", {})
        if "mode" in env_config:
            env["MTOP_MODE"] = env_config["mode"]

        # Apply overrides from recipe
        overrides = recipe.get("overrides", {})
        for key, value in overrides.items():
            env[key] = str(value)

        # Set configuration file if specified
        if "config" in env_config:
            config_file = self.repo_root / "mocks" / "config" / env_config["config"]
            if config_file.exists():
                env["MTOP_CONFIG_PATH"] = str(config_file)

        return env

    def print_banner(self, recipe: Dict[str, Any]):
        """Print a friendly banner for the demo"""
        name = recipe.get("name", "Demo")
        description = recipe.get("description", "")
        emoji = recipe.get("emoji", "🎯")

        print(f"\n{emoji} {name}")
        print("=" * (len(name) + 3))
        print(f"{description}\n")

        # Show what we're about to do
        steps = recipe.get("steps", [])
        if steps:
            print("Demo Steps:")
            for i, step in enumerate(steps, 1):
                action = step.get("action", "unknown")
                desc = step.get("description", "")
                print(f"  {i}. {action}: {desc}")
            print()

    def print_outcomes(self, recipe: Dict[str, Any]):
        """Print expected outcomes"""
        outcomes = recipe.get("outcomes", [])
        if outcomes:
            print("\n✅ Expected Outcomes:")
            for outcome in outcomes:
                print(f"  • {outcome}")
            print()

    def run_demo_steps(self, recipe: Dict[str, Any], env: Dict[str, str], interactive: bool = True):
        """Execute the demo steps"""
        steps = recipe.get("steps", [])

        for i, step in enumerate(steps, 1):
            action = step.get("action", "")
            description = step.get("description", "")
            duration = step.get("duration", None)
            target = step.get("target", None)

            print(f"\n🎬 Step {i}: {description}")

            if interactive:
                input("Press Enter to continue...")

            # Build command based on action
            cmd = [str(self.mtop_cmd)]

            if action == "list":
                cmd.append("list")
            elif action == "get" and target:
                cmd.extend(["get", target])
            elif action == "ldtop" or action == "monitor":
                cmd.append("ldtop")
                if duration:
                    cmd.extend(["--interval", "1"])  # Set interval instead of duration
            elif action == "simulate":
                cmd.append("simulate")
                sim_type = step.get("type", "canary")
                cmd.append(sim_type)
                if target:
                    cmd.extend(["--target", target])
            elif action == "cost_analysis":
                cmd.extend(["cost", "analyze"])
            elif action == "cost_report":
                cmd.extend(["cost", "report"])
            else:
                print(f"⚠️  Unknown action: {action}")
                continue

            # Run the command
            try:
                print(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, env=env, cwd=self.repo_root)
                if result.returncode != 0:
                    print(f"⚠️  Command failed with exit code {result.returncode}")
            except FileNotFoundError:
                print("⚠️  mtop command not found. Make sure it's executable: chmod +x mtop")
            except Exception as e:
                print(f"⚠️  Error running command: {e}")

    def run_recipe(self, recipe_name: str, interactive: bool = True, dry_run: bool = False):
        """Run a complete demo recipe"""
        try:
            recipe = self.load_recipe(recipe_name)
            env = self.set_environment(recipe)

            self.print_banner(recipe)

            if dry_run:
                print("🔍 DRY RUN - Would set these environment variables:")
                for key, value in env.items():
                    if key.startswith("MTOP_") or key in ["LLD_MODE"]:
                        print(f"  {key}={value}")
                print("\n🔍 DRY RUN - Would execute these steps:")
                steps = recipe.get("steps", [])
                for i, step in enumerate(steps, 1):
                    print(f"  {i}. {step.get('action', 'unknown')}: {step.get('description', '')}")
                return

            # Show environment setup
            print("🔧 Environment Setup:")
            env_vars = {k: v for k, v in env.items() if k.startswith("MTOP_") or k == "LLD_MODE"}
            for key, value in env_vars.items():
                print(f"  {key}={value}")
            print()

            # Run the demo steps
            self.run_demo_steps(recipe, env, interactive)

            # Show expected outcomes
            self.print_outcomes(recipe)

        except Exception as e:
            print(f"❌ Demo failed: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="🎯 Super Simple mtop Demo Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./scripts/demo.py startup          # Run startup demo
  ./scripts/demo.py enterprise       # Run enterprise demo  
  ./scripts/demo.py canary-failure   # Run canary failure demo
  ./scripts/demo.py --list           # Show available demos
  ./scripts/demo.py startup --dry-run  # See what would happen
  ./scripts/demo.py enterprise --no-interactive  # Run without pauses

Available Recipes:
  startup         🚀 Small startup with limited resources
  enterprise      🏢 Large enterprise with multiple teams  
  canary-failure  🚨 Canary deployment failure scenario
  cost-optimization 💰 GPU cost optimization demo
  research-lab    🔬 Experimental research environment
        """,
    )

    parser.add_argument(
        "recipe", nargs="?", help="Demo recipe to run (use --list to see available recipes)"
    )
    parser.add_argument("--list", action="store_true", help="List available demo recipes")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be executed without running"
    )
    parser.add_argument(
        "--no-interactive", action="store_true", help="Run without interactive pauses"
    )

    args = parser.parse_args()

    runner = DemoRunner()

    if args.list:
        recipes = runner.list_recipes()
        if recipes:
            print("🎯 Available Demo Recipes:")
            for recipe in recipes:
                try:
                    recipe_data = runner.load_recipe(recipe)
                    emoji = recipe_data.get("emoji", "📋")
                    description = recipe_data.get("description", "No description")
                    print(f"  {recipe:<20} {emoji} {description}")
                except Exception:
                    print(f"  {recipe:<20} ❓ (error loading recipe)")
        else:
            print("No demo recipes found.")
        return

    if not args.recipe:
        parser.print_help()
        return

    runner.run_recipe(args.recipe, interactive=not args.no_interactive, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
