"""
Comprehensive integration test for the complete self-optimization system
including LAN synchronization, dynamic analytics, and web dashboard.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from caelum_analytics.self_optimization.caelum_integration import caelum_self_optimizer
from caelum_analytics.self_optimization.lan_synchronization import optimization_synchronizer
from caelum_analytics.self_optimization.analytics_integration import enhanced_analytics
from caelum_analytics.dynamic_server_explorer import dynamic_explorer

class TestCompleteOptimizationSystem:
    """Test the complete self-optimization ecosystem"""
    
    @pytest.fixture
    async def setup_system(self):
        """Set up the complete optimization system for testing"""
        
        # Initialize all components
        await dynamic_explorer.initialize()
        await enhanced_analytics.initialize_enhanced_analytics()
        await caelum_self_optimizer.initialize_self_optimization()
        
        return {
            'optimizer': caelum_self_optimizer,
            'synchronizer': optimization_synchronizer,
            'analytics': enhanced_analytics,
            'explorer': dynamic_explorer
        }
    
    @pytest.mark.asyncio
    async def test_principle_learning_and_sync(self, setup_system):
        """Test that learned principles are automatically synced across LAN"""
        
        system = await setup_system
        optimizer = system['optimizer']
        
        # Mock LAN synchronization
        with patch.object(optimization_synchronizer, 'sync_optimization_data', new_callable=AsyncMock) as mock_sync:
            
            # Simulate a high-success optimization cycle that should learn new principles
            mock_observation = {
                'current_performance': {'success_rate': 0.9, 'areas_for_observation': []}
            }
            
            mock_monitoring = {
                'performance_summary': {'monitoring_status': 'active'},
                'active_alerts': [],
                'recommendations': []
            }
            
            # Mock implementation with high success rate
            with patch.object(optimizer, '_observe_with_development_workflow', return_value=mock_observation), \
                 patch.object(optimizer, '_monitor_with_business_intelligence', return_value=mock_monitoring), \
                 patch.object(optimizer, '_suggest_with_caelum_analytics', return_value=[
                     Mock(title='Test Optimization', category='efficiency', priority=8, confidence_score=0.85,
                          description='Test optimization suggestion', implementation_steps=['step1'])
                 ]), \
                 patch.object(optimizer, '_simulate_workflow_implementation', return_value={
                     'success': True, 'workflow_used': 'infrastructure', 'execution_time': 1.5
                 }):
                
                # Run optimization cycle
                result = await optimizer.optimize_using_caelum_intelligence()
                
                # Verify optimization was successful
                assert result['status'] == 'completed'
                assert 'principles_learned' in result
                
                # Verify LAN sync was called for principle updates
                mock_sync.assert_called()
                
                # Check that the sync call was for learned principles
                call_args = mock_sync.call_args[0]
                assert call_args[0] == 'learned_principles'  # data_type
                assert 'principles' in call_args[1]  # payload contains principles
    
    @pytest.mark.asyncio
    async def test_performance_alert_triggers_sync(self, setup_system):
        """Test that performance alerts trigger immediate LAN synchronization"""
        
        system = await setup_system
        optimizer = system['optimizer']
        
        # Mock performance alert
        mock_alert = Mock()
        mock_alert.alert_id = 'test_alert_123'
        mock_alert.metric_name = 'success_rate'
        mock_alert.severity = 'critical'
        mock_alert.message = 'Success rate dropped below 70%'
        mock_alert.timestamp = datetime.now()
        mock_alert.suggested_actions = ['Review tool selection', 'Check server health']
        
        with patch.object(optimization_synchronizer, 'sync_optimization_data', new_callable=AsyncMock) as mock_sync:
            
            # Handle performance alert
            await optimizer._handle_performance_alert(mock_alert)
            
            # Verify immediate sync was triggered
            mock_sync.assert_called_with(
                'performance_alerts',
                {
                    'alert_id': mock_alert.alert_id,
                    'metric_name': mock_alert.metric_name,
                    'severity': mock_alert.severity,
                    'message': mock_alert.message,
                    'timestamp': mock_alert.timestamp.isoformat(),
                    'suggested_actions': mock_alert.suggested_actions
                },
                force_immediate=True
            )
    
    @pytest.mark.asyncio
    async def test_analytics_integration_with_optimization(self, setup_system):
        """Test that dynamic analytics properly integrates with optimization system"""
        
        system = await setup_system
        analytics = system['analytics']
        
        # Test enhanced ecosystem analysis
        analysis = await analytics.get_enhanced_ecosystem_analysis()
        
        # Verify analysis contains optimization insights
        assert 'optimization_insights' in analysis
        assert 'server_performance' in analysis['optimization_insights']
        assert 'tool_effectiveness' in analysis['optimization_insights']
        assert 'workflow_efficiency' in analysis['optimization_insights']
        
        # Verify recommendations are generated
        assert 'recommendations' in analysis
        assert isinstance(analysis['recommendations'], list)
        
        # Verify adaptation opportunities identified
        assert 'adaptation_opportunities' in analysis
        assert isinstance(analysis['adaptation_opportunities'], list)
    
    @pytest.mark.asyncio
    async def test_lan_synchronization_robustness(self, setup_system):
        """Test LAN synchronization robustness and priority handling"""
        
        system = await setup_system
        synchronizer = system['synchronizer']
        
        # Test different priority sync operations
        test_data = {
            'test_metric': 'test_value',
            'timestamp': datetime.now().isoformat()
        }
        
        # Test critical priority sync
        await synchronizer.sync_optimization_data(
            'performance_alerts',
            test_data,
            force_immediate=True
        )
        
        # Test high priority sync
        await synchronizer.sync_optimization_data(
            'learned_principles',
            test_data
        )
        
        # Test medium priority sync
        await synchronizer.sync_optimization_data(
            'optimization_results',
            test_data
        )
        
        # Verify sync queue contains items
        status = synchronizer.get_sync_status()
        assert status['sync_active']
        assert 'sync_queue_size' in status
        assert 'known_nodes' in status
        assert 'active_nodes' in status
    
    @pytest.mark.asyncio
    async def test_real_time_adaptation_system(self, setup_system):
        """Test real-time adaptation capabilities"""
        
        system = await setup_system
        analytics = system['analytics']
        
        # Test adaptation generation
        trigger_event = 'performance_degradation'
        context = {
            'performance_alert': {
                'severity': 'high',
                'metric_name': 'success_rate',
                'message': 'Success rate declined to 65%'
            }
        }
        
        adaptation = await analytics.generate_real_time_adaptation(trigger_event, context)
        
        # Verify adaptation structure
        assert 'adaptation_id' in adaptation
        assert 'trigger_event' in adaptation
        assert 'analysis' in adaptation
        assert 'recommendations' in adaptation
        assert 'expected_impact' in adaptation
        assert 'confidence' in adaptation
        
        # Verify adaptation was recorded
        assert len(analytics.real_time_adaptations) > 0
        assert adaptation in analytics.real_time_adaptations
    
    def test_dynamic_server_explorer_integration(self, setup_system):
        """Test dynamic server explorer integration with optimization system"""
        
        system = setup_system
        explorer = system['explorer']
        
        # Test server hierarchy generation
        hierarchy = explorer.get_server_hierarchy(expand_tools=True)
        
        # Verify workflow servers are present
        assert 'workflow_servers' in hierarchy
        workflow_servers = hierarchy['workflow_servers']
        
        expected_workflows = [
            'caelum-development-workflow',
            'caelum-business-workflow', 
            'caelum-infrastructure-workflow',
            'caelum-communication-workflow',
            'caelum-security-workflow'
        ]
        
        for workflow_server in expected_workflows:
            assert workflow_server in workflow_servers
            server_info = workflow_servers[workflow_server]
            assert 'tools' in server_info
            assert 'capabilities' in server_info
            assert 'workflows' in server_info
        
        # Test capability search
        search_results = explorer.search_by_capability('analysis')
        assert 'servers' in search_results
        assert 'tools' in search_results
        assert 'workflows' in search_results
        
        # Test ecosystem map generation
        ecosystem_map = explorer.generate_ecosystem_map()
        assert 'ecosystem_overview' in ecosystem_map
        assert ecosystem_map['ecosystem_overview']['external_llm_compatible']
        assert ecosystem_map['ecosystem_overview']['max_tools_exposed'] <= 100  # GitHub Copilot limit
    
    @pytest.mark.asyncio
    async def test_end_to_end_optimization_cycle(self, setup_system):
        """Test complete end-to-end optimization cycle with all integrations"""
        
        system = await setup_system
        optimizer = system['optimizer']
        
        # Mock all external dependencies
        with patch.multiple(
            optimizer,
            _observe_with_development_workflow=AsyncMock(return_value={
                'current_performance': {'success_rate': 0.85},
                'workflow': 'development',
                'insights': ['System performing well']
            }),
            _monitor_with_business_intelligence=AsyncMock(return_value={
                'performance_summary': {'monitoring_status': 'active'},
                'active_alerts': 0,
                'workflow': 'business_intelligence'
            }),
            _suggest_with_caelum_analytics=AsyncMock(return_value=[
                Mock(title='Optimize Response Time', category='performance', priority=7,
                     confidence_score=0.8, description='Reduce average response time',
                     implementation_steps=['Enable caching', 'Optimize queries'])
            ]),
            _simulate_workflow_implementation=AsyncMock(return_value={
                'success': True, 'workflow_used': 'infrastructure'
            })
        ), patch.object(optimization_synchronizer, 'sync_optimization_data', new_callable=AsyncMock):
            
            # Run complete optimization cycle
            result = await optimizer.optimize_using_caelum_intelligence()
            
            # Verify successful completion
            assert result['status'] == 'completed'
            assert 'optimization_id' in result
            assert 'results' in result
            
            # Verify all phases completed
            phases = result['results']['phases']
            assert 'observation' in phases
            assert 'monitoring' in phases
            assert 'suggestions' in phases
            assert 'implementation' in phases
            assert 'evaluation' in phases
            
            # Verify optimization was recorded
            history = optimizer.get_optimization_history()
            assert len(history) > 0
    
    def test_overarching_principles_structure(self, setup_system):
        """Test that overarching principles have the correct structure"""
        
        system = setup_system
        optimizer = system['optimizer']
        
        principles = optimizer.get_current_principles()
        
        # Verify principles structure
        assert 'principles' in principles
        assert 'total_principles' in principles
        assert 'avg_evidence_strength' in principles
        assert 'strongest_principles' in principles
        
        # Verify individual principle structure
        for principle_id, principle in principles['principles'].items():
            assert 'title' in principle
            assert 'description' in principle
            assert 'conditions' in principle
            assert 'actions' in principle
            assert 'evidence_strength' in principle
            assert 'category' in principle
            
            # Verify evidence strength is within valid range
            assert 0.0 <= principle['evidence_strength'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, setup_system):
        """Test system health monitoring integration"""
        
        system = await setup_system
        
        # Import web dashboard functions
        from caelum_analytics.web.optimization_dashboard import (
            get_performance_dashboard, 
            get_lan_synchronization_status,
            get_optimization_ecosystem_overview
        )
        
        # Test performance dashboard
        dashboard_data = await get_performance_dashboard()
        
        assert 'system_health' in dashboard_data
        assert 'performance_metrics' in dashboard_data
        assert 'optimization_insights' in dashboard_data
        
        # Test LAN sync status
        sync_status = await get_lan_synchronization_status()
        
        assert 'sync_health' in sync_status
        assert 'priority_queue_analysis' in sync_status
        assert 'node_health_summary' in sync_status
        assert 'recommendations' in sync_status
        
        # Test ecosystem overview
        ecosystem_overview = await get_optimization_ecosystem_overview()
        
        assert 'system_architecture' in ecosystem_overview
        assert 'optimization_status' in ecosystem_overview
        assert 'lan_synchronization' in ecosystem_overview
        assert 'performance_metrics' in ecosystem_overview
        assert 'system_recommendations' in ecosystem_overview

if __name__ == '__main__':
    pytest.main([__file__, '-v'])