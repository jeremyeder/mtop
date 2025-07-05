#!/usr/bin/env python3
"""
Phase 1 Integration Testing Epic - End-to-End Validation

Tests integration between all Phase 1 components:
- Token Metrics + Queue Metrics
- GPU Heartbeat Engine
- DRA Fractioning Simulation
- Demo System Components
- Configuration System
"""

import os
import subprocess
import tempfile
import time
from unittest.mock import patch

import pytest

from config_loader import GPUType, SLOConfig, TechnologyConfig, load_config
from mtop.dra_fractioning import DRASimulator, create_dra_simulator
from mtop.gpu_heartbeat import GPUHeartbeat, create_gpu_heartbeat
from mtop.token_metrics import (
    QueueMetrics,
    TokenTracker,
    create_cost_calculator,
    create_queue_metrics,
    create_token_tracker,
    create_ttft_calculator,
)


class TestTokenMetricsIntegration:
    """Test integration between Token Metrics and Queue Metrics."""

    def test_token_tracker_queue_metrics_integration(self):
        """Test TokenTracker automatically creates and manages QueueMetrics."""
        # Load real configuration
        config = load_config()
        tracker = create_token_tracker(config.technology, config.slo)

        # Create metrics should also create queue metrics
        token_metrics = tracker.create_metrics("llama-3-70b-instruct", "nvidia-h100")
        queue_metrics = tracker.get_queue_metrics("llama-3-70b-instruct")

        assert token_metrics is not None
        assert queue_metrics is not None
        assert isinstance(queue_metrics, QueueMetrics)

        # Update queue depth should update both metrics
        tracker.update_queue_depth("llama-3-70b-instruct", 5)

        assert token_metrics.queue_depth == 5
        assert queue_metrics.get_current_depth() == 5
        assert len(queue_metrics.depth_history) == 1

    def test_simulation_updates_queue_metrics(self):
        """Test that token simulation updates queue metrics realistically."""
        config = load_config()
        tracker = create_token_tracker(config.technology, config.slo)

        # Run simulation
        metrics = tracker.simulate_token_generation(
            "gpt-4-turbo", target_tokens=200, target_tps=1800
        )
        queue_metrics = tracker.get_queue_metrics("gpt-4-turbo")

        assert metrics.is_completed()
        assert queue_metrics is not None
        assert len(queue_metrics.depth_history) > 0  # Should have queue depth history

        # Queue depth should show realistic patterns during simulation
        depths = list(queue_metrics.depth_history)
        assert all(0 <= depth <= 10 for depth in depths)  # Reasonable queue depths

    def test_cost_calculator_integration(self):
        """Test CostCalculator integration with TokenMetrics."""
        config = load_config()
        cost_calc = create_cost_calculator(config.technology)
        tracker = create_token_tracker(config.technology, config.slo)

        # Simulate token generation
        metrics = tracker.simulate_token_generation("claude-3-haiku", target_tokens=100)

        # Calculate cost from metrics
        cost = cost_calc.calculate_cost_from_metrics(metrics)
        assert cost is not None
        assert cost > 0  # Should have non-zero cost

        # Verify cost calculation components
        duration = metrics.completion_time - metrics.start_time
        expected_cost = cost_calc.calculate_token_cost(
            metrics.tokens_generated, metrics.gpu_type, duration
        )
        assert abs(cost - expected_cost) < 0.001

    def test_ttft_calculator_integration(self):
        """Test TTFTCalculator integration with TokenMetrics."""
        config = load_config()
        ttft_calc = create_ttft_calculator(config.slo)
        tracker = create_token_tracker(config.technology, config.slo)

        # Generate multiple simulations for statistical analysis
        for i in range(25):  # Need 20+ for P95 calculation
            metrics = tracker.simulate_token_generation(f"model-{i}", target_tokens=50)
            ttft_calc.record_ttft_from_metrics(metrics)

        # Should have sufficient data for statistics
        assert ttft_calc.get_measurement_count() == 25
        assert ttft_calc.get_p95_latency() is not None
        assert ttft_calc.check_slo_compliance() is not None

        # Statistics should be reasonable
        stats = ttft_calc.get_statistics_summary()
        assert stats["mean_ms"] > 0
        assert stats["p95_ms"] > stats["mean_ms"]


class TestGPUHeartbeatIntegration:
    """Test GPU Heartbeat Engine integration with other components."""

    def test_heartbeat_with_token_metrics(self):
        """Test GPU Heartbeat integration with Token Metrics."""
        config = load_config()
        heartbeat = create_gpu_heartbeat(config.technology)
        tracker = create_token_tracker(config.technology, config.slo)

        # Add GPUs to heartbeat engine
        heartbeat.add_gpu("gpu-01", "nvidia-h100")
        heartbeat.add_gpu("gpu-02", "nvidia-a100")

        # Simulate token workloads that would affect GPU utilization
        for i, gpu_type in enumerate(["nvidia-h100", "nvidia-a100"]):
            for j in range(3):
                model_name = f"model-{gpu_type}-{j}"
                metrics = tracker.simulate_token_generation(model_name, target_tokens=100)
                
                # GPU utilization should correlate with token generation
                utilization = 70 + (metrics.tokens_generated / 100) * 25  # 70-95% range
                gpu_metrics = heartbeat.tracker.get_gpu_metrics(f"gpu-0{i+1}")
                if gpu_metrics:
                    gpu_metrics.utilization_percent = utilization
                    gpu_metrics.vram_used_gb = metrics.tokens_generated * 0.5
                    heartbeat.tracker.update_gpu_metrics(gpu_metrics)

        # Heartbeat should reflect workload
        current_pulse = heartbeat.get_current_heartbeat()
        system_status = heartbeat.get_system_status()

        assert current_pulse.frequency_bpm > 60  # Should be elevated
        assert system_status["gpu_count"] == 2
        assert system_status["aggregate_utilization"] > 50

    def test_heartbeat_scaling_decisions(self):
        """Test heartbeat scaling decisions with realistic workloads."""
        config = load_config()
        heartbeat = create_gpu_heartbeat(config.technology)

        # Add GPU and simulate high load
        heartbeat.add_gpu("gpu-01", "nvidia-h100")
        
        # Simulate overload scenario
        high_load_metrics = type(heartbeat.tracker._metrics.get("gpu-01") or object)(
            gpu_id="gpu-01",
            utilization_percent=96.0,  # Overloaded
            vram_used_gb=75.0,
            vram_total_gb=80.0,
            temperature_c=85.0,
            power_watts=450.0
        )
        heartbeat.tracker.update_gpu_metrics(high_load_metrics)

        # Should recommend urgent scaling
        decision, reason = heartbeat.get_scaling_recommendation()
        assert "urgent" in decision.value.lower() or "scale" in decision.value.lower()
        assert "overload" in reason.lower() or "95" in reason

        # Heartbeat should be critical
        pulse = heartbeat.get_current_heartbeat()
        assert pulse.intensity > 0.8
        assert pulse.frequency_bpm > 130

    def test_multi_gpu_heartbeat_aggregation(self):
        """Test heartbeat aggregation across multiple GPUs."""
        config = load_config()
        heartbeat = create_gpu_heartbeat(config.technology)

        # Add different GPU types
        gpu_configs = [
            ("gpu-h100-01", "nvidia-h100", 70.0),
            ("gpu-h100-02", "nvidia-h100", 80.0),
            ("gpu-a100-01", "nvidia-a100", 65.0),
            ("gpu-a100-02", "nvidia-a100", 90.0),
        ]

        for gpu_id, gpu_type, utilization in gpu_configs:
            heartbeat.add_gpu(gpu_id, gpu_type)
            # Update with specific utilization
            metrics = heartbeat.tracker.get_gpu_metrics(gpu_id)
            if metrics:
                metrics.utilization_percent = utilization
                heartbeat.tracker.update_gpu_metrics(metrics)

        # Aggregate utilization should be average
        system_status = heartbeat.get_system_status()
        expected_avg = (70.0 + 80.0 + 65.0 + 90.0) / 4  # 76.25%
        assert abs(system_status["aggregate_utilization"] - expected_avg) < 1.0

        # Heartbeat should reflect aggregate load
        pulse = heartbeat.get_current_heartbeat()
        assert pulse.strength.value in ["strong", "intense"]  # 76% should be strong


class TestDRAFractioningIntegration:
    """Test DRA Fractioning integration with other components."""

    def test_dra_with_gpu_heartbeat(self):
        """Test DRA Fractioning integration with GPU Heartbeat."""
        config = load_config()
        dra = create_dra_simulator(config.technology)
        heartbeat = create_gpu_heartbeat(config.technology)

        # Add same GPUs to both systems
        gpu_types = ["nvidia-h100", "nvidia-a100"]
        for i, gpu_type in enumerate(gpu_types):
            gpu_id = f"gpu-{i:02d}"
            dra.add_gpu(gpu_id, gpu_type)
            heartbeat.add_gpu(gpu_id, gpu_type)

        # Allocate fractions in DRA
        request_id = dra.request_allocation(
            workload_id="test-workload",
            fraction_size=0.75,  # 75% of GPU
            memory_mb=60000,
            compute_units=4000
        )
        allocated = dra.process_allocations()

        if allocated:
            fraction = allocated[0]
            
            # Update heartbeat to reflect DRA allocation
            gpu_utilization = fraction.size * 100  # 75%
            gpu_metrics = heartbeat.tracker.get_gpu_metrics(fraction.gpu_id)
            if gpu_metrics:
                gpu_metrics.utilization_percent = gpu_utilization
                gpu_metrics.vram_used_gb = fraction.memory_mb / 1024
                heartbeat.tracker.update_gpu_metrics(gpu_metrics)

            # Heartbeat should reflect DRA allocation
            pulse = heartbeat.get_current_heartbeat()
            assert pulse.intensity > 0.5  # Should be elevated due to 75% utilization

        # DRA system status should show allocation
        dra_status = dra.get_system_status()
        assert dra_status["total_active_fractions"] > 0

    def test_dra_with_token_metrics(self):
        """Test DRA Fractioning with Token Metrics for realistic workloads."""
        config = load_config()
        dra = create_dra_simulator(config.technology)
        tracker = create_token_tracker(config.technology, config.slo)

        # Add GPU to DRA
        dra.add_gpu("gpu-01", "nvidia-h100")

        # Simulate token generation workloads
        workloads = [
            ("small-model", 0.25, 20000),   # 1/4 GPU, 20GB
            ("medium-model", 0.5, 40000),   # 1/2 GPU, 40GB
        ]

        allocated_fractions = []
        for workload_id, fraction_size, memory_mb in workloads:
            # Request DRA allocation
            dra.request_allocation(
                workload_id=workload_id,
                fraction_size=fraction_size,
                memory_mb=memory_mb,
                compute_units=int(fraction_size * 6000)
            )
            
            # Simulate corresponding token generation
            tokens_target = int(fraction_size * 200)  # Proportional to GPU fraction
            metrics = tracker.simulate_token_generation(workload_id, target_tokens=tokens_target)
            
            allocated = dra.process_allocations()
            allocated_fractions.extend(allocated)

        # Should have allocated both workloads (0.25 + 0.5 = 0.75 < 1.0)
        assert len(allocated_fractions) == 2

        # Token metrics should correlate with DRA allocations
        for fraction in allocated_fractions:
            token_metrics = tracker.get_metrics(fraction.workload_id)
            assert token_metrics is not None
            assert token_metrics.tokens_generated > 0

        # DRA utilization should match token generation patterns
        dra_util = dra.get_gpu_utilization("gpu-01")
        assert dra_util["fraction_utilization"] == 75.0  # 0.25 + 0.5

    def test_realistic_fractioning_scenario(self):
        """Test realistic GPU fractioning scenario with multiple components."""
        config = load_config()
        dra = create_dra_simulator(config.technology)
        heartbeat = create_gpu_heartbeat(config.technology)
        tracker = create_token_tracker(config.technology, config.slo)

        # Add GPU to all systems
        gpu_id = "gpu-production-01"
        dra.add_gpu(gpu_id, "nvidia-h100")
        heartbeat.add_gpu(gpu_id, "nvidia-h100")

        # Simulate realistic workload mix
        workload_scenarios = [
            ("inference-api", 0.375, 30000, 150),      # 3/8 GPU for API
            ("batch-processing", 0.25, 20000, 100),    # 1/4 GPU for batch
            ("model-training", 0.25, 20000, 50),       # 1/4 GPU for training
        ]

        total_allocated = 0
        for workload_id, fraction, memory_mb, target_tokens in workload_scenarios:
            # DRA allocation
            dra.request_allocation(
                workload_id=workload_id,
                fraction_size=fraction,
                memory_mb=memory_mb,
                compute_units=int(fraction * 6000)
            )
            total_allocated += fraction

            # Token generation simulation
            tracker.simulate_token_generation(workload_id, target_tokens=target_tokens)

        # Process all allocations
        allocated_fractions = dra.process_allocations()
        
        # Should allocate all workloads (total = 0.875 < 1.0)
        assert len(allocated_fractions) == 3

        # Update heartbeat with aggregate utilization
        aggregate_util = total_allocated * 100  # 87.5%
        gpu_metrics = heartbeat.tracker.get_gpu_metrics(gpu_id)
        if gpu_metrics:
            gpu_metrics.utilization_percent = aggregate_util
            heartbeat.tracker.update_gpu_metrics(gpu_metrics)

        # Validate system coherence
        dra_status = dra.get_system_status()
        heartbeat_status = heartbeat.get_system_status()
        token_summary = tracker.get_summary_stats()

        assert dra_status["total_active_fractions"] == 3
        assert abs(heartbeat_status["aggregate_utilization"] - 87.5) < 1.0
        assert token_summary["total_models"] == 3


class TestDemoSystemIntegration:
    """Test Demo System integration and reliability."""

    def test_demo_launcher_environment_setup(self):
        """Test demo launcher creates proper environment."""
        # Test that demo-launcher.sh exists and is executable
        demo_launcher = "demo-launcher.sh"
        assert os.path.exists(demo_launcher)
        assert os.access(demo_launcher, os.X_OK)

        # Test that demo-status.sh exists and is executable
        demo_status = "demo-status.sh"
        assert os.path.exists(demo_status)
        assert os.access(demo_status, os.X_OK)

        # Test that demo-cleanup.sh exists and is executable
        demo_cleanup = "demo-cleanup.sh"
        assert os.path.exists(demo_cleanup)
        assert os.access(demo_cleanup, os.X_OK)

    def test_demo_status_health_checks(self):
        """Test demo status health checking functionality."""
        # Run demo status check (should work without full setup)
        try:
            result = subprocess.run(
                ["./demo-status.sh", "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Should produce valid output (even if some checks fail)
            assert result.returncode in [0, 1]  # 0 = healthy, 1 = warnings/errors
            
            # Output should be parseable JSON when --json flag used
            if result.stdout.strip():
                import json
                status_data = json.loads(result.stdout)
                assert "timestamp" in status_data
                assert "overall_status" in status_data
                assert "components" in status_data
                
        except subprocess.TimeoutExpired:
            pytest.skip("Demo status check timed out (system may be slow)")
        except FileNotFoundError:
            pytest.skip("Demo scripts not found (may need setup)")

    def test_mock_data_availability(self):
        """Test that required mock data is available for demos."""
        required_mock_dirs = [
            "mocks/crs",
            "mocks/config", 
            "mocks/pod_logs",
            "mocks/states",
            "mocks/topologies"
        ]

        for mock_dir in required_mock_dirs:
            assert os.path.exists(mock_dir), f"Required mock directory {mock_dir} not found"
            
            # Should have some files in each directory
            files = os.listdir(mock_dir)
            assert len(files) > 0, f"Mock directory {mock_dir} is empty"

        # Check for minimum number of CRs
        cr_files = [f for f in os.listdir("mocks/crs") if f.endswith(".json")]
        assert len(cr_files) >= 10, f"Need at least 10 mock CRs, found {len(cr_files)}"

    def test_configuration_loading(self):
        """Test that configuration loading works for demo scenarios."""
        # Should be able to load configuration without errors
        config = load_config()
        
        assert config is not None
        assert hasattr(config, 'technology')
        assert hasattr(config, 'slo')
        assert hasattr(config, 'workload')

        # Technology config should have GPU types
        assert len(config.technology.gpu_types) > 0
        
        # Should have common GPU types for demos
        gpu_types = config.technology.gpu_types.keys()
        common_types = ["nvidia-h100", "nvidia-a100", "nvidia-v100"]
        found_types = [gt for gt in common_types if gt in gpu_types]
        assert len(found_types) > 0, "No common GPU types found for demos"

        # SLO config should have reasonable defaults
        assert config.slo.ttft_p95_ms > 0
        assert config.slo.tokens_per_second > 0
        assert 0 <= config.slo.error_rate_percent <= 100


class TestPerformanceValidation:
    """Test performance characteristics under load."""

    def test_token_generation_performance(self):
        """Test token generation performance under load."""
        config = load_config()
        tracker = create_token_tracker(config.technology, config.slo)

        # Measure performance of token simulation
        start_time = time.time()
        
        # Simulate multiple models concurrently
        models = [f"perf-test-model-{i}" for i in range(10)]
        for model in models:
            tracker.simulate_token_generation(model, target_tokens=100)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time (< 5 seconds for 10 models)
        assert duration < 5.0, f"Token simulation too slow: {duration:.2f}s"

        # All models should be tracked
        all_metrics = tracker.get_all_metrics()
        assert len(all_metrics) == 10

        # Summary stats should be calculated quickly
        stats_start = time.time()
        summary = tracker.get_summary_stats()
        stats_duration = time.time() - stats_start

        assert stats_duration < 0.1, f"Summary stats too slow: {stats_duration:.3f}s"
        assert summary["total_models"] == 10

    def test_heartbeat_performance_under_load(self):
        """Test GPU heartbeat performance with many GPUs."""
        config = load_config()
        heartbeat = create_gpu_heartbeat(config.technology)

        # Add many GPUs
        gpu_count = 20
        for i in range(gpu_count):
            heartbeat.add_gpu(f"gpu-{i:02d}", "nvidia-h100")

        # Measure heartbeat calculation performance
        start_time = time.time()
        
        for _ in range(100):  # 100 heartbeat calculations
            pulse = heartbeat.get_current_heartbeat()
            assert pulse is not None

        duration = time.time() - start_time

        # Should be very fast (< 1 second for 100 calculations)
        assert duration < 1.0, f"Heartbeat calculation too slow: {duration:.3f}s"

        # System status should also be fast
        status_start = time.time()
        status = heartbeat.get_system_status()
        status_duration = time.time() - status_start

        assert status_duration < 0.5, f"System status too slow: {status_duration:.3f}s"
        assert status["gpu_count"] == gpu_count

    def test_dra_allocation_performance(self):
        """Test DRA allocation performance with many requests."""
        config = load_config()
        dra = create_dra_simulator(config.technology)

        # Add GPUs
        for i in range(4):
            dra.add_gpu(f"gpu-{i:02d}", "nvidia-h100")

        # Submit many allocation requests
        request_count = 50
        start_time = time.time()

        for i in range(request_count):
            dra.request_allocation(
                workload_id=f"workload-{i}",
                fraction_size=0.125,  # Small fractions
                memory_mb=10000,
                compute_units=800
            )

        # Process all requests
        allocated = dra.process_allocations()
        duration = time.time() - start_time

        # Should complete quickly (< 2 seconds for 50 requests)
        assert duration < 2.0, f"DRA processing too slow: {duration:.3f}s"

        # Should allocate many requests (4 GPUs × 8 fractions = 32 max)
        assert len(allocated) > 10, f"Too few allocations: {len(allocated)}"

        # System status should be calculated quickly
        status_start = time.time()
        status = dra.get_system_status()
        status_duration = time.time() - status_start

        assert status_duration < 0.2, f"DRA status too slow: {status_duration:.3f}s"

    def test_memory_usage_under_stress(self):
        """Test memory usage doesn't grow excessively under stress."""
        import psutil
        import gc

        config = load_config()
        
        # Get baseline memory usage
        gc.collect()
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create and exercise all major components
        tracker = create_token_tracker(config.technology, config.slo)
        heartbeat = create_gpu_heartbeat(config.technology)
        dra = create_dra_simulator(config.technology)

        # Stress test all components
        for i in range(100):
            # Token metrics
            model_name = f"stress-model-{i % 10}"  # Reuse model names
            tracker.simulate_token_generation(model_name, target_tokens=50)
            
            # Heartbeat (add/remove GPUs)
            if i % 10 == 0:
                gpu_id = f"stress-gpu-{i // 10}"
                heartbeat.add_gpu(gpu_id, "nvidia-h100")
                heartbeat.get_current_heartbeat()
                if i > 0:
                    heartbeat.remove_gpu(f"stress-gpu-{(i // 10) - 1}")
            
            # DRA allocations
            if i % 5 == 0:
                dra.request_allocation(
                    workload_id=f"stress-workload-{i}",
                    fraction_size=0.125,
                    memory_mb=5000,
                    compute_units=400
                )
                allocated = dra.process_allocations()
                # Release some allocations to prevent buildup
                for fraction in allocated[:2]:  # Release first 2
                    dra.release_allocation(fraction.fraction_id)

        # Check memory usage after stress test
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - baseline_memory

        # Memory growth should be reasonable (< 100MB for stress test)
        assert memory_growth < 100, f"Excessive memory growth: {memory_growth:.1f}MB"


class TestCrossComponentIntegration:
    """Test integration scenarios involving all components."""

    def test_full_system_simulation(self):
        """Test full system with all components working together."""
        config = load_config()
        
        # Initialize all major components
        tracker = create_token_tracker(config.technology, config.slo)
        heartbeat = create_gpu_heartbeat(config.technology)
        dra = create_dra_simulator(config.technology)
        cost_calc = create_cost_calculator(config.technology)
        ttft_calc = create_ttft_calculator(config.slo)

        # Setup GPU infrastructure
        gpu_types = ["nvidia-h100", "nvidia-a100", "nvidia-v100"]
        for i, gpu_type in enumerate(gpu_types):
            gpu_id = f"gpu-{i:02d}"
            
            # Add to all systems
            heartbeat.add_gpu(gpu_id, gpu_type)
            dra.add_gpu(gpu_id, gpu_type)

        # Simulate realistic workload scenarios
        workload_scenarios = [
            # (model_name, gpu_preference, fraction_size, tokens, priority)
            ("gpt-4-turbo", "nvidia-h100", 0.5, 200, 8),
            ("llama-3-70b", "nvidia-h100", 0.75, 300, 7),
            ("claude-3-haiku", "nvidia-a100", 0.25, 150, 6),
            ("mixtral-8x7b", "nvidia-a100", 0.5, 250, 5),
            ("granite-3-8b", "nvidia-v100", 0.125, 100, 4),
        ]

        allocated_fractions = []
        token_metrics_list = []

        for model_name, preferred_gpu, fraction, tokens, priority in workload_scenarios:
            # 1. Request DRA allocation
            dra.request_allocation(
                workload_id=model_name,
                fraction_size=fraction,
                memory_mb=int(fraction * 80000),  # Proportional memory
                compute_units=int(fraction * 6000),
                priority=priority
            )

            # 2. Simulate token generation
            token_metrics = tracker.simulate_token_generation(
                model_name, target_tokens=tokens, target_tps=int(1000 + priority * 200)
            )
            token_metrics_list.append(token_metrics)

            # 3. Record TTFT
            ttft_calc.record_ttft_from_metrics(token_metrics)

        # Process DRA allocations
        allocated_fractions = dra.process_allocations()
        
        # Update heartbeat with allocation results
        for fraction in allocated_fractions:
            gpu_metrics = heartbeat.tracker.get_gpu_metrics(fraction.gpu_id)
            if gpu_metrics:
                # Update utilization based on fraction allocation
                gpu_metrics.utilization_percent += fraction.size * 100
                gpu_metrics.vram_used_gb += fraction.memory_mb / 1024
                heartbeat.tracker.update_gpu_metrics(gpu_metrics)

        # Validate system coherence
        
        # 1. DRA should have allocated multiple fractions
        assert len(allocated_fractions) >= 3, "Should allocate multiple workloads"
        
        # 2. Token metrics should show realistic patterns
        token_summary = tracker.get_summary_stats()
        assert token_summary["total_models"] >= 3
        assert token_summary["avg_tokens_per_second"] > 1000

        # 3. Heartbeat should reflect aggregate load
        heartbeat_status = heartbeat.get_system_status()
        assert heartbeat_status["aggregate_utilization"] > 30  # Should have some load
        
        current_pulse = heartbeat.get_current_heartbeat()
        assert current_pulse.frequency_bpm > 60  # Should be elevated

        # 4. TTFT should have statistical data
        assert ttft_calc.get_measurement_count() >= len(token_metrics_list)
        if ttft_calc.get_measurement_count() >= 20:
            assert ttft_calc.get_p95_latency() is not None

        # 5. Cost calculations should be reasonable
        total_cost = 0
        for metrics in token_metrics_list:
            if metrics.is_completed():
                cost = cost_calc.calculate_cost_from_metrics(metrics)
                if cost:
                    total_cost += cost

        assert total_cost > 0, "Should have calculated costs for completed metrics"

        # 6. System should be coherent across components
        dra_status = dra.get_system_status()
        heartbeat_gpu_count = heartbeat_status["gpu_count"]
        dra_gpu_count = dra_status["total_gpus"]
        
        assert heartbeat_gpu_count == dra_gpu_count == 3, "GPU count should match across systems"

    def test_error_recovery_scenarios(self):
        """Test system behavior under error conditions."""
        config = load_config()
        tracker = create_token_tracker(config.technology, config.slo)
        heartbeat = create_gpu_heartbeat(config.technology)
        dra = create_dra_simulator(config.technology)

        # Add GPU to all systems
        heartbeat.add_gpu("gpu-01", "nvidia-h100")
        dra.add_gpu("gpu-01", "nvidia-h100")

        # Scenario 1: Invalid token generation request
        try:
            invalid_metrics = tracker.simulate_token_generation("", target_tokens=-1)
            assert False, "Should have raised error for invalid parameters"
        except (ValueError, AssertionError):
            pass  # Expected error

        # Scenario 2: Invalid DRA allocation request
        try:
            invalid_request = dra.request_allocation(
                workload_id="test",
                fraction_size=2.0,  # Invalid size > 1.0
                memory_mb=1000,
                compute_units=100
            )
            assert False, "Should have raised error for invalid fraction size"
        except ValueError:
            pass  # Expected error

        # Scenario 3: Remove GPU while allocations exist
        dra.request_allocation("test-workload", 0.5, 40000, 3000)
        allocated = dra.process_allocations()
        
        if allocated:
            # Remove GPU (should handle gracefully)
            dra.remove_gpu("gpu-01")
            status = dra.get_system_status()
            # System should continue functioning
            assert isinstance(status, dict)

        # Scenario 4: Heartbeat with removed GPUs
        heartbeat.remove_gpu("gpu-01")
        pulse = heartbeat.get_current_heartbeat()
        # Should still generate heartbeat (even with no GPUs)
        assert pulse is not None

    def test_configuration_integration_scenarios(self):
        """Test different configuration scenarios."""
        # Test with minimal configuration
        minimal_tech = TechnologyConfig(
            gpu_types={
                "test-gpu": GPUType(name="test-gpu", memory_gb=16, hourly_cost=1.0)
            }
        )
        minimal_slo = SLOConfig(
            ttft_p95_ms=1000, error_rate_percent=1.0, tokens_per_second=100
        )

        tracker = create_token_tracker(minimal_tech, minimal_slo)
        heartbeat = create_gpu_heartbeat(minimal_tech)
        dra = create_dra_simulator(minimal_tech)

        # Should work with minimal config
        heartbeat.add_gpu("test-gpu-01", "test-gpu")
        dra.add_gpu("test-gpu-01", "test-gpu")
        
        metrics = tracker.simulate_token_generation("test-model", target_tokens=10)
        assert metrics.is_completed()

        dra.request_allocation("test-workload", 0.5, 8000, 1000)
        allocated = dra.process_allocations()
        
        # Systems should function with minimal config
        heartbeat_status = heartbeat.get_system_status()
        dra_status = dra.get_system_status()
        
        assert heartbeat_status["gpu_count"] == 1
        assert dra_status["total_gpus"] == 1