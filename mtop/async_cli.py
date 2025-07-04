"""Async CLI operations for mtop."""

import asyncio
from typing import Any, Dict, List, Optional

from .container import inject
from .interfaces import FileSystem, KubernetesClient, Logger


class AsyncKubectlLD:
    """Async version of KubectlLD operations."""

    def __init__(
        self,
        mode: str = "mock",
        k8s_client: Optional[KubernetesClient] = None,
        logger: Optional[Logger] = None,
        file_system: Optional[FileSystem] = None,
    ) -> None:
        self.mode = mode
        self.is_live = mode == "live"
        self.k8s_client = k8s_client or inject(KubernetesClient)
        self.logger = logger or inject(Logger)
        self.file_system = file_system or inject(FileSystem)

    async def list_crs(self) -> List[Dict[str, Any]]:
        """List all LLMInferenceService resources asynchronously."""
        try:
            data = await self.k8s_client.get_resource("llminferenceservice")
            if "items" in data:
                return data["items"]
            else:
                return [data]
        except Exception as e:
            self.logger.error(f"Failed to list CRs: {e}")
            return []

    async def get_cr(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific CR by name asynchronously."""
        try:
            return await self.k8s_client.get_resource("llminferenceservice", name)
        except Exception as e:
            self.logger.error(f"Failed to get CR {name}: {e}")
            return None

    async def create_cr(self, resource_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a CR asynchronously."""
        try:
            return await self.k8s_client.create_resource(resource_data)
        except Exception as e:
            self.logger.error(f"Failed to create CR: {e}")
            return None

    async def delete_cr(self, name: str) -> bool:
        """Delete a CR asynchronously."""
        try:
            return await self.k8s_client.delete_resource("llminferenceservice", name)
        except Exception as e:
            self.logger.error(f"Failed to delete CR {name}: {e}")
            return False

    async def get_logs(self, name: str) -> str:
        """Get logs for a service asynchronously."""
        try:
            return await self.k8s_client.get_logs(name)
        except Exception as e:
            self.logger.error(f"Failed to get logs for {name}: {e}")
            return f"Error getting logs: {e}"

    async def get_multiple_crs(self, names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple CRs concurrently."""
        tasks = [self.get_cr(name) for name in names]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        response = {}
        for name, result in zip(names, results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to get CR {name}: {result}")
                response[name] = None
            else:
                response[name] = result

        return response

    async def batch_operations(self, operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple operations concurrently."""
        tasks = []

        for op in operations:
            op_type = op.get("type")
            if op_type == "get":
                tasks.append(self._wrap_operation(self.get_cr(op["name"]), op_type, op["name"]))
            elif op_type == "create":
                tasks.append(
                    self._wrap_operation(
                        self.create_cr(op["data"]), op_type, op["data"]["metadata"]["name"]
                    )
                )
            elif op_type == "delete":
                tasks.append(self._wrap_operation(self.delete_cr(op["name"]), op_type, op["name"]))
            elif op_type == "logs":
                tasks.append(self._wrap_operation(self.get_logs(op["name"]), op_type, op["name"]))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                formatted_results.append(
                    {
                        "operation": operations[i],
                        "success": False,
                        "error": str(result),
                        "result": None,
                    }
                )
            else:
                formatted_results.append(result)

        return formatted_results

    async def _wrap_operation(self, coro: Any, op_type: str, name: str) -> Dict[str, Any]:
        """Wrap an operation with metadata."""
        try:
            result = await coro
            return {
                "operation": {"type": op_type, "name": name},
                "success": True,
                "error": None,
                "result": result,
            }
        except Exception as e:
            return {
                "operation": {"type": op_type, "name": name},
                "success": False,
                "error": str(e),
                "result": None,
            }


class AsyncResourceMonitor:
    """Async resource monitoring with concurrent updates."""

    def __init__(
        self, kubectl_ld: AsyncKubectlLD, interval: float = 1.0, logger: Optional[Logger] = None
    ) -> None:
        self.kubectl_ld = kubectl_ld
        self.interval = interval
        self.logger = logger or inject(Logger)
        self._running = False
        self._stop_event = asyncio.Event()
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def start(self) -> None:
        """Start monitoring."""
        self._running = True
        self._stop_event.clear()

        self.logger.info("Starting async resource monitor")

        try:
            while self._running:
                # Update cache concurrently
                await self._update_cache()

                # Wait for next interval or stop signal
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval)
                    break  # Stop event was set
                except asyncio.TimeoutError:
                    continue  # Continue monitoring
        except Exception as e:
            self.logger.error(f"Monitor error: {e}")
        finally:
            self._running = False
            self.logger.info("Async resource monitor stopped")

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        self._stop_event.set()

    async def _update_cache(self) -> None:
        """Update resource cache concurrently."""
        try:
            # Get all CRs concurrently
            crs = await self.kubectl_ld.list_crs()
            names = [cr["metadata"]["name"] for cr in crs]

            # Update cache with latest data
            updated_crs = await self.kubectl_ld.get_multiple_crs(names)

            for name, cr_data in updated_crs.items():
                if cr_data:
                    self._cache[name] = cr_data
                elif name in self._cache:
                    # Remove deleted resources
                    del self._cache[name]

            self.logger.debug(f"Updated cache with {len(self._cache)} resources")

        except Exception as e:
            self.logger.error(f"Failed to update cache: {e}")

    def get_cached_resources(self) -> Dict[str, Dict[str, Any]]:
        """Get currently cached resources."""
        return self._cache.copy()

    @property
    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running


async def run_concurrent_operations(operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run multiple mtop operations concurrently."""
    kubectl_ld = AsyncKubectlLD()
    return await kubectl_ld.batch_operations(operations)
