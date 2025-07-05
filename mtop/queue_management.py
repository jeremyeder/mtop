#!/usr/bin/env python3
"""
Queue management system for visual queue depth and flow management.

This module provides intelligent queue management with visual representation,
flow control, and integration with workload patterns and SLO convergence.
"""

import math
import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

from config_loader import SLOConfig


class QueueState(Enum):
    """Queue state indicators."""
    EMPTY = "empty"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    OVERFLOWING = "overflowing"


class FlowControlAction(Enum):
    """Flow control actions."""
    ALLOW_ALL = "allow_all"
    RATE_LIMIT = "rate_limit"
    PRIORITY_ONLY = "priority_only"
    EMERGENCY_THROTTLE = "emergency_throttle"
    REJECT_NEW = "reject_new"


class RequestPriority(Enum):
    """Request priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QueueRequest:
    """Represents a request in the queue."""
    
    request_id: str
    priority: RequestPriority
    arrival_time: float
    estimated_tokens: int
    model_name: str
    timeout_seconds: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate queue request."""
        if not self.request_id:
            raise ValueError("Request ID cannot be empty")
        if self.estimated_tokens <= 0:
            raise ValueError(f"Estimated tokens must be positive, got {self.estimated_tokens}")
        if self.timeout_seconds <= 0:
            raise ValueError(f"Timeout must be positive, got {self.timeout_seconds}")
        if not self.model_name:
            raise ValueError("Model name cannot be empty")
    
    def is_expired(self, current_time: float) -> bool:
        """Check if request has expired."""
        return current_time - self.arrival_time > self.timeout_seconds
    
    def get_wait_time(self, current_time: float) -> float:
        """Get current wait time in seconds."""
        return current_time - self.arrival_time


@dataclass
class QueueMetrics:
    """Queue performance metrics."""
    
    current_depth: int = 0
    max_depth: int = 0
    average_depth: float = 0.0
    current_wait_time: float = 0.0
    average_wait_time: float = 0.0
    p95_wait_time: float = 0.0
    throughput_qps: float = 0.0
    rejection_rate: float = 0.0
    timeout_rate: float = 0.0
    queue_state: QueueState = QueueState.EMPTY
    
    def get_efficiency_score(self) -> float:
        """Calculate queue efficiency score (0-1)."""
        if self.current_depth == 0:
            return 1.0
        
        # Efficiency decreases with depth and wait time
        depth_factor = max(0, 1 - (self.current_depth / 100))  # Assume 100 is max efficient depth
        wait_factor = max(0, 1 - (self.current_wait_time / 10))  # Assume 10s is max efficient wait
        throughput_factor = min(1, self.throughput_qps / 50)  # Assume 50 QPS is good throughput
        
        return (depth_factor + wait_factor + throughput_factor) / 3


class QueueFlowController:
    """Controls queue flow based on current conditions."""
    
    def __init__(self, slo_config: SLOConfig):
        """Initialize flow controller.
        
        Args:
            slo_config: SLO configuration for decision making
        """
        self.slo_config = slo_config
        
        # Flow control thresholds
        self.depth_thresholds = {
            QueueState.LOW: 5,
            QueueState.NORMAL: 20,
            QueueState.HIGH: 50,
            QueueState.CRITICAL: 100,
            QueueState.OVERFLOWING: 200
        }
        
        self.wait_time_thresholds = {
            'normal': 1.0,      # 1 second normal wait
            'high': 5.0,        # 5 seconds high wait
            'critical': 10.0,   # 10 seconds critical wait
            'emergency': 20.0   # 20 seconds emergency
        }
        
        # Flow control state
        self.current_action = FlowControlAction.ALLOW_ALL
        self.rate_limit_qps = None
        self.emergency_mode = False
    
    def evaluate_flow_control(self, metrics: QueueMetrics) -> FlowControlAction:
        """Evaluate and determine flow control action.
        
        Args:
            metrics: Current queue metrics
            
        Returns:
            Recommended flow control action
        """
        # Check for emergency conditions
        if (metrics.current_wait_time > self.wait_time_thresholds['emergency'] or
            metrics.current_depth > self.depth_thresholds[QueueState.OVERFLOWING]):
            self.emergency_mode = True
            self.current_action = FlowControlAction.REJECT_NEW
            return self.current_action
        
        # Check for critical conditions
        if (metrics.current_wait_time > self.wait_time_thresholds['critical'] or
            metrics.current_depth > self.depth_thresholds[QueueState.CRITICAL]):
            self.current_action = FlowControlAction.EMERGENCY_THROTTLE
            self.rate_limit_qps = max(1, metrics.throughput_qps * 0.5)  # 50% throttle
            return self.current_action
        
        # Check for high load conditions
        if (metrics.current_wait_time > self.wait_time_thresholds['high'] or
            metrics.current_depth > self.depth_thresholds[QueueState.HIGH]):
            self.current_action = FlowControlAction.PRIORITY_ONLY
            return self.current_action
        
        # Check for moderate load
        if (metrics.current_wait_time > self.wait_time_thresholds['normal'] or
            metrics.current_depth > self.depth_thresholds[QueueState.NORMAL]):
            self.current_action = FlowControlAction.RATE_LIMIT
            self.rate_limit_qps = metrics.throughput_qps * 0.8  # 20% throttle
            return self.current_action
        
        # Normal operation
        self.emergency_mode = False
        self.current_action = FlowControlAction.ALLOW_ALL
        self.rate_limit_qps = None
        return self.current_action
    
    def should_accept_request(self, request: QueueRequest, current_metrics: QueueMetrics) -> bool:
        """Determine if a request should be accepted.
        
        Args:
            request: Incoming request
            current_metrics: Current queue metrics
            
        Returns:
            True if request should be accepted
        """
        action = self.evaluate_flow_control(current_metrics)
        
        if action == FlowControlAction.ALLOW_ALL:
            return True
        elif action == FlowControlAction.REJECT_NEW:
            return False
        elif action == FlowControlAction.PRIORITY_ONLY:
            return request.priority in [RequestPriority.HIGH, RequestPriority.CRITICAL]
        elif action == FlowControlAction.EMERGENCY_THROTTLE:
            return request.priority == RequestPriority.CRITICAL
        elif action == FlowControlAction.RATE_LIMIT:
            # Simple rate limiting - could be more sophisticated
            return current_metrics.throughput_qps < (self.rate_limit_qps or float('inf'))
        
        return False


class QueueVisualizer:
    """Provides visual representation of queue state and flow."""
    
    def __init__(self):
        """Initialize queue visualizer."""
        self.max_visual_depth = 50  # Maximum items to show visually
        self.depth_chars = {
            QueueState.EMPTY: "⬜",
            QueueState.LOW: "🟢",
            QueueState.NORMAL: "🟡",
            QueueState.HIGH: "🟠",
            QueueState.CRITICAL: "🔴",
            QueueState.OVERFLOWING: "💥"
        }
        
        self.priority_chars = {
            RequestPriority.LOW: "·",
            RequestPriority.NORMAL: "○",
            RequestPriority.HIGH: "●",
            RequestPriority.CRITICAL: "★"
        }
    
    def render_queue_depth(self, metrics: QueueMetrics) -> str:
        """Render visual queue depth indicator.
        
        Args:
            metrics: Current queue metrics
            
        Returns:
            Visual representation of queue depth
        """
        depth = min(metrics.current_depth, self.max_visual_depth)
        state_char = self.depth_chars[metrics.queue_state]
        
        # Create visual bar
        bar_length = 20
        filled_length = int((depth / self.max_visual_depth) * bar_length)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        return f"{state_char} Queue [{bar}] {metrics.current_depth}/{self.max_visual_depth}"
    
    def render_flow_state(self, controller: QueueFlowController) -> str:
        """Render flow control state.
        
        Args:
            controller: Flow controller with current state
            
        Returns:
            Visual representation of flow control
        """
        action_symbols = {
            FlowControlAction.ALLOW_ALL: "🟢 OPEN",
            FlowControlAction.RATE_LIMIT: "🟡 LIMITED",
            FlowControlAction.PRIORITY_ONLY: "🟠 PRIORITY",
            FlowControlAction.EMERGENCY_THROTTLE: "🔴 THROTTLED",
            FlowControlAction.REJECT_NEW: "⛔ CLOSED"
        }
        
        symbol = action_symbols.get(controller.current_action, "❓ UNKNOWN")
        
        additional_info = ""
        if controller.rate_limit_qps:
            additional_info = f" ({controller.rate_limit_qps:.1f} QPS)"
        if controller.emergency_mode:
            additional_info += " [EMERGENCY]"
        
        return f"Flow: {symbol}{additional_info}"
    
    def render_queue_requests(self, requests: List[QueueRequest], limit: int = 10) -> str:
        """Render current queue requests.
        
        Args:
            requests: List of requests in queue
            limit: Maximum requests to show
            
        Returns:
            Visual representation of queued requests
        """
        if not requests:
            return "Queue: [empty]"
        
        shown_requests = requests[:limit]
        request_chars = []
        
        for request in shown_requests:
            priority_char = self.priority_chars[request.priority]
            wait_time = request.get_wait_time(time.time())
            
            # Color by wait time
            if wait_time > 10:
                char = f"🔴{priority_char}"
            elif wait_time > 5:
                char = f"🟠{priority_char}"
            elif wait_time > 1:
                char = f"🟡{priority_char}"
            else:
                char = f"🟢{priority_char}"
            
            request_chars.append(char)
        
        request_display = "".join(request_chars)
        
        if len(requests) > limit:
            request_display += f"... (+{len(requests) - limit} more)"
        
        return f"Queue: {request_display}"


class QueueManager:
    """Main queue management system."""
    
    def __init__(self, slo_config: SLOConfig, max_queue_size: int = 1000):
        """Initialize queue manager.
        
        Args:
            slo_config: SLO configuration
            max_queue_size: Maximum queue size before rejecting requests
        """
        self.slo_config = slo_config
        self.max_queue_size = max_queue_size
        
        # Queue data structures
        self.request_queue: deque = deque()
        self.processing_requests: Dict[str, QueueRequest] = {}
        self.completed_requests: deque = deque(maxlen=10000)  # Keep history
        
        # Components
        self.flow_controller = QueueFlowController(slo_config)
        self.visualizer = QueueVisualizer()
        
        # Metrics tracking
        self.current_metrics = QueueMetrics()
        self.metrics_history: deque = deque(maxlen=1000)
        self.wait_times: deque = deque(maxlen=1000)
        
        # Threading
        self._lock = Lock()
        
        # Statistics
        self.total_requests = 0
        self.total_completed = 0
        self.total_rejected = 0
        self.total_timeouts = 0
    
    def enqueue_request(self, request: QueueRequest) -> bool:
        """Add request to queue.
        
        Args:
            request: Request to add to queue
            
        Returns:
            True if request was accepted, False if rejected
        """
        current_time = time.time()
        
        with self._lock:
            # Update current metrics before flow control decision
            self._update_metrics(current_time)
            
            # Check flow control
            if not self.flow_controller.should_accept_request(request, self.current_metrics):
                self.total_rejected += 1
                return False
            
            # Check queue size limit
            if len(self.request_queue) >= self.max_queue_size:
                self.total_rejected += 1
                return False
            
            # Add to queue with priority ordering
            self._insert_by_priority(request)
            self.total_requests += 1
            
            return True
    
    def _insert_by_priority(self, request: QueueRequest) -> None:
        """Insert request into queue maintaining priority order."""
        # Convert to list for insertion, then back to deque
        queue_list = list(self.request_queue)
        
        # Find insertion point (higher priority first)
        priority_values = {
            RequestPriority.CRITICAL: 4,
            RequestPriority.HIGH: 3,
            RequestPriority.NORMAL: 2,
            RequestPriority.LOW: 1
        }
        
        request_priority = priority_values[request.priority]
        insert_index = len(queue_list)
        
        for i, existing_request in enumerate(queue_list):
            existing_priority = priority_values[existing_request.priority]
            if request_priority > existing_priority:
                insert_index = i
                break
        
        queue_list.insert(insert_index, request)
        self.request_queue = deque(queue_list)
    
    def dequeue_request(self) -> Optional[QueueRequest]:
        """Remove and return next request from queue.
        
        Returns:
            Next request or None if queue is empty
        """
        current_time = time.time()
        
        with self._lock:
            # Clean expired requests first
            self._clean_expired_requests(current_time)
            
            if not self.request_queue:
                return None
            
            request = self.request_queue.popleft()
            self.processing_requests[request.request_id] = request
            
            return request
    
    def complete_request(self, request_id: str, processing_time: float) -> bool:
        """Mark request as completed.
        
        Args:
            request_id: ID of completed request
            processing_time: Time taken to process request
            
        Returns:
            True if request was found and completed
        """
        current_time = time.time()
        
        with self._lock:
            if request_id not in self.processing_requests:
                return False
            
            request = self.processing_requests.pop(request_id)
            
            # Calculate wait time
            wait_time = current_time - request.arrival_time - processing_time
            self.wait_times.append(wait_time)
            
            # Add to completed history
            request.metadata['completion_time'] = current_time
            request.metadata['processing_time'] = processing_time
            request.metadata['wait_time'] = wait_time
            self.completed_requests.append(request)
            
            self.total_completed += 1
            
            return True
    
    def _clean_expired_requests(self, current_time: float) -> None:
        """Remove expired requests from queue."""
        expired_count = 0
        
        # Clean main queue
        queue_list = []
        for request in self.request_queue:
            if request.is_expired(current_time):
                expired_count += 1
            else:
                queue_list.append(request)
        
        self.request_queue = deque(queue_list)
        
        # Clean processing requests
        expired_processing = []
        for request_id, request in self.processing_requests.items():
            if request.is_expired(current_time):
                expired_processing.append(request_id)
        
        for request_id in expired_processing:
            self.processing_requests.pop(request_id)
            expired_count += 1
        
        self.total_timeouts += expired_count
    
    def _update_metrics(self, current_time: float) -> None:
        """Update current queue metrics."""
        # Current depth
        self.current_metrics.current_depth = len(self.request_queue)
        
        # Max depth
        if self.current_metrics.current_depth > self.current_metrics.max_depth:
            self.current_metrics.max_depth = self.current_metrics.current_depth
        
        # Wait times
        if self.request_queue:
            current_waits = [req.get_wait_time(current_time) for req in self.request_queue]
            self.current_metrics.current_wait_time = max(current_waits)
        else:
            self.current_metrics.current_wait_time = 0.0
        
        # Historical averages
        if self.wait_times:
            self.current_metrics.average_wait_time = statistics.mean(self.wait_times)
            if len(self.wait_times) >= 20:
                self.current_metrics.p95_wait_time = statistics.quantiles(
                    list(self.wait_times), n=20
                )[18]
        
        # Throughput calculation
        if len(self.metrics_history) > 0:
            time_window = 60.0  # 1 minute window
            recent_completions = sum(
                1 for record in self.metrics_history
                if current_time - record['timestamp'] <= time_window
            )
            self.current_metrics.throughput_qps = recent_completions / time_window
        
        # Rejection and timeout rates
        total_attempts = self.total_requests + self.total_rejected
        if total_attempts > 0:
            self.current_metrics.rejection_rate = self.total_rejected / total_attempts
        
        total_processed = self.total_completed + self.total_timeouts
        if total_processed > 0:
            self.current_metrics.timeout_rate = self.total_timeouts / total_processed
        
        # Queue state determination
        self._determine_queue_state()
        
        # Record metrics history
        self.metrics_history.append({
            'timestamp': current_time,
            'depth': self.current_metrics.current_depth,
            'wait_time': self.current_metrics.current_wait_time,
            'throughput': self.current_metrics.throughput_qps,
            'queue_state': self.current_metrics.queue_state.value
        })
    
    def _determine_queue_state(self) -> None:
        """Determine current queue state based on metrics."""
        depth = self.current_metrics.current_depth
        wait_time = self.current_metrics.current_wait_time
        
        thresholds = self.flow_controller.depth_thresholds
        
        if depth == 0:
            self.current_metrics.queue_state = QueueState.EMPTY
        elif depth <= thresholds[QueueState.LOW]:
            self.current_metrics.queue_state = QueueState.LOW
        elif depth <= thresholds[QueueState.NORMAL]:
            self.current_metrics.queue_state = QueueState.NORMAL
        elif depth <= thresholds[QueueState.HIGH]:
            self.current_metrics.queue_state = QueueState.HIGH
        elif depth <= thresholds[QueueState.CRITICAL]:
            self.current_metrics.queue_state = QueueState.CRITICAL
        else:
            self.current_metrics.queue_state = QueueState.OVERFLOWING
        
        # Override based on wait time if more severe
        if wait_time > 20:
            self.current_metrics.queue_state = QueueState.OVERFLOWING
        elif wait_time > 10:
            if self.current_metrics.queue_state.value < QueueState.CRITICAL.value:
                self.current_metrics.queue_state = QueueState.CRITICAL
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get comprehensive queue status.
        
        Returns:
            Dictionary with queue status and metrics
        """
        current_time = time.time()
        
        with self._lock:
            self._update_metrics(current_time)
            
            return {
                'metrics': {
                    'current_depth': self.current_metrics.current_depth,
                    'max_depth': self.current_metrics.max_depth,
                    'current_wait_time': self.current_metrics.current_wait_time,
                    'average_wait_time': self.current_metrics.average_wait_time,
                    'p95_wait_time': self.current_metrics.p95_wait_time,
                    'throughput_qps': self.current_metrics.throughput_qps,
                    'rejection_rate': self.current_metrics.rejection_rate,
                    'timeout_rate': self.current_metrics.timeout_rate,
                    'queue_state': self.current_metrics.queue_state.value,
                    'efficiency_score': self.current_metrics.get_efficiency_score()
                },
                'flow_control': {
                    'current_action': self.flow_controller.current_action.value,
                    'rate_limit_qps': self.flow_controller.rate_limit_qps,
                    'emergency_mode': self.flow_controller.emergency_mode
                },
                'statistics': {
                    'total_requests': self.total_requests,
                    'total_completed': self.total_completed,
                    'total_rejected': self.total_rejected,
                    'total_timeouts': self.total_timeouts,
                    'processing_requests': len(self.processing_requests)
                },
                'visualizations': {
                    'depth_bar': self.visualizer.render_queue_depth(self.current_metrics),
                    'flow_state': self.visualizer.render_flow_state(self.flow_controller),
                    'queue_requests': self.visualizer.render_queue_requests(list(self.request_queue))
                }
            }
    
    def simulate_request_processing(self, duration: float = 60.0) -> Dict[str, Any]:
        """Simulate request processing for demonstration.
        
        Args:
            duration: Simulation duration in seconds
            
        Returns:
            Simulation results
        """
        import random
        
        start_time = time.time()
        simulation_stats = {
            'requests_generated': 0,
            'requests_processed': 0,
            'avg_queue_depth': 0.0,
            'max_queue_depth': 0,
            'avg_wait_time': 0.0
        }
        
        depths = []
        
        while time.time() - start_time < duration:
            current_time = time.time()
            
            # Generate random requests
            if random.random() < 0.3:  # 30% chance each iteration
                request = QueueRequest(
                    request_id=f"req_{simulation_stats['requests_generated']}",
                    priority=random.choice(list(RequestPriority)),
                    arrival_time=current_time,
                    estimated_tokens=random.randint(100, 2000),
                    model_name=random.choice(["gpt-4", "gpt-3.5", "claude-3"])
                )
                
                if self.enqueue_request(request):
                    simulation_stats['requests_generated'] += 1
            
            # Process requests
            if random.random() < 0.8:  # 80% chance to process
                request = self.dequeue_request()
                if request:
                    processing_time = random.uniform(0.1, 2.0)
                    time.sleep(processing_time)  # Simulate processing
                    
                    if self.complete_request(request.request_id, processing_time):
                        simulation_stats['requests_processed'] += 1
            
            # Track metrics
            depths.append(self.current_metrics.current_depth)
            
            time.sleep(0.1)  # Small delay between iterations
        
        # Calculate final statistics
        if depths:
            simulation_stats['avg_queue_depth'] = statistics.mean(depths)
            simulation_stats['max_queue_depth'] = max(depths)
        
        if self.wait_times:
            simulation_stats['avg_wait_time'] = statistics.mean(self.wait_times)
        
        return simulation_stats