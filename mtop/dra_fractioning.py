#!/usr/bin/env python3
"""
Dynamic Resource Allocation (DRA) fractioning simulation for GPU resources.

This module simulates Kubernetes DRA for GPU fractioning, including allocation/deallocation
timing, memory isolation, and visual representation of GPU fractions.
"""

import random
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional, Set, Tuple

from config_loader import TechnologyConfig


class FractionSize(Enum):
    """Standard GPU fraction sizes."""

    FULL = 1.0  # Full GPU
    HALF = 0.5  # 1/2 GPU
    QUARTER = 0.25  # 1/4 GPU
    EIGHTH = 0.125  # 1/8 GPU (minimum)


class AllocationStatus(Enum):
    """Status of GPU fraction allocation."""

    PENDING = "pending"  # Allocation requested
    PROVISIONING = "provisioning"  # Being allocated
    ALLOCATED = "allocated"  # Successfully allocated
    DEPROVISIONING = "deprovisioning"  # Being deallocated
    FAILED = "failed"  # Allocation failed
    RELEASED = "released"  # Successfully deallocated


@dataclass
class GPUFraction:
    """Represents a fraction of GPU resources."""

    fraction_id: str
    gpu_id: str
    size: float  # Fraction size (0.0 to 1.0)
    memory_mb: int
    compute_units: int
    status: AllocationStatus = AllocationStatus.PENDING
    workload_id: Optional[str] = None
    allocated_at: Optional[float] = None
    released_at: Optional[float] = None

    def __post_init__(self):
        """Validate GPU fraction configuration."""
        if not self.fraction_id:
            raise ValueError("fraction_id cannot be empty")

        if not self.gpu_id:
            raise ValueError("gpu_id cannot be empty")

        if not 0.0 < self.size <= 1.0:
            raise ValueError(f"size must be between 0 and 1, got {self.size}")

        if self.memory_mb <= 0:
            raise ValueError(f"memory_mb must be positive, got {self.memory_mb}")

        if self.compute_units <= 0:
            raise ValueError(f"compute_units must be positive, got {self.compute_units}")

    def get_memory_range(self, total_memory_mb: int) -> Tuple[int, int]:
        """Get memory range for this fraction.

        Args:
            total_memory_mb: Total GPU memory in MB

        Returns:
            Tuple of (start_mb, end_mb) for memory isolation
        """
        # Calculate proportional memory allocation
        fraction_memory = int(total_memory_mb * self.size)

        # For demonstration, assume fractions are allocated sequentially
        # In real DRA, this would be managed by the GPU driver
        fraction_index = hash(self.fraction_id) % 8  # 0-7 for up to 8 fractions
        start_mb = fraction_index * (total_memory_mb // 8)
        end_mb = start_mb + fraction_memory

        return (start_mb, min(end_mb, total_memory_mb))

    def is_active(self) -> bool:
        """Check if fraction is actively allocated."""
        return self.status == AllocationStatus.ALLOCATED

    def get_allocation_duration(self) -> Optional[float]:
        """Get duration since allocation in seconds."""
        if self.allocated_at is None:
            return None

        end_time = self.released_at or time.time()
        return end_time - self.allocated_at


@dataclass
class AllocationRequest:
    """Request for GPU fraction allocation."""

    request_id: str
    workload_id: str
    requested_size: float
    memory_requirements_mb: int
    compute_requirements: int
    priority: int = 1  # 1-10, higher = more priority
    max_wait_seconds: float = 300.0
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        """Validate allocation request."""
        if not self.request_id:
            raise ValueError("request_id cannot be empty")

        if not self.workload_id:
            raise ValueError("workload_id cannot be empty")

        if not 0.0 < self.requested_size <= 1.0:
            raise ValueError(f"requested_size must be between 0 and 1, got {self.requested_size}")

        if self.memory_requirements_mb <= 0:
            raise ValueError("memory_requirements_mb must be positive")

        if not 1 <= self.priority <= 10:
            raise ValueError(f"priority must be 1-10, got {self.priority}")

    def is_expired(self) -> bool:
        """Check if request has exceeded max wait time."""
        return time.time() - self.created_at > self.max_wait_seconds


class MemoryIsolation:
    """Manages GPU memory isolation between fractions."""

    def __init__(self, total_memory_mb: int):
        """Initialize memory isolation manager.

        Args:
            total_memory_mb: Total GPU memory in MB
        """
        self.total_memory_mb = total_memory_mb
        self._memory_map: Dict[str, Tuple[int, int]] = {}  # fraction_id -> (start, end)
        self._allocated_ranges: Set[Tuple[int, int]] = set()
        self._lock = Lock()

    def allocate_memory(self, fraction: GPUFraction) -> bool:
        """Allocate memory range for fraction.

        Args:
            fraction: GPU fraction to allocate memory for

        Returns:
            True if allocation successful, False if insufficient memory
        """
        with self._lock:
            required_memory = fraction.memory_mb

            # Find available contiguous memory range
            available_start = self._find_available_range(required_memory)
            if available_start is None:
                return False

            # Allocate the range
            memory_range = (available_start, available_start + required_memory)
            self._memory_map[fraction.fraction_id] = memory_range
            self._allocated_ranges.add(memory_range)

            return True

    def deallocate_memory(self, fraction_id: str) -> bool:
        """Deallocate memory for fraction.

        Args:
            fraction_id: ID of fraction to deallocate

        Returns:
            True if deallocation successful
        """
        with self._lock:
            if fraction_id not in self._memory_map:
                return False

            memory_range = self._memory_map[fraction_id]
            self._allocated_ranges.discard(memory_range)
            del self._memory_map[fraction_id]

            return True

    def _find_available_range(self, required_memory_mb: int) -> Optional[int]:
        """Find available contiguous memory range.

        Args:
            required_memory_mb: Required memory in MB

        Returns:
            Start position if available, None otherwise
        """
        # Check if request exceeds total memory capacity
        if required_memory_mb > self.total_memory_mb:
            return None

        # Sort allocated ranges by start position
        sorted_ranges = sorted(self._allocated_ranges)

        # Check if we can fit at the beginning
        if not sorted_ranges or sorted_ranges[0][0] >= required_memory_mb:
            return 0

        # Check gaps between allocated ranges
        for i in range(len(sorted_ranges) - 1):
            gap_start = sorted_ranges[i][1]
            gap_end = sorted_ranges[i + 1][0]
            gap_size = gap_end - gap_start

            if gap_size >= required_memory_mb:
                return gap_start

        # Check if we can fit at the end
        last_end = sorted_ranges[-1][1] if sorted_ranges else 0
        if self.total_memory_mb - last_end >= required_memory_mb:
            return last_end

        return None

    def get_memory_utilization(self) -> float:
        """Get current memory utilization percentage.

        Returns:
            Memory utilization percentage (0.0 to 100.0)
        """
        with self._lock:
            total_allocated = sum(end - start for start, end in self._allocated_ranges)
            return (total_allocated / self.total_memory_mb) * 100.0

    def get_memory_map(self) -> Dict[str, Tuple[int, int]]:
        """Get current memory allocation map.

        Returns:
            Dictionary mapping fraction IDs to memory ranges
        """
        with self._lock:
            return self._memory_map.copy()

    def get_fragmentation_stats(self) -> Dict[str, Any]:
        """Get memory fragmentation statistics.

        Returns:
            Dictionary with fragmentation metrics
        """
        with self._lock:
            if not self._allocated_ranges:
                return {
                    "total_fragments": 0,
                    "largest_gap_mb": self.total_memory_mb,
                    "fragmentation_ratio": 0.0,
                }

            sorted_ranges = sorted(self._allocated_ranges)
            gaps = []

            # Check gap at beginning
            if sorted_ranges[0][0] > 0:
                gaps.append(sorted_ranges[0][0])

            # Check gaps between ranges
            for i in range(len(sorted_ranges) - 1):
                gap_size = sorted_ranges[i + 1][0] - sorted_ranges[i][1]
                if gap_size > 0:
                    gaps.append(gap_size)

            # Check gap at end
            last_end = sorted_ranges[-1][1]
            if last_end < self.total_memory_mb:
                gaps.append(self.total_memory_mb - last_end)

            total_allocated = sum(end - start for start, end in self._allocated_ranges)
            total_free = self.total_memory_mb - total_allocated

            return {
                "total_fragments": len(gaps),
                "largest_gap_mb": max(gaps) if gaps else 0,
                "average_gap_mb": sum(gaps) / len(gaps) if gaps else 0,
                "fragmentation_ratio": len(gaps) / max(1, len(sorted_ranges)),
                "total_free_mb": total_free,
                "utilization_percent": (total_allocated / self.total_memory_mb) * 100.0,
            }


class AllocationManager:
    """Manages GPU fraction allocation and scheduling."""

    def __init__(
        self, provisioning_time_seconds: float = 5.0, deprovisioning_time_seconds: float = 2.0
    ):
        """Initialize allocation manager.

        Args:
            provisioning_time_seconds: Time to provision a fraction
            deprovisioning_time_seconds: Time to deprovision a fraction
        """
        self.provisioning_time = provisioning_time_seconds
        self.deprovisioning_time = deprovisioning_time_seconds
        self._pending_requests: List[AllocationRequest] = []
        self._active_allocations: Dict[str, GPUFraction] = {}
        self._allocation_history: List[GPUFraction] = []
        self._lock = Lock()

    def submit_request(self, request: AllocationRequest) -> str:
        """Submit allocation request.

        Args:
            request: Allocation request

        Returns:
            Request ID for tracking
        """
        with self._lock:
            self._pending_requests.append(request)
            # Sort by priority (high to low) and creation time (old to new)
            self._pending_requests.sort(key=lambda r: (-r.priority, r.created_at))
            return request.request_id

    def process_requests(self, available_gpus: Dict[str, Dict[str, Any]]) -> List[GPUFraction]:
        """Process pending allocation requests.

        Args:
            available_gpus: Dictionary of available GPUs with capacity info

        Returns:
            List of newly allocated fractions
        """
        with self._lock:
            allocated_fractions = []
            remaining_requests = []

            for request in self._pending_requests:
                # Remove expired requests
                if request.is_expired():
                    continue

                # Try to allocate
                fraction = self._try_allocate(request, available_gpus)
                if fraction:
                    allocated_fractions.append(fraction)
                    self._active_allocations[fraction.fraction_id] = fraction
                else:
                    remaining_requests.append(request)

            self._pending_requests = remaining_requests
            return allocated_fractions

    def _try_allocate(
        self, request: AllocationRequest, available_gpus: Dict[str, Dict[str, Any]]
    ) -> Optional[GPUFraction]:
        """Try to allocate GPU fraction for request.

        Args:
            request: Allocation request
            available_gpus: Available GPU capacity

        Returns:
            Allocated fraction or None if allocation failed
        """
        # Find GPU with sufficient capacity
        for gpu_id, gpu_info in available_gpus.items():
            available_fraction = gpu_info.get("available_fraction", 0.0)
            available_memory = gpu_info.get("available_memory_mb", 0)

            if (
                available_fraction >= request.requested_size
                and available_memory >= request.memory_requirements_mb
            ):
                # Create fraction
                fraction_id = str(uuid.uuid4())
                fraction = GPUFraction(
                    fraction_id=fraction_id,
                    gpu_id=gpu_id,
                    size=request.requested_size,
                    memory_mb=request.memory_requirements_mb,
                    compute_units=request.compute_requirements,
                    status=AllocationStatus.PROVISIONING,
                    workload_id=request.workload_id,
                    allocated_at=time.time(),
                )

                # Simulate provisioning delay
                # In real implementation, this would be async
                time.sleep(min(0.1, self.provisioning_time / 50))  # Shortened for demo

                fraction.status = AllocationStatus.ALLOCATED
                return fraction

        return None

    def release_allocation(self, fraction_id: str) -> bool:
        """Release GPU fraction allocation.

        Args:
            fraction_id: ID of fraction to release

        Returns:
            True if release successful
        """
        with self._lock:
            if fraction_id not in self._active_allocations:
                return False

            fraction = self._active_allocations[fraction_id]
            fraction.status = AllocationStatus.DEPROVISIONING

            # Simulate deprovisioning delay
            time.sleep(min(0.05, self.deprovisioning_time / 40))  # Shortened for demo

            fraction.status = AllocationStatus.RELEASED
            fraction.released_at = time.time()

            # Move to history
            self._allocation_history.append(fraction)
            del self._active_allocations[fraction_id]

            return True

    def get_active_allocations(self) -> Dict[str, GPUFraction]:
        """Get all active allocations.

        Returns:
            Dictionary of active allocations
        """
        with self._lock:
            return self._active_allocations.copy()

    def get_pending_requests(self) -> List[AllocationRequest]:
        """Get pending allocation requests.

        Returns:
            List of pending requests
        """
        with self._lock:
            return self._pending_requests.copy()

    def get_allocation_stats(self) -> Dict[str, Any]:
        """Get allocation statistics.

        Returns:
            Dictionary with allocation metrics
        """
        with self._lock:
            total_allocated = len(self._active_allocations)
            total_historical = len(self._allocation_history)
            pending_count = len(self._pending_requests)

            # Calculate average allocation duration for completed allocations
            completed_durations = [
                frac.get_allocation_duration()
                for frac in self._allocation_history
                if frac.get_allocation_duration() is not None
            ]

            avg_duration = (
                sum(completed_durations) / len(completed_durations) if completed_durations else 0.0
            )

            return {
                "active_allocations": total_allocated,
                "pending_requests": pending_count,
                "completed_allocations": total_historical,
                "average_allocation_duration": avg_duration,
                "provisioning_time_seconds": self.provisioning_time,
                "deprovisioning_time_seconds": self.deprovisioning_time,
            }


class DRASimulator:
    """Main DRA fractioning simulator coordinating all components."""

    def __init__(self, technology_config: Optional[TechnologyConfig] = None):
        """Initialize DRA simulator.

        Args:
            technology_config: Technology configuration for GPU types
        """
        self.technology_config = technology_config
        self.allocation_manager = AllocationManager()
        self._gpu_isolation: Dict[str, MemoryIsolation] = {}
        self._gpu_capacity: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def add_gpu(
        self,
        gpu_id: str,
        gpu_type: str,
        total_memory_mb: Optional[int] = None,
        compute_units: Optional[int] = None,
    ) -> None:
        """Add GPU to DRA system.

        Args:
            gpu_id: Unique GPU identifier
            gpu_type: GPU type (e.g., 'nvidia-h100')
            total_memory_mb: Total memory in MB (auto-detected if None)
            compute_units: Total compute units (auto-detected if None)
        """
        with self._lock:
            # Auto-detect specifications if not provided
            if total_memory_mb is None and self.technology_config:
                if gpu_type in self.technology_config.gpu_types:
                    total_memory_mb = int(
                        self.technology_config.gpu_types[gpu_type].memory_gb * 1024
                    )
                else:
                    total_memory_mb = 80 * 1024  # Default 80GB
            elif total_memory_mb is None:
                total_memory_mb = 80 * 1024  # Default 80GB

            if compute_units is None:
                # Estimate compute units based on GPU type
                compute_unit_map = {
                    "nvidia-h100": 16896,  # SMs * cores per SM
                    "nvidia-a100": 6912,
                    "nvidia-v100": 5120,
                }
                compute_units = compute_unit_map.get(gpu_type, 6912)

            # Initialize memory isolation
            self._gpu_isolation[gpu_id] = MemoryIsolation(total_memory_mb)

            # Initialize capacity tracking
            self._gpu_capacity[gpu_id] = {
                "gpu_type": gpu_type,
                "total_memory_mb": total_memory_mb,
                "total_compute_units": compute_units,
                "available_fraction": 1.0,
                "available_memory_mb": total_memory_mb,
                "available_compute_units": compute_units,
                "active_fractions": [],
            }

    def remove_gpu(self, gpu_id: str) -> None:
        """Remove GPU from DRA system.

        Args:
            gpu_id: GPU identifier to remove
        """
        with self._lock:
            if gpu_id in self._gpu_isolation:
                del self._gpu_isolation[gpu_id]
            if gpu_id in self._gpu_capacity:
                del self._gpu_capacity[gpu_id]

    def request_allocation(
        self,
        workload_id: str,
        fraction_size: float,
        memory_mb: int,
        compute_units: int,
        priority: int = 5,
    ) -> str:
        """Request GPU fraction allocation.

        Args:
            workload_id: Workload identifier
            fraction_size: Requested fraction size (0.0 to 1.0)
            memory_mb: Required memory in MB
            compute_units: Required compute units
            priority: Request priority (1-10)

        Returns:
            Request ID for tracking
        """
        request = AllocationRequest(
            request_id=str(uuid.uuid4()),
            workload_id=workload_id,
            requested_size=fraction_size,
            memory_requirements_mb=memory_mb,
            compute_requirements=compute_units,
            priority=priority,
        )

        return self.allocation_manager.submit_request(request)

    def process_allocations(self) -> List[GPUFraction]:
        """Process pending allocation requests.

        Returns:
            List of newly allocated fractions
        """
        with self._lock:
            available_gpus = self._get_available_capacity()
            allocated_fractions = self.allocation_manager.process_requests(available_gpus)

            # Update capacity and memory isolation
            for fraction in allocated_fractions:
                self._allocate_fraction_resources(fraction)

            return allocated_fractions

    def release_allocation(self, fraction_id: str) -> bool:
        """Release GPU fraction allocation.

        Args:
            fraction_id: ID of fraction to release

        Returns:
            True if release successful
        """
        # Get fraction details before release
        active_allocations = self.allocation_manager.get_active_allocations()
        if fraction_id not in active_allocations:
            return False

        fraction = active_allocations[fraction_id]

        # Release from allocation manager
        success = self.allocation_manager.release_allocation(fraction_id)

        if success:
            with self._lock:
                self._deallocate_fraction_resources(fraction)

        return success

    def _get_available_capacity(self) -> Dict[str, Dict[str, Any]]:
        """Get current available capacity for all GPUs.

        Returns:
            Dictionary with available capacity per GPU
        """
        available = {}
        for gpu_id, capacity in self._gpu_capacity.items():
            available[gpu_id] = {
                "available_fraction": capacity["available_fraction"],
                "available_memory_mb": capacity["available_memory_mb"],
                "available_compute_units": capacity["available_compute_units"],
            }
        return available

    def _allocate_fraction_resources(self, fraction: GPUFraction) -> None:
        """Allocate resources for fraction.

        Args:
            fraction: Fraction to allocate resources for
        """
        gpu_id = fraction.gpu_id

        if gpu_id not in self._gpu_capacity:
            return

        # Update capacity
        capacity = self._gpu_capacity[gpu_id]
        capacity["available_fraction"] -= fraction.size
        capacity["available_memory_mb"] -= fraction.memory_mb
        capacity["available_compute_units"] -= fraction.compute_units
        capacity["active_fractions"].append(fraction.fraction_id)

        # Allocate memory isolation
        if gpu_id in self._gpu_isolation:
            self._gpu_isolation[gpu_id].allocate_memory(fraction)

    def _deallocate_fraction_resources(self, fraction: GPUFraction) -> None:
        """Deallocate resources for fraction.

        Args:
            fraction: Fraction to deallocate resources for
        """
        gpu_id = fraction.gpu_id

        if gpu_id not in self._gpu_capacity:
            return

        # Update capacity
        capacity = self._gpu_capacity[gpu_id]
        capacity["available_fraction"] += fraction.size
        capacity["available_memory_mb"] += fraction.memory_mb
        capacity["available_compute_units"] += fraction.compute_units

        if fraction.fraction_id in capacity["active_fractions"]:
            capacity["active_fractions"].remove(fraction.fraction_id)

        # Deallocate memory isolation
        if gpu_id in self._gpu_isolation:
            self._gpu_isolation[gpu_id].deallocate_memory(fraction.fraction_id)

    def get_gpu_utilization(self, gpu_id: str) -> Dict[str, Any]:
        """Get utilization statistics for specific GPU.

        Args:
            gpu_id: GPU identifier

        Returns:
            Dictionary with utilization metrics
        """
        with self._lock:
            if gpu_id not in self._gpu_capacity:
                return {}

            capacity = self._gpu_capacity[gpu_id]
            isolation = self._gpu_isolation.get(gpu_id)

            total_fraction = 1.0
            used_fraction = total_fraction - capacity["available_fraction"]

            result = {
                "gpu_id": gpu_id,
                "gpu_type": capacity["gpu_type"],
                "fraction_utilization": used_fraction * 100.0,
                "memory_utilization": (
                    (capacity["total_memory_mb"] - capacity["available_memory_mb"])
                    / capacity["total_memory_mb"]
                )
                * 100.0,
                "compute_utilization": (
                    (capacity["total_compute_units"] - capacity["available_compute_units"])
                    / capacity["total_compute_units"]
                )
                * 100.0,
                "active_fractions": len(capacity["active_fractions"]),
                "available_fraction": capacity["available_fraction"],
                "available_memory_mb": capacity["available_memory_mb"],
            }

            if isolation:
                fragmentation = isolation.get_fragmentation_stats()
                result.update(
                    {
                        "memory_fragmentation": fragmentation,
                        "memory_map": isolation.get_memory_map(),
                    }
                )

            return result

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive DRA system status.

        Returns:
            Dictionary with complete system status
        """
        with self._lock:
            gpu_utilizations = {
                gpu_id: self.get_gpu_utilization(gpu_id) for gpu_id in self._gpu_capacity.keys()
            }

            allocation_stats = self.allocation_manager.get_allocation_stats()
            pending_requests = self.allocation_manager.get_pending_requests()
            active_allocations = self.allocation_manager.get_active_allocations()

            # Calculate aggregate statistics
            total_gpus = len(self._gpu_capacity)
            total_active_fractions = sum(
                len(cap["active_fractions"]) for cap in self._gpu_capacity.values()
            )

            avg_fraction_utilization = sum(
                util.get("fraction_utilization", 0) for util in gpu_utilizations.values()
            ) / max(1, total_gpus)

            return {
                "timestamp": time.time(),
                "total_gpus": total_gpus,
                "total_active_fractions": total_active_fractions,
                "pending_requests_count": len(pending_requests),
                "average_fraction_utilization": avg_fraction_utilization,
                "allocation_statistics": allocation_stats,
                "gpu_utilizations": gpu_utilizations,
                "active_allocations": {
                    frac_id: {
                        "fraction_id": frac.fraction_id,
                        "gpu_id": frac.gpu_id,
                        "size": frac.size,
                        "memory_mb": frac.memory_mb,
                        "workload_id": frac.workload_id,
                        "status": frac.status.value,
                        "allocated_at": frac.allocated_at,
                        "duration_seconds": frac.get_allocation_duration(),
                    }
                    for frac_id, frac in active_allocations.items()
                },
                "pending_requests": [
                    {
                        "request_id": req.request_id,
                        "workload_id": req.workload_id,
                        "requested_size": req.requested_size,
                        "memory_requirements_mb": req.memory_requirements_mb,
                        "priority": req.priority,
                        "wait_time_seconds": time.time() - req.created_at,
                    }
                    for req in pending_requests
                ],
            }

    def simulate_workload_pattern(self, duration_seconds: float = 60.0) -> None:
        """Simulate realistic workload allocation patterns.

        Args:
            duration_seconds: Duration of simulation
        """
        start_time = time.time()
        request_interval = 3.0  # Request every 3 seconds
        last_request_time = start_time

        workload_counter = 0
        active_workloads = set()

        max_iterations = int(duration_seconds / 0.1) + 100  # Safety valve
        iteration = 0

        while time.time() - start_time < duration_seconds and iteration < max_iterations:
            current_time = time.time()
            iteration += 1

            # Submit new requests periodically
            if current_time - last_request_time >= request_interval:
                workload_counter += 1
                workload_id = f"workload-{workload_counter:03d}"

                # Random workload characteristics
                fraction_sizes = [0.125, 0.25, 0.5, 1.0]
                size = random.choice(fraction_sizes)
                memory_mb = int(size * random.uniform(8000, 40000))  # 8-40GB
                compute_units = int(size * random.uniform(1000, 5000))
                priority = random.randint(1, 10)

                self.request_allocation(workload_id, size, memory_mb, compute_units, priority)
                active_workloads.add(workload_id)
                last_request_time = current_time

            # Process allocations
            self.process_allocations()

            # Randomly release some allocations
            active_allocations = self.allocation_manager.get_active_allocations()
            for fraction_id, fraction in list(active_allocations.items()):
                # 10% chance of release per iteration, higher for longer-running
                duration = fraction.get_allocation_duration() or 0
                release_probability = 0.1 + (duration / 300.0) * 0.2  # Increase with time

                if random.random() < release_probability:
                    self.release_allocation(fraction_id)
                    if fraction.workload_id in active_workloads:
                        active_workloads.remove(fraction.workload_id)

            time.sleep(0.5)  # Update every 500ms


def create_dra_simulator(technology_config: Optional[TechnologyConfig] = None) -> DRASimulator:
    """Factory function to create a configured DRA simulator.

    Args:
        technology_config: Technology configuration for GPU types

    Returns:
        Configured DRASimulator instance
    """
    return DRASimulator(technology_config)


def simulate_fractioning_demo(
    gpu_count: int = 2,
    duration_seconds: float = 30.0,
    technology_config: Optional[TechnologyConfig] = None,
) -> DRASimulator:
    """Create and run a DRA fractioning demonstration.

    Args:
        gpu_count: Number of GPUs to simulate
        duration_seconds: Simulation duration
        technology_config: Technology configuration

    Returns:
        DRASimulator with completed simulation
    """
    simulator = create_dra_simulator(technology_config)

    # Add GPUs with different types
    gpu_types = ["nvidia-h100", "nvidia-a100", "nvidia-v100"]
    for i in range(gpu_count):
        gpu_type = gpu_types[i % len(gpu_types)]
        simulator.add_gpu(f"gpu-{i:02d}", gpu_type)

    # Run simulation
    simulator.simulate_workload_pattern(duration_seconds)

    return simulator
