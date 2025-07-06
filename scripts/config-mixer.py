#!/usr/bin/env python3
"""
Interactive Configuration Mixer for mtop Demos

Like a recipe builder but for demo configurations! 
Choose your adventure style interface to create custom demo scenarios.

Usage:
  ./scripts/config-mixer.py  # Interactive mode
  ./scripts/config-mixer.py --save my-custom-demo  # Save the recipe
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigMixer:
    """Mix and match demo configurations like a DJ! 🎧"""

    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.recipes_dir = self.repo_root / "demos" / "recipes"
        self.mocks_dir = self.repo_root / "mocks"

        # Available options for each category
        self.environments = {
            "development": {
                "description": "Small startup, CPU-only, debug mode",
                "emoji": "🏠",
                "config": "development-config.json",
                "cost_multiplier": 0.5,
            },
            "production": {
                "description": "High-performance production environment",
                "emoji": "🏭",
                "config": "production-config.json",
                "cost_multiplier": 1.0,
            },
            "enterprise": {
                "description": "Multi-tenant enterprise deployment",
                "emoji": "🏢",
                "config": "enterprise-config.json",
                "cost_multiplier": 1.2,
            },
            "research": {
                "description": "Academic research lab settings",
                "emoji": "🔬",
                "config": "research-config.json",
                "cost_multiplier": 0.7,
            },
            "edge": {
                "description": "Edge computing, limited resources",
                "emoji": "☁️",
                "config": "edge-config.json",
                "cost_multiplier": 0.3,
            },
        }

        self.topologies = {
            "enterprise": {
                "description": "Multiple namespaces, complex routing",
                "emoji": "🌐",
                "models": ["gpt-4-turbo", "claude-3-haiku", "granite-3-8b-instruct"],
            },
            "edge": {
                "description": "Single node, minimal footprint",
                "emoji": "📱",
                "models": ["gpt2", "bert-base-uncased"],
            },
            "research": {
                "description": "Experimental models, flexible resources",
                "emoji": "🧪",
                "models": ["deepseek-r1-distill-llama-8b", "stable-code-instruct-3b"],
            },
            "gradual": {
                "description": "Progressive scaling demonstration",
                "emoji": "📈",
                "models": ["gpt2", "granite-3-8b-instruct", "llama-3-70b-instruct"],
            },
        }

        self.scenarios = {
            "normal": {
                "description": "Steady state operations",
                "emoji": "😌",
                "qps_range": (50, 300),
                "error_rate": 0.5,
            },
            "spike": {
                "description": "Traffic spikes and load testing",
                "emoji": "📈",
                "qps_range": (200, 1000),
                "error_rate": 1.0,
            },
            "failure": {
                "description": "Failure injection and recovery",
                "emoji": "🚨",
                "qps_range": (100, 400),
                "error_rate": 5.0,
            },
            "cost-optimization": {
                "description": "Cost efficiency focus",
                "emoji": "💰",
                "qps_range": (75, 250),
                "error_rate": 0.8,
            },
        }

        self.rollout_types = {
            "canary": {"description": "Gradual canary deployment", "emoji": "🐤", "safety": "high"},
            "bluegreen": {
                "description": "Blue-green instant switch",
                "emoji": "🔄",
                "safety": "medium",
            },
            "rolling": {"description": "Rolling update one by one", "emoji": "🌊", "safety": "high"},
            "shadow": {
                "description": "Shadow testing in parallel",
                "emoji": "👥",
                "safety": "very_high",
            },
        }

    def print_header(self):
        """Print a fancy header"""
        print("\n🎛️  mtop Configuration Mixer")
        print("=" * 35)
        print("Build your perfect demo configuration!")
        print("Choose from the options below...\n")

    def choose_from_options(self, category: str, options: Dict[str, Dict]) -> str:
        """Let user choose from a category of options"""
        print(f"🎯 Choose your {category}:")
        print()

        option_keys = list(options.keys())
        for i, (key, info) in enumerate(options.items(), 1):
            emoji = info.get("emoji", "📋")
            description = info.get("description", "No description")
            print(f"  {i}. {key:<15} {emoji} {description}")

        print()
        while True:
            try:
                choice = input(f"Enter choice (1-{len(option_keys)}): ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(option_keys):
                        selected = option_keys[idx]
                        print(f"✅ Selected: {selected} {options[selected]['emoji']}")
                        print()
                        return selected

                print("❌ Invalid choice. Please try again.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)

    def get_custom_values(self) -> Dict[str, Any]:
        """Get custom values from user"""
        print("🔧 Custom Settings (press Enter to skip):")

        custom = {}

        # QPS
        qps = input("  Baseline QPS (default: auto): ").strip()
        if qps.isdigit():
            custom["baseline_qps"] = int(qps)

        # GPU cost
        cost = input("  GPU hourly cost in $ (default: auto): ").strip()
        try:
            if cost:
                custom["gpu_cost"] = float(cost)
        except ValueError:
            pass

        # Error tolerance
        error = input("  Error rate tolerance % (default: auto): ").strip()
        try:
            if error:
                custom["error_rate"] = float(error)
        except ValueError:
            pass

        print()
        return custom

    def build_recipe(self, choices: Dict[str, str], custom: Dict[str, Any]) -> Dict[str, Any]:
        """Build the demo recipe from choices"""
        env_info = self.environments[choices["environment"]]
        topo_info = self.topologies[choices["topology"]]
        scenario_info = self.scenarios[choices["scenario"]]
        rollout_info = self.rollout_types.get(choices.get("rollout", "canary"), {})

        # Generate a name
        name_parts = []
        if choices["scenario"] != "normal":
            name_parts.append(choices["scenario"])
        name_parts.extend([choices["environment"], choices["topology"]])
        if choices.get("rollout") and choices["rollout"] != "canary":
            name_parts.append(choices["rollout"])

        recipe_name = "-".join(name_parts).title().replace("-", " ")

        # Build the recipe
        recipe = {
            "name": f"{recipe_name} Demo",
            "description": f"{scenario_info['description']} in {env_info['description'].lower()}",
            "emoji": scenario_info["emoji"],
            "environment": {
                "mode": "mock",
                "config": env_info["config"],
                "topology": choices["topology"],
            },
            "overrides": {},
            "models": topo_info["models"],
            "steps": [
                {"action": "list", "description": "Show current model deployments"},
                {"action": "monitor", "duration": 30, "description": "Watch real-time metrics"},
            ],
            "outcomes": [
                f"{len(topo_info['models'])} models running in {choices['topology']} topology",
                f"Configured for {scenario_info['description'].lower()}",
            ],
        }

        # Apply scenario-specific settings
        qps_min, qps_max = scenario_info["qps_range"]
        baseline_qps = custom.get("baseline_qps", (qps_min + qps_max) // 2)

        recipe["overrides"]["MTOP_WORKLOAD_BASELINE_QPS"] = baseline_qps
        recipe["overrides"]["MTOP_SLO_ERROR_RATE_PERCENT"] = custom.get(
            "error_rate", scenario_info["error_rate"]
        )

        # Apply cost settings
        if custom.get("gpu_cost"):
            recipe["overrides"]["MTOP_TECHNOLOGY_GPU_A100_COST"] = custom["gpu_cost"]
        else:
            base_cost = 3.0
            adjusted_cost = base_cost * env_info["cost_multiplier"]
            recipe["overrides"]["MTOP_TECHNOLOGY_GPU_A100_COST"] = adjusted_cost

        # Add rollout simulation if specified
        if choices.get("rollout") and choices["rollout"] != "normal":
            rollout_step = {
                "action": "simulate",
                "type": choices["rollout"],
                "description": f"Demonstrate {rollout_info['description'].lower()}",
            }
            recipe["steps"].insert(1, rollout_step)

        # Add scenario-specific steps
        if choices["scenario"] == "failure":
            recipe["steps"].append(
                {
                    "action": "simulate",
                    "type": "canary",
                    "description": "Inject failure and watch recovery",
                    "inject_failure": True,
                }
            )
        elif choices["scenario"] == "cost-optimization":
            recipe["steps"].append(
                {
                    "action": "cost_analysis",
                    "description": "Analyze cost optimization opportunities",
                }
            )

        return recipe

    def preview_recipe(self, recipe: Dict[str, Any]):
        """Show a preview of the generated recipe"""
        print("📋 Recipe Preview:")
        print("=" * 20)
        print(f"Name: {recipe['name']}")
        print(f"Description: {recipe['description']}")
        print()

        print("Environment Variables:")
        for key, value in recipe.get("overrides", {}).items():
            print(f"  {key}={value}")
        print()

        print("Demo Steps:")
        for i, step in enumerate(recipe.get("steps", []), 1):
            print(f"  {i}. {step['action']}: {step['description']}")
        print()

    def save_recipe(self, recipe: Dict[str, Any], filename: str):
        """Save the recipe to a file"""
        self.recipes_dir.mkdir(parents=True, exist_ok=True)

        if not filename.endswith(".yaml"):
            filename += ".yaml"

        recipe_path = self.recipes_dir / filename

        with open(recipe_path, "w") as f:
            yaml.safe_dump(recipe, f, default_flow_style=False, sort_keys=False)

        print(f"✅ Recipe saved to: {recipe_path}")
        print(f"🎯 Run it with: ./scripts/demo.py {filename[:-5]}")

    def run_interactive(self):
        """Run the interactive mixer"""
        self.print_header()

        # Collect choices
        choices = {}
        choices["environment"] = self.choose_from_options("Environment", self.environments)
        choices["topology"] = self.choose_from_options("Topology", self.topologies)
        choices["scenario"] = self.choose_from_options("Scenario", self.scenarios)

        # Ask about rollout type for certain scenarios
        if choices["scenario"] in ["failure", "spike"]:
            choices["rollout"] = self.choose_from_options("Rollout Type", self.rollout_types)

        # Get custom values
        custom = self.get_custom_values()

        # Build and preview recipe
        recipe = self.build_recipe(choices, custom)
        self.preview_recipe(recipe)

        return recipe


def main():
    parser = argparse.ArgumentParser(
        description="🎛️ Interactive mtop Configuration Mixer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./scripts/config-mixer.py                    # Interactive mode
  ./scripts/config-mixer.py --save my-demo    # Save generated recipe
  ./scripts/config-mixer.py --quick           # Quick preset selection

The mixer will guide you through:
  1. Environment (development, production, enterprise, research, edge)
  2. Topology (enterprise, edge, research, gradual)  
  3. Scenario (normal, spike, failure, cost-optimization)
  4. Custom settings (QPS, costs, error rates)

Your custom recipe will be saved and ready to run!
        """,
    )

    parser.add_argument(
        "--save", metavar="FILENAME", help="Save the generated recipe with this name"
    )
    parser.add_argument("--quick", action="store_true", help="Use quick preset selection mode")

    args = parser.parse_args()

    mixer = ConfigMixer()

    try:
        if args.quick:
            # Quick mode - just ask for basic choices
            print("🚀 Quick Demo Setup")
            print("1. Startup (development + edge)")
            print("2. Enterprise (production + enterprise)")
            print("3. Research (research + research)")

            choice = input("Choose (1-3): ").strip()
            if choice == "1":
                choices = {"environment": "development", "topology": "edge", "scenario": "normal"}
            elif choice == "2":
                choices = {
                    "environment": "production",
                    "topology": "enterprise",
                    "scenario": "normal",
                }
            elif choice == "3":
                choices = {"environment": "research", "topology": "research", "scenario": "normal"}
            else:
                print("Invalid choice")
                return

            recipe = mixer.build_recipe(choices, {})
        else:
            # Full interactive mode
            recipe = mixer.run_interactive()

        # Ask about saving
        if args.save:
            mixer.save_recipe(recipe, args.save)
        else:
            save_choice = input("\n💾 Save this recipe? (y/N): ").strip().lower()
            if save_choice in ["y", "yes"]:
                filename = input("Enter filename (without .yaml): ").strip()
                if filename:
                    mixer.save_recipe(recipe, filename)
                else:
                    print("❌ No filename provided, recipe not saved")
            else:
                print("Recipe not saved. You can copy the configuration above if needed.")

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
