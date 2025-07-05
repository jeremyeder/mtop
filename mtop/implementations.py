"""Concrete implementations of interfaces."""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .container import singleton, transient
from .interfaces import FileSystem, KubernetesClient, Logger


def get_kubectl_command() -> str:
    """Get kubectl command name, could be configurable in future."""
    return "kubectl"


@singleton(FileSystem)
class LocalFileSystem:
    """Local file system implementation."""

    def read_file(self, path: Path) -> str:
        """Read file contents."""
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            raise IOError(f"Error reading file {path}: {e}")

    def write_file(self, path: Path, content: str) -> None:
        """Write file contents."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise IOError(f"Error writing file {path}: {e}")

    def exists(self, path: Path) -> bool:
        """Check if path exists."""
        return path.exists()

    def list_files(self, path: Path, pattern: str = "*") -> List[Path]:
        """List files matching pattern."""
        if not path.exists() or not path.is_dir():
            return []
        return list(path.glob(pattern))


@transient(KubernetesClient)
class KubectlClient:
    """Kubectl-based Kubernetes client."""

    def __init__(self, logger: Optional[Logger] = None) -> None:
        if logger is None:
            # Simple logger for standalone use
            import logging

            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

    async def get_resource(
        self, resource_type: str, name: Optional[str] = None, namespace: str = "default"
    ) -> Dict[str, Any]:
        """Get Kubernetes resource."""
        cmd = [get_kubectl_command(), "get", resource_type]
        if name:
            cmd.append(name)
        cmd.extend(["-n", namespace, "-o", "json"])

        self.logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode().strip()
                self.logger.error(f"{get_kubectl_command()} command failed: {error_msg}")
                raise RuntimeError(f"{get_kubectl_command()} error: {error_msg}")

            return json.loads(stdout.decode())
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse {get_kubectl_command()} JSON output: {e}")
            raise
        except Exception as e:
            self.logger.error(f"{get_kubectl_command()} command failed: {e}")
            raise

    async def create_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Kubernetes resource."""
        # Create temporary file with resource data
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(resource_data, f)
            temp_file = f.name

        try:
            cmd = [get_kubectl_command(), "apply", "-f", temp_file]
            self.logger.debug(f"Running command: {' '.join(cmd)}")

            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode().strip()
                self.logger.error(f"{get_kubectl_command()} create failed: {error_msg}")
                raise RuntimeError(f"{get_kubectl_command()} error: {error_msg}")

            # Return the created resource
            resource_name = resource_data["metadata"]["name"]
            resource_type = resource_data["kind"].lower()
            namespace = resource_data["metadata"].get("namespace", "default")

            return await self.get_resource(resource_type, resource_name, namespace)
        finally:
            Path(temp_file).unlink(missing_ok=True)

    async def delete_resource(
        self, resource_type: str, name: str, namespace: str = "default"
    ) -> bool:
        """Delete Kubernetes resource."""
        cmd = [get_kubectl_command(), "delete", resource_type, name, "-n", namespace]
        self.logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"{get_kubectl_command()} delete failed: {e}")
            return False

    async def get_logs(self, deployment_name: str, namespace: str = "default") -> str:
        """Get deployment logs."""
        cmd = [get_kubectl_command(), "logs", f"deployment/{deployment_name}", "-n", namespace]
        self.logger.debug(f"Running command: {' '.join(cmd)}")

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode().strip()
                self.logger.warning(f"{get_kubectl_command()} logs failed: {error_msg}")
                return f"Error getting logs: {error_msg}"

            return stdout.decode()
        except Exception as e:
            self.logger.error(f"{get_kubectl_command()} logs failed: {e}")
            return f"Error getting logs: {e}"


@transient(KubernetesClient)
class MockKubernetesClient:
    """Mock Kubernetes client for testing."""

    def __init__(
        self, file_system: Optional[FileSystem] = None, logger: Optional[Logger] = None
    ) -> None:
        if file_system is None:
            self.file_system = LocalFileSystem()
        else:
            self.file_system = file_system

        if logger is None:
            import logging

            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        self.mock_root = Path("mocks")

    async def get_resource(
        self, resource_type: str, name: Optional[str] = None, namespace: str = "default"
    ) -> Dict[str, Any]:
        """Get mock Kubernetes resource."""
        if name:
            # Single resource
            cr_path = self.mock_root / "crs" / f"{name}.json"
            if not self.file_system.exists(cr_path):
                raise RuntimeError(f"Resource {name} not found")

            content = self.file_system.read_file(cr_path)
            return json.loads(content)
        else:
            # List resources
            crs_dir = self.mock_root / "crs"
            items = []
            for cr_file in self.file_system.list_files(crs_dir, "*.json"):
                content = self.file_system.read_file(cr_file)
                items.append(json.loads(content))

            return {"items": items}

    async def create_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create mock Kubernetes resource."""
        name = resource_data["metadata"]["name"]
        cr_path = self.mock_root / "crs" / f"{name}.json"

        content = json.dumps(resource_data, indent=2)
        self.file_system.write_file(cr_path, content)

        return resource_data

    async def delete_resource(
        self, resource_type: str, name: str, namespace: str = "default"
    ) -> bool:
        """Delete mock Kubernetes resource."""
        cr_path = self.mock_root / "crs" / f"{name}.json"
        if self.file_system.exists(cr_path):
            cr_path.unlink()
            return True
        return False

    async def get_logs(self, deployment_name: str, namespace: str = "default") -> str:
        """Get mock deployment logs."""
        log_path = self.mock_root / "pod_logs" / f"{deployment_name}.txt"
        if self.file_system.exists(log_path):
            return self.file_system.read_file(log_path)
        return f"No logs found for {deployment_name}"
