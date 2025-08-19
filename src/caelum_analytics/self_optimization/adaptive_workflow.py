"""
Adaptive Self-Optimization Workflow System

This module implements a complete self-improvement cycle that creates workflows from knowledge
and adapts them into overarching principles. Implements Phases 4 & 5: Implementation and Evaluation.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .self_observer import self_observer, TaskMetrics
from .performance_monitor import performance_monitor, PerformanceAlert
from .change_suggester import change_suggester, OptimizationSuggestion

logger = logging.getLogger(__name__)

class WorkflowPhase(Enum):
    OBSERVE = "observe"
    MONITOR = "monitor" 
    SUGGEST = "suggest"
    IMPLEMENT = "implement"
    EVALUATE = "evaluate"
    ADAPT = "adapt"

@dataclass
class AdaptationPrinciple:
    """An overarching principle learned from successful adaptations"""
    principle_id: str
    title: str
    description: str
    conditions: List[str]  # When to apply this principle
    actions: List[str]     # What actions to take
    success_rate: float    # Historical success rate
    confidence: float      # Confidence in principle
    evidence_count: int    # Number of successful applications
    last_updated: datetime
    category: str         # 'efficiency', 'accuracy', 'user_experience', 'workflow'

@dataclass
class WorkflowExecution:
    """Record of a complete workflow execution cycle"""
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime]
    phases_completed: List[WorkflowPhase]
    observations_collected: int
    alerts_generated: int
    suggestions_made: int
    implementations_attempted: int
    evaluations_completed: int
    overall_success: bool
    principles_learned: List[str]  # IDs of principles learned
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]

class AdaptiveWorkflow:
    """Complete self-optimization workflow that learns and adapts principles"""
    
    def __init__(self):
        self.principles: Dict[str, AdaptationPrinciple] = {}
        self.execution_history: List[WorkflowExecution] = []
        self.current_execution: Optional[WorkflowExecution] = None
        self.adaptation_callbacks: List[Callable[[AdaptationPrinciple], None]] = []
        self.workflow_rules: Dict[str, Any] = self._initialize_workflow_rules()
        self.learning_threshold = 0.8  # Minimum success rate to create principle
        
    def _initialize_workflow_rules(self) -> Dict[str, Any]:
        """Initialize basic workflow rules that can be adapted"""
        return {
            'observation_frequency': 'continuous',
            'monitoring_sensitivity': 'medium',
            'suggestion_threshold': 3,  # Minimum alerts before suggesting
            'implementation_confidence_threshold': 0.7,
            'evaluation_period_hours': 24,
            'adaptation_learning_rate': 0.1
        }
        
    async def start_optimization_cycle(self) -> str:
        """Start a complete optimization cycle"""
        execution_id = f"exec_{int(datetime.now().timestamp())}"
        
        # Capture baseline metrics
        observer_analysis = self_observer.get_self_analysis()
        performance_summary = performance_monitor.get_performance_summary()
        
        baseline_metrics = self._extract_baseline_metrics(observer_analysis, performance_summary)
        
        self.current_execution = WorkflowExecution(
            execution_id=execution_id,
            start_time=datetime.now(),
            end_time=None,
            phases_completed=[],
            observations_collected=0,
            alerts_generated=0,
            suggestions_made=0,
            implementations_attempted=0,
            evaluations_completed=0,
            overall_success=False,
            principles_learned=[],
            metrics_before=baseline_metrics,
            metrics_after={}
        )
        
        logger.info(f"Started optimization cycle: {execution_id}")
        
        # Execute the workflow phases
        await self._execute_workflow_phases()
        
        return execution_id
        
    async def _execute_workflow_phases(self):
        """Execute all phases of the optimization workflow"""
        if not self.current_execution:
            raise ValueError("No active execution")
            
        try:
            # Phase 1: Observe
            await self._phase_observe()
            
            # Phase 2: Monitor  
            await self._phase_monitor()
            
            # Phase 3: Suggest
            suggestions = await self._phase_suggest()
            
            # Phase 4: Implement
            if suggestions:
                await self._phase_implement(suggestions)
                
            # Phase 5: Evaluate
            await self._phase_evaluate()
            
            # Phase 6: Adapt (learn principles)
            await self._phase_adapt()
            
            # Complete execution
            self._complete_execution()
            
        except Exception as e:
            logger.error(f"Error in workflow execution: {e}")
            if self.current_execution:
                self.current_execution.overall_success = False
                self._complete_execution()
                
    async def _phase_observe(self):
        """Phase 1: Observe current behavior and performance"""
        if not self.current_execution:
            return
            
        logger.info("Phase 1: Observing behavior patterns")
        
        # Trigger comprehensive self-analysis
        analysis = self_observer.get_self_analysis()
        self.current_execution.observations_collected = len(analysis.get('areas_for_observation', []))
        self.current_execution.phases_completed.append(WorkflowPhase.OBSERVE)
        
        # Apply learned principles for observation
        await self._apply_principles('observation', analysis)
        
    async def _phase_monitor(self):
        """Phase 2: Monitor performance metrics and generate alerts"""
        if not self.current_execution:
            return
            
        logger.info("Phase 2: Monitoring performance metrics")
        
        # Ensure monitoring is active
        if not performance_monitor.monitoring_active:
            performance_monitor.start_monitoring()
            
        # Check for active alerts
        alerts = performance_monitor.get_active_alerts()
        self.current_execution.alerts_generated = len(alerts)
        self.current_execution.phases_completed.append(WorkflowPhase.MONITOR)
        
        # Apply learned principles for monitoring
        await self._apply_principles('monitoring', {'alerts': alerts})
        
    async def _phase_suggest(self) -> List[OptimizationSuggestion]:
        """Phase 3: Generate optimization suggestions"""
        if not self.current_execution:
            return []
            
        logger.info("Phase 3: Generating optimization suggestions")
        
        # Get current analysis data
        observer_data = self_observer.get_self_analysis()
        performance_data = performance_monitor.get_performance_summary()
        
        # Generate suggestions
        suggestions = await change_suggester.analyze_and_suggest(observer_data, performance_data)
        self.current_execution.suggestions_made = len(suggestions)
        self.current_execution.phases_completed.append(WorkflowPhase.SUGGEST)
        
        # Apply learned principles for suggestion filtering
        filtered_suggestions = await self._apply_principles('suggestion', {
            'suggestions': suggestions,
            'observer_data': observer_data,
            'performance_data': performance_data
        })
        
        return filtered_suggestions.get('filtered_suggestions', suggestions)
        
    async def _phase_implement(self, suggestions: List[OptimizationSuggestion]):
        """Phase 4: Implement selected suggestions"""
        if not self.current_execution:
            return
            
        logger.info("Phase 4: Implementing optimization suggestions")
        
        implemented_count = 0
        
        for suggestion in suggestions:
            # Check if suggestion meets implementation criteria
            if (suggestion.confidence_score >= self.workflow_rules['implementation_confidence_threshold'] 
                and suggestion.implementation_effort in ['low', 'medium']):
                
                success = await self._implement_suggestion(suggestion)
                if success:
                    implemented_count += 1
                    change_suggester.mark_suggestion_implemented(suggestion.suggestion_id)
                    
        self.current_execution.implementations_attempted = implemented_count
        self.current_execution.phases_completed.append(WorkflowPhase.IMPLEMENT)
        
    async def _implement_suggestion(self, suggestion: OptimizationSuggestion) -> bool:
        """Implement a specific optimization suggestion"""
        try:
            logger.info(f"Implementing suggestion: {suggestion.title}")
            
            # Route implementation based on category
            if suggestion.category == 'tool_selection':
                return await self._implement_tool_optimization(suggestion)
            elif suggestion.category == 'workflow':
                return await self._implement_workflow_optimization(suggestion)
            elif suggestion.category == 'error_handling':
                return await self._implement_error_handling_optimization(suggestion)
            elif suggestion.category == 'efficiency':
                return await self._implement_efficiency_optimization(suggestion)
            else:
                # Generic implementation
                return await self._implement_generic_optimization(suggestion)
                
        except Exception as e:
            logger.error(f"Error implementing suggestion {suggestion.suggestion_id}: {e}")
            return False
            
    async def _implement_tool_optimization(self, suggestion: OptimizationSuggestion) -> bool:
        """Implement tool-related optimizations"""
        # Update tool selection preferences based on suggestion
        if "consolidate" in suggestion.title.lower():
            self.workflow_rules['tool_selection_diversity'] = 0.7  # Reduce diversity
        elif "focus" in suggestion.title.lower():
            self.workflow_rules['prefer_proven_tools'] = True
            
        return True
        
    async def _implement_workflow_optimization(self, suggestion: OptimizationSuggestion) -> bool:
        """Implement workflow-related optimizations"""
        if "context switching" in suggestion.title.lower():
            self.workflow_rules['context_switch_penalty'] = 0.8  # Penalize context switches
        elif "task handling" in suggestion.title.lower():
            self.workflow_rules['task_specific_strategies'] = True
            
        return True
        
    async def _implement_error_handling_optimization(self, suggestion: OptimizationSuggestion) -> bool:
        """Implement error handling improvements"""
        if "error rate" in suggestion.title.lower():
            self.workflow_rules['error_prevention_enabled'] = True
            self.workflow_rules['validation_level'] = 'high'
            
        return True
        
    async def _implement_efficiency_optimization(self, suggestion: OptimizationSuggestion) -> bool:
        """Implement efficiency improvements"""
        if "response time" in suggestion.title.lower():
            self.workflow_rules['enable_caching'] = True
            self.workflow_rules['parallel_processing'] = True
        elif "tool efficiency" in suggestion.title.lower():
            self.workflow_rules['tool_result_caching'] = True
            
        return True
        
    async def _implement_generic_optimization(self, suggestion: OptimizationSuggestion) -> bool:
        """Generic optimization implementation"""
        # Add to workflow rules as configuration
        rule_key = f"optimization_{suggestion.category}_{suggestion.suggestion_id[-8:]}"
        self.workflow_rules[rule_key] = {
            'title': suggestion.title,
            'enabled': True,
            'confidence': suggestion.confidence_score,
            'implementation_date': datetime.now().isoformat()
        }
        
        return True
        
    async def _phase_evaluate(self):
        """Phase 5: Evaluate the effectiveness of implemented changes"""
        if not self.current_execution:
            return
            
        logger.info("Phase 5: Evaluating optimization effectiveness")
        
        # Wait a short period for changes to take effect
        await asyncio.sleep(2)
        
        # Collect post-implementation metrics
        observer_analysis = self_observer.get_self_analysis()
        performance_summary = performance_monitor.get_performance_summary()
        
        current_metrics = self._extract_baseline_metrics(observer_analysis, performance_summary)
        self.current_execution.metrics_after = current_metrics
        
        # Evaluate each implemented suggestion
        evaluations_completed = 0
        for suggestion_id in change_suggester.get_implemented_suggestions():
            if suggestion_id not in [s.suggestion_id for s in change_suggester.get_suggestion_history()]:
                continue
                
            evaluation = change_suggester.analyze_suggestion_success(
                suggestion_id, 
                self.current_execution.metrics_before,
                current_metrics
            )
            
            if evaluation and 'overall_success_rate' in evaluation:
                evaluations_completed += 1
                
        self.current_execution.evaluations_completed = evaluations_completed
        self.current_execution.phases_completed.append(WorkflowPhase.EVALUATE)
        
    async def _phase_adapt(self):
        """Phase 6: Learn principles from successful adaptations"""
        if not self.current_execution:
            return
            
        logger.info("Phase 6: Adapting and learning principles")
        
        # Analyze what worked and create/update principles
        success_patterns = self._analyze_success_patterns()
        
        for pattern in success_patterns:
            principle = await self._create_or_update_principle(pattern)
            if principle:
                self.current_execution.principles_learned.append(principle.principle_id)
                
                # Notify adaptation callbacks
                for callback in self.adaptation_callbacks:
                    try:
                        callback(principle)
                    except Exception as e:
                        logger.error(f"Error in adaptation callback: {e}")
                        
        self.current_execution.phases_completed.append(WorkflowPhase.ADAPT)
        
    def _analyze_success_patterns(self) -> List[Dict[str, Any]]:
        """Analyze patterns in successful optimizations"""
        patterns = []
        
        if not self.current_execution:
            return patterns
            
        # Compare before/after metrics to identify improvements
        before = self.current_execution.metrics_before
        after = self.current_execution.metrics_after
        
        improvements = []
        for metric, before_value in before.items():
            if metric in after:
                after_value = after[metric]
                
                # Determine improvement direction
                if metric in ['task_success_rate', 'tool_efficiency']:
                    improved = after_value > before_value
                    improvement = (after_value - before_value) / before_value if before_value > 0 else 0
                else:
                    improved = after_value < before_value
                    improvement = (before_value - after_value) / before_value if before_value > 0 else 0
                    
                if improved and improvement > 0.05:  # At least 5% improvement
                    improvements.append({
                        'metric': metric,
                        'improvement_percent': improvement * 100,
                        'before': before_value,
                        'after': after_value
                    })
                    
        # If we had significant improvements, analyze what caused them
        if len(improvements) >= 2:  # Multiple metrics improved
            patterns.append({
                'type': 'multi_metric_improvement',
                'improvements': improvements,
                'workflow_rules_at_time': self.workflow_rules.copy(),
                'success_rate': len(improvements) / len(before),
                'confidence': min(0.9, len(improvements) * 0.3)
            })
            
        return patterns
        
    async def _create_or_update_principle(self, pattern: Dict[str, Any]) -> Optional[AdaptationPrinciple]:
        """Create or update an adaptation principle from a success pattern"""
        
        if pattern['type'] == 'multi_metric_improvement':
            principle_id = f"multi_improvement_{pattern['success_rate']:.2f}"
            
            # Check if similar principle exists
            existing = self.principles.get(principle_id)
            
            if existing:
                # Update existing principle
                existing.evidence_count += 1
                existing.success_rate = (existing.success_rate * (existing.evidence_count - 1) + pattern['success_rate']) / existing.evidence_count
                existing.confidence = min(0.95, existing.confidence + 0.1)
                existing.last_updated = datetime.now()
                
                logger.info(f"Updated principle: {existing.title}")
                return existing
            else:
                # Create new principle
                principle = AdaptationPrinciple(
                    principle_id=principle_id,
                    title=f"Multi-Metric Optimization Strategy",
                    description=f"Applying workflow optimizations that improve multiple metrics simultaneously",
                    conditions=[
                        "Multiple performance metrics are below target",
                        "System confidence is high (>0.7)",
                        "Implementation effort is manageable"
                    ],
                    actions=[
                        "Implement multiple low-risk optimizations together",
                        "Monitor metrics for compound effects",
                        "Focus on workflow-level improvements over tool-specific changes"
                    ],
                    success_rate=pattern['success_rate'],
                    confidence=pattern['confidence'],
                    evidence_count=1,
                    last_updated=datetime.now(),
                    category='workflow'
                )
                
                self.principles[principle_id] = principle
                logger.info(f"Created new principle: {principle.title}")
                return principle
                
        return None
        
    async def _apply_principles(self, phase: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply learned principles to current workflow phase"""
        results = {'applied_principles': [], 'modifications': {}}
        
        for principle in self.principles.values():
            if principle.confidence >= 0.6:  # Only apply high-confidence principles
                
                # Check if conditions are met
                conditions_met = self._evaluate_principle_conditions(principle, context)
                
                if conditions_met:
                    modifications = self._apply_principle_actions(principle, phase, context)
                    if modifications:
                        results['applied_principles'].append(principle.principle_id)
                        results['modifications'].update(modifications)
                        
        # Special handling for suggestion phase
        if phase == 'suggestion' and 'suggestions' in context:
            results['filtered_suggestions'] = self._filter_suggestions_by_principles(
                context['suggestions'], results['applied_principles']
            )
            
        return results
        
    def _evaluate_principle_conditions(self, principle: AdaptationPrinciple, context: Dict[str, Any]) -> bool:
        """Evaluate if principle conditions are met in current context"""
        # Simple condition evaluation - in a full implementation, this would be more sophisticated
        
        if principle.category == 'workflow':
            # Check if we're in a workflow optimization context
            return 'performance_data' in context or 'observer_data' in context
        elif principle.category == 'efficiency':
            # Check if efficiency metrics are available
            return any('efficiency' in str(key) for key in context.keys())
            
        return True  # Default to applying principle
        
    def _apply_principle_actions(self, principle: AdaptationPrinciple, phase: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply principle actions to modify workflow behavior"""
        modifications = {}
        
        # Apply principle-based modifications based on the phase
        if principle.category == 'workflow' and phase in ['suggest', 'implement']:
            modifications['workflow_optimization_focus'] = True
            modifications['multi_metric_targeting'] = True
            
        elif principle.category == 'efficiency' and phase == 'monitor':
            modifications['efficiency_monitoring_enhanced'] = True
            
        return modifications
        
    def _filter_suggestions_by_principles(self, suggestions: List[OptimizationSuggestion], 
                                        applied_principles: List[str]) -> List[OptimizationSuggestion]:
        """Filter and prioritize suggestions based on learned principles"""
        filtered = []
        
        for suggestion in suggestions:
            # Boost priority if suggestion aligns with successful principles
            priority_boost = 0
            
            for principle_id in applied_principles:
                principle = self.principles.get(principle_id)
                if principle and principle.category == suggestion.category:
                    priority_boost += principle.confidence * 2
                    
            # Apply boost
            if priority_boost > 0:
                suggestion.priority = min(10, suggestion.priority + int(priority_boost))
                suggestion.confidence_score = min(1.0, suggestion.confidence_score + priority_boost * 0.1)
                
            filtered.append(suggestion)
            
        # Sort by boosted priority
        filtered.sort(key=lambda x: x.priority * x.confidence_score, reverse=True)
        
        return filtered
        
    def _extract_baseline_metrics(self, observer_data: Dict[str, Any], 
                                performance_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract key metrics for before/after comparison"""
        metrics = {}
        
        # From observer data
        perf_summary = observer_data.get('performance_summary', {})
        metrics['task_success_rate'] = perf_summary.get('success_rate', 0.0)
        metrics['avg_tools_per_task'] = perf_summary.get('avg_tools_per_task', 0.0)
        
        # From performance data
        scores = performance_data.get('performance_scores', {})
        for metric_name, data in scores.items():
            if isinstance(data, dict) and 'current_average' in data:
                metrics[metric_name] = data['current_average']
                
        return metrics
        
    def _complete_execution(self):
        """Complete the current workflow execution"""
        if not self.current_execution:
            return
            
        self.current_execution.end_time = datetime.now()
        
        # Determine overall success
        phases_completed = len(self.current_execution.phases_completed)
        implementations = self.current_execution.implementations_attempted
        evaluations = self.current_execution.evaluations_completed
        
        self.current_execution.overall_success = (
            phases_completed >= 4 and  # At least observe, monitor, suggest, implement
            (implementations > 0 or evaluations > 0)
        )
        
        # Store execution history
        self.execution_history.append(self.current_execution)
        
        # Keep only last 50 executions
        self.execution_history = self.execution_history[-50:]
        
        logger.info(f"Completed optimization cycle: {self.current_execution.execution_id} "
                   f"(success={self.current_execution.overall_success})")
        
        self.current_execution = None
        
    def get_principles_summary(self) -> Dict[str, Any]:
        """Get summary of learned principles"""
        if not self.principles:
            return {"message": "No principles learned yet"}
            
        categories = {}
        for principle in self.principles.values():
            if principle.category not in categories:
                categories[principle.category] = []
            categories[principle.category].append({
                'id': principle.principle_id,
                'title': principle.title,
                'success_rate': principle.success_rate,
                'confidence': principle.confidence,
                'evidence_count': principle.evidence_count
            })
            
        return {
            'total_principles': len(self.principles),
            'by_category': categories,
            'avg_confidence': sum(p.confidence for p in self.principles.values()) / len(self.principles),
            'avg_success_rate': sum(p.success_rate for p in self.principles.values()) / len(self.principles),
            'total_evidence': sum(p.evidence_count for p in self.principles.values())
        }
        
    def add_adaptation_callback(self, callback: Callable[[AdaptationPrinciple], None]):
        """Add callback to be notified when principles are learned/updated"""
        self.adaptation_callbacks.append(callback)
        
    def get_workflow_rules(self) -> Dict[str, Any]:
        """Get current workflow rules (can be adapted over time)"""
        return self.workflow_rules.copy()
        
    def update_workflow_rule(self, rule_name: str, value: Any):
        """Update a workflow rule (part of adaptation process)"""
        self.workflow_rules[rule_name] = value
        logger.info(f"Updated workflow rule: {rule_name} = {value}")

# Global instance
adaptive_workflow = AdaptiveWorkflow()