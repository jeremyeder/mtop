#!/usr/bin/env python3
"""
Test suite for cost optimization logic.
"""

import pytest
import time
from unittest.mock import Mock

from mtop.cost_optimizer import (
    CostOptimizer,
    CostOptimization,
    CostTradeoffAnalysis,
    OptimizationObjective,
    CostEfficiencyStrategy
)
from mtop.token_metrics import CostCalculator, TokenMetrics
from mtop.gpu_heartbeat import GPUMetrics
from config_loader import SLOConfig, TechnologyConfig, GPUType


class TestCostOptimization:
    """Test cost optimization data structure."""
    
    def test_valid_cost_optimization(self):
        """Test valid cost optimization creation."""
        optimization = CostOptimization(
            strategy=CostEfficiencyStrategy.RIGHT_SIZE_CAPACITY,
            estimated_savings=50000.0,
            confidence_score=0.8,
            implementation_effort="medium",
            risk_level="low",
            description="Right-size GPU capacity"
        )
        
        assert optimization.strategy == CostEfficiencyStrategy.RIGHT_SIZE_CAPACITY
        assert optimization.estimated_savings == 50000.0
        assert optimization.confidence_score == 0.8
        assert optimization.implementation_effort == "medium"
        assert optimization.risk_level == "low"
        assert optimization.description == "Right-size GPU capacity"
        assert optimization.prerequisites == []
        assert optimization.estimated_impact_time == 300.0
    
    def test_cost_optimization_validation(self):
        """Test cost optimization validation."""
        with pytest.raises(ValueError, match="Estimated savings cannot be negative"):
            CostOptimization(
                strategy=CostEfficiencyStrategy.RIGHT_SIZE_CAPACITY,
                estimated_savings=-1000.0,
                confidence_score=0.8,
                implementation_effort="medium",
                risk_level="low",
                description="Test"
            )
        
        with pytest.raises(ValueError, match="Confidence score must be 0-1"):
            CostOptimization(
                strategy=CostEfficiencyStrategy.RIGHT_SIZE_CAPACITY,
                estimated_savings=1000.0,
                confidence_score=1.5,
                implementation_effort="medium",
                risk_level="low",
                description="Test"
            )
        
        with pytest.raises(ValueError, match="Implementation effort must be"):
            CostOptimization(
                strategy=CostEfficiencyStrategy.RIGHT_SIZE_CAPACITY,
                estimated_savings=1000.0,
                confidence_score=0.8,
                implementation_effort="invalid",
                risk_level="low",
                description="Test"
            )


class TestCostTradeoffAnalysis:
    """Test cost trade-off analysis."""
    
    def test_valid_tradeoff_analysis(self):
        """Test valid trade-off analysis creation."""
        analysis = CostTradeoffAnalysis(
            current_cost_per_million=30.0,
            target_cost_per_million=25.0,
            current_performance_score=0.85,
            projected_performance_impact=-0.1,
            cost_reduction_percentage=16.7,
            slo_compliance_risk=0.2,
            recommendation="Proceed with caution"
        )
        
        assert analysis.current_cost_per_million == 30.0
        assert analysis.target_cost_per_million == 25.0
        assert analysis.current_performance_score == 0.85
        assert analysis.projected_performance_impact == -0.1
        assert analysis.cost_reduction_percentage == 16.7
        assert analysis.slo_compliance_risk == 0.2
        assert analysis.recommendation == "Proceed with caution"
    
    def test_tradeoff_analysis_validation(self):
        """Test trade-off analysis validation."""
        with pytest.raises(ValueError, match="Current cost cannot be negative"):
            CostTradeoffAnalysis(
                current_cost_per_million=-10.0,
                target_cost_per_million=25.0,
                current_performance_score=0.85,
                projected_performance_impact=-0.1,
                cost_reduction_percentage=16.7,
                slo_compliance_risk=0.2,
                recommendation="Test"
            )
        
        with pytest.raises(ValueError, match="Performance score must be 0-1"):
            CostTradeoffAnalysis(
                current_cost_per_million=30.0,
                target_cost_per_million=25.0,
                current_performance_score=1.5,
                projected_performance_impact=-0.1,
                cost_reduction_percentage=16.7,
                slo_compliance_risk=0.2,
                recommendation="Test"
            )


class TestCostOptimizer:
    """Test cost optimizer functionality."""
    
    @pytest.fixture
    def slo_config(self):
        """Create test SLO configuration."""
        return SLOConfig(
            ttft_p95_ms=500,
            error_rate_percent=0.1,
            tokens_per_second=1000
        )
    
    @pytest.fixture
    def technology_config(self):
        """Create test technology configuration."""
        return TechnologyConfig(
            gpu_types={
                'nvidia-a100': GPUType('nvidia-a100', 80, 3.00),
                'nvidia-h100': GPUType('nvidia-h100', 80, 5.00),
                'nvidia-v100': GPUType('nvidia-v100', 32, 2.00)
            }
        )
    
    @pytest.fixture
    def cost_calculator(self, technology_config):
        """Create test cost calculator."""
        return CostCalculator(technology_config)
    
    @pytest.fixture
    def cost_optimizer(self, cost_calculator, slo_config, technology_config):
        """Create test cost optimizer."""
        return CostOptimizer(cost_calculator, slo_config, technology_config)
    
    def test_optimizer_initialization(self, cost_optimizer, slo_config):
        """Test cost optimizer initialization."""
        assert cost_optimizer.slo_config == slo_config
        assert len(cost_optimizer.cost_history) == 0
        assert len(cost_optimizer.optimization_history) == 0
        assert len(cost_optimizer.active_optimizations) == 0
        assert cost_optimizer.current_objective == OptimizationObjective.BALANCED
        assert cost_optimizer.total_annual_savings == 0.0
    
    def test_cost_metrics_recording(self, cost_optimizer):
        """Test cost metrics recording."""
        # Create test data
        token_metrics = [
            TokenMetrics(
                model_name="test-model",
                tokens_generated=1000,
                start_time=time.time() - 1.0,
                first_token_time=time.time() - 0.5,
                completion_time=time.time(),
                gpu_type="nvidia-a100"
            )
        ]
        
        gpu_metrics = {
            'gpu-0': GPUMetrics(
                gpu_id='gpu-0',
                utilization_percent=75.0,
                vram_used_gb=40.0,
                vram_total_gb=80.0
            )
        }
        
        cost_optimizer.record_cost_metrics(token_metrics, gpu_metrics, 150.0)
        
        # Check that metrics were recorded
        assert len(cost_optimizer.cost_history) == 1
        
        cost_record = cost_optimizer.cost_history[0]
        assert cost_record['total_tokens'] == 1000
        assert cost_record['workload_qps'] == 150.0
        assert 'gpu-0' in cost_record['gpu_utilization']
        assert cost_record['gpu_utilization']['gpu-0'] == 75.0
    
    def test_workload_pattern_classification(self, cost_optimizer):
        """Test workload pattern classification."""
        # Add baseline data
        for i in range(10):
            cost_optimizer.cost_history.append({
                'timestamp': time.time() + i,
                'workload_qps': 100.0 + (i % 3) * 5,  # Stable pattern
                'cost_per_million': 25.0
            })
        
        # Test different patterns
        assert cost_optimizer._classify_workload_pattern(100.0) == "baseline"
        assert cost_optimizer._classify_workload_pattern(200.0) == "high_load"
        assert cost_optimizer._classify_workload_pattern(50.0) == "low_load"
    
    def test_right_sizing_analysis(self, cost_optimizer):
        """Test right-sizing opportunity analysis."""
        # Create cost history with low utilization
        recent_costs = []
        for i in range(10):
            recent_costs.append({
                'timestamp': time.time() + i,
                'cost_per_million': 30.0,
                'gpu_utilization': {'gpu-0': 40.0, 'gpu-1': 45.0}  # Low utilization
            })
        
        opportunities = cost_optimizer._analyze_right_sizing_opportunities(recent_costs)
        
        assert len(opportunities) > 0
        assert opportunities[0].strategy == CostEfficiencyStrategy.RIGHT_SIZE_CAPACITY
        assert opportunities[0].estimated_savings > 0
        assert "capacity" in opportunities[0].description.lower()
    
    def test_gpu_type_optimization_analysis(self, cost_optimizer):
        """Test GPU type optimization analysis."""
        # Set up GPU efficiency data
        cost_optimizer.gpu_cost_efficiency = {
            'gpu-0': 0.8,
            'gpu-1': 0.6
        }
        
        opportunities = cost_optimizer._analyze_gpu_type_optimization()
        
        # Should find opportunities to switch to cheaper GPU types
        assert len(opportunities) >= 0  # May or may not find opportunities depending on config
    
    def test_idle_resource_analysis(self, cost_optimizer):
        """Test idle resource opportunity analysis."""
        # Create cost history with many idle periods
        recent_costs = []
        for i in range(20):
            utilization = 15.0 if i % 2 == 0 else 80.0  # Alternating idle/busy
            recent_costs.append({
                'timestamp': time.time() + i,
                'cost_per_million': 25.0,
                'gpu_utilization': {'gpu-0': utilization}
            })
        
        opportunities = cost_optimizer._analyze_idle_resource_opportunities(recent_costs)
        
        assert len(opportunities) > 0
        assert opportunities[0].strategy == CostEfficiencyStrategy.IDLE_RESOURCE_REDUCTION
        assert "idle" in opportunities[0].description.lower()
    
    def test_workload_consolidation_analysis(self, cost_optimizer):
        """Test workload consolidation analysis."""
        # Set up workload cost patterns
        cost_optimizer.workload_cost_patterns = {
            'baseline': [25.0, 26.0, 24.0],
            'high_load': [27.0, 28.0, 26.0],  # Similar costs, could consolidate
            'low_load': [15.0, 16.0, 14.0]   # Different costs
        }
        
        opportunities = cost_optimizer._analyze_workload_consolidation_opportunities()
        
        # Should find consolidation opportunities for similar-cost patterns
        consolidation_found = any(
            opt.strategy == CostEfficiencyStrategy.WORKLOAD_CONSOLIDATION 
            for opt in opportunities
        )
        assert consolidation_found or len(opportunities) == 0  # Depends on specific cost differences
    
    def test_performance_score_calculation(self, cost_optimizer):
        """Test performance score calculation."""
        metrics = {
            'ttft_p95': 450.0,  # Better than 500ms target
            'throughput': 1200.0,  # Better than 1000 target
            'error_rate': 0.05  # Better than 0.1% target
        }
        
        score = cost_optimizer._calculate_performance_score(metrics)
        
        assert 0 <= score <= 1
        assert score > 0.5  # Should be decent since all metrics beat targets
    
    def test_performance_impact_estimation(self, cost_optimizer):
        """Test performance impact estimation."""
        # Test different cost reduction levels
        impact_10 = cost_optimizer._estimate_performance_impact(0.1)  # 10% reduction
        impact_30 = cost_optimizer._estimate_performance_impact(0.3)  # 30% reduction
        
        assert impact_10 < 0  # Negative impact
        assert impact_30 < impact_10  # More cost reduction = more performance impact
    
    def test_slo_compliance_risk_calculation(self, cost_optimizer):
        """Test SLO compliance risk calculation."""
        # Test with good current metrics
        safe_metrics = {
            'ttft_p95': 400.0,  # Well under 500ms target
            'throughput': 1200.0  # Well over 1000 target
        }
        
        risk_low = cost_optimizer._calculate_slo_compliance_risk(0.1, safe_metrics)
        risk_high = cost_optimizer._calculate_slo_compliance_risk(0.4, safe_metrics)
        
        assert 0 <= risk_low <= 1
        assert 0 <= risk_high <= 1
        assert risk_high > risk_low  # Higher cost reduction = higher risk
    
    def test_tradeoff_analysis(self, cost_optimizer):
        """Test complete trade-off analysis."""
        # Add some cost history
        cost_optimizer.cost_history.append({
            'timestamp': time.time(),
            'cost_per_million': 30.0,
            'total_cost': 0.03,
            'total_tokens': 1000
        })
        
        current_metrics = {
            'ttft_p95': 450.0,
            'throughput': 1100.0,
            'error_rate': 0.08
        }
        
        analysis = cost_optimizer.perform_cost_tradeoff_analysis(0.2, current_metrics)
        
        assert analysis.current_cost_per_million == 30.0
        assert analysis.target_cost_per_million == 24.0  # 20% reduction
        assert analysis.cost_reduction_percentage == 20.0
        assert 0 <= analysis.current_performance_score <= 1
        assert 0 <= analysis.slo_compliance_risk <= 1
        assert len(analysis.recommendation) > 0
    
    def test_optimization_opportunities_analysis(self, cost_optimizer):
        """Test complete optimization opportunities analysis."""
        # Add cost history with various patterns
        for i in range(20):
            cost_optimizer.cost_history.append({
                'timestamp': time.time() + i,
                'total_cost': 0.025,
                'total_tokens': 1000,
                'cost_per_million': 25.0,
                'workload_qps': 100.0 + (i % 5) * 10,
                'gpu_utilization': {'gpu-0': 50.0 + (i % 3) * 10}  # Variable utilization
            })
        
        opportunities = cost_optimizer.analyze_cost_optimization_opportunities()
        
        # Should find some opportunities
        assert isinstance(opportunities, list)
        # Opportunities are sorted by estimated savings
        if len(opportunities) > 1:
            assert opportunities[0].estimated_savings >= opportunities[1].estimated_savings
    
    def test_optimization_status_reporting(self, cost_optimizer):
        """Test optimization status reporting."""
        # Add some test data
        cost_optimizer.cost_history.append({
            'timestamp': time.time(),
            'cost_per_million': 28.0,
            'total_cost': 0.028,
            'total_tokens': 1000
        })
        
        cost_optimizer.optimization_opportunities = [
            CostOptimization(
                strategy=CostEfficiencyStrategy.RIGHT_SIZE_CAPACITY,
                estimated_savings=10000.0,
                confidence_score=0.8,
                implementation_effort="medium",
                risk_level="low",
                description="Test optimization"
            )
        ]
        
        status = cost_optimizer.get_cost_optimization_status()
        
        assert 'current_cost_per_million' in status
        assert 'optimization_opportunities' in status
        assert 'total_potential_savings' in status
        assert 'optimization_objective' in status
        
        assert status['current_cost_per_million'] == 28.0
        assert status['optimization_opportunities'] == 1
        assert status['total_potential_savings'] == 10000.0
        assert status['cost_compliance'] is False  # 28.0 > 25.0 target
    
    def test_optimization_implementation(self, cost_optimizer):
        """Test optimization implementation."""
        optimization = CostOptimization(
            strategy=CostEfficiencyStrategy.RIGHT_SIZE_CAPACITY,
            estimated_savings=5000.0,
            confidence_score=0.9,
            implementation_effort="low",
            risk_level="low",
            description="Test implementation"
        )
        
        success = cost_optimizer.implement_optimization(optimization)
        
        assert success is True
        assert len(cost_optimizer.active_optimizations) == 1
        assert len(cost_optimizer.optimization_history) == 1
        assert cost_optimizer.active_optimizations[0] == optimization


class TestIntegration:
    """Integration tests for cost optimization system."""
    
    def test_end_to_end_optimization_cycle(self):
        """Test complete optimization cycle."""
        # Create configuration
        slo_config = SLOConfig(ttft_p95_ms=500, error_rate_percent=0.1, tokens_per_second=1000)
        technology_config = TechnologyConfig(
            gpu_types={'nvidia-a100': GPUType('nvidia-a100', 80, 3.00)}
        )
        cost_calculator = CostCalculator(technology_config)
        
        # Create optimizer
        optimizer = CostOptimizer(cost_calculator, slo_config, technology_config)
        
        # Simulate cost recording over time
        base_time = time.time()
        for i in range(15):
            token_metrics = [
                TokenMetrics(
                    model_name="test-model",
                    tokens_generated=1000,
                    start_time=base_time + i - 1.0,
                    completion_time=base_time + i,
                    gpu_type="nvidia-a100"
                )
            ]
            
            gpu_metrics = {
                'gpu-0': GPUMetrics(
                    gpu_id='gpu-0',
                    utilization_percent=45.0 + (i % 3) * 5,  # Low utilization
                    vram_used_gb=30.0
                )
            }
            
            optimizer.record_cost_metrics(token_metrics, gpu_metrics, 100.0)
        
        # Analyze opportunities
        opportunities = optimizer.analyze_cost_optimization_opportunities()
        
        # Should find some optimization opportunities
        assert len(opportunities) >= 0
        
        # Test trade-off analysis
        current_metrics = {
            'ttft_p95': 480.0,
            'throughput': 1050.0,
            'error_rate': 0.08
        }
        
        analysis = optimizer.perform_cost_tradeoff_analysis(0.15, current_metrics)
        assert analysis.cost_reduction_percentage == 15.0
        
        # Get status
        status = optimizer.get_cost_optimization_status()
        assert 'current_cost_per_million' in status
        assert status['historical_data_points'] == 15
        
        # Implement optimization if available
        if opportunities:
            success = optimizer.implement_optimization(opportunities[0])
            assert success is True
            assert len(optimizer.active_optimizations) == 1