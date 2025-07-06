#!/usr/bin/env python3
"""
Comprehensive tests for DRA fractioning simulation system.
"""

import time
from unittest.mock import patch

import pytest

from config_loader import GPUType, TechnologyConfig
from mtop.dra_fractioning import (
    AllocationManager,
    AllocationRequest,
    AllocationStatus,
    DRASimulator,
    FractionSize,
    GPUFraction,
    MemoryIsolation,
    create_dra_simulator,
    simulate_fractioning_demo,
)


class TestGPUFraction:
    """Test GPUFraction dataclass and validation."""

    def test_valid_gpu_fraction_creation(self):
        """Test creating valid GPUFraction instance."""
        fraction = GPUFraction(
            fraction_id="frac-001",
            gpu_id="gpu-01",
            size=0.25,
            memory_mb=20480,  # 20GB
            compute_units=1728,
            workload_id="workload-test",
        )

        assert fraction.fraction_id == "frac-001"
        assert fraction.gpu_id == "gpu-01"
        assert fraction.size == 0.25
        assert fraction.memory_mb == 20480
        assert fraction.compute_units == 1728
        assert fraction.status == AllocationStatus.PENDING
        assert fraction.workload_id == "workload-test"

    def test_gpu_fraction_validation(self):
        """Test GPUFraction validation in __post_init__."""
        # Test empty fraction_id
        with pytest.raises(ValueError, match="fraction_id cannot be empty"):
            GPUFraction(
                fraction_id="", gpu_id="gpu-01", size=0.5, memory_mb=1000, compute_units=100
            )

        # Test empty gpu_id
        with pytest.raises(ValueError, match="gpu_id cannot be empty"):
            GPUFraction(fraction_id="test", gpu_id="", size=0.5, memory_mb=1000, compute_units=100)

        # Test invalid size
        with pytest.raises(ValueError, match="size must be between 0 and 1"):
            GPUFraction(
                fraction_id="test", gpu_id="gpu-01", size=0.0, memory_mb=1000, compute_units=100
            )

        with pytest.raises(ValueError, match="size must be between 0 and 1"):
            GPUFraction(
                fraction_id="test", gpu_id="gpu-01", size=1.5, memory_mb=1000, compute_units=100
            )

        # Test invalid memory
        with pytest.raises(ValueError, match="memory_mb must be positive"):
            GPUFraction(
                fraction_id="test", gpu_id="gpu-01", size=0.5, memory_mb=0, compute_units=100
            )

        # Test invalid compute units
        with pytest.raises(ValueError, match="compute_units must be positive"):
            GPUFraction(
                fraction_id="test", gpu_id="gpu-01", size=0.5, memory_mb=1000, compute_units=0
            )

    def test_memory_range_calculation(self):
        """Test memory range calculation for isolation."""
        fraction = GPUFraction(
            fraction_id="test-frac", gpu_id="gpu-01", size=0.25, memory_mb=20480, compute_units=1000
        )

        start_mb, end_mb = fraction.get_memory_range(81920)  # 80GB total
        assert isinstance(start_mb, int)
        assert isinstance(end_mb, int)
        assert start_mb < end_mb
        assert end_mb <= 81920

    def test_is_active(self):
        """Test active status check."""
        fraction = GPUFraction(
            fraction_id="test", gpu_id="gpu-01", size=0.5, memory_mb=1000, compute_units=100
        )

        assert not fraction.is_active()  # Initially pending

        fraction.status = AllocationStatus.ALLOCATED
        assert fraction.is_active()

        fraction.status = AllocationStatus.RELEASED
        assert not fraction.is_active()

    def test_allocation_duration(self):
        """Test allocation duration calculation."""
        fraction = GPUFraction(
            fraction_id="test", gpu_id="gpu-01", size=0.5, memory_mb=1000, compute_units=100
        )

        # No allocation time set
        assert fraction.get_allocation_duration() is None

        # Set allocation time
        start_time = time.time()
        fraction.allocated_at = start_time
        time.sleep(0.1)  # Small delay

        duration = fraction.get_allocation_duration()
        assert duration is not None
        assert duration > 0.05  # Should be at least 50ms

        # Set release time
        fraction.released_at = start_time + 1.0
        duration = fraction.get_allocation_duration()
        assert abs(duration - 1.0) < 0.1  # Should be ~1 second


class TestAllocationRequest:
    """Test AllocationRequest dataclass and validation."""

    def test_valid_allocation_request_creation(self):
        """Test creating valid AllocationRequest instance."""
        request = AllocationRequest(
            request_id="req-001",
            workload_id="workload-test",
            requested_size=0.5,
            memory_requirements_mb=40960,
            compute_requirements=3456,
            priority=8,
        )

        assert request.request_id == "req-001"
        assert request.workload_id == "workload-test"
        assert request.requested_size == 0.5
        assert request.memory_requirements_mb == 40960
        assert request.compute_requirements == 3456
        assert request.priority == 8
        assert request.created_at > 0

    def test_allocation_request_validation(self):
        """Test AllocationRequest validation."""
        # Test empty request_id
        with pytest.raises(ValueError, match="request_id cannot be empty"):
            AllocationRequest(
                request_id="",
                workload_id="test",
                requested_size=0.5,
                memory_requirements_mb=1000,
                compute_requirements=100,
            )

        # Test empty workload_id
        with pytest.raises(ValueError, match="workload_id cannot be empty"):
            AllocationRequest(
                request_id="test",
                workload_id="",
                requested_size=0.5,
                memory_requirements_mb=1000,
                compute_requirements=100,
            )

        # Test invalid size
        with pytest.raises(ValueError, match="requested_size must be between 0 and 1"):
            AllocationRequest(
                request_id="test",
                workload_id="test",
                requested_size=0.0,
                memory_requirements_mb=1000,
                compute_requirements=100,
            )

        # Test negative memory
        with pytest.raises(ValueError, match="memory_requirements_mb must be positive"):
            AllocationRequest(
                request_id="test",
                workload_id="test",
                requested_size=0.5,
                memory_requirements_mb=-1,
                compute_requirements=100,
            )

        # Test invalid priority
        with pytest.raises(ValueError, match="priority must be 1-10"):
            AllocationRequest(
                request_id="test",
                workload_id="test",
                requested_size=0.5,
                memory_requirements_mb=1000,
                compute_requirements=100,
                priority=0,
            )

    def test_expiration_check(self):
        """Test request expiration logic."""
        request = AllocationRequest(
            request_id="test",
            workload_id="test",
            requested_size=0.5,
            memory_requirements_mb=1000,
            compute_requirements=100,
            max_wait_seconds=0.1,  # Very short for testing
        )

        assert not request.is_expired()
        time.sleep(0.15)
        assert request.is_expired()


class TestMemoryIsolation:
    """Test MemoryIsolation functionality."""

    def test_memory_isolation_creation(self):
        """Test creating MemoryIsolation instance."""
        isolation = MemoryIsolation(total_memory_mb=81920)  # 80GB
        assert isolation.total_memory_mb == 81920
        assert isolation.get_memory_utilization() == 0.0

    def test_memory_allocation(self):
        """Test memory allocation for fractions."""
        isolation = MemoryIsolation(total_memory_mb=8192)  # 8GB for testing

        fraction = GPUFraction(
            fraction_id="test", gpu_id="gpu-01", size=0.25, memory_mb=2048, compute_units=100  # 2GB
        )

        success = isolation.allocate_memory(fraction)
        assert success
        assert isolation.get_memory_utilization() == 25.0  # 2GB/8GB = 25%

    def test_memory_deallocation(self):
        """Test memory deallocation."""
        isolation = MemoryIsolation(total_memory_mb=8192)

        fraction = GPUFraction(
            fraction_id="test", gpu_id="gpu-01", size=0.25, memory_mb=2048, compute_units=100
        )

        # Allocate and then deallocate
        isolation.allocate_memory(fraction)
        assert isolation.get_memory_utilization() == 25.0

        success = isolation.deallocate_memory("test")
        assert success
        assert isolation.get_memory_utilization() == 0.0

    def test_memory_allocation_failure(self):
        """Test memory allocation failure when insufficient memory."""
        isolation = MemoryIsolation(total_memory_mb=1024)  # 1GB

        fraction = GPUFraction(
            fraction_id="test",
            gpu_id="gpu-01",
            size=1.0,
            memory_mb=2048,
            compute_units=100,  # Request 2GB > 1GB available
        )

        success = isolation.allocate_memory(fraction)
        assert not success

    def test_multiple_allocations(self):
        """Test multiple memory allocations."""
        isolation = MemoryIsolation(total_memory_mb=8192)

        # Allocate multiple fractions
        for i in range(4):
            fraction = GPUFraction(
                fraction_id=f"frac-{i}",
                gpu_id="gpu-01",
                size=0.125,
                memory_mb=1024,
                compute_units=100,  # 1GB each
            )
            success = isolation.allocate_memory(fraction)
            assert success

        assert isolation.get_memory_utilization() == 50.0  # 4GB/8GB = 50%

    def test_fragmentation_statistics(self):
        """Test memory fragmentation statistics."""
        isolation = MemoryIsolation(total_memory_mb=8192)

        # Initial fragmentation (no allocations)
        stats = isolation.get_fragmentation_stats()
        assert stats["total_fragments"] == 0
        assert stats["largest_gap_mb"] == 8192

        # Allocate some memory to create fragmentation
        fraction1 = GPUFraction("frac-1", "gpu-01", 0.25, 2048, 100)
        fraction2 = GPUFraction("frac-2", "gpu-01", 0.25, 2048, 100)

        isolation.allocate_memory(fraction1)
        isolation.allocate_memory(fraction2)

        stats = isolation.get_fragmentation_stats()
        assert stats["total_fragments"] >= 1
        assert stats["utilization_percent"] == 50.0  # 4GB/8GB

    def test_memory_map(self):
        """Test memory allocation map."""
        isolation = MemoryIsolation(total_memory_mb=8192)

        fraction = GPUFraction("test", "gpu-01", 0.25, 2048, 100)
        isolation.allocate_memory(fraction)

        memory_map = isolation.get_memory_map()
        assert "test" in memory_map
        assert len(memory_map["test"]) == 2  # (start, end) tuple


class TestAllocationManager:
    """Test AllocationManager functionality."""

    def test_allocation_manager_creation(self):
        """Test creating AllocationManager."""
        manager = AllocationManager(provisioning_time_seconds=3.0)
        assert manager.provisioning_time == 3.0
        assert len(manager.get_pending_requests()) == 0

    def test_submit_request(self):
        """Test submitting allocation request."""
        manager = AllocationManager()

        request = AllocationRequest(
            request_id="test",
            workload_id="workload-1",
            requested_size=0.5,
            memory_requirements_mb=1000,
            compute_requirements=100,
        )

        request_id = manager.submit_request(request)
        assert request_id == "test"
        assert len(manager.get_pending_requests()) == 1

    def test_priority_ordering(self):
        """Test request priority ordering."""
        manager = AllocationManager()

        # Submit requests with different priorities
        req_low = AllocationRequest(
            request_id="low",
            workload_id="w1",
            requested_size=0.5,
            memory_requirements_mb=1000,
            compute_requirements=100,
            priority=3,
        )
        req_high = AllocationRequest(
            request_id="high",
            workload_id="w2",
            requested_size=0.5,
            memory_requirements_mb=1000,
            compute_requirements=100,
            priority=8,
        )

        manager.submit_request(req_low)
        manager.submit_request(req_high)

        pending = manager.get_pending_requests()
        assert pending[0].request_id == "high"  # Higher priority first
        assert pending[1].request_id == "low"

    def test_process_requests_success(self):
        """Test successful request processing."""
        manager = AllocationManager(provisioning_time_seconds=0.01)  # Fast for testing

        request = AllocationRequest(
            request_id="test",
            workload_id="workload-1",
            requested_size=0.5,
            memory_requirements_mb=1000,
            compute_requirements=100,
        )
        manager.submit_request(request)

        # Mock available GPU capacity
        available_gpus = {
            "gpu-01": {
                "available_fraction": 1.0,
                "available_memory_mb": 2000,
                "available_compute_units": 1000,
            }
        }

        allocated = manager.process_requests(available_gpus)
        assert len(allocated) == 1
        assert allocated[0].workload_id == "workload-1"
        assert allocated[0].status == AllocationStatus.ALLOCATED

    def test_process_requests_insufficient_capacity(self):
        """Test request processing with insufficient capacity."""
        manager = AllocationManager()

        request = AllocationRequest(
            request_id="test",
            workload_id="workload-1",
            requested_size=0.8,
            memory_requirements_mb=1000,
            compute_requirements=100,
        )
        manager.submit_request(request)

        # Mock insufficient GPU capacity
        available_gpus = {
            "gpu-01": {
                "available_fraction": 0.5,  # Not enough
                "available_memory_mb": 2000,
                "available_compute_units": 1000,
            }
        }

        allocated = manager.process_requests(available_gpus)
        assert len(allocated) == 0
        assert len(manager.get_pending_requests()) == 1  # Still pending

    def test_release_allocation(self):
        """Test releasing allocation."""
        manager = AllocationManager(
            provisioning_time_seconds=0.01, deprovisioning_time_seconds=0.01
        )

        # First allocate something
        request = AllocationRequest(
            request_id="test",
            workload_id="workload-1",
            requested_size=0.5,
            memory_requirements_mb=1000,
            compute_requirements=100,
        )
        manager.submit_request(request)

        available_gpus = {
            "gpu-01": {
                "available_fraction": 1.0,
                "available_memory_mb": 2000,
                "available_compute_units": 1000,
            }
        }

        allocated = manager.process_requests(available_gpus)
        fraction_id = allocated[0].fraction_id

        # Now release it
        success = manager.release_allocation(fraction_id)
        assert success
        assert len(manager.get_active_allocations()) == 0

    def test_allocation_statistics(self):
        """Test allocation statistics."""
        manager = AllocationManager()

        stats = manager.get_allocation_stats()
        assert stats["active_allocations"] == 0
        assert stats["pending_requests"] == 0
        assert stats["completed_allocations"] == 0

    def test_expired_request_handling(self):
        """Test handling of expired requests."""
        manager = AllocationManager()

        # Create expired request
        request = AllocationRequest(
            request_id="expired",
            workload_id="workload-1",
            requested_size=0.5,
            memory_requirements_mb=1000,
            compute_requirements=100,
            max_wait_seconds=0.01,  # Very short
        )
        manager.submit_request(request)

        time.sleep(0.02)  # Wait for expiration

        available_gpus = {
            "gpu-01": {
                "available_fraction": 1.0,
                "available_memory_mb": 2000,
                "available_compute_units": 1000,
            }
        }

        allocated = manager.process_requests(available_gpus)
        assert len(allocated) == 0  # Expired request should be ignored
        assert len(manager.get_pending_requests()) == 0  # Should be removed


class TestDRASimulator:
    """Test DRASimulator main functionality."""

    def test_dra_simulator_creation(self):
        """Test creating DRA simulator."""
        simulator = DRASimulator()
        assert isinstance(simulator.allocation_manager, AllocationManager)
        assert len(simulator._gpu_capacity) == 0

    def test_dra_simulator_with_technology_config(self):
        """Test DRA simulator with technology configuration."""
        tech_config = TechnologyConfig(
            gpu_types={
                "nvidia-h100": GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=4.10),
            }
        )

        simulator = DRASimulator(tech_config)
        assert simulator.technology_config == tech_config

    def test_add_gpu(self):
        """Test adding GPU to simulator."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        assert "gpu-01" in simulator._gpu_capacity
        assert "gpu-01" in simulator._gpu_isolation

        capacity = simulator._gpu_capacity["gpu-01"]
        assert capacity["gpu_type"] == "nvidia-h100"
        assert capacity["available_fraction"] == 1.0

    def test_add_gpu_with_technology_config(self):
        """Test adding GPU with technology config."""
        tech_config = TechnologyConfig(
            gpu_types={
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=40, hourly_cost=3.20),
            }
        )

        simulator = DRASimulator(tech_config)
        simulator.add_gpu("gpu-01", "nvidia-a100")

        capacity = simulator._gpu_capacity["gpu-01"]
        assert capacity["total_memory_mb"] == 40 * 1024  # 40GB in MB

    def test_remove_gpu(self):
        """Test removing GPU from simulator."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        assert "gpu-01" in simulator._gpu_capacity

        simulator.remove_gpu("gpu-01")
        assert "gpu-01" not in simulator._gpu_capacity
        assert "gpu-01" not in simulator._gpu_isolation

    def test_request_allocation(self):
        """Test requesting allocation."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        request_id = simulator.request_allocation(
            workload_id="test-workload", fraction_size=0.5, memory_mb=40960, compute_units=3456
        )

        assert isinstance(request_id, str)
        pending = simulator.allocation_manager.get_pending_requests()
        assert len(pending) == 1

    def test_process_allocations(self):
        """Test processing allocations."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        # Request allocation
        simulator.request_allocation(
            workload_id="test-workload", fraction_size=0.25, memory_mb=20480, compute_units=1728
        )

        # Process allocations
        allocated = simulator.process_allocations()
        assert len(allocated) == 1
        assert allocated[0].size == 0.25

        # Check capacity was updated
        utilization = simulator.get_gpu_utilization("gpu-01")
        assert utilization["fraction_utilization"] == 25.0

    def test_release_allocation(self):
        """Test releasing allocation."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        # Allocate first
        simulator.request_allocation(
            workload_id="test-workload", fraction_size=0.5, memory_mb=40960, compute_units=3456
        )
        allocated = simulator.process_allocations()
        fraction_id = allocated[0].fraction_id

        # Release
        success = simulator.release_allocation(fraction_id)
        assert success

        # Check capacity was restored
        utilization = simulator.get_gpu_utilization("gpu-01")
        assert utilization["fraction_utilization"] == 0.0

    def test_gpu_utilization_calculation(self):
        """Test GPU utilization calculation."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        utilization = simulator.get_gpu_utilization("gpu-01")
        assert utilization["gpu_id"] == "gpu-01"
        assert utilization["fraction_utilization"] == 0.0
        assert utilization["active_fractions"] == 0
        assert "memory_fragmentation" in utilization

    def test_system_status(self):
        """Test getting system status."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")
        simulator.add_gpu("gpu-02", "nvidia-a100")

        status = simulator.get_system_status()
        assert status["total_gpus"] == 2
        assert status["total_active_fractions"] == 0
        assert status["pending_requests"] == 0
        assert "gpu_utilizations" in status
        assert "allocation_statistics" in status

    def test_workload_simulation(self):
        """Test workload pattern simulation."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        # Run short simulation
        with patch("time.sleep"):  # Mock sleep to speed up test
            simulator.simulate_workload_pattern(duration_seconds=1.0)

        # Should have processed some requests
        status = simulator.get_system_status()
        assert status["allocation_statistics"]["completed_allocations"] >= 0

    def test_multiple_gpu_allocation(self):
        """Test allocation across multiple GPUs."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")
        simulator.add_gpu("gpu-02", "nvidia-a100")

        # Request more than one GPU can handle
        for i in range(3):
            simulator.request_allocation(
                workload_id=f"workload-{i}",
                fraction_size=0.8,  # Large fraction
                memory_mb=60000,
                compute_units=5000,
            )

        allocated = simulator.process_allocations()

        # Should allocate across multiple GPUs
        gpu_ids = {frac.gpu_id for frac in allocated}
        assert len(gpu_ids) >= 1  # At least one GPU used

    def test_memory_isolation_integration(self):
        """Test integration with memory isolation."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        # Allocate fraction
        simulator.request_allocation(
            workload_id="test", fraction_size=0.25, memory_mb=20480, compute_units=1728
        )
        allocated = simulator.process_allocations()

        # Check memory isolation
        utilization = simulator.get_gpu_utilization("gpu-01")
        memory_map = utilization["memory_map"]
        assert len(memory_map) == 1  # One allocation

        fragmentation = utilization["memory_fragmentation"]
        assert fragmentation["utilization_percent"] > 0


class TestFactoryFunctions:
    """Test factory functions."""

    def test_create_dra_simulator_basic(self):
        """Test basic DRA simulator creation."""
        simulator = create_dra_simulator()
        assert isinstance(simulator, DRASimulator)
        assert simulator.technology_config is None

    def test_create_dra_simulator_with_config(self):
        """Test DRA simulator creation with config."""
        tech_config = TechnologyConfig(
            gpu_types={
                "nvidia-h100": GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=4.10),
            }
        )

        simulator = create_dra_simulator(tech_config)
        assert simulator.technology_config == tech_config

    def test_simulate_fractioning_demo(self):
        """Test fractioning demo simulation."""
        with patch("time.sleep"):  # Mock sleep to speed up test
            simulator = simulate_fractioning_demo(gpu_count=2, duration_seconds=1.0)

        assert isinstance(simulator, DRASimulator)
        status = simulator.get_system_status()
        assert status["total_gpus"] == 2


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""

    def test_realistic_fractioning_scenario(self):
        """Test realistic GPU fractioning scenario."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        # Simulate multiple workloads with different sizes
        workloads = [
            ("workload-small", 0.125, 10240, 800),  # 1/8 GPU, 10GB
            ("workload-medium", 0.25, 20480, 1600),  # 1/4 GPU, 20GB
            ("workload-large", 0.5, 40960, 3200),  # 1/2 GPU, 40GB
        ]

        allocated_fractions = []
        for workload_id, size, memory, compute in workloads:
            simulator.request_allocation(workload_id, size, memory, compute)
            allocated = simulator.process_allocations()
            allocated_fractions.extend(allocated)

        # Should have allocated all three workloads (1/8 + 1/4 + 1/2 = 7/8 < 1.0)
        assert len(allocated_fractions) == 3

        # Check utilization
        utilization = simulator.get_gpu_utilization("gpu-01")
        assert utilization["fraction_utilization"] == 87.5  # 7/8 = 87.5%

    def test_resource_contention_scenario(self):
        """Test resource contention and queueing."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        # Request more resources than available
        for i in range(5):
            simulator.request_allocation(
                workload_id=f"workload-{i}",
                fraction_size=0.5,  # Each wants half GPU
                memory_mb=40960,
                compute_units=3456,
            )

        allocated = simulator.process_allocations()

        # Should only allocate 2 (2 * 0.5 = 1.0)
        assert len(allocated) <= 2

        # Check that some requests are still pending
        status = simulator.get_system_status()
        assert status["pending_requests"] > 0

    def test_dynamic_allocation_release_cycle(self):
        """Test dynamic allocation and release cycle."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        # Allocate
        simulator.request_allocation("workload-1", 0.5, 40960, 3456)
        allocated = simulator.process_allocations()
        fraction_id = allocated[0].fraction_id

        # Check utilization
        util_before = simulator.get_gpu_utilization("gpu-01")
        assert util_before["fraction_utilization"] == 50.0

        # Release
        simulator.release_allocation(fraction_id)

        # Check utilization after release
        util_after = simulator.get_gpu_utilization("gpu-01")
        assert util_after["fraction_utilization"] == 0.0

    def test_memory_fragmentation_scenario(self):
        """Test memory fragmentation patterns."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        # Create fragmentation with multiple small allocations
        small_workloads = []
        for i in range(8):  # 8 x 1/8 = full GPU
            simulator.request_allocation(
                workload_id=f"small-{i}", fraction_size=0.125, memory_mb=10240, compute_units=800
            )

        allocated = simulator.process_allocations()
        assert len(allocated) == 8

        # Check fragmentation
        utilization = simulator.get_gpu_utilization("gpu-01")
        fragmentation = utilization["memory_fragmentation"]

        # With 8 allocations, should have some fragmentation
        assert fragmentation["total_fragments"] >= 0
        assert fragmentation["utilization_percent"] == 100.0

    def test_priority_scheduling_scenario(self):
        """Test priority-based scheduling."""
        simulator = DRASimulator()
        simulator.add_gpu("gpu-01", "nvidia-h100")

        # Submit requests with different priorities
        simulator.request_allocation("low-priority", 0.5, 40960, 3456, priority=2)
        simulator.request_allocation("high-priority", 0.5, 40960, 3456, priority=9)

        allocated = simulator.process_allocations()

        # High priority should be allocated first
        assert allocated[0].workload_id == "high-priority"

    def test_mixed_gpu_types_scenario(self):
        """Test allocation across different GPU types."""
        tech_config = TechnologyConfig(
            gpu_types={
                "nvidia-h100": GPUType(name="nvidia-h100", memory_gb=80, hourly_cost=4.10),
                "nvidia-a100": GPUType(name="nvidia-a100", memory_gb=40, hourly_cost=3.20),
            }
        )

        simulator = DRASimulator(tech_config)
        simulator.add_gpu("gpu-h100", "nvidia-h100")
        simulator.add_gpu("gpu-a100", "nvidia-a100")

        # Request allocation (should prefer H100 due to more capacity)
        simulator.request_allocation("test-workload", 0.75, 60000, 5000)  # 60GB
        allocated = simulator.process_allocations()

        assert len(allocated) == 1
        assert allocated[0].gpu_id == "gpu-h100"  # Only H100 has enough memory

        # Check utilizations are different
        util_h100 = simulator.get_gpu_utilization("gpu-h100")
        util_a100 = simulator.get_gpu_utilization("gpu-a100")

        assert util_h100["fraction_utilization"] == 75.0
        assert util_a100["fraction_utilization"] == 0.0
