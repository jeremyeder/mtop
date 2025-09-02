#!/usr/bin/env python3
"""
Build script for generating configurable program from templates
Usage: python build.py [config.yaml]
"""

import shutil
import stat
import sys
from pathlib import Path
from string import Template
from typing import Dict

# Import configuration system
try:
    from config_loader import Config, load_config

    CONFIG_AVAILABLE = True
except ImportError:
    print("❌ Configuration system not available. Please ensure config_loader.py is present.")
    sys.exit(1)


class ProgramBuilder:
    """Builds program from templates and configuration"""

    def __init__(self, config: Config, output_dir: str = "dist"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.templates_dir = Path("templates")
        self.variables = self._build_template_variables()

    def _build_template_variables(self) -> Dict[str, str]:
        """Build template variables from configuration"""
        program_name = self.config.build.program.name
        monitor_name = self.config.build.program.monitor_name
        class_prefix = self.config.build.program.class_prefix

        return {
            # Program identity
            "PROGRAM_NAME": program_name,
            "PROGRAM_DESCRIPTION": self.config.build.program.description,
            "MONITOR_NAME": monitor_name,
            "CLASS_PREFIX": class_prefix,
            # Variable names (for code generation)
            "PROGRAM_VARIABLE": self._to_variable_name(program_name),
            "MONITOR_VARIABLE": self._to_variable_name(monitor_name),
            # Branding
            "EMOJI": self.config.build.branding.emoji,
            "TAGLINE": self.config.build.branding.tagline,
            "GITHUB_REPO": self.config.build.branding.github_repo,
        }

    def _to_variable_name(self, name: str) -> str:
        """Convert program name to valid Python variable name"""
        # Replace hyphens with underscores and ensure valid identifier
        var_name = name.replace("-", "_").replace(" ", "_").lower()
        # Ensure it starts with a letter
        if var_name and not var_name[0].isalpha():
            var_name = "prog_" + var_name
        return var_name or "program"

    def build(self):
        """Build the complete program"""
        print(f"🔨 Building {self.config.build.program.name}...")

        # Create output directory
        self.output_dir.mkdir(exist_ok=True)

        # Copy configuration system files
        self._copy_support_files()

        # Process templates
        self._process_main_template()
        self._process_readme_template()

        # Create symlinks and set permissions
        self._create_program_files()

        # Copy runtime config
        self._copy_runtime_config()

        print(f"✅ Build complete! Program available in {self.output_dir}/")
        self._show_usage_info()

    def _copy_support_files(self):
        """Copy configuration system and support files"""
        support_files = [
            "config_loader.py",
            "column_engine.py",
        ]

        for file_name in support_files:
            if Path(file_name).exists():
                shutil.copy(file_name, self.output_dir / file_name)
                print(f"📄 Copied {file_name}")

    def _process_main_template(self):
        """Process main program template"""
        template_path = self.templates_dir / "main-program.py.template"
        output_path = self.output_dir / self.config.build.program.name

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        # Read template
        with open(template_path, "r") as f:
            template_content = f.read()

        # Process template
        template = Template(template_content)
        processed_content = template.safe_substitute(self.variables)

        # Write output
        with open(output_path, "w") as f:
            f.write(processed_content)

        # Make executable
        output_path.chmod(output_path.stat().st_mode | stat.S_IEXEC)

        print(f"🚀 Generated {output_path}")

    def _process_readme_template(self):
        """Process README template if it exists"""
        template_path = self.templates_dir / "README.md.template"
        output_path = self.output_dir / "README.md"

        if template_path.exists():
            with open(template_path, "r") as f:
                template_content = f.read()

            template = Template(template_content)
            processed_content = template.safe_substitute(self.variables)

            with open(output_path, "w") as f:
                f.write(processed_content)

            print(f"📚 Generated {output_path}")

    def _create_program_files(self):
        """Create symlinks and set up program structure"""
        program_name = self.config.build.program.name
        monitor_name = self.config.build.program.monitor_name

        # Create main symlink if monitor name is different
        if monitor_name != program_name:
            symlink_name = f"{program_name}-{monitor_name}"
            symlink_path = self.output_dir / symlink_name

            # Remove existing symlink if present
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()

            # Create symlink
            symlink_path.symlink_to(program_name)
            print(f"🔗 Created symlink {symlink_name} -> {program_name}")

    def _copy_runtime_config(self):
        """Copy runtime configuration files"""
        # Copy the build config for runtime use
        config_source = Path("config.yaml")
        config_dest = self.output_dir / "config.yaml"

        if config_source.exists():
            shutil.copy(config_source, config_dest)
            print(f"⚙️ Copied runtime config to {config_dest}")

        # Copy mocks directory if it exists
        mocks_source = Path("mocks")
        mocks_dest = self.output_dir / "mocks"

        if mocks_source.exists():
            if mocks_dest.exists():
                shutil.rmtree(mocks_dest)
            shutil.copytree(mocks_source, mocks_dest)
            print(f"📁 Copied mocks directory to {mocks_dest}")

    def _show_usage_info(self):
        """Show usage information for the built program"""
        program_name = self.config.build.program.name
        monitor_name = self.config.build.program.monitor_name

        print()
        print("🎯 Usage:")
        print(f"  cd {self.output_dir}")
        print(f"  ./{program_name} --help")
        print(f"  ./{program_name} list")
        print(f"  ./{program_name} {monitor_name}")

        if monitor_name != program_name:
            symlink_name = f"{program_name}-{monitor_name}"
            print(f"  ./{symlink_name}  # Direct monitoring")


def create_readme_template():
    """Create README template from current README"""
    readme_source = Path("README.md")
    readme_template = Path("templates/README.md.template")

    if not readme_source.exists():
        print("⚠️ README.md not found, skipping template creation")
        return

    # Ensure templates directory exists
    Path("templates").mkdir(exist_ok=True)

    # Read current README
    with open(readme_source, "r") as f:
        content = f.read()

    # Replace common patterns with template variables
    replacements = {
        "mtop": "${PROGRAM_NAME}",
        "mtop": "${PROGRAM_NAME}",
        "ldtop": "${MONITOR_NAME}",
        "🚀": "${EMOJI}",
        "Mock CLI tool for debugging LLMInferenceService CRDs": "${PROGRAM_DESCRIPTION}",
        "jeremyeder/mtop": "${GITHUB_REPO}",
    }

    template_content = content
    for old, new in replacements.items():
        template_content = template_content.replace(old, new)

    # Write template
    with open(readme_template, "w") as f:
        f.write(template_content)

    print(f"📝 Created README template at {readme_template}")


def main():
    """Main build function"""
    # Parse command line arguments
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"

    # Create README template if it doesn't exist
    readme_template = Path("templates/README.md.template")
    if not readme_template.exists():
        create_readme_template()

    try:
        # Load configuration
        config = load_config(config_file)

        # Create builder and build
        builder = ProgramBuilder(config)
        builder.build()

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print(f"💡 Make sure {config_file} exists")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
