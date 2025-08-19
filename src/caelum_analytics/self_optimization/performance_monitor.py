"""
Performance Monitor for Self-Optimization System

This module implements Phase 2: real-time performance monitoring with alerts and analytics.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import statistics
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceAlert:
    """Alert for performance degradation"""
    alert_id: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    timestamp: datetime
    suggested_actions: List[str]

class PerformanceMonitor:
    """Real-time performance monitoring and alerting system"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.thresholds: Dict[str, Dict[str, float]] = self._default_thresholds()
        self.alerts: List[PerformanceAlert] = []
        self.monitoring_active = False
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        self.performance_targets: Dict[str, float] = self._default_targets()
        
    def _default_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Default performance thresholds for alerts"""
        return {
            'task_success_rate': {
                'critical': 0.7,  # Below 70% success rate
                'high': 0.8,      # Below 80% success rate
                'medium': 0.9,    # Below 90% success rate
                'low': 0.95       # Below 95% success rate
            },
            'avg_response_time': {
                'critical': 300.0,  # Over 5 minutes
                'high': 180.0,      # Over 3 minutes
                'medium': 120.0,    # Over 2 minutes
                'low': 60.0         # Over 1 minute
            },
            'error_rate': {
                'critical': 0.2,   # Over 20% error rate
                'high': 0.15,      # Over 15% error rate
                'medium': 0.1,     # Over 10% error rate
                'low': 0.05        # Over 5% error rate
            },
            'tool_efficiency': {
                'critical': 0.5,   # Less than 0.5 tools per minute
                'high': 1.0,       # Less than 1 tool per minute
                'medium': 1.5,     # Less than 1.5 tools per minute
                'low': 2.0         # Less than 2 tools per minute
            },
            'context_switch_rate': {
                'critical': 5.0,   # More than 5 context switches per task
                'high': 4.0,       # More than 4 context switches per task
                'medium': 3.0,     # More than 3 context switches per task
                'low': 2.0         # More than 2 context switches per task
            }
        }
        
    def _default_targets(self) -> Dict[str, float]:
        """Default performance targets to strive for"""
        return {
            'task_success_rate': 0.98,      # 98% success rate
            'avg_response_time': 45.0,      # Under 45 seconds average
            'error_rate': 0.02,             # Under 2% error rate
            'tool_efficiency': 3.0,         # 3+ tools per minute
            'context_switch_rate': 1.0,     # 1 or fewer context switches per task
            'user_satisfaction': 4.5,       # 4.5+ out of 5 user rating
            'token_efficiency': 0.8         # High value per token used
        }
        
    def start_monitoring(self):
        """Start real-time performance monitoring"""
        self.monitoring_active = True
        logger.info("Performance monitoring started")
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        logger.info("Performance monitoring stopped")
        
    def record_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Record a performance metric value"""
        if not self.monitoring_active:
            return
            
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
            
        self.metrics[metric_name].append(value)
        
        # Keep only last 100 values per metric
        self.metrics[metric_name] = self.metrics[metric_name][-100:]
        
        # Check for threshold violations
        self._check_thresholds(metric_name, value, timestamp or datetime.now())
        
    def _check_thresholds(self, metric_name: str, value: float, timestamp: datetime):
        """Check if metric value violates thresholds and generate alerts"""
        if metric_name not in self.thresholds:
            return
            
        thresholds = self.thresholds[metric_name]
        
        # Determine severity (check from most severe to least)
        severity = None
        threshold_value = None
        
        for sev in ['critical', 'high', 'medium', 'low']:
            if sev in thresholds:
                threshold = thresholds[sev]
                
                # For success rates and efficiency, lower values are worse
                if metric_name in ['task_success_rate', 'tool_efficiency'] and value < threshold:
                    severity = sev
                    threshold_value = threshold
                    break
                # For response time, error rate, context switches, higher values are worse
                elif metric_name in ['avg_response_time', 'error_rate', 'context_switch_rate'] and value > threshold:
                    severity = sev
                    threshold_value = threshold
                    break
                    
        if severity:
            self._create_alert(metric_name, value, threshold_value, severity, timestamp)
            
    def _create_alert(self, metric_name: str, current_value: float, threshold: float, 
                     severity: str, timestamp: datetime):
        """Create and process a performance alert"""
        alert_id = f"alert_{metric_name}_{int(timestamp.timestamp())}"
        
        # Generate appropriate message and suggestions
        message, suggestions = self._generate_alert_content(metric_name, current_value, threshold, severity)
        
        alert = PerformanceAlert(
            alert_id=alert_id,
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold,
            severity=severity,
            message=message,
            timestamp=timestamp,
            suggested_actions=suggestions
        )
        
        self.alerts.append(alert)
        
        # Keep only last 50 alerts
        self.alerts = self.alerts[-50:]
        
        # Notify alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
                
        logger.warning(f"Performance Alert [{severity.upper()}]: {message}")
        
    def _generate_alert_content(self, metric_name: str, current_value: float, 
                              threshold: float, severity: str) -> tuple[str, List[str]]:
        """Generate alert message and suggested actions"""
        
        messages = {
            'task_success_rate': f"Task success rate dropped to {current_value:.1%} (threshold: {threshold:.1%})",
            'avg_response_time': f"Response time increased to {current_value:.1f}s (threshold: {threshold:.1f}s)",
            'error_rate': f"Error rate increased to {current_value:.1%} (threshold: {threshold:.1%})",
            'tool_efficiency': f"Tool efficiency dropped to {current_value:.1f} tools/min (threshold: {threshold:.1f})",
            'context_switch_rate': f"Context switches increased to {current_value:.1f} per task (threshold: {threshold:.1f})"
        }
        
        suggestions_map = {
            'task_success_rate': [
                "Review recent failed tasks for common patterns",
                "Check tool selection strategy for appropriateness",
                "Analyze error messages for systematic issues",
                "Consider simplifying complex workflows"
            ],
            'avg_response_time': [
                "Optimize tool selection for faster execution",
                "Reduce unnecessary context switching",
                "Pre-cache frequently used information",
                "Break down complex tasks into smaller steps"
            ],
            'error_rate': [
                "Implement better error handling patterns",
                "Add validation before tool execution",
                "Review tool usage patterns for common mistakes",
                "Enhance error recovery strategies"
            ],
            'tool_efficiency': [
                "Review tool selection for redundancy",
                "Implement smarter tool pre-screening",
                "Cache tool results where appropriate",
                "Streamline workflow execution paths"
            ],
            'context_switch_rate': [
                "Improve task planning to reduce context changes",
                "Group related operations together",
                "Use more focused tool selections",
                "Implement better state management"
            ]
        }
        
        message = messages.get(metric_name, f"{metric_name} threshold violated: {current_value} vs {threshold}")
        suggestions = suggestions_map.get(metric_name, ["Review and optimize current approach"])
        
        return message, suggestions
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.metrics:
            return {"message": "No performance data available"}
            
        summary = {
            'monitoring_status': 'active' if self.monitoring_active else 'inactive',
            'data_points_collected': sum(len(values) for values in self.metrics.values()),
            'metrics_tracked': list(self.metrics.keys()),
            'recent_alerts': len([alert for alert in self.alerts if 
                                (datetime.now() - alert.timestamp).total_seconds() < 3600]),  # Last hour
            'performance_scores': {},
            'trending_analysis': {},
            'target_achievement': {}
        }
        
        # Calculate performance scores
        for metric_name, values in self.metrics.items():
            if len(values) >= 3:  # Need at least 3 data points
                recent_avg = statistics.mean(values[-10:])  # Last 10 values
                summary['performance_scores'][metric_name] = {
                    'current_average': recent_avg,
                    'min_recent': min(values[-10:]),
                    'max_recent': max(values[-10:]),
                    'std_deviation': statistics.stdev(values[-10:]) if len(values[-10:]) > 1 else 0,
                    'data_points': len(values)
                }
                
                # Trend analysis
                if len(values) >= 10:
                    older_avg = statistics.mean(values[-20:-10]) if len(values) >= 20 else recent_avg
                    if recent_avg > older_avg * 1.05:  # 5% improvement threshold
                        trend = 'improving'
                    elif recent_avg < older_avg * 0.95:  # 5% decline threshold
                        trend = 'declining'
                    else:
                        trend = 'stable'
                        
                    summary['trending_analysis'][metric_name] = {
                        'trend': trend,
                        'change_percent': ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
                    }
                    
                # Target achievement
                if metric_name in self.performance_targets:
                    target = self.performance_targets[metric_name]
                    if metric_name in ['task_success_rate', 'tool_efficiency']:
                        # Higher is better
                        achievement = (recent_avg / target) * 100
                    else:
                        # Lower is better
                        achievement = (target / recent_avg) * 100 if recent_avg > 0 else 100
                        
                    summary['target_achievement'][metric_name] = {
                        'target': target,
                        'current': recent_avg,
                        'achievement_percent': min(100, achievement),
                        'on_target': abs(recent_avg - target) < target * 0.1  # Within 10% of target
                    }
                    
        return summary
        
    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get alerts from the last 24 hours"""
        cutoff = datetime.now() - timedelta(hours=24)
        return [alert for alert in self.alerts if alert.timestamp > cutoff]
        
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add a callback function to be called when alerts are generated"""
        self.alert_callbacks.append(callback)
        
    def clear_old_alerts(self, hours_old: int = 24):
        """Clear alerts older than specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours_old)
        self.alerts = [alert for alert in self.alerts if alert.timestamp > cutoff]
        
    def set_custom_threshold(self, metric_name: str, severity: str, value: float):
        """Set custom threshold for a metric"""
        if metric_name not in self.thresholds:
            self.thresholds[metric_name] = {}
        self.thresholds[metric_name][severity] = value
        logger.info(f"Set {severity} threshold for {metric_name} to {value}")
        
    def get_recommendations(self) -> List[str]:
        """Get performance improvement recommendations based on current metrics"""
        recommendations = []
        
        # Analyze recent alerts for patterns
        recent_alerts = self.get_active_alerts()
        alert_patterns = {}
        
        for alert in recent_alerts:
            metric = alert.metric_name
            if metric not in alert_patterns:
                alert_patterns[metric] = []
            alert_patterns[metric].append(alert)
            
        # Generate recommendations based on alert patterns
        for metric, alerts in alert_patterns.items():
            if len(alerts) >= 3:  # Multiple alerts for same metric
                recommendations.append(
                    f"Multiple {metric} alerts detected. Consider implementing suggested actions: " +
                    ", ".join(alerts[0].suggested_actions[:2])
                )
                
        # Check performance vs targets
        summary = self.get_performance_summary()
        target_achievements = summary.get('target_achievement', {})
        
        for metric, achievement_data in target_achievements.items():
            if achievement_data['achievement_percent'] < 80:  # Less than 80% of target
                recommendations.append(
                    f"Performance below target for {metric}: {achievement_data['current']:.2f} vs target {achievement_data['target']:.2f}"
                )
                
        if not recommendations:
            recommendations.append("Performance is within acceptable ranges. Continue monitoring.")
            
        return recommendations

# Global instance
performance_monitor = PerformanceMonitor()