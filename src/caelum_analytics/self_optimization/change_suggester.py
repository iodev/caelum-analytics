"""
Change Suggester for Self-Optimization System

This module implements Phase 3: analyzing performance data and suggesting specific improvements.
Uses Caelum's business intelligence and analytics capabilities.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics
import logging

logger = logging.getLogger(__name__)

@dataclass
class OptimizationSuggestion:
    """A specific suggestion for improving performance"""
    suggestion_id: str
    category: str  # 'tool_selection', 'workflow', 'error_handling', 'efficiency', 'user_experience'
    priority: int  # 1-10, higher is more important
    title: str
    description: str
    expected_impact: str
    implementation_effort: str  # 'low', 'medium', 'high'
    success_metrics: List[str]
    implementation_steps: List[str]
    risks: List[str]
    confidence_score: float  # 0.0-1.0
    timestamp: datetime

class ChangeSuggester:
    """Analyzes performance data and generates optimization suggestions"""
    
    def __init__(self):
        self.suggestion_history: List[OptimizationSuggestion] = []
        self.implemented_suggestions: List[str] = []
        self.analysis_cache: Dict[str, Any] = {}
        
    async def analyze_and_suggest(self, observer_data: Dict[str, Any], 
                                performance_data: Dict[str, Any]) -> List[OptimizationSuggestion]:
        """Main method to analyze data and generate suggestions"""
        suggestions = []
        
        # Analyze different aspects of performance
        tool_suggestions = await self._analyze_tool_usage(observer_data, performance_data)
        workflow_suggestions = await self._analyze_workflow_patterns(observer_data, performance_data)
        error_suggestions = await self._analyze_error_patterns(observer_data, performance_data)
        efficiency_suggestions = await self._analyze_efficiency_patterns(observer_data, performance_data)
        
        suggestions.extend(tool_suggestions)
        suggestions.extend(workflow_suggestions)
        suggestions.extend(error_suggestions)
        suggestions.extend(efficiency_suggestions)
        
        # Sort by priority and confidence
        suggestions.sort(key=lambda x: (x.priority * x.confidence_score), reverse=True)
        
        # Store suggestions
        for suggestion in suggestions:
            self.suggestion_history.append(suggestion)
            
        # Keep only last 100 suggestions
        self.suggestion_history = self.suggestion_history[-100:]
        
        return suggestions[:10]  # Return top 10 suggestions
        
    async def _analyze_tool_usage(self, observer_data: Dict[str, Any], 
                                performance_data: Dict[str, Any]) -> List[OptimizationSuggestion]:
        """Analyze tool usage patterns and suggest optimizations"""
        suggestions = []
        
        tool_patterns = observer_data.get('tool_usage_patterns', {})
        top_tools = tool_patterns.get('top_tools', [])
        
        if not top_tools:
            return suggestions
            
        # Suggestion 1: Tool consolidation if using too many different tools
        total_tools = tool_patterns.get('total_unique_tools', 0)
        if total_tools > 15:
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"tool_consolidation_{int(datetime.now().timestamp())}",
                category='tool_selection',
                priority=7,
                title="Consolidate Tool Usage",
                description=f"Currently using {total_tools} different tools. Consider focusing on the most effective ones.",
                expected_impact="Reduced complexity, faster tool selection, fewer context switches",
                implementation_effort="medium",
                success_metrics=["tool_efficiency", "context_switch_rate", "avg_response_time"],
                implementation_steps=[
                    "Analyze effectiveness of each tool",
                    "Identify overlapping functionality",
                    "Create preferred tool selection strategy",
                    "Update tool pre-screening logic"
                ],
                risks=["May miss specialized functionality", "Learning curve for new patterns"],
                confidence_score=0.8,
                timestamp=datetime.now()
            ))
            
        # Suggestion 2: Focus on high-performing tools
        if len(top_tools) >= 5:
            top_5_usage = sum(count for _, count in top_tools[:5])
            total_usage = sum(count for _, count in top_tools)
            
            if top_5_usage / total_usage < 0.7:  # Top 5 tools used less than 70% of time
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"focus_top_tools_{int(datetime.now().timestamp())}",
                    category='tool_selection',
                    priority=6,
                    title="Focus on High-Performance Tools",
                    description="Top 5 tools are underutilized. Consider prioritizing proven effective tools.",
                    expected_impact="Improved success rates, reduced trial-and-error",
                    implementation_effort="low",
                    success_metrics=["task_success_rate", "tool_efficiency"],
                    implementation_steps=[
                        "Review success rates for top tools",
                        "Update tool selection algorithm weights",
                        "Create tool effectiveness scoring"
                    ],
                    risks=["May become too rigid in tool selection"],
                    confidence_score=0.7,
                    timestamp=datetime.now()
                ))
                
        return suggestions
        
    async def _analyze_workflow_patterns(self, observer_data: Dict[str, Any], 
                                       performance_data: Dict[str, Any]) -> List[OptimizationSuggestion]:
        """Analyze workflow patterns and suggest improvements"""
        suggestions = []
        
        task_performance = observer_data.get('task_type_performance', {})
        
        # Identify underperforming task types
        for task_type, performance in task_performance.items():
            success_rate = performance.get('success_rate', 1.0)
            
            if success_rate < 0.8 and performance.get('total', 0) >= 3:  # At least 3 attempts
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"improve_task_type_{task_type}_{int(datetime.now().timestamp())}",
                    category='workflow',
                    priority=8,
                    title=f"Improve {task_type.title()} Task Handling",
                    description=f"Success rate for {task_type} tasks is {success_rate:.1%}. Needs improvement.",
                    expected_impact="Higher success rates for specific task types",
                    implementation_effort="medium",
                    success_metrics=[f"{task_type}_success_rate", "overall_success_rate"],
                    implementation_steps=[
                        f"Analyze failed {task_type} tasks for common patterns",
                        f"Develop specialized approach for {task_type}",
                        "Create task-specific tool selection strategy",
                        "Add validation steps for this task type"
                    ],
                    risks=["May over-specialize", "Increased complexity"],
                    confidence_score=0.85,
                    timestamp=datetime.now()
                ))
                
        # Check for context switching issues
        trends = performance_data.get('trending_analysis', {})
        if 'context_switch_rate' in trends:
            switch_trend = trends['context_switch_rate']
            if switch_trend.get('trend') == 'increasing':
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"reduce_context_switching_{int(datetime.now().timestamp())}",
                    category='workflow',
                    priority=7,
                    title="Reduce Context Switching",
                    description="Context switching rate is increasing, reducing efficiency.",
                    expected_impact="Faster task completion, better focus, improved efficiency",
                    implementation_effort="medium",
                    success_metrics=["context_switch_rate", "avg_response_time"],
                    implementation_steps=[
                        "Analyze when context switches occur",
                        "Group related operations together",
                        "Improve task planning phase",
                        "Create context-aware tool selection"
                    ],
                    risks=["May miss important connections", "Could reduce flexibility"],
                    confidence_score=0.75,
                    timestamp=datetime.now()
                ))
                
        return suggestions
        
    async def _analyze_error_patterns(self, observer_data: Dict[str, Any], 
                                    performance_data: Dict[str, Any]) -> List[OptimizationSuggestion]:
        """Analyze error patterns and suggest improvements"""
        suggestions = []
        
        scores = performance_data.get('performance_scores', {})
        error_rate_data = scores.get('error_rate')
        
        if error_rate_data and error_rate_data.get('current_average', 0) > 0.05:  # Over 5% error rate
            error_rate = error_rate_data['current_average']
            
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"reduce_error_rate_{int(datetime.now().timestamp())}",
                category='error_handling',
                priority=9,
                title="Improve Error Handling",
                description=f"Current error rate of {error_rate:.1%} is above optimal threshold.",
                expected_impact="Higher success rates, better user experience",
                implementation_effort="high",
                success_metrics=["error_rate", "task_success_rate"],
                implementation_steps=[
                    "Categorize error types and frequencies",
                    "Implement proactive error prevention",
                    "Add validation before risky operations",
                    "Create better error recovery strategies",
                    "Add error pattern detection"
                ],
                risks=["May slow down execution", "Could become overly cautious"],
                confidence_score=0.9,
                timestamp=datetime.now()
            ))
            
        return suggestions
        
    async def _analyze_efficiency_patterns(self, observer_data: Dict[str, Any], 
                                         performance_data: Dict[str, Any]) -> List[OptimizationSuggestion]:
        """Analyze efficiency patterns and suggest improvements"""
        suggestions = []
        
        scores = performance_data.get('performance_scores', {})
        
        # Check response time
        response_time_data = scores.get('avg_response_time')
        if response_time_data and response_time_data.get('current_average', 0) > 90:  # Over 90 seconds
            response_time = response_time_data['current_average']
            
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"improve_response_time_{int(datetime.now().timestamp())}",
                category='efficiency',
                priority=6,
                title="Optimize Response Time",
                description=f"Average response time of {response_time:.1f}s could be improved.",
                expected_impact="Faster user interactions, better experience",
                implementation_effort="medium",
                success_metrics=["avg_response_time", "user_satisfaction"],
                implementation_steps=[
                    "Profile slow operations to identify bottlenecks",
                    "Implement result caching where appropriate",
                    "Optimize tool execution order",
                    "Add parallel processing where possible",
                    "Pre-fetch commonly needed information"
                ],
                risks=["May increase complexity", "Caching could cause stale data issues"],
                confidence_score=0.7,
                timestamp=datetime.now()
            ))
            
        # Check tool efficiency
        tool_efficiency_data = scores.get('tool_efficiency')
        if tool_efficiency_data and tool_efficiency_data.get('current_average', 0) < 1.5:  # Less than 1.5 tools/min
            efficiency = tool_efficiency_data['current_average']
            
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"improve_tool_efficiency_{int(datetime.now().timestamp())}",
                category='efficiency',
                priority=5,
                title="Improve Tool Efficiency",
                description=f"Tool usage efficiency of {efficiency:.1f} tools/min is below optimal.",
                expected_impact="Faster task completion, better resource utilization",
                implementation_effort="medium",
                success_metrics=["tool_efficiency", "avg_response_time"],
                implementation_steps=[
                    "Analyze tool execution times",
                    "Identify redundant tool usage",
                    "Implement smarter tool pre-selection",
                    "Cache tool results where possible",
                    "Optimize tool parameter selection"
                ],
                risks=["May reduce thoroughness", "Cache invalidation complexity"],
                confidence_score=0.6,
                timestamp=datetime.now()
            ))
            
        return suggestions
        
    def get_suggestion_history(self) -> List[OptimizationSuggestion]:
        """Get history of all suggestions"""
        return self.suggestion_history.copy()
        
    def mark_suggestion_implemented(self, suggestion_id: str):
        """Mark a suggestion as implemented"""
        self.implemented_suggestions.append(suggestion_id)
        logger.info(f"Marked suggestion {suggestion_id} as implemented")
        
    def get_implemented_suggestions(self) -> List[str]:
        """Get list of implemented suggestion IDs"""
        return self.implemented_suggestions.copy()
        
    def analyze_suggestion_success(self, suggestion_id: str, 
                                 before_metrics: Dict[str, float], 
                                 after_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Analyze the success of an implemented suggestion"""
        suggestion = next((s for s in self.suggestion_history if s.suggestion_id == suggestion_id), None)
        if not suggestion:
            return {"error": "Suggestion not found"}
            
        improvements = {}
        for metric in suggestion.success_metrics:
            if metric in before_metrics and metric in after_metrics:
                before = before_metrics[metric]
                after = after_metrics[metric]
                
                # Determine if improvement means higher or lower values
                if metric in ['task_success_rate', 'tool_efficiency']:
                    # Higher is better
                    improvement = ((after - before) / before) * 100 if before > 0 else 0
                else:
                    # Lower is better (response time, error rate, etc.)
                    improvement = ((before - after) / before) * 100 if before > 0 else 0
                    
                improvements[metric] = {
                    'before': before,
                    'after': after,
                    'improvement_percent': improvement,
                    'improved': improvement > 0
                }
                
        overall_success = sum(1 for imp in improvements.values() if imp['improved']) / len(improvements) if improvements else 0
        
        return {
            'suggestion_id': suggestion_id,
            'suggestion_title': suggestion.title,
            'metrics_analyzed': improvements,
            'overall_success_rate': overall_success,
            'summary': f"{overall_success:.1%} of targeted metrics improved",
            'analysis_timestamp': datetime.now().isoformat()
        }

# Global instance
change_suggester = ChangeSuggester()