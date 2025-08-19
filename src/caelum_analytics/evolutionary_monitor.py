"""
Evolutionary Monitoring for Caelum MCP Cost Optimization
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import asyncio
from dataclasses import dataclass, asdict
from pathlib import Path
import aiofiles
import logging

logger = logging.getLogger(__name__)

@dataclass
class EvolutionaryMetric:
    """Represents a single evolutionary data point"""
    timestamp: datetime
    session_id: str
    source: str  # e.g., 'caelum-mcp-servers'
    metric_type: str  # e.g., 'cost-optimization', 'value-metrics'
    data: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class EvolutionarySnapshot:
    """Comprehensive snapshot of evolutionary progress"""
    timestamp: datetime
    local_processing_ratio: float
    cost_savings_total: float
    monthly_projection: float
    quality_score: float
    learning_rate: float
    target_achievement: bool
    session_count: int
    trend_direction: str
    alerts: List[Dict[str, Any]]

class EvolutionaryMonitor:
    """
    Monitors and analyzes evolutionary improvements in cost optimization
    """
    
    def __init__(self, shared_data_path: str = "shared-data"):
        self.shared_data_path = Path(shared_data_path)
        self.shared_data_path.mkdir(exist_ok=True)
        
        self.metrics: List[EvolutionaryMetric] = []
        self.snapshots: List[EvolutionarySnapshot] = []
        self.active_sessions: Dict[str, Dict] = {}
        
        # Thresholds for alerting
        self.targets = {
            'local_processing_ratio': 0.8,
            'quality_score_min': 0.7,
            'learning_rate_min': 0.05,
            'cost_savings_threshold': 10.0
        }
        
        logger.info("Evolutionary Monitor initialized")

    async def start_monitoring(self):
        """Start the evolutionary monitoring process"""
        # Start background tasks
        asyncio.create_task(self._watch_shared_data())
        asyncio.create_task(self._periodic_analysis())
        asyncio.create_task(self._cleanup_old_data())
        
        logger.info("Evolutionary monitoring started")

    async def _watch_shared_data(self):
        """Watch for new data files from MCP servers"""
        while True:
            try:
                # Check for new analytics files
                for filepath in self.shared_data_path.glob("mcp-analytics-*.json"):
                    await self._process_analytics_file(filepath)
                    
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error watching shared data: {e}")
                await asyncio.sleep(30)

    async def _process_analytics_file(self, filepath: Path):
        """Process a single analytics file from MCP servers"""
        try:
            async with aiofiles.open(filepath, 'r') as f:
                content = await f.read()
                data = json.loads(content)
            
            # Process each metric in the batch
            for item in data.get('batch', []):
                metric = EvolutionaryMetric(
                    timestamp=datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00')),
                    session_id=item['sessionId'],
                    source=item['source'],
                    metric_type=item['type'],
                    data=item['data'],
                    metadata=item['metadata']
                )
                
                self.metrics.append(metric)
                await self._update_session_state(metric)
            
            # Archive processed file
            archive_path = self.shared_data_path / "processed" / filepath.name
            archive_path.parent.mkdir(exist_ok=True)
            filepath.rename(archive_path)
            
            logger.info(f"Processed analytics file: {filepath.name}")
            
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {e}")

    async def _update_session_state(self, metric: EvolutionaryMetric):
        """Update the state for a specific session"""
        session_id = metric.session_id
        
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                'start_time': metric.timestamp,
                'last_update': metric.timestamp,
                'total_requests': 0,
                'local_successes': 0,
                'cost_savings': 0.0,
                'quality_scores': [],
                'learning_indicators': []
            }
        
        session = self.active_sessions[session_id]
        session['last_update'] = metric.timestamp
        
        # Update based on metric type
        if metric.metric_type == 'cost-optimization':
            if metric.data.get('type') == 'optimization-success':
                session['local_successes'] += 1
                session['cost_savings'] += metric.data.get('costSaved', 0)
            
            session['total_requests'] += 1
            
        elif metric.metric_type == 'value-metrics':
            quality_score = metric.data.get('qualityScore')
            if quality_score is not None:
                session['quality_scores'].append(quality_score)

    async def _periodic_analysis(self):
        """Perform periodic evolutionary analysis"""
        while True:
            try:
                await self._generate_snapshot()
                await self._check_alerts()
                await asyncio.sleep(300)  # Every 5 minutes
            except Exception as e:
                logger.error(f"Error in periodic analysis: {e}")
                await asyncio.sleep(60)

    async def _generate_snapshot(self):
        """Generate a comprehensive evolutionary snapshot"""
        if not self.active_sessions:
            return
        
        # Aggregate metrics across all active sessions
        total_requests = sum(s['total_requests'] for s in self.active_sessions.values())
        total_local_successes = sum(s['local_successes'] for s in self.active_sessions.values())
        total_cost_savings = sum(s['cost_savings'] for s in self.active_sessions.values())
        
        local_processing_ratio = total_local_successes / max(total_requests, 1)
        
        # Calculate quality metrics
        all_quality_scores = []
        for session in self.active_sessions.values():
            all_quality_scores.extend(session['quality_scores'])
        
        quality_score = sum(all_quality_scores) / max(len(all_quality_scores), 1) if all_quality_scores else 0.7
        
        # Calculate learning rate (improvement over time)
        learning_rate = self._calculate_learning_rate()
        
        # Monthly projection
        if self.snapshots:
            days_tracked = (datetime.utcnow() - self.snapshots[0].timestamp).days or 1
            monthly_projection = (total_cost_savings / days_tracked) * 30
        else:
            monthly_projection = total_cost_savings * 30  # Conservative estimate
        
        # Determine trend
        trend_direction = self._determine_trend()
        
        # Check target achievement
        target_achievement = local_processing_ratio >= self.targets['local_processing_ratio']
        
        # Generate alerts
        alerts = await self._generate_alerts(local_processing_ratio, quality_score, learning_rate)
        
        snapshot = EvolutionarySnapshot(
            timestamp=datetime.utcnow(),
            local_processing_ratio=local_processing_ratio,
            cost_savings_total=total_cost_savings,
            monthly_projection=monthly_projection,
            quality_score=quality_score,
            learning_rate=learning_rate,
            target_achievement=target_achievement,
            session_count=len(self.active_sessions),
            trend_direction=trend_direction,
            alerts=alerts
        )
        
        self.snapshots.append(snapshot)
        
        # Keep only last 1000 snapshots
        if len(self.snapshots) > 1000:
            self.snapshots = self.snapshots[-1000:]
        
        logger.info(f"Generated evolutionary snapshot: {local_processing_ratio:.1%} local processing")

    def _calculate_learning_rate(self) -> float:
        """Calculate the learning rate based on recent improvements"""
        if len(self.snapshots) < 2:
            return 0.0
        
        # Compare last 10 snapshots with previous 10
        recent = self.snapshots[-10:] if len(self.snapshots) >= 10 else self.snapshots
        previous = self.snapshots[-20:-10] if len(self.snapshots) >= 20 else []
        
        if not previous:
            return 0.0
        
        recent_avg = sum(s.local_processing_ratio for s in recent) / len(recent)
        previous_avg = sum(s.local_processing_ratio for s in previous) / len(previous)
        
        return (recent_avg - previous_avg) / max(previous_avg, 0.1)

    def _determine_trend(self) -> str:
        """Determine the overall trend direction"""
        learning_rate = self._calculate_learning_rate()
        
        if learning_rate > 0.05:
            return 'improving'
        elif learning_rate < -0.05:
            return 'declining'
        else:
            return 'stable'

    async def _generate_alerts(self, local_ratio: float, quality: float, learning_rate: float) -> List[Dict[str, Any]]:
        """Generate alerts based on current metrics"""
        alerts = []
        
        # Target achievement alert
        if local_ratio >= 0.9:
            alerts.append({
                'type': 'success',
                'severity': 'success',
                'message': f'Outstanding optimization: {local_ratio:.1%} local processing achieved!',
                'metric': 'local_processing_ratio',
                'value': local_ratio
            })
        elif local_ratio < 0.5:
            alerts.append({
                'type': 'warning',
                'severity': 'warning',
                'message': f'Low local processing ratio: {local_ratio:.1%} (target: 80%)',
                'metric': 'local_processing_ratio',
                'value': local_ratio
            })
        
        # Quality alerts
        if quality < self.targets['quality_score_min']:
            alerts.append({
                'type': 'quality',
                'severity': 'warning',
                'message': f'Quality score below threshold: {quality:.2f}',
                'metric': 'quality_score',
                'value': quality
            })
        
        # Learning rate alerts
        if learning_rate < -0.1:
            alerts.append({
                'type': 'regression',
                'severity': 'error',
                'message': f'Performance regression detected: {learning_rate:.1%}',
                'metric': 'learning_rate',
                'value': learning_rate
            })
        
        return alerts

    async def _check_alerts(self):
        """Check for alert conditions and log them"""
        if not self.snapshots:
            return
        
        latest = self.snapshots[-1]
        
        for alert in latest.alerts:
            level = getattr(logging, alert['severity'].upper(), logging.INFO)
            logger.log(level, f"Evolutionary Alert: {alert['message']}")

    async def _cleanup_old_data(self):
        """Clean up old data to prevent memory issues"""
        while True:
            try:
                # Clean up old metrics (keep last 7 days)
                cutoff = datetime.utcnow() - timedelta(days=7)
                self.metrics = [m for m in self.metrics if m.timestamp > cutoff]
                
                # Clean up inactive sessions (no activity for 1 hour)
                session_cutoff = datetime.utcnow() - timedelta(hours=1)
                inactive_sessions = [
                    sid for sid, session in self.active_sessions.items()
                    if session['last_update'] < session_cutoff
                ]
                
                for sid in inactive_sessions:
                    del self.active_sessions[sid]
                
                if inactive_sessions:
                    logger.info(f"Cleaned up {len(inactive_sessions)} inactive sessions")
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error(f"Error in cleanup: {e}")
                await asyncio.sleep(1800)  # Retry in 30 minutes

    # Public API methods
    def get_current_status(self) -> Dict[str, Any]:
        """Get current evolutionary status"""
        if not self.snapshots:
            return {
                'status': 'no_data',
                'message': 'No evolutionary data available yet'
            }
        
        latest = self.snapshots[-1]
        
        return {
            'status': 'active',
            'timestamp': latest.timestamp.isoformat(),
            'metrics': {
                'local_processing_ratio': latest.local_processing_ratio,
                'cost_savings_total': latest.cost_savings_total,
                'monthly_projection': latest.monthly_projection,
                'quality_score': latest.quality_score,
                'learning_rate': latest.learning_rate,
                'target_achievement': latest.target_achievement,
                'trend_direction': latest.trend_direction
            },
            'sessions': {
                'active_count': latest.session_count,
                'total_tracked': len(self.active_sessions)
            },
            'alerts': latest.alerts
        }

    def get_evolution_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get evolutionary history for the specified time period"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_snapshots = [s for s in self.snapshots if s.timestamp > cutoff]
        
        return [asdict(snapshot) for snapshot in recent_snapshots]

    def get_session_details(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get details for a specific session or all sessions"""
        if session_id:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                return {
                    'session_id': session_id,
                    'start_time': session['start_time'].isoformat(),
                    'last_update': session['last_update'].isoformat(),
                    'metrics': session
                }
            else:
                return {'error': 'Session not found'}
        else:
            return {
                'active_sessions': len(self.active_sessions),
                'sessions': {
                    sid: {
                        'start_time': session['start_time'].isoformat(),
                        'last_update': session['last_update'].isoformat(),
                        'local_processing_ratio': session['local_successes'] / max(session['total_requests'], 1),
                        'cost_savings': session['cost_savings']
                    }
                    for sid, session in self.active_sessions.items()
                }
            }

# Global instance
evolutionary_monitor = EvolutionaryMonitor()