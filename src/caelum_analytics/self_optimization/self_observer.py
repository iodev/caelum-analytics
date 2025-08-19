"""
Self-Observation Module for Claude Code Integration

This module implements Phase 1 of the self-optimization system: observing myself.
It tracks behavior patterns, tool usage, performance metrics, and task outcomes.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class TaskMetrics:
    """Metrics for a single task or interaction"""
    task_id: str
    task_type: str
    start_time: datetime
    end_time: Optional[datetime]
    tools_used: List[str]
    success: bool
    error_messages: List[str]
    user_feedback_score: Optional[float]
    tokens_consumed: Optional[int]
    complexity_level: str
    context_switches: int
    
class SelfObserver:
    """Observes and tracks Claude's own behavior patterns and performance"""
    
    def __init__(self, metrics_file: str = "/home/rford/.claude/self_metrics.json"):
        self.metrics_file = Path(metrics_file)
        self.current_session: Dict[str, Any] = {}
        self.session_start_time = datetime.now()
        self.task_history: List[TaskMetrics] = []
        self.tool_usage_patterns: Dict[str, int] = {}
        self.performance_trends: Dict[str, List[float]] = {}
        self.load_historical_data()
        
    def load_historical_data(self):
        """Load existing metrics data"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    self.tool_usage_patterns = data.get('tool_usage_patterns', {})
                    self.performance_trends = data.get('performance_trends', {})
                    # Load recent task history
                    recent_tasks = data.get('recent_tasks', [])
                    self.task_history = [
                        TaskMetrics(**task) for task in recent_tasks[-100:]  # Keep last 100 tasks
                    ]
            except Exception as e:
                logger.error(f"Error loading metrics data: {e}")
                
    def start_task_observation(self, task_type: str, task_description: str) -> str:
        """Begin observing a new task"""
        task_id = f"task_{int(time.time())}"
        
        self.current_session[task_id] = {
            'task_type': task_type,
            'task_description': task_description,
            'start_time': datetime.now(),
            'tools_used': [],
            'context_switches': 0,
            'errors': []
        }
        
        logger.info(f"Started observing task: {task_id} ({task_type})")
        return task_id
        
    def record_tool_usage(self, task_id: str, tool_name: str):
        """Record that a tool was used in the current task"""
        if task_id in self.current_session:
            self.current_session[task_id]['tools_used'].append({
                'tool': tool_name,
                'timestamp': datetime.now().isoformat()
            })
            
            # Update tool usage patterns
            self.tool_usage_patterns[tool_name] = self.tool_usage_patterns.get(tool_name, 0) + 1
            
    def record_context_switch(self, task_id: str, from_context: str, to_context: str):
        """Record when context switches between different problem domains"""
        if task_id in self.current_session:
            self.current_session[task_id]['context_switches'] += 1
            
    def record_error(self, task_id: str, error_message: str, error_type: str):
        """Record an error that occurred during task execution"""
        if task_id in self.current_session:
            self.current_session[task_id]['errors'].append({
                'message': error_message,
                'type': error_type,
                'timestamp': datetime.now().isoformat()
            })
            
    def complete_task_observation(self, task_id: str, success: bool, 
                                user_feedback_score: Optional[float] = None,
                                tokens_consumed: Optional[int] = None) -> TaskMetrics:
        """Complete observation of a task and calculate metrics"""
        if task_id not in self.current_session:
            raise ValueError(f"Task {task_id} not found in current session")
            
        session_data = self.current_session[task_id]
        end_time = datetime.now()
        duration = (end_time - session_data['start_time']).total_seconds()
        
        # Determine complexity based on tools used and duration
        tool_count = len(session_data['tools_used'])
        if duration < 30 and tool_count <= 2:
            complexity = "low"
        elif duration < 120 and tool_count <= 5:
            complexity = "medium"
        else:
            complexity = "high"
            
        metrics = TaskMetrics(
            task_id=task_id,
            task_type=session_data['task_type'],
            start_time=session_data['start_time'],
            end_time=end_time,
            tools_used=[tool['tool'] for tool in session_data['tools_used']],
            success=success,
            error_messages=[error['message'] for error in session_data['errors']],
            user_feedback_score=user_feedback_score,
            tokens_consumed=tokens_consumed,
            complexity_level=complexity,
            context_switches=session_data['context_switches']
        )
        
        self.task_history.append(metrics)
        del self.current_session[task_id]
        
        # Update performance trends
        self._update_performance_trends(metrics, duration)
        
        logger.info(f"Completed task observation: {task_id} (success={success}, duration={duration:.1f}s)")
        return metrics
        
    def _update_performance_trends(self, metrics: TaskMetrics, duration: float):
        """Update performance trend data"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        trends = {
            'task_duration': duration,
            'success_rate': 1.0 if metrics.success else 0.0,
            'tool_efficiency': len(metrics.tools_used) / max(1, duration / 60),  # tools per minute
            'error_rate': len(metrics.error_messages),
            'context_switch_rate': metrics.context_switches
        }
        
        for metric_name, value in trends.items():
            if metric_name not in self.performance_trends:
                self.performance_trends[metric_name] = []
            self.performance_trends[metric_name].append(value)
            
            # Keep only last 100 data points per metric
            self.performance_trends[metric_name] = self.performance_trends[metric_name][-100:]
            
    def get_self_analysis(self) -> Dict[str, Any]:
        """Analyze current performance patterns and behavior"""
        if not self.task_history:
            return {"message": "No task history available for analysis"}
            
        recent_tasks = self.task_history[-20:]  # Last 20 tasks
        
        # Calculate key metrics
        success_rate = sum(1 for task in recent_tasks if task.success) / len(recent_tasks)
        avg_tools_per_task = sum(len(task.tools_used) for task in recent_tasks) / len(recent_tasks)
        avg_complexity_score = sum(self._complexity_to_score(task.complexity_level) for task in recent_tasks) / len(recent_tasks)
        
        # Most used tools
        tool_counts = {}
        for task in recent_tasks:
            for tool in task.tools_used:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
                
        top_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Task type performance
        task_type_performance = {}
        for task in recent_tasks:
            if task.task_type not in task_type_performance:
                task_type_performance[task.task_type] = {'total': 0, 'success': 0}
            task_type_performance[task.task_type]['total'] += 1
            if task.success:
                task_type_performance[task.task_type]['success'] += 1
                
        for task_type in task_type_performance:
            performance = task_type_performance[task_type]
            performance['success_rate'] = performance['success'] / performance['total']
            
        # Performance trends
        trend_analysis = {}
        for metric_name, values in self.performance_trends.items():
            if len(values) >= 5:  # Need at least 5 data points
                recent_avg = sum(values[-5:]) / 5
                older_avg = sum(values[-10:-5]) / 5 if len(values) >= 10 else recent_avg
                trend = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"
                trend_analysis[metric_name] = {
                    'current_avg': recent_avg,
                    'trend': trend,
                    'change_percent': ((recent_avg - older_avg) / max(0.01, older_avg)) * 100 if older_avg > 0 else 0
                }
                
        return {
            'observation_period': {
                'start': self.session_start_time.isoformat(),
                'tasks_analyzed': len(recent_tasks),
                'total_task_history': len(self.task_history)
            },
            'performance_summary': {
                'success_rate': success_rate,
                'avg_tools_per_task': avg_tools_per_task,
                'avg_complexity_score': avg_complexity_score
            },
            'tool_usage_patterns': {
                'top_tools': top_tools,
                'total_unique_tools': len(tool_counts),
                'tool_usage_diversity': len(tool_counts) / max(1, len(recent_tasks))
            },
            'task_type_performance': task_type_performance,
            'performance_trends': trend_analysis,
            'areas_for_observation': self._identify_observation_areas(recent_tasks, trend_analysis)
        }
        
    def _complexity_to_score(self, complexity: str) -> float:
        """Convert complexity level to numeric score"""
        scores = {'low': 1.0, 'medium': 2.0, 'high': 3.0}
        return scores.get(complexity, 2.0)
        
    def _identify_observation_areas(self, recent_tasks: List[TaskMetrics], trends: Dict[str, Any]) -> List[str]:
        """Identify areas that need focused observation"""
        areas = []
        
        # Check for declining performance trends
        for metric, data in trends.items():
            if data['trend'] == 'declining' and abs(data['change_percent']) > 10:
                areas.append(f"Declining {metric.replace('_', ' ')}: {data['change_percent']:.1f}% change")
                
        # Check for high error rates
        error_tasks = [task for task in recent_tasks if task.error_messages]
        if len(error_tasks) > len(recent_tasks) * 0.2:  # More than 20% error rate
            areas.append(f"High error rate: {len(error_tasks)}/{len(recent_tasks)} tasks had errors")
            
        # Check for excessive context switching
        high_context_switch_tasks = [task for task in recent_tasks if task.context_switches > 3]
        if len(high_context_switch_tasks) > len(recent_tasks) * 0.3:
            areas.append(f"Excessive context switching in {len(high_context_switch_tasks)} tasks")
            
        # Check for tool usage inefficiency
        tool_counts = {}
        for task in recent_tasks:
            for tool in task.tools_used:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
                
        if len(tool_counts) > 20:  # Using too many different tools
            areas.append(f"High tool diversity: {len(tool_counts)} different tools used")
            
        return areas
        
    def save_metrics(self):
        """Save current metrics to file"""
        try:
            # Ensure directory exists
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'session_start': self.session_start_time.isoformat(),
                'tool_usage_patterns': self.tool_usage_patterns,
                'performance_trends': self.performance_trends,
                'recent_tasks': [asdict(task) for task in self.task_history[-100:]],  # Save last 100 tasks
                'last_updated': datetime.now().isoformat()
            }
            
            # Convert datetime objects to strings for JSON serialization
            for task_data in data['recent_tasks']:
                if 'start_time' in task_data and isinstance(task_data['start_time'], datetime):
                    task_data['start_time'] = task_data['start_time'].isoformat()
                if 'end_time' in task_data and task_data['end_time'] and isinstance(task_data['end_time'], datetime):
                    task_data['end_time'] = task_data['end_time'].isoformat()
            
            with open(self.metrics_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            logger.info(f"Metrics saved to {self.metrics_file}")
            
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

# Global instance for easy access
self_observer = SelfObserver()