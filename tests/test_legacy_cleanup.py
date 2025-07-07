#!/usr/bin/env python3
"""
Test for detecting kubectl legacy references in the codebase.
This test ensures that old kubectl-ld references are cleaned up and
the codebase uses consistent mtop branding.
"""

import re
from pathlib import Path
from typing import List, Tuple


def test_no_kubectl_legacy_references():
    """
    Test that kubectl legacy references have been cleaned up from the codebase.

    This test scans Python, Markdown, YAML, and TOML files for case-insensitive
    kubectl references and fails if unauthorized references are found.
    """
    project_root = Path(__file__).parent.parent

    # File patterns to check
    patterns_to_check = ["**/*.py", "**/*.md", "**/*.yaml", "**/*.yml", "**/*.toml", "**/*.txt"]

    # Directories to exclude from scanning
    exclude_dirs = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        ".egg-info",
        "mtop.egg-info",
    }

    # Allowed kubectl references (legitimate usage)
    allowed_patterns = [
        # Comments about live kubectl integration
        r"#.*kubectl.*integration",
        r"#.*live.*kubectl",
        r"#.*actual.*kubectl",
        r"#.*use.*kubectl",
        # Documentation about live mode needing kubectl
        r"live mode requires kubectl",
        r"uses kubectl to",
        r"kubectl.*cluster",
        # Test descriptions that mention kubectl as external dependency
        r"mock.*kubectl",
        r"without.*kubectl",
        # Configuration comments about kubectl context/namespace
        r"kubectl.*context",
        r"kubectl.*namespace",
        r"kubectl.*timeout",
        r"# kubectl settings for live mode",
        # Live implementation that actually uses kubectl command
        r'return "kubectl"',
        r"using kubectl commands",
        # Documentation files that reference kubectl as external tool
        r"- \*\*kubectl\*\*.*Kubernetes CLI tool",
        r"- \*\*kubectl\*\* for Kubernetes testing",
        # Operational procedures in deployment and operations guides
        r"kubectl get pods",
        r"kubectl describe",
        r"kubectl logs",
        r"kubectl create secret",
        r"kubectl scale deployment",
        r"kubectl exec",
        r"kubectl run.*backup",
        r"kubectl run.*restore",
        r"kubectl create ns",
        r"kubectl apply -f",
    ]

    violations: List[Tuple[Path, int, str]] = []

    for pattern in patterns_to_check:
        for file_path in project_root.glob(pattern):
            # Skip files in excluded directories
            if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
                continue

            # Skip this test file itself
            if file_path.name == "test_legacy_cleanup.py":
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        # Case-insensitive search for kubectl
                        if re.search(r"\bkubectl\b", line, re.IGNORECASE):
                            # Check if this is an allowed reference
                            is_allowed = any(
                                re.search(pattern, line, re.IGNORECASE)
                                for pattern in allowed_patterns
                            )

                            if not is_allowed:
                                violations.append((file_path, line_num, line.strip()))

            except (UnicodeDecodeError, PermissionError):
                # Skip files that can't be read
                continue

    # Report violations
    if violations:
        error_msg = "Found kubectl legacy references that need cleanup:\n"
        for file_path, line_num, line in violations:
            relative_path = file_path.relative_to(project_root)
            error_msg += f"  {relative_path}:{line_num}: {line}\n"

        error_msg += "\nPlease replace kubectl references with mtop branding."
        error_msg += "\nIf this is a legitimate kubectl reference (e.g., for live mode),"
        error_msg += "\nupdate the allowed_patterns in test_legacy_cleanup.py"

        raise AssertionError(error_msg)


def test_consistent_mtop_branding():
    """
    Test that the codebase uses consistent mtop branding in key locations.
    """
    project_root = Path(__file__).parent.parent

    # Check that main executable is named mtop
    mtop_executable = project_root / "mtop"
    assert mtop_executable.exists(), "Main executable should be named 'mtop'"

    # Check that package directory is named mtop
    mtop_package = project_root / "mtop"
    assert mtop_package.is_dir(), "Package directory should be named 'mtop'"

    # Check pyproject.toml uses mtop name
    pyproject_file = project_root / "pyproject.toml"
    if pyproject_file.exists():
        content = pyproject_file.read_text()
        assert 'name = "mtop"' in content, "pyproject.toml should use mtop as package name"


def test_class_naming_consistency():
    """
    Test that class names follow mtop conventions rather than kubectl legacy.
    """
    project_root = Path(__file__).parent.parent

    violations = []

    # Scan Python files for problematic class names
    for py_file in project_root.glob("**/*.py"):
        if any(exclude in py_file.parts for exclude in [".git", "__pycache__", ".pytest_cache"]):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")

            # Check for kubectl-related class names
            problematic_patterns = [
                r"class\s+Kubectl\w+",
                r"class\s+.*KubectlLD.*",
            ]

            for line_num, line in enumerate(content.splitlines(), 1):
                for pattern in problematic_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append((py_file, line_num, line.strip()))

        except (UnicodeDecodeError, PermissionError):
            continue

    if violations:
        error_msg = "Found kubectl-related class names that should use mtop conventions:\n"
        for file_path, line_num, line in violations:
            relative_path = file_path.relative_to(project_root)
            error_msg += f"  {relative_path}:{line_num}: {line}\n"

        raise AssertionError(error_msg)


if __name__ == "__main__":
    # Allow running test directly for debugging
    test_no_kubectl_legacy_references()
    test_consistent_mtop_branding()
    test_class_naming_consistency()
    print("All legacy cleanup tests passed!")
