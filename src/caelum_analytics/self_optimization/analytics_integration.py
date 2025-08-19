"""
Analytics Integration for Self-Optimization System

This module integrates our dynamic analytics, server explorer, and web interface
with the self-optimization system to provide comprehensive insights and real-time
adaptation capabilities.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from ..dynamic_server_explorer import dynamic_explorer
from .self_observer import self_observer
from .performance_monitor import performance_monitor
from .caelum_integration import caelum_self_optimizer

logger = logging.getLogger(__name__)

class OptimizedAnalytics:
    """Enhanced analytics system with self-optimization integration"""
    
    def __init__(self):
        self.optimization_insights: Dict[str, Any] = {}
        self.server_performance_map: Dict[str, Dict[str, float]] = {}
        self.tool_effectiveness_scores: Dict[str, float] = {}
        self.workflow_efficiency_metrics: Dict[str, Dict[str, Any]] = {}
        self.real_time_adaptations: List[Dict[str, Any]] = []
        
    async def initialize_enhanced_analytics(self):
        """Initialize enhanced analytics with self-optimization data"""
        
        # Initialize dynamic explorer
        await dynamic_explorer.initialize()
        
        # Enhance with optimization data
        await self._enhance_server_data_with_optimization()
        await self._calculate_tool_effectiveness_scores()
        await self._analyze_workflow_efficiency()
        
        logger.info("🔬 Enhanced analytics initialized with self-optimization data")
        
    async def _enhance_server_data_with_optimization(self):
        """Enhance server data with optimization metrics"""
        
        # Get current performance data
        performance_data = performance_monitor.get_performance_summary()
        observer_data = self_observer.get_self_analysis()
        
        for server_name, server_info in dynamic_explorer.servers.items():
            # Calculate server-specific performance metrics
            self.server_performance_map[server_name] = {
                'success_rate': self._calculate_server_success_rate(server_name, observer_data),
                'response_time': self._calculate_server_response_time(server_name),
                'error_rate': self._calculate_server_error_rate(server_name),
                'optimization_potential': self._assess_optimization_potential(server_name),
                'tool_efficiency': self._calculate_tool_efficiency(server_name)
            }
            
    def _calculate_server_success_rate(self, server_name: str, observer_data: Dict[str, Any]) -> float:
        """Calculate success rate for a specific server based on tool usage"""
        
        # Get tools for this server
        server_tools = [tool.name for tool in dynamic_explorer.tools.values() 
                       if tool.underlying_service == server_name]
        
        # Calculate success rate based on task performance
        task_performance = observer_data.get('task_type_performance', {})
        
        # Map server to likely task types (simplified)
        server_task_mapping = {
            'caelum-development-workflow': ['development', 'coding', 'analysis'],
            'caelum-business-workflow': ['business', 'research', 'intelligence'],
            'caelum-infrastructure-workflow': ['infrastructure', 'deployment', 'orchestration'],
            'caelum-communication-workflow': ['communication', 'notification', 'knowledge'],
            'caelum-security-workflow': ['security', 'compliance', 'audit']
        }
        
        relevant_tasks = server_task_mapping.get(server_name, [])
        
        success_rates = []
        for task_type, performance in task_performance.items():
            if any(keyword in task_type.lower() for keyword in relevant_tasks):
                success_rates.append(performance.get('success_rate', 0.8))
                
        return sum(success_rates) / len(success_rates) if success_rates else 0.85
        
    def _calculate_server_response_time(self, server_name: str) -> float:
        """Calculate average response time for server (simulated based on complexity)"""
        
        server_info = dynamic_explorer.servers.get(server_name)
        if not server_info:
            return 30.0
            
        # Estimate based on tool count and complexity
        base_time = 15.0  # Base response time
        tool_complexity = server_info.tool_count * 2.5  # More tools = slightly more time
        
        # Workflow servers are optimized, so they're faster
        if server_info.type == 'workflow':
            return base_time + (tool_complexity * 0.3)
        else:
            return base_time + tool_complexity
            
    def _calculate_server_error_rate(self, server_name: str) -> float:
        """Calculate error rate for server (based on optimization data)"""
        
        # Get alerts related to this server
        active_alerts = performance_monitor.get_active_alerts()
        server_alerts = [alert for alert in active_alerts 
                        if server_name in alert.message or any(server_name in action for action in alert.suggested_actions)]
        
        # Base error rate is low for optimized workflow servers
        base_error_rate = 0.02 if 'workflow' in server_name else 0.05
        
        # Increase based on alerts
        alert_penalty = len(server_alerts) * 0.01
        
        return min(0.15, base_error_rate + alert_penalty)
        
    def _assess_optimization_potential(self, server_name: str) -> float:
        """Assess optimization potential for a server (0.0-1.0)"""
        
        server_metrics = self.server_performance_map.get(server_name, {})
        
        success_rate = server_metrics.get('success_rate', 0.85)
        error_rate = server_metrics.get('error_rate', 0.05)
        
        # Higher potential if performance is below optimal
        potential = 0.0
        
        if success_rate < 0.9:
            potential += (0.9 - success_rate) * 2  # Scale success rate impact
            
        if error_rate > 0.03:
            potential += error_rate * 10  # Scale error rate impact
            
        return min(1.0, potential)
        
    def _calculate_tool_efficiency(self, server_name: str) -> float:
        """Calculate tool efficiency for server"""
        
        server_info = dynamic_explorer.servers.get(server_name)
        if not server_info:
            return 1.0
            
        # Base efficiency for workflow servers is higher
        base_efficiency = 2.5 if server_info.type == 'workflow' else 1.8
        
        # Adjust based on tool count (fewer tools per server = higher efficiency)
        tool_penalty = max(0, (server_info.tool_count - 15) * 0.05)
        
        return max(0.5, base_efficiency - tool_penalty)
        
    async def _calculate_tool_effectiveness_scores(self):
        """Calculate effectiveness scores for individual tools"""
        
        observer_data = self_observer.get_self_analysis()
        tool_usage = observer_data.get('tool_usage_patterns', {}).get('top_tools', [])
        
        # Calculate effectiveness based on usage frequency and success
        for tool_name, tool_info in dynamic_explorer.tools.items():
            # Find usage data
            usage_count = 0
            for tool, count in tool_usage:
                if tool == tool_name:
                    usage_count = count
                    break
                    
            # Calculate effectiveness score
            base_score = tool_info.priority / 10.0  # Priority as base score
            usage_boost = min(0.3, usage_count * 0.02)  # Usage frequency boost
            
            effectiveness = base_score + usage_boost
            self.tool_effectiveness_scores[tool_name] = effectiveness
            
    async def _analyze_workflow_efficiency(self):
        """Analyze efficiency of different workflows"""
        
        for workflow_name, workflow_info in dynamic_explorer.workflows.items():
            
            # Calculate metrics for this workflow
            servers_involved = workflow_info.servers_involved
            avg_server_performance = 0.0
            
            for server_name in servers_involved:
                server_perf = self.server_performance_map.get(server_name, {})
                success_rate = server_perf.get('success_rate', 0.8)
                response_time = server_perf.get('response_time', 30.0)
                
                # Normalize and combine metrics
                perf_score = success_rate * (60.0 / max(response_time, 1.0))  # 60s as baseline
                avg_server_performance += perf_score
                
            avg_server_performance /= len(servers_involved) if servers_involved else 1
            
            self.workflow_efficiency_metrics[workflow_name] = {
                'efficiency_score': avg_server_performance,
                'servers_count': len(servers_involved),
                'tools_count': workflow_info.tools_count,
                'complexity_factor': {'simple': 1.0, 'moderate': 0.8, 'complex': 0.6}.get(workflow_info.complexity, 0.8),
                'optimization_priority': self._calculate_workflow_optimization_priority(workflow_name, avg_server_performance)
            }
            
    def _calculate_workflow_optimization_priority(self, workflow_name: str, performance: float) -> int:
        """Calculate optimization priority for workflow (1-10)"""
        
        if performance > 0.9:
            return 2  # Low priority - already performing well
        elif performance > 0.7:
            return 5  # Medium priority
        else:
            return 8  # High priority - needs optimization
            
    async def get_enhanced_ecosystem_analysis(self) -> Dict[str, Any]:
        """Get comprehensive ecosystem analysis with optimization insights"""
        
        # Get base ecosystem data
        base_hierarchy = dynamic_explorer.get_server_hierarchy(expand_tools=True)
        
        # Enhance with optimization data
        enhanced_analysis = {
            'ecosystem_overview': base_hierarchy,
            'optimization_insights': {
                'server_performance': self.server_performance_map,
                'tool_effectiveness': self.tool_effectiveness_scores,
                'workflow_efficiency': self.workflow_efficiency_metrics
            },
            'recommendations': await self._generate_ecosystem_recommendations(),
            'adaptation_opportunities': await self._identify_adaptation_opportunities(),
            'performance_trends': self._analyze_performance_trends(),
            'optimization_impact': self._calculate_optimization_impact()
        }
        
        return enhanced_analysis
        
    async def _generate_ecosystem_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for ecosystem optimization"""
        
        recommendations = []
        
        # Analyze server performance
        for server_name, metrics in self.server_performance_map.items():
            
            optimization_potential = metrics.get('optimization_potential', 0)
            
            if optimization_potential > 0.3:  # High optimization potential
                recommendations.append({
                    'type': 'server_optimization',
                    'target': server_name,
                    'priority': int(optimization_potential * 10),
                    'title': f"Optimize {server_name} Performance",
                    'description': f"Server shows {optimization_potential:.1%} optimization potential",
                    'expected_impact': f"Improve success rate by {optimization_potential * 50:.1f}%",
                    'actions': [
                        f"Review tool selection strategy for {server_name}",
                        "Implement error reduction measures",
                        "Optimize response time through caching"
                    ]
                })
                
        # Analyze workflow efficiency
        for workflow_name, metrics in self.workflow_efficiency_metrics.items():
            
            priority = metrics.get('optimization_priority', 5)
            
            if priority >= 7:  # High priority workflows
                recommendations.append({
                    'type': 'workflow_optimization',
                    'target': workflow_name,
                    'priority': priority,
                    'title': f"Enhance {workflow_name} Efficiency",
                    'description': f"Workflow efficiency score: {metrics['efficiency_score']:.2f}",
                    'expected_impact': "Improve workflow completion time and success rate",
                    'actions': [
                        "Streamline server coordination",
                        "Optimize tool selection within workflow",
                        "Reduce complexity where possible"
                    ]
                })
                
        # Sort by priority
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return recommendations[:10]  # Top 10 recommendations
        
    async def _identify_adaptation_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for dynamic adaptation"""
        
        opportunities = []
        
        # Check for underutilized high-effectiveness tools
        sorted_tools = sorted(
            self.tool_effectiveness_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        high_effectiveness_tools = [tool for tool, score in sorted_tools[:10] if score > 0.7]
        observer_data = self_observer.get_self_analysis()
        used_tools = [tool for tool, count in observer_data.get('tool_usage_patterns', {}).get('top_tools', [])]
        
        underutilized_tools = [tool for tool in high_effectiveness_tools if tool not in used_tools[:5]]
        
        if underutilized_tools:
            opportunities.append({
                'type': 'tool_utilization',
                'opportunity': 'Increase usage of high-effectiveness tools',
                'tools': underutilized_tools[:3],
                'potential_benefit': 'Improved task success rates',
                'adaptation_strategy': 'Update tool selection algorithm to prefer these tools'
            })
            
        # Check for server load balancing opportunities
        server_loads = {}
        for server_name, metrics in self.server_performance_map.items():
            response_time = metrics.get('response_time', 30.0)
            server_loads[server_name] = response_time
            
        # Identify heavily loaded servers
        avg_load = sum(server_loads.values()) / len(server_loads)
        heavy_servers = [server for server, load in server_loads.items() if load > avg_load * 1.5]
        
        if heavy_servers:
            opportunities.append({
                'type': 'load_balancing',
                'opportunity': 'Balance load across servers',
                'heavy_servers': heavy_servers,
                'potential_benefit': 'Improved response times across ecosystem',
                'adaptation_strategy': 'Implement intelligent routing to less loaded servers'
            })
            
        return opportunities
        
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends across the ecosystem"""
        
        # Get recent performance data
        performance_data = performance_monitor.get_performance_summary()
        
        trends = {
            'overall_trend': 'stable',  # stable, improving, declining
            'key_metrics': {},
            'concerning_areas': [],
            'positive_developments': []
        }
        
        # Analyze trending data
        trending = performance_data.get('trending_analysis', {})
        
        improving_count = 0
        declining_count = 0
        
        for metric, trend_data in trending.items():
            trend = trend_data.get('trend', 'stable')
            change_percent = trend_data.get('change_percent', 0)
            
            trends['key_metrics'][metric] = {
                'trend': trend,
                'change_percent': change_percent
            }
            
            if trend == 'improving':
                improving_count += 1
                if abs(change_percent) > 5:  # Significant improvement
                    trends['positive_developments'].append(f"{metric} improved by {change_percent:.1f}%")
                    
            elif trend == 'declining':
                declining_count += 1
                if abs(change_percent) > 5:  # Significant decline
                    trends['concerning_areas'].append(f"{metric} declined by {abs(change_percent):.1f}%")
                    
        # Determine overall trend
        if improving_count > declining_count:
            trends['overall_trend'] = 'improving'
        elif declining_count > improving_count:
            trends['overall_trend'] = 'declining'
            
        return trends
        
    def _calculate_optimization_impact(self) -> Dict[str, Any]:
        """Calculate the impact of optimization efforts"""
        
        # Get optimization history
        optimization_history = caelum_self_optimizer.get_optimization_history()
        
        impact = {
            'total_optimizations': len(optimization_history),
            'successful_optimizations': 0,
            'avg_improvement': 0.0,
            'most_effective_optimizations': [],
            'optimization_roi': 0.0
        }
        
        if not optimization_history:
            return impact
            
        successful_optimizations = [opt for opt in optimization_history if opt.get('success', False)]
        impact['successful_optimizations'] = len(successful_optimizations)
        
        # Calculate average improvement
        improvements = []
        for opt in successful_optimizations:
            phases = opt.get('phases', {})
            evaluation = phases.get('evaluation', {})
            success_rate = evaluation.get('success_rate', 0)
            if success_rate > 0:
                improvements.append(success_rate)
                
        if improvements:
            impact['avg_improvement'] = sum(improvements) / len(improvements)
            
        # Calculate ROI (simplified)
        if impact['total_optimizations'] > 0:
            impact['optimization_roi'] = impact['successful_optimizations'] / impact['total_optimizations']
            
        return impact
        
    async def generate_real_time_adaptation(self, trigger_event: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate real-time adaptation based on current state and trigger event"""
        
        adaptation = {
            'adaptation_id': f"adapt_{int(datetime.now().timestamp())}",
            'trigger_event': trigger_event,
            'timestamp': datetime.now().isoformat(),
            'analysis': await self._analyze_adaptation_need(context),
            'recommendations': await self._generate_adaptation_actions(context),
            'expected_impact': self._estimate_adaptation_impact(context),
            'confidence': self._calculate_adaptation_confidence(context)
        }
        
        self.real_time_adaptations.append(adaptation)
        
        # Keep only recent adaptations
        self.real_time_adaptations = self.real_time_adaptations[-50:]
        
        return adaptation
        
    async def _analyze_adaptation_need(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the need for adaptation based on context"""
        
        analysis = {
            'severity': 'low',  # low, medium, high, critical
            'affected_components': [],
            'root_cause': 'unknown',
            'adaptation_urgency': 1  # 1-10 scale
        }
        
        # Analyze context for patterns
        if 'performance_alert' in context:
            alert = context['performance_alert']
            analysis['severity'] = alert.get('severity', 'medium')
            analysis['affected_components'] = [alert.get('metric_name', 'unknown')]
            analysis['root_cause'] = 'performance_degradation'
            analysis['adaptation_urgency'] = {'low': 3, 'medium': 5, 'high': 8, 'critical': 10}.get(alert.get('severity', 'medium'), 5)
            
        return analysis
        
    async def _generate_adaptation_actions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific adaptation actions"""
        
        actions = []
        
        # Based on context, generate appropriate actions
        if 'performance_alert' in context:
            alert = context['performance_alert']
            metric = alert.get('metric_name', '')
            
            if 'success_rate' in metric:
                actions.append({
                    'action': 'adjust_tool_selection',
                    'description': 'Modify tool selection algorithm to prefer higher success rate tools',
                    'implementation': 'Update tool weighting in selection algorithm'
                })
                
            elif 'response_time' in metric:
                actions.append({
                    'action': 'enable_caching',
                    'description': 'Enable result caching for frequently used tools',
                    'implementation': 'Activate caching layer for top 10 most used tools'
                })
                
        return actions
        
    def _estimate_adaptation_impact(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate the impact of proposed adaptations"""
        
        return {
            'expected_improvement': 0.15,  # 15% improvement expected
            'risk_level': 'low',
            'time_to_effect': '5-10 minutes',
            'metrics_affected': ['success_rate', 'response_time'],
            'rollback_complexity': 'simple'
        }
        
    def _calculate_adaptation_confidence(self, context: Dict[str, Any]) -> float:
        """Calculate confidence in adaptation recommendation"""
        
        # Base confidence
        confidence = 0.7
        
        # Increase confidence based on historical data
        successful_adaptations = len([a for a in self.real_time_adaptations 
                                    if a.get('expected_impact', {}).get('expected_improvement', 0) > 0])
        
        if successful_adaptations > 5:
            confidence += 0.1
            
        return min(0.95, confidence)

# Global enhanced analytics instance
enhanced_analytics = OptimizedAnalytics()