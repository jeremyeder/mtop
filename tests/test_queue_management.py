#!/usr/bin/env python3
"""
Test suite for queue management system.
"""

import pytest
import time
from unittest.mock import patch

from mtop.queue_management import (
    QueueManager,
    QueueRequest,
    QueueMetrics,
    QueueFlowController,
    QueueVisualizer,
    QueueState,
    FlowControlAction,
    RequestPriority
)
from config_loader import SLOConfig


class TestQueueRequest:
    """Test queue request functionality."""
    
    def test_valid_queue_request(self):
        """Test valid queue request creation."""
        request = QueueRequest(
            request_id="test-123",
            priority=RequestPriority.NORMAL,
            arrival_time=time.time(),
            estimated_tokens=1000,
            model_name="gpt-4"
        )
        
        assert request.request_id == "test-123"
        assert request.priority == RequestPriority.NORMAL
        assert request.estimated_tokens == 1000
        assert request.model_name == "gpt-4"
        assert request.timeout_seconds == 30.0
        assert request.metadata == {}
    
    def test_queue_request_validation(self):
        """Test queue request validation."""
        base_time = time.time()
        
        with pytest.raises(ValueError, match="Request ID cannot be empty"):
            QueueRequest(
                request_id="",
                priority=RequestPriority.NORMAL,
                arrival_time=base_time,
                estimated_tokens=1000,
                model_name="gpt-4"
            )
        
        with pytest.raises(ValueError, match="Estimated tokens must be positive"):
            QueueRequest(
                request_id="test",
                priority=RequestPriority.NORMAL,
                arrival_time=base_time,
                estimated_tokens=-100,
                model_name="gpt-4"
            )
        
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            QueueRequest(
                request_id="test",
                priority=RequestPriority.NORMAL,
                arrival_time=base_time,
                estimated_tokens=1000,
                model_name=""
            )
    
    def test_request_expiration(self):
        """Test request expiration logic."""
        base_time = time.time()
        request = QueueRequest(
            request_id="test",
            priority=RequestPriority.NORMAL,
            arrival_time=base_time,
            estimated_tokens=1000,
            model_name="gpt-4",
            timeout_seconds=5.0
        )
        
        # Should not be expired immediately
        assert not request.is_expired(base_time + 1.0)
        
        # Should be expired after timeout
        assert request.is_expired(base_time + 10.0)
    
    def test_wait_time_calculation(self):
        """Test wait time calculation."""
        base_time = time.time()
        request = QueueRequest(
            request_id="test",
            priority=RequestPriority.NORMAL,
            arrival_time=base_time,
            estimated_tokens=1000,
            model_name="gpt-4"
        )
        
        wait_time = request.get_wait_time(base_time + 5.0)
        assert wait_time == 5.0


class TestQueueMetrics:
    """Test queue metrics functionality."""
    
    def test_efficiency_score_calculation(self):
        """Test efficiency score calculation."""
        # Perfect efficiency (empty queue)
        metrics = QueueMetrics()
        assert metrics.get_efficiency_score() == 1.0
        
        # Good efficiency
        metrics = QueueMetrics(
            current_depth=10,
            current_wait_time=2.0,
            throughput_qps=40.0
        )
        score = metrics.get_efficiency_score()
        assert 0 <= score <= 1
        assert score > 0.5  # Should be decent
        
        # Poor efficiency
        metrics = QueueMetrics(
            current_depth=150,
            current_wait_time=15.0,
            throughput_qps=1.0
        )
        score = metrics.get_efficiency_score()
        assert 0 <= score <= 1
        assert score < 0.5  # Should be poor


class TestQueueFlowController:
    """Test queue flow controller functionality."""
    
    @pytest.fixture
    def slo_config(self):
        """Create test SLO configuration."""
        return SLOConfig(
            ttft_p95_ms=500,
            error_rate_percent=0.1,
            tokens_per_second=1000
        )
    
    @pytest.fixture
    def flow_controller(self, slo_config):
        """Create test flow controller."""
        return QueueFlowController(slo_config)
    
    def test_flow_controller_initialization(self, flow_controller):
        """Test flow controller initialization."""
        assert flow_controller.current_action == FlowControlAction.ALLOW_ALL
        assert flow_controller.rate_limit_qps is None
        assert flow_controller.emergency_mode is False
        
        # Check thresholds are set
        assert QueueState.LOW in flow_controller.depth_thresholds
        assert QueueState.NORMAL in flow_controller.depth_thresholds
        assert QueueState.HIGH in flow_controller.depth_thresholds
        assert QueueState.CRITICAL in flow_controller.depth_thresholds
        assert QueueState.OVERFLOWING in flow_controller.depth_thresholds
    
    def test_normal_flow_control(self, flow_controller):
        """Test normal flow control conditions."""
        # Normal metrics
        metrics = QueueMetrics(
            current_depth=10,
            current_wait_time=0.5,
            throughput_qps=50.0
        )
        
        action = flow_controller.evaluate_flow_control(metrics)
        assert action == FlowControlAction.ALLOW_ALL
        assert not flow_controller.emergency_mode
    
    def test_rate_limiting_flow_control(self, flow_controller):
        """Test rate limiting flow control."""
        # Moderate load metrics
        metrics = QueueMetrics(
            current_depth=25,
            current_wait_time=2.0,
            throughput_qps=30.0
        )
        
        action = flow_controller.evaluate_flow_control(metrics)
        assert action == FlowControlAction.RATE_LIMIT
        assert flow_controller.rate_limit_qps is not None
        assert flow_controller.rate_limit_qps == 24.0  # 80% of 30 QPS
    
    def test_priority_only_flow_control(self, flow_controller):
        """Test priority-only flow control."""
        # High load metrics
        metrics = QueueMetrics(
            current_depth=60,
            current_wait_time=7.0,
            throughput_qps=20.0
        )
        
        action = flow_controller.evaluate_flow_control(metrics)
        assert action == FlowControlAction.PRIORITY_ONLY
    
    def test_emergency_flow_control(self, flow_controller):
        """Test emergency flow control."""
        # Critical metrics
        metrics = QueueMetrics(
            current_depth=250,
            current_wait_time=25.0,
            throughput_qps=5.0
        )
        
        action = flow_controller.evaluate_flow_control(metrics)
        assert action == FlowControlAction.REJECT_NEW
        assert flow_controller.emergency_mode is True
    
    def test_request_acceptance_logic(self, flow_controller):
        """Test request acceptance logic."""
        current_time = time.time()
        
        # Normal request
        normal_request = QueueRequest(
            request_id="normal",
            priority=RequestPriority.NORMAL,
            arrival_time=current_time,
            estimated_tokens=1000,
            model_name="gpt-4"
        )
        
        # Critical request
        critical_request = QueueRequest(
            request_id="critical",
            priority=RequestPriority.CRITICAL,
            arrival_time=current_time,
            estimated_tokens=1000,
            model_name="gpt-4"
        )
        
        # Test under normal conditions
        normal_metrics = QueueMetrics(current_depth=5, current_wait_time=0.5)
        assert flow_controller.should_accept_request(normal_request, normal_metrics)
        assert flow_controller.should_accept_request(critical_request, normal_metrics)
        
        # Test under emergency conditions
        emergency_metrics = QueueMetrics(current_depth=250, current_wait_time=25.0)
        assert not flow_controller.should_accept_request(normal_request, emergency_metrics)
        assert not flow_controller.should_accept_request(critical_request, emergency_metrics)  # Even critical rejected in emergency


class TestQueueVisualizer:
    """Test queue visualizer functionality."""
    
    @pytest.fixture
    def visualizer(self):
        """Create test visualizer."""
        return QueueVisualizer()
    
    @pytest.fixture
    def flow_controller(self):
        """Create test flow controller."""
        slo_config = SLOConfig(ttft_p95_ms=500, error_rate_percent=0.1, tokens_per_second=1000)
        return QueueFlowController(slo_config)
    
    def test_queue_depth_rendering(self, visualizer):
        """Test queue depth visualization."""
        metrics = QueueMetrics(
            current_depth=25,
            queue_state=QueueState.NORMAL
        )
        
        visual = visualizer.render_queue_depth(metrics)
        
        assert "Queue" in visual
        assert "25" in visual
        assert "🟡" in visual  # Normal state emoji
        assert "█" in visual or "░" in visual  # Progress bar
    
    def test_flow_state_rendering(self, visualizer, flow_controller):
        """Test flow state visualization."""
        flow_controller.current_action = FlowControlAction.RATE_LIMIT
        flow_controller.rate_limit_qps = 25.0
        
        visual = visualizer.render_flow_state(flow_controller)
        
        assert "Flow:" in visual
        assert "LIMITED" in visual
        assert "25.0" in visual
    
    def test_queue_requests_rendering(self, visualizer):
        """Test queue requests visualization."""
        current_time = time.time()
        requests = [
            QueueRequest(
                request_id="req1",
                priority=RequestPriority.HIGH,
                arrival_time=current_time - 2.0,  # 2 seconds wait
                estimated_tokens=1000,
                model_name="gpt-4"
            ),
            QueueRequest(
                request_id="req2",
                priority=RequestPriority.NORMAL,
                arrival_time=current_time - 0.5,  # 0.5 seconds wait
                estimated_tokens=500,
                model_name="gpt-3.5"
            )
        ]
        
        visual = visualizer.render_queue_requests(requests)
        
        assert "Queue:" in visual
        assert "●" in visual  # High priority symbol
        assert "○" in visual  # Normal priority symbol
        assert "🟡" in visual or "🟢" in visual  # Wait time colors


class TestQueueManager:
    """Test queue manager functionality."""
    
    @pytest.fixture
    def slo_config(self):
        """Create test SLO configuration."""
        return SLOConfig(
            ttft_p95_ms=500,
            error_rate_percent=0.1,
            tokens_per_second=1000
        )
    
    @pytest.fixture
    def queue_manager(self, slo_config):
        """Create test queue manager."""
        return QueueManager(slo_config, max_queue_size=100)
    
    def test_queue_manager_initialization(self, queue_manager, slo_config):
        """Test queue manager initialization."""
        assert queue_manager.slo_config == slo_config
        assert queue_manager.max_queue_size == 100
        assert len(queue_manager.request_queue) == 0
        assert len(queue_manager.processing_requests) == 0
        assert queue_manager.total_requests == 0
        assert queue_manager.total_completed == 0
        assert queue_manager.total_rejected == 0
        assert queue_manager.total_timeouts == 0
    
    def test_request_enqueue_dequeue(self, queue_manager):
        """Test basic request enqueue and dequeue."""
        current_time = time.time()
        request = QueueRequest(
            request_id="test-1",
            priority=RequestPriority.NORMAL,
            arrival_time=current_time,
            estimated_tokens=1000,
            model_name="gpt-4"
        )
        
        # Enqueue request
        success = queue_manager.enqueue_request(request)
        assert success is True
        assert len(queue_manager.request_queue) == 1
        assert queue_manager.total_requests == 1
        
        # Dequeue request
        dequeued = queue_manager.dequeue_request()
        assert dequeued is not None
        assert dequeued.request_id == "test-1"
        assert len(queue_manager.request_queue) == 0
        assert len(queue_manager.processing_requests) == 1
    
    def test_priority_ordering(self, queue_manager):
        """Test priority-based queue ordering."""
        current_time = time.time()
        
        # Add requests in mixed priority order
        requests = [
            QueueRequest("low", RequestPriority.LOW, current_time, 1000, "gpt-4"),
            QueueRequest("critical", RequestPriority.CRITICAL, current_time, 1000, "gpt-4"),
            QueueRequest("normal", RequestPriority.NORMAL, current_time, 1000, "gpt-4"),
            QueueRequest("high", RequestPriority.HIGH, current_time, 1000, "gpt-4")
        ]
        
        for request in requests:
            queue_manager.enqueue_request(request)
        
        # Dequeue and check order: CRITICAL, HIGH, NORMAL, LOW
        order = []
        while len(queue_manager.request_queue) > 0:
            request = queue_manager.dequeue_request()
            order.append(request.priority)
        
        expected_order = [
            RequestPriority.CRITICAL,
            RequestPriority.HIGH,
            RequestPriority.NORMAL,
            RequestPriority.LOW
        ]
        
        assert order == expected_order
    
    def test_request_completion(self, queue_manager):
        """Test request completion."""
        current_time = time.time()
        request = QueueRequest(
            request_id="complete-test",
            priority=RequestPriority.NORMAL,
            arrival_time=current_time,
            estimated_tokens=1000,
            model_name="gpt-4"
        )
        
        # Enqueue and dequeue
        queue_manager.enqueue_request(request)
        dequeued = queue_manager.dequeue_request()
        
        # Complete request
        success = queue_manager.complete_request(dequeued.request_id, 1.5)
        assert success is True
        assert len(queue_manager.processing_requests) == 0
        assert len(queue_manager.completed_requests) == 1
        assert queue_manager.total_completed == 1
        
        completed = queue_manager.completed_requests[0]
        assert 'completion_time' in completed.metadata
        assert 'processing_time' in completed.metadata
        assert 'wait_time' in completed.metadata
    
    def test_expired_request_cleanup(self, queue_manager):
        """Test expired request cleanup."""
        old_time = time.time() - 100  # 100 seconds ago
        
        # Add expired request
        expired_request = QueueRequest(
            request_id="expired",
            priority=RequestPriority.NORMAL,
            arrival_time=old_time,
            estimated_tokens=1000,
            model_name="gpt-4",
            timeout_seconds=10.0
        )
        
        # Bypass flow control for testing by adding directly to queue
        queue_manager.request_queue.append(expired_request)
        queue_manager.total_requests += 1
        
        # Add current request
        current_request = QueueRequest(
            request_id="current",
            priority=RequestPriority.NORMAL,
            arrival_time=time.time(),
            estimated_tokens=1000,
            model_name="gpt-4"
        )
        
        queue_manager.request_queue.append(current_request)
        queue_manager.total_requests += 1
        
        # Dequeue should clean expired and return current
        dequeued = queue_manager.dequeue_request()
        assert dequeued is not None
        assert dequeued.request_id == "current"
        assert queue_manager.total_timeouts > 0
    
    def test_queue_size_limit(self, queue_manager):
        """Test queue size limit enforcement."""
        current_time = time.time()
        
        # Temporarily disable flow control for size limit testing
        original_should_accept = queue_manager.flow_controller.should_accept_request
        queue_manager.flow_controller.should_accept_request = lambda req, metrics: True
        
        # Fill queue to limit
        for i in range(queue_manager.max_queue_size):
            request = QueueRequest(
                request_id=f"req-{i}",
                priority=RequestPriority.NORMAL,
                arrival_time=current_time,
                estimated_tokens=1000,
                model_name="gpt-4"
            )
            success = queue_manager.enqueue_request(request)
            assert success is True
        
        # Next request should be rejected due to size limit
        overflow_request = QueueRequest(
            request_id="overflow",
            priority=RequestPriority.NORMAL,
            arrival_time=current_time,
            estimated_tokens=1000,
            model_name="gpt-4"
        )
        
        success = queue_manager.enqueue_request(overflow_request)
        assert success is False
        assert queue_manager.total_rejected > 0
        
        # Restore original flow control
        queue_manager.flow_controller.should_accept_request = original_should_accept
    
    def test_metrics_calculation(self, queue_manager):
        """Test metrics calculation."""
        current_time = time.time()
        
        # Disable flow control for testing
        queue_manager.flow_controller.should_accept_request = lambda req, metrics: True
        
        # Add some requests with different wait times
        for i in range(5):
            request = QueueRequest(
                request_id=f"metrics-{i}",
                priority=RequestPriority.NORMAL,
                arrival_time=current_time - i,  # Different arrival times
                estimated_tokens=1000,
                model_name="gpt-4"
            )
            success = queue_manager.enqueue_request(request)
            assert success is True  # Should all be accepted with flow control disabled
        
        # Update metrics manually
        queue_manager._update_metrics(current_time)
        
        assert queue_manager.current_metrics.current_depth == 5
        assert queue_manager.current_metrics.current_wait_time >= 4.0  # Oldest request waits 4 seconds
        assert queue_manager.current_metrics.queue_state != QueueState.EMPTY
    
    def test_queue_status_reporting(self, queue_manager):
        """Test comprehensive queue status reporting."""
        current_time = time.time()
        
        # Add some test data
        request = QueueRequest(
            request_id="status-test",
            priority=RequestPriority.HIGH,
            arrival_time=current_time,
            estimated_tokens=1000,
            model_name="gpt-4"
        )
        
        queue_manager.enqueue_request(request)
        
        status = queue_manager.get_queue_status()
        
        # Check structure
        assert 'metrics' in status
        assert 'flow_control' in status
        assert 'statistics' in status
        assert 'visualizations' in status
        
        # Check metrics
        assert 'current_depth' in status['metrics']
        assert 'queue_state' in status['metrics']
        assert 'efficiency_score' in status['metrics']
        
        # Check flow control
        assert 'current_action' in status['flow_control']
        assert 'emergency_mode' in status['flow_control']
        
        # Check statistics
        assert 'total_requests' in status['statistics']
        assert 'total_completed' in status['statistics']
        
        # Check visualizations
        assert 'depth_bar' in status['visualizations']
        assert 'flow_state' in status['visualizations']
        assert 'queue_requests' in status['visualizations']


class TestIntegration:
    """Integration tests for queue management system."""
    
    def test_end_to_end_queue_processing(self):
        """Test complete queue processing workflow."""
        slo_config = SLOConfig(ttft_p95_ms=500, error_rate_percent=0.1, tokens_per_second=1000)
        queue_manager = QueueManager(slo_config)
        
        current_time = time.time()
        
        # Create multiple requests with different priorities
        requests = [
            QueueRequest("req1", RequestPriority.LOW, current_time, 500, "gpt-3.5"),
            QueueRequest("req2", RequestPriority.CRITICAL, current_time, 2000, "gpt-4"),
            QueueRequest("req3", RequestPriority.NORMAL, current_time, 1000, "gpt-4"),
            QueueRequest("req4", RequestPriority.HIGH, current_time, 1500, "claude-3")
        ]
        
        # Enqueue all requests
        for request in requests:
            success = queue_manager.enqueue_request(request)
            assert success is True
        
        # Process requests in priority order
        processed_priorities = []
        while len(queue_manager.request_queue) > 0:
            request = queue_manager.dequeue_request()
            processed_priorities.append(request.priority)
            
            # Simulate processing time
            processing_time = 0.5
            success = queue_manager.complete_request(request.request_id, processing_time)
            assert success is True
        
        # Verify priority order
        expected_order = [
            RequestPriority.CRITICAL,
            RequestPriority.HIGH,
            RequestPriority.NORMAL,
            RequestPriority.LOW
        ]
        assert processed_priorities == expected_order
        
        # Verify final state
        assert queue_manager.total_requests == 4
        assert queue_manager.total_completed == 4
        assert queue_manager.total_rejected == 0
        assert len(queue_manager.completed_requests) == 4
        
        # Check metrics
        status = queue_manager.get_queue_status()
        assert status['metrics']['current_depth'] == 0
        assert status['statistics']['total_completed'] == 4
    
    @patch('time.sleep')  # Speed up simulation
    def test_queue_simulation(self, mock_sleep):
        """Test queue simulation functionality."""
        slo_config = SLOConfig(ttft_p95_ms=500, error_rate_percent=0.1, tokens_per_second=1000)
        queue_manager = QueueManager(slo_config)
        
        # Run short simulation
        results = queue_manager.simulate_request_processing(duration=0.1)  # Very short for testing
        
        # Check results structure
        assert 'requests_generated' in results
        assert 'requests_processed' in results
        assert 'avg_queue_depth' in results
        assert 'max_queue_depth' in results
        assert 'avg_wait_time' in results
        
        # Should have some activity (though amounts depend on randomness)
        assert results['requests_generated'] >= 0
        assert results['requests_processed'] >= 0