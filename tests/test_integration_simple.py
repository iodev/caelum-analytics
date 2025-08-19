"""
Simple integration test for the self-optimization system
"""

import pytest
import asyncio
from datetime import datetime

def test_dynamic_server_explorer():
    """Test dynamic server explorer basic functionality"""
    
    from caelum_analytics.dynamic_server_explorer import dynamic_explorer
    
    # Test basic initialization
    assert hasattr(dynamic_explorer, 'servers')
    assert hasattr(dynamic_explorer, 'tools')
    assert hasattr(dynamic_explorer, 'workflows')
    
    # Test server hierarchy without initialization
    hierarchy = dynamic_explorer.get_server_hierarchy()
    
    assert 'workflow_servers' in hierarchy
    assert 'individual_servers' in hierarchy
    assert 'core_servers' in hierarchy
    assert 'summary' in hierarchy

def test_optimization_synchronizer():
    """Test LAN synchronization basic functionality"""
    
    from caelum_analytics.self_optimization.lan_synchronization import optimization_synchronizer
    
    # Test sync status
    status = optimization_synchronizer.get_sync_status()
    
    assert 'sync_active' in status
    assert 'instance_id' in status
    assert 'optimization_version' in status
    assert 'known_nodes' in status
    assert 'sync_queue_size' in status

def test_caelum_optimizer():
    """Test Caelum self optimizer basic functionality"""
    
    from caelum_analytics.self_optimization.caelum_integration import caelum_self_optimizer
    
    # Test principles structure
    principles = caelum_self_optimizer.get_current_principles()
    
    assert 'principles' in principles
    assert 'total_principles' in principles
    assert isinstance(principles['principles'], dict)
    assert principles['total_principles'] >= 0
    
    # Test optimization history
    history = caelum_self_optimizer.get_optimization_history()
    assert isinstance(history, list)

def test_enhanced_analytics():
    """Test enhanced analytics basic functionality"""
    
    from caelum_analytics.self_optimization.analytics_integration import enhanced_analytics
    
    # Test basic structure
    assert hasattr(enhanced_analytics, 'server_performance_map')
    assert hasattr(enhanced_analytics, 'tool_effectiveness_scores')
    assert hasattr(enhanced_analytics, 'workflow_efficiency_metrics')
    assert hasattr(enhanced_analytics, 'real_time_adaptations')
    
    # Test data structures are proper types
    assert isinstance(enhanced_analytics.server_performance_map, dict)
    assert isinstance(enhanced_analytics.tool_effectiveness_scores, dict)
    assert isinstance(enhanced_analytics.workflow_efficiency_metrics, dict)
    assert isinstance(enhanced_analytics.real_time_adaptations, list)

@pytest.mark.asyncio
async def test_async_initialization():
    """Test async initialization of system components"""
    
    from caelum_analytics.dynamic_server_explorer import dynamic_explorer
    from caelum_analytics.self_optimization.analytics_integration import enhanced_analytics
    
    # Test dynamic explorer initialization
    await dynamic_explorer.initialize()
    
    # Verify servers were discovered
    assert len(dynamic_explorer.servers) > 0
    assert len(dynamic_explorer.tools) > 0
    assert len(dynamic_explorer.workflows) > 0
    
    # Test analytics initialization
    await enhanced_analytics.initialize_enhanced_analytics()
    
    # Verify analytics data was populated
    assert len(enhanced_analytics.server_performance_map) > 0

def test_web_dashboard_imports():
    """Test that web dashboard components can be imported"""
    
    try:
        from caelum_analytics.web.optimization_dashboard import router
        assert router is not None
    except ImportError as e:
        pytest.fail(f"Could not import optimization dashboard: {e}")

def test_lan_sync_priority_system():
    """Test LAN synchronization priority system"""
    
    from caelum_analytics.self_optimization.lan_synchronization import SyncPriority, optimization_synchronizer
    
    # Test priority enum
    assert SyncPriority.CRITICAL.value == "critical"
    assert SyncPriority.HIGH.value == "high"
    assert SyncPriority.MEDIUM.value == "medium"
    assert SyncPriority.LOW.value == "low"
    
    # Test sync intervals configuration
    assert hasattr(optimization_synchronizer, 'sync_intervals')
    assert SyncPriority.CRITICAL in optimization_synchronizer.sync_intervals
    assert optimization_synchronizer.sync_intervals[SyncPriority.CRITICAL] <= optimization_synchronizer.sync_intervals[SyncPriority.HIGH]

def test_overarching_principles_structure():
    """Test that overarching principles have correct structure"""
    
    from caelum_analytics.self_optimization.caelum_integration import caelum_self_optimizer
    
    # Trigger initialization by calling get_current_principles
    principles_info = caelum_self_optimizer.get_current_principles()
    principles = caelum_self_optimizer.overarching_principles
    
    # Should have at least the 5 core principles
    assert len(principles) >= 5
    
    expected_categories = ['architecture', 'compatibility', 'decision_making', 'adaptation', 'organization']
    found_categories = set(principle['category'] for principle in principles.values())
    
    for expected_category in expected_categories:
        assert expected_category in found_categories, f"Missing principle category: {expected_category}"
    
    # Test principle structure
    for principle_id, principle in principles.items():
        assert 'title' in principle
        assert 'description' in principle
        assert 'conditions' in principle
        assert 'actions' in principle
        assert 'evidence_strength' in principle
        assert 'category' in principle
        
        # Verify evidence strength is valid
        assert 0.0 <= principle['evidence_strength'] <= 1.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])