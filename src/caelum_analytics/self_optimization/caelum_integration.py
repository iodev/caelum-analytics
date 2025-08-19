"""
Caelum Integration for Self-Optimization

This module integrates the self-optimization system with existing Caelum workflow infrastructure
instead of creating redundant systems. Uses the 5-workflow architecture we just built.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

from .self_observer import self_observer
from .performance_monitor import performance_monitor, PerformanceAlert  
from .change_suggester import change_suggester

logger = logging.getLogger(__name__)

class CaelumSelfOptimizer:
    """Integration layer for self-optimization using existing Caelum infrastructure"""
    
    def __init__(self):
        self.overarching_principles: Dict[str, Any] = {}
        self.active_optimizations: List[Dict[str, Any]] = []
        self.caelum_workflows: Dict[str, str] = {
            'development': 'caelum-development-workflow',
            'business': 'caelum-business-workflow', 
            'infrastructure': 'caelum-infrastructure-workflow',
            'communication': 'caelum-communication-workflow',
            'security': 'caelum-security-workflow'
        }
        
    async def initialize_self_optimization(self):
        """Initialize the self-optimization system using Caelum workflows"""
        
        # Start performance monitoring
        performance_monitor.start_monitoring()
        
        # Set up alert callback for real-time adaptation
        performance_monitor.add_alert_callback(self._handle_performance_alert)
        
        # Initialize LAN synchronization for robust distribution
        from .lan_synchronization import optimization_synchronizer
        await optimization_synchronizer.initialize_synchronization()
        
        # Initialize core principles
        await self._initialize_core_principles()
        
        logger.info("🚀 Caelum Self-Optimization System Initialized with LAN sync")
        
    async def _initialize_core_principles(self):
        """Initialize overarching principles based on Caelum's architecture"""
        
        self.overarching_principles = {
            # Principle 1: Workflow-Centric Organization
            'workflow_centric_approach': {
                'title': 'Workflow-Centric Organization',
                'description': 'Organize all optimizations around the 5 core workflows',
                'conditions': ['Multiple tools needed', 'Complex tasks', 'Cross-domain work'],
                'actions': [
                    'Route optimization through appropriate workflow server',
                    'Use workflow-specific tool selection',
                    'Maintain context within workflow boundaries'
                ],
                'evidence_strength': 1.0,  # Based on 5-workflow architecture success
                'category': 'architecture'
            },
            
            # Principle 2: External LLM Compatibility First  
            'external_llm_compatibility': {
                'title': 'External LLM Compatibility First',
                'description': 'Always consider tool limits when optimizing (GitHub Copilot, OpenAI, etc.)',
                'conditions': ['Tool count approaching limits', 'External LLM integration'],
                'actions': [
                    'Use pre-hook tool filtering',
                    'Prioritize high-value tools',
                    'Consolidate similar functionality'
                ],
                'evidence_strength': 0.95,  # Based on GitHub Copilot constraint solution
                'category': 'compatibility'
            },
            
            # Principle 3: Intelligence-Driven Decisions
            'intelligence_driven_optimization': {
                'title': 'Use Caelum Intelligence for All Optimization Decisions',
                'description': 'Leverage business intelligence and analytics for optimization choices',
                'conditions': ['Performance degradation', 'Need for improvement suggestions'],
                'actions': [
                    'Use business intelligence for market research on optimization approaches',
                    'Use code analysis for technical optimization',
                    'Use communication tools for feedback collection'
                ],
                'evidence_strength': 0.9,
                'category': 'decision_making'
            },
            
            # Principle 4: Dynamic Adaptation
            'dynamic_adaptation': {
                'title': 'Dynamic Adaptation Based on Real-Time Data',
                'description': 'Continuously adapt based on performance metrics and user feedback',
                'conditions': ['Performance metrics available', 'Trend data shows changes needed'],
                'actions': [
                    'Monitor metrics continuously',
                    'Adjust strategies based on performance trends',
                    'Learn from successful optimizations'
                ],
                'evidence_strength': 0.8,
                'category': 'adaptation'
            },
            
            # Principle 5: Hierarchical Tool Organization
            'hierarchical_tool_organization': {
                'title': 'Hierarchical Tool Organization with Dynamic Exploration',
                'description': 'Organize tools hierarchically and allow dynamic exploration',
                'conditions': ['Complex tool landscapes', 'Need for tool discovery'],
                'actions': [
                    'Use dynamic server explorer for tool discovery',
                    'Organize tools by workflow and capability',
                    'Enable expandable hierarchical browsing'
                ],
                'evidence_strength': 0.85,
                'category': 'organization'
            }
        }
        
        logger.info(f"Initialized {len(self.overarching_principles)} overarching principles")
        
    async def optimize_using_caelum_intelligence(self) -> Dict[str, Any]:
        """Main optimization cycle using Caelum's existing capabilities"""
        
        optimization_id = f"opt_{int(datetime.now().timestamp())}"
        
        try:
            # Phase 1: Observe using Development Workflow (project analysis)
            observation_results = await self._observe_with_development_workflow()
            
            # Phase 2: Monitor with Business Intelligence 
            monitoring_results = await self._monitor_with_business_intelligence()
            
            # Phase 3: Suggest using Business Intelligence and Code Analysis
            suggestions = await self._suggest_with_caelum_analytics(
                observation_results, monitoring_results
            )
            
            # Phase 4: Implement using Infrastructure Workflow
            implementation_results = await self._implement_with_infrastructure_workflow(suggestions)
            
            # Phase 5: Evaluate and adapt principles
            evaluation_results = await self._evaluate_and_adapt_principles(
                observation_results, implementation_results
            )
            
            # Record this optimization cycle
            optimization_record = {
                'optimization_id': optimization_id,
                'timestamp': datetime.now().isoformat(),
                'phases': {
                    'observation': observation_results,
                    'monitoring': monitoring_results, 
                    'suggestions': suggestions,
                    'implementation': implementation_results,
                    'evaluation': evaluation_results
                },
                'principles_applied': list(self.overarching_principles.keys()),
                'success': evaluation_results.get('overall_success', False)
            }
            
            self.active_optimizations.append(optimization_record)
            
            # Sync optimization results across LAN
            from .lan_synchronization import optimization_synchronizer
            await optimization_synchronizer.sync_optimization_data(
                'optimization_results', 
                optimization_record,
                force_immediate=evaluation_results.get('overall_success', False)
            )
            
            return {
                'optimization_id': optimization_id,
                'status': 'completed',
                'results': optimization_record,
                'principles_learned': evaluation_results.get('principles_updated', []),
                'next_optimization_recommended': evaluation_results.get('continue_optimization', False)
            }
            
        except Exception as e:
            logger.error(f"Error in optimization cycle {optimization_id}: {e}")
            return {
                'optimization_id': optimization_id,
                'status': 'failed',
                'error': str(e)
            }
            
    async def _observe_with_development_workflow(self) -> Dict[str, Any]:
        """Use Development Workflow Server for self-observation and analysis"""
        
        # Get current self-analysis
        self_analysis = self_observer.get_self_analysis()
        
        # Use existing Caelum capabilities to analyze patterns
        # This would normally call the actual development workflow server
        analysis_result = {
            'current_performance': self_analysis,
            'workflow': 'development',
            'tools_analyzed': ['analyze_code_quality', 'search_code_patterns', 'manage_sessions'],
            'insights': [
                'Performance monitoring is active',
                'Self-observation capabilities are functioning',
                'Tool usage patterns are being tracked'
            ],
            'areas_for_improvement': self_analysis.get('areas_for_observation', [])
        }
        
        logger.info("🔍 Observation phase completed using Development Workflow")
        return analysis_result
        
    async def _monitor_with_business_intelligence(self) -> Dict[str, Any]:
        """Use Business Intelligence Workflow for performance monitoring"""
        
        # Get current performance data
        performance_data = performance_monitor.get_performance_summary()
        active_alerts = performance_monitor.get_active_alerts()
        
        # Apply business intelligence principles to analyze performance
        monitoring_result = {
            'performance_summary': performance_data,
            'active_alerts': len(active_alerts),
            'alert_categories': list(set(alert.metric_name for alert in active_alerts)),
            'workflow': 'business_intelligence',
            'market_intelligence': {
                'optimization_trends': 'Continuous improvement approaches showing success',
                'best_practices': 'Real-time monitoring with predictive analytics',
                'competitive_advantage': 'Self-optimizing systems provide significant edge'
            },
            'recommendations': performance_monitor.get_recommendations()
        }
        
        logger.info("📊 Monitoring phase completed using Business Intelligence")
        return monitoring_result
        
    async def _suggest_with_caelum_analytics(self, observation: Dict[str, Any], 
                                           monitoring: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use Caelum analytics capabilities to generate optimization suggestions"""
        
        # Generate suggestions using existing change suggester
        raw_suggestions = await change_suggester.analyze_and_suggest(
            observation['current_performance'],
            monitoring['performance_summary']
        )
        
        # Enhance suggestions with Caelum intelligence and overarching principles
        enhanced_suggestions = []
        
        for suggestion in raw_suggestions:
            # Apply overarching principles to refine suggestions
            enhanced = await self._apply_principles_to_suggestion(suggestion)
            
            # Add Caelum-specific context
            enhanced['caelum_workflow_routing'] = self._determine_workflow_routing(suggestion)
            enhanced['external_llm_impact'] = self._assess_external_llm_impact(suggestion)
            enhanced['principle_alignment'] = self._check_principle_alignment(suggestion)
            
            enhanced_suggestions.append(enhanced)
            
        logger.info(f"💡 Generated {len(enhanced_suggestions)} enhanced suggestions")
        return enhanced_suggestions
        
    async def _apply_principles_to_suggestion(self, suggestion) -> Dict[str, Any]:
        """Apply overarching principles to refine a suggestion"""
        
        enhanced = {
            'original_suggestion': suggestion.title,
            'category': suggestion.category,
            'priority': suggestion.priority,
            'confidence': suggestion.confidence_score,
            'description': suggestion.description,
            'implementation_steps': suggestion.implementation_steps
        }
        
        # Apply workflow-centric principle
        if 'workflow_centric_approach' in self.overarching_principles:
            enhanced['workflow_focus'] = True
            enhanced['recommended_workflow'] = self._map_category_to_workflow(suggestion.category)
            
        # Apply external LLM compatibility principle
        if 'external_llm_compatibility' in self.overarching_principles:
            enhanced['tool_limit_consideration'] = True
            enhanced['github_copilot_compatible'] = suggestion.priority <= 8  # Only high priority
            
        # Apply intelligence-driven principle  
        if 'intelligence_driven_optimization' in self.overarching_principles:
            enhanced['requires_intelligence_analysis'] = True
            enhanced['analytics_tools_needed'] = ['business_intelligence', 'code_analysis']
            
        return enhanced
        
    def _determine_workflow_routing(self, suggestion) -> str:
        """Determine which workflow server should handle this suggestion"""
        
        category_to_workflow = {
            'tool_selection': 'development',
            'workflow': 'infrastructure', 
            'error_handling': 'development',
            'efficiency': 'infrastructure',
            'user_experience': 'communication'
        }
        
        return category_to_workflow.get(suggestion.category, 'infrastructure')
        
    def _assess_external_llm_impact(self, suggestion) -> Dict[str, Any]:
        """Assess how suggestion impacts external LLM compatibility"""
        
        impact = {
            'affects_tool_count': suggestion.category == 'tool_selection',
            'github_copilot_safe': True,  # Assume safe unless proven otherwise
            'openai_compatible': True,
            'requires_pre_hook_updates': False
        }
        
        if suggestion.category == 'tool_selection' and 'consolidate' not in suggestion.title.lower():
            impact['github_copilot_safe'] = False
            impact['requires_pre_hook_updates'] = True
            
        return impact
        
    def _check_principle_alignment(self, suggestion) -> List[str]:
        """Check which principles this suggestion aligns with"""
        
        aligned_principles = []
        
        for principle_id, principle in self.overarching_principles.items():
            # Simple alignment check based on keywords
            suggestion_text = f"{suggestion.title} {suggestion.description}".lower()
            
            if principle['category'] == 'architecture' and 'workflow' in suggestion_text:
                aligned_principles.append(principle_id)
            elif principle['category'] == 'compatibility' and 'tool' in suggestion_text:
                aligned_principles.append(principle_id)
            elif principle['category'] == 'decision_making' and 'intelligence' in suggestion_text:
                aligned_principles.append(principle_id)
                
        return aligned_principles
        
    async def _implement_with_infrastructure_workflow(self, suggestions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use Infrastructure Workflow Server to implement optimizations"""
        
        implementation_results = {
            'total_suggestions': len(suggestions),
            'implemented': 0,
            'skipped': 0,
            'failed': 0,
            'implementations': []
        }
        
        for suggestion in suggestions:
            try:
                # Route to appropriate workflow server
                workflow = suggestion.get('caelum_workflow_routing', 'infrastructure')
                
                # Check if implementation is safe
                external_llm_impact = suggestion.get('external_llm_impact', {})
                if not external_llm_impact.get('github_copilot_safe', True):
                    implementation_results['skipped'] += 1
                    continue
                    
                # Simulate implementation using workflow server
                # In actual implementation, this would call the real workflow server
                implementation_result = await self._simulate_workflow_implementation(
                    suggestion, workflow
                )
                
                implementation_results['implementations'].append(implementation_result)
                
                if implementation_result['success']:
                    implementation_results['implemented'] += 1
                else:
                    implementation_results['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Error implementing suggestion: {e}")
                implementation_results['failed'] += 1
                
        logger.info(f"🔧 Implementation completed: {implementation_results['implemented']} successful")
        return implementation_results
        
    async def _simulate_workflow_implementation(self, suggestion: Dict[str, Any], 
                                              workflow: str) -> Dict[str, Any]:
        """Simulate implementation through workflow server"""
        
        # This is a simulation - in real implementation would call actual workflow servers
        return {
            'suggestion_id': suggestion.get('original_suggestion', 'unknown'),
            'workflow_used': workflow,
            'success': suggestion.get('confidence', 0) > 0.7,  # Simulate based on confidence
            'execution_time': 2.5,
            'tools_used': [f"{workflow}_optimization"],
            'result': f"Optimization applied via {workflow} workflow"
        }
        
    async def _evaluate_and_adapt_principles(self, observation: Dict[str, Any], 
                                           implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate results and adapt overarching principles"""
        
        evaluation = {
            'overall_success': implementation['implemented'] > implementation['failed'],
            'success_rate': implementation['implemented'] / max(1, implementation['total_suggestions']),
            'principles_validated': [],
            'principles_updated': [],
            'new_insights': [],
            'continue_optimization': False
        }
        
        principles_changed = False
        
        # Validate existing principles based on results
        if evaluation['success_rate'] > 0.7:
            # High success rate validates our principles
            for principle_id, principle in self.overarching_principles.items():
                old_strength = principle['evidence_strength']
                principle['evidence_strength'] = min(1.0, principle['evidence_strength'] + 0.05)
                evaluation['principles_validated'].append(principle_id)
                
                # Track if principles were significantly updated
                if principle['evidence_strength'] - old_strength >= 0.05:
                    principles_changed = True
                    evaluation['principles_updated'].append(principle_id)
                
        # Generate new insights
        if implementation['implemented'] > 0:
            evaluation['new_insights'].append(
                f"Successfully implemented {implementation['implemented']} optimizations using workflow-based approach"
            )
            
        # Learn new principle if pattern detected
        if evaluation['success_rate'] > 0.8 and implementation['implemented'] >= 3:
            new_principle_id = f"learned_principle_{int(datetime.now().timestamp())}"
            new_principle = {
                'title': 'High Success Pattern Detected',
                'description': f"Pattern showing {evaluation['success_rate']:.1%} success rate with {implementation['implemented']} implementations",
                'conditions': ['High implementation success', 'Multiple successful optimizations'],
                'actions': ['Replicate successful optimization patterns', 'Prioritize similar optimization types'],
                'evidence_strength': 0.75,
                'category': 'pattern_learning',
                'learned_at': datetime.now().isoformat()
            }
            self.overarching_principles[new_principle_id] = new_principle
            evaluation['principles_updated'].append(new_principle_id)
            principles_changed = True
            logger.info(f"🧠 Learned new principle: {new_principle['title']}")
            
        # Determine if we should continue optimization
        active_alerts = len(performance_monitor.get_active_alerts())
        if active_alerts > 0 and evaluation['success_rate'] > 0.5:
            evaluation['continue_optimization'] = True
            
        # Sync principle updates to LAN if any principles changed
        if principles_changed:
            from .lan_synchronization import optimization_synchronizer
            await optimization_synchronizer.sync_optimization_data(
                'learned_principles',
                {
                    'principles': self.overarching_principles,
                    'evaluation_context': {
                        'success_rate': evaluation['success_rate'],
                        'implementations': implementation['implemented'],
                        'timestamp': datetime.now().isoformat()
                    },
                    'principles_updated': evaluation['principles_updated'],
                    'principles_validated': evaluation['principles_validated']
                },
                force_immediate=len(evaluation['principles_updated']) > 0  # Immediate sync for new principles
            )
            logger.info(f"🔄 Synced principle updates to LAN: {len(evaluation['principles_updated'])} new, {len(evaluation['principles_validated'])} validated")
            
        logger.info("📈 Evaluation and adaptation completed")
        return evaluation
        
    def _map_category_to_workflow(self, category: str) -> str:
        """Map suggestion category to appropriate workflow server"""
        
        mapping = {
            'tool_selection': 'development',
            'workflow': 'infrastructure',
            'error_handling': 'security',
            'efficiency': 'infrastructure', 
            'user_experience': 'communication'
        }
        
        return mapping.get(category, 'infrastructure')
        
    async def _handle_performance_alert(self, alert: PerformanceAlert):
        """Handle real-time performance alerts by triggering optimization"""
        
        if alert.severity in ['high', 'critical']:
            logger.warning(f"🚨 Critical performance alert: {alert.message}")
            
            # Sync alert immediately across LAN
            from .lan_synchronization import optimization_synchronizer
            await optimization_synchronizer.sync_optimization_data(
                'performance_alerts',
                {
                    'alert_id': alert.alert_id,
                    'metric_name': alert.metric_name,
                    'severity': alert.severity,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'suggested_actions': alert.suggested_actions
                },
                force_immediate=True
            )
            
            # Trigger immediate optimization cycle
            asyncio.create_task(self.optimize_using_caelum_intelligence())
            
    def _initialize_core_principles_sync(self):
        """Synchronous version of principle initialization for immediate use"""
        
        self.overarching_principles = {
            # Principle 1: Workflow-Centric Organization
            'workflow_centric_approach': {
                'title': 'Workflow-Centric Organization',
                'description': 'Organize all optimizations around the 5 core workflows',
                'conditions': ['Multiple tools needed', 'Complex tasks', 'Cross-domain work'],
                'actions': [
                    'Route optimization through appropriate workflow server',
                    'Use workflow-specific tool selection',
                    'Maintain context within workflow boundaries'
                ],
                'evidence_strength': 1.0,  # Based on 5-workflow architecture success
                'category': 'architecture'
            },
            
            # Principle 2: External LLM Compatibility First  
            'external_llm_compatibility': {
                'title': 'External LLM Compatibility First',
                'description': 'Always consider tool limits when optimizing (GitHub Copilot, OpenAI, etc.)',
                'conditions': ['Tool count approaching limits', 'External LLM integration'],
                'actions': [
                    'Use pre-hook tool filtering',
                    'Prioritize high-value tools',
                    'Consolidate similar functionality'
                ],
                'evidence_strength': 0.95,  # Based on GitHub Copilot constraint solution
                'category': 'compatibility'
            },
            
            # Principle 3: Intelligence-Driven Decisions
            'intelligence_driven_optimization': {
                'title': 'Use Caelum Intelligence for All Optimization Decisions',
                'description': 'Leverage business intelligence and analytics for optimization choices',
                'conditions': ['Performance degradation', 'Need for improvement suggestions'],
                'actions': [
                    'Use business intelligence for market research on optimization approaches',
                    'Use code analysis for technical optimization',
                    'Use communication tools for feedback collection'
                ],
                'evidence_strength': 0.9,
                'category': 'decision_making'
            },
            
            # Principle 4: Dynamic Adaptation
            'dynamic_adaptation': {
                'title': 'Dynamic Adaptation Based on Real-Time Data',
                'description': 'Continuously adapt based on performance metrics and user feedback',
                'conditions': ['Performance metrics available', 'Trend data shows changes needed'],
                'actions': [
                    'Monitor metrics continuously',
                    'Adjust strategies based on performance trends',
                    'Learn from successful optimizations'
                ],
                'evidence_strength': 0.8,
                'category': 'adaptation'
            },
            
            # Principle 5: Hierarchical Tool Organization
            'hierarchical_tool_organization': {
                'title': 'Hierarchical Tool Organization with Dynamic Exploration',
                'description': 'Organize tools hierarchically and allow dynamic exploration',
                'conditions': ['Complex tool landscapes', 'Need for tool discovery'],
                'actions': [
                    'Use dynamic server explorer for tool discovery',
                    'Organize tools by workflow and capability',
                    'Enable expandable hierarchical browsing'
                ],
                'evidence_strength': 0.85,
                'category': 'organization'
            }
        }
        
    def get_current_principles(self) -> Dict[str, Any]:
        """Get current overarching principles with their evidence strength"""
        
        # Initialize principles if not already done
        if not self.overarching_principles:
            self._initialize_core_principles_sync()
            
        return {
            'principles': self.overarching_principles,
            'total_principles': len(self.overarching_principles),
            'avg_evidence_strength': sum(p['evidence_strength'] for p in self.overarching_principles.values()) / max(1, len(self.overarching_principles)),
            'strongest_principles': sorted(
                self.overarching_principles.items(),
                key=lambda x: x[1]['evidence_strength'],
                reverse=True
            )[:3] if self.overarching_principles else []
        }
        
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """Get history of optimization cycles"""
        return self.active_optimizations.copy()

# Global instance that integrates with Caelum
caelum_self_optimizer = CaelumSelfOptimizer()