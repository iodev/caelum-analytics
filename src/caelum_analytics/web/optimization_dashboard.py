"""
Self-Optimization Dashboard API

Provides API endpoints for the self-optimization dashboard that integrates
with the dynamic analytics and server explorer.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
import asyncio
import logging

from ..self_optimization.analytics_integration import enhanced_analytics
from ..self_optimization.caelum_integration import caelum_self_optimizer
from ..self_optimization.performance_monitor import performance_monitor
from ..self_optimization.self_observer import self_observer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/optimization", tags=["Self-Optimization"])

@router.on_event("startup")
async def startup_optimization_dashboard():
    """Initialize optimization dashboard on startup"""
    try:
        await enhanced_analytics.initialize_enhanced_analytics()
        logger.info("🚀 Optimization dashboard initialized")
    except Exception as e:
        logger.error(f"Failed to initialize optimization dashboard: {e}")

@router.get("/ecosystem-analysis")
async def get_enhanced_ecosystem_analysis() -> Dict[str, Any]:
    """Get comprehensive ecosystem analysis with optimization insights"""
    try:
        analysis = await enhanced_analytics.get_enhanced_ecosystem_analysis()
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-dashboard")
async def get_performance_dashboard() -> Dict[str, Any]:
    """Get real-time performance dashboard data"""
    try:
        # Get current performance data
        performance_summary = performance_monitor.get_performance_summary()
        observer_analysis = self_observer.get_self_analysis()
        principles = caelum_self_optimizer.get_current_principles()
        
        # Get server performance mapping
        server_performance = enhanced_analytics.server_performance_map
        
        dashboard_data = {
            "timestamp": "now",
            "system_health": {
                "overall_score": _calculate_overall_health_score(performance_summary, observer_analysis),
                "monitoring_active": performance_summary.get('monitoring_status') == 'active',
                "optimization_active": len(caelum_self_optimizer.active_optimizations) > 0,
                "alerts_count": performance_summary.get('recent_alerts', 0)
            },
            "performance_metrics": {
                "success_rate": observer_analysis.get('performance_summary', {}).get('success_rate', 0.0),
                "avg_response_time": _get_avg_response_time(performance_summary),
                "tool_efficiency": _get_tool_efficiency(performance_summary),
                "error_rate": _get_error_rate(performance_summary)
            },
            "server_performance": server_performance,
            "optimization_insights": {
                "active_principles": len(principles['principles']),
                "avg_principle_strength": principles.get('avg_evidence_strength', 0.0),
                "recent_adaptations": len(enhanced_analytics.real_time_adaptations),
                "optimization_cycles": len(caelum_self_optimizer.active_optimizations)
            },
            "tool_effectiveness": enhanced_analytics.tool_effectiveness_scores,
            "workflow_efficiency": enhanced_analytics.workflow_efficiency_metrics
        }
        
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations")
async def get_optimization_recommendations() -> Dict[str, Any]:
    """Get current optimization recommendations"""
    try:
        recommendations = await enhanced_analytics._generate_ecosystem_recommendations()
        adaptation_opportunities = await enhanced_analytics._identify_adaptation_opportunities()
        
        return {
            "ecosystem_recommendations": recommendations,
            "adaptation_opportunities": adaptation_opportunities,
            "priority_count": len([r for r in recommendations if r['priority'] >= 7]),
            "total_recommendations": len(recommendations) + len(adaptation_opportunities)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/principles")
async def get_optimization_principles() -> Dict[str, Any]:
    """Get learned optimization principles with evidence"""
    try:
        principles = caelum_self_optimizer.get_current_principles()
        
        # Enhance with application statistics
        enhanced_principles = {}
        for principle_id, principle in principles['principles'].items():
            enhanced_principles[principle_id] = {
                **principle,
                "applications_count": 0,  # Would track real usage
                "success_rate": principle.get('evidence_strength', 0.0),
                "last_applied": None,  # Would track last application
                "effectiveness_trend": "stable"  # Would track over time
            }
            
        return {
            "principles": enhanced_principles,
            "summary": {
                "total_principles": len(enhanced_principles),
                "avg_evidence_strength": principles.get('avg_evidence_strength', 0.0),
                "strongest_principle": principles.get('strongest_principles', [{}])[0] if principles.get('strongest_principles') else None,
                "categories": list(set(p['category'] for p in enhanced_principles.values()))
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-trends")
async def get_performance_trends(
    hours: int = Query(24, description="Hours of trend data to retrieve")
) -> Dict[str, Any]:
    """Get performance trends over specified time period"""
    try:
        trends = enhanced_analytics._analyze_performance_trends()
        
        # Add historical context (simulated for demo)
        historical_data = {
            "success_rate": [0.92, 0.91, 0.93, 0.94, 0.93, 0.95],
            "response_time": [35.2, 33.1, 32.8, 30.5, 29.7, 28.9],
            "error_rate": [0.03, 0.025, 0.02, 0.018, 0.015, 0.012],
            "tool_efficiency": [2.1, 2.3, 2.4, 2.6, 2.8, 2.9]
        }
        
        return {
            "trends": trends,
            "historical_data": historical_data,
            "time_period_hours": hours,
            "data_points": len(historical_data["success_rate"]),
            "trend_analysis": {
                "improving_metrics": len([t for t in trends['key_metrics'].values() if t['trend'] == 'improving']),
                "declining_metrics": len([t for t in trends['key_metrics'].values() if t['trend'] == 'declining']),
                "stable_metrics": len([t for t in trends['key_metrics'].values() if t['trend'] == 'stable'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger-optimization")
async def trigger_manual_optimization() -> Dict[str, Any]:
    """Manually trigger an optimization cycle"""
    try:
        result = await caelum_self_optimizer.optimize_using_caelum_intelligence()
        return {
            "trigger_status": "success",
            "optimization_id": result.get("optimization_id"),
            "status": result.get("status"),
            "message": "Manual optimization cycle triggered successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/adapt-real-time")
async def trigger_real_time_adaptation(
    trigger_event: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Trigger real-time adaptation based on event"""
    try:
        adaptation = await enhanced_analytics.generate_real_time_adaptation(trigger_event, context)
        return {
            "adaptation_triggered": True,
            "adaptation_id": adaptation["adaptation_id"],
            "confidence": adaptation["confidence"],
            "expected_impact": adaptation["expected_impact"],
            "recommendations": adaptation["recommendations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/adaptation-history")
async def get_adaptation_history(limit: int = Query(20, description="Number of adaptations to retrieve")) -> Dict[str, Any]:
    """Get recent adaptation history"""
    try:
        adaptations = enhanced_analytics.real_time_adaptations[-limit:]
        
        return {
            "adaptations": adaptations,
            "total_adaptations": len(enhanced_analytics.real_time_adaptations),
            "success_rate": _calculate_adaptation_success_rate(adaptations),
            "most_common_triggers": _analyze_adaptation_triggers(adaptations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimization-impact")
async def get_optimization_impact() -> Dict[str, Any]:
    """Get analysis of optimization impact over time"""
    try:
        impact = enhanced_analytics._calculate_optimization_impact()
        
        # Add trend analysis
        optimization_history = caelum_self_optimizer.get_optimization_history()
        recent_optimizations = optimization_history[-10:] if optimization_history else []
        
        return {
            "impact_summary": impact,
            "recent_performance": {
                "last_10_cycles": len(recent_optimizations),
                "success_rate": len([opt for opt in recent_optimizations if opt.get('success', False)]) / max(1, len(recent_optimizations)),
                "avg_improvement": _calculate_avg_improvement(recent_optimizations)
            },
            "trend_direction": _determine_optimization_trend(optimization_history),
            "recommendations": _generate_impact_recommendations(impact)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-insights")
async def get_comprehensive_system_insights() -> Dict[str, Any]:
    """Get comprehensive insights about the self-optimization system"""
    try:
        # Import the insights function from the main module
        from ..self_optimization import get_system_insights
        
        insights = get_system_insights()
        
        # Enhance with additional analytics
        enhanced_insights = {
            **insights,
            "analytics_integration": {
                "server_analytics_active": len(enhanced_analytics.server_performance_map) > 0,
                "tool_effectiveness_tracked": len(enhanced_analytics.tool_effectiveness_scores) > 0,
                "workflow_efficiency_monitored": len(enhanced_analytics.workflow_efficiency_metrics) > 0,
                "real_time_adaptations": len(enhanced_analytics.real_time_adaptations)
            },
            "ecosystem_health": await _assess_ecosystem_health(),
            "optimization_readiness": _assess_optimization_readiness()
        }
        
        return enhanced_insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lan-sync-status")
async def get_lan_synchronization_status() -> Dict[str, Any]:
    """Get comprehensive LAN synchronization status and health"""
    try:
        from ..self_optimization.lan_synchronization import optimization_synchronizer
        
        # Get basic sync status
        sync_status = optimization_synchronizer.get_sync_status()
        
        # Add detailed analysis
        enhanced_status = {
            **sync_status,
            "sync_health": {
                "overall_health": "healthy" if sync_status["sync_active"] and sync_status["active_nodes"] > 0 else "degraded",
                "network_coverage": f"{sync_status['active_nodes']} of {sync_status['known_nodes']} nodes active",
                "sync_efficiency": _calculate_sync_efficiency(sync_status),
                "last_successful_sync": _get_last_successful_sync_time(sync_status)
            },
            "priority_queue_analysis": {
                "total_items": sync_status["sync_queue_size"],
                "estimated_sync_time": _estimate_queue_processing_time(sync_status["sync_queue_size"]),
                "high_priority_pending": _count_high_priority_items()
            },
            "node_health_summary": {
                "active_nodes": sync_status["active_nodes"],
                "total_nodes": sync_status["known_nodes"],
                "connectivity_ratio": sync_status["active_nodes"] / max(1, sync_status["known_nodes"]),
                "problem_nodes": [node_id for node_id, details in sync_status.get("node_details", {}).items() 
                               if details["status"] != "active"]
            },
            "recommendations": _generate_sync_recommendations(sync_status)
        }
        
        return enhanced_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimization-ecosystem-overview")
async def get_optimization_ecosystem_overview() -> Dict[str, Any]:
    """Get comprehensive overview of the entire optimization ecosystem"""
    try:
        from ..self_optimization.lan_synchronization import optimization_synchronizer
        from ..dynamic_server_explorer import dynamic_explorer
        
        # Get all system components
        ecosystem_data = dynamic_explorer.generate_ecosystem_map()
        sync_status = optimization_synchronizer.get_sync_status()
        performance_dashboard = await get_performance_dashboard()
        optimization_principles = await get_optimization_principles()
        
        # Create comprehensive overview
        ecosystem_overview = {
            "system_architecture": {
                "architecture_type": ecosystem_data["ecosystem_overview"]["architecture_type"],
                "total_servers": ecosystem_data["ecosystem_overview"]["total_servers"],
                "total_tools": ecosystem_data["ecosystem_overview"]["total_tools"],
                "total_workflows": ecosystem_data["ecosystem_overview"]["total_workflows"],
                "external_llm_compatible": ecosystem_data["ecosystem_overview"]["external_llm_compatible"],
                "max_tools_exposed": ecosystem_data["ecosystem_overview"]["max_tools_exposed"]
            },
            "optimization_status": {
                "self_optimization_active": performance_dashboard["system_health"]["optimization_active"],
                "monitoring_active": performance_dashboard["system_health"]["monitoring_active"],
                "overall_health_score": performance_dashboard["system_health"]["overall_score"],
                "active_principles": optimization_principles["summary"]["total_principles"],
                "avg_principle_strength": optimization_principles["summary"]["avg_evidence_strength"],
                "recent_adaptations": performance_dashboard["optimization_insights"]["recent_adaptations"]
            },
            "lan_synchronization": {
                "sync_active": sync_status["sync_active"],
                "connected_instances": sync_status["active_nodes"],
                "total_instances": sync_status["known_nodes"],
                "sync_queue_size": sync_status["sync_queue_size"],
                "last_sync_activity": max(sync_status.get("last_sync_times", {}).values()) if sync_status.get("last_sync_times") else None
            },
            "performance_metrics": {
                "success_rate": performance_dashboard["performance_metrics"]["success_rate"],
                "avg_response_time": performance_dashboard["performance_metrics"]["avg_response_time"],
                "tool_efficiency": performance_dashboard["performance_metrics"]["tool_efficiency"],
                "error_rate": performance_dashboard["performance_metrics"]["error_rate"]
            },
            "server_distribution": {
                "workflow_servers": len([s for s in ecosystem_data["servers"]["workflow_servers"]]),
                "individual_servers": len([s for s in ecosystem_data["servers"]["individual_servers"]]),
                "core_servers": len([s for s in ecosystem_data["servers"]["core_servers"]])
            },
            "capability_coverage": {
                "total_capabilities": len(ecosystem_data["capability_matrix"]),
                "redundant_capabilities": len([cap for cap, servers in ecosystem_data["capability_matrix"].items() if len(servers) > 1]),
                "single_point_capabilities": len([cap for cap, servers in ecosystem_data["capability_matrix"].items() if len(servers) == 1])
            },
            "optimization_readiness": _assess_optimization_readiness(),
            "system_recommendations": await _generate_system_recommendations(ecosystem_data, sync_status, performance_dashboard)
        }
        
        return ecosystem_overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def _calculate_overall_health_score(performance_summary: Dict[str, Any], observer_analysis: Dict[str, Any]) -> float:
    """Calculate overall system health score (0.0-1.0)"""
    
    success_rate = observer_analysis.get('performance_summary', {}).get('success_rate', 0.8)
    monitoring_active = 1.0 if performance_summary.get('monitoring_status') == 'active' else 0.5
    recent_alerts = performance_summary.get('recent_alerts', 0)
    alert_penalty = min(0.3, recent_alerts * 0.05)  # Cap penalty at 30%
    
    health_score = (success_rate * 0.5 + monitoring_active * 0.3 + (1.0 - alert_penalty) * 0.2)
    
    return round(health_score, 3)

def _get_avg_response_time(performance_summary: Dict[str, Any]) -> float:
    """Extract average response time from performance summary"""
    scores = performance_summary.get('performance_scores', {})
    response_time_data = scores.get('avg_response_time', {})
    return response_time_data.get('current_average', 30.0)

def _get_tool_efficiency(performance_summary: Dict[str, Any]) -> float:
    """Extract tool efficiency from performance summary"""
    scores = performance_summary.get('performance_scores', {})
    efficiency_data = scores.get('tool_efficiency', {})
    return efficiency_data.get('current_average', 2.0)

def _get_error_rate(performance_summary: Dict[str, Any]) -> float:
    """Extract error rate from performance summary"""
    scores = performance_summary.get('performance_scores', {})
    error_data = scores.get('error_rate', {})
    return error_data.get('current_average', 0.05)

def _calculate_adaptation_success_rate(adaptations: List[Dict[str, Any]]) -> float:
    """Calculate success rate of recent adaptations"""
    if not adaptations:
        return 0.0
        
    successful = sum(1 for adaptation in adaptations 
                    if adaptation.get('expected_impact', {}).get('expected_improvement', 0) > 0)
    
    return successful / len(adaptations)

def _analyze_adaptation_triggers(adaptations: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze most common adaptation triggers"""
    triggers = {}
    for adaptation in adaptations:
        trigger = adaptation.get('trigger_event', 'unknown')
        triggers[trigger] = triggers.get(trigger, 0) + 1
        
    return dict(sorted(triggers.items(), key=lambda x: x[1], reverse=True))

def _calculate_avg_improvement(optimizations: List[Dict[str, Any]]) -> float:
    """Calculate average improvement from recent optimizations"""
    if not optimizations:
        return 0.0
        
    improvements = []
    for opt in optimizations:
        phases = opt.get('phases', {})
        evaluation = phases.get('evaluation', {})
        success_rate = evaluation.get('success_rate', 0)
        if success_rate > 0:
            improvements.append(success_rate)
            
    return sum(improvements) / len(improvements) if improvements else 0.0

def _determine_optimization_trend(optimization_history: List[Dict[str, Any]]) -> str:
    """Determine if optimization effectiveness is trending up, down, or stable"""
    if len(optimization_history) < 5:
        return "insufficient_data"
        
    recent = optimization_history[-5:]
    older = optimization_history[-10:-5] if len(optimization_history) >= 10 else []
    
    if not older:
        return "stable"
        
    recent_success_rate = sum(1 for opt in recent if opt.get('success', False)) / len(recent)
    older_success_rate = sum(1 for opt in older if opt.get('success', False)) / len(older)
    
    if recent_success_rate > older_success_rate + 0.1:
        return "improving"
    elif recent_success_rate < older_success_rate - 0.1:
        return "declining"
    else:
        return "stable"

def _generate_impact_recommendations(impact: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on optimization impact"""
    recommendations = []
    
    success_rate = impact.get('optimization_roi', 0)
    
    if success_rate < 0.5:
        recommendations.append("Review optimization strategies - success rate is below 50%")
    elif success_rate < 0.7:
        recommendations.append("Fine-tune optimization algorithms to improve success rate")
    else:
        recommendations.append("Optimization effectiveness is good - consider expanding scope")
        
    total_optimizations = impact.get('total_optimizations', 0)
    if total_optimizations < 5:
        recommendations.append("Increase optimization frequency to gather more data")
        
    return recommendations

async def _assess_ecosystem_health() -> Dict[str, Any]:
    """Assess overall ecosystem health"""
    
    server_performance = enhanced_analytics.server_performance_map
    
    if not server_performance:
        return {"status": "unknown", "message": "No server performance data available"}
        
    avg_success_rate = sum(metrics.get('success_rate', 0) for metrics in server_performance.values()) / len(server_performance)
    avg_response_time = sum(metrics.get('response_time', 30) for metrics in server_performance.values()) / len(server_performance)
    avg_error_rate = sum(metrics.get('error_rate', 0.05) for metrics in server_performance.values()) / len(server_performance)
    
    health_score = (avg_success_rate * 0.5 + 
                   (60 / max(avg_response_time, 1)) * 0.3 +  # Normalize response time
                   (1 - avg_error_rate) * 0.2)
    
    if health_score > 0.85:
        status = "excellent"
    elif health_score > 0.75:
        status = "good"
    elif health_score > 0.60:
        status = "fair"
    else:
        status = "needs_attention"
        
    return {
        "status": status,
        "health_score": round(health_score, 3),
        "avg_success_rate": round(avg_success_rate, 3),
        "avg_response_time": round(avg_response_time, 1),
        "avg_error_rate": round(avg_error_rate, 4)
    }

def _assess_optimization_readiness() -> Dict[str, Any]:
    """Assess system readiness for optimization"""
    
    performance_summary = performance_monitor.get_performance_summary()
    observer_analysis = self_observer.get_self_analysis()
    
    readiness_factors = {
        "monitoring_active": performance_summary.get('monitoring_status') == 'active',
        "sufficient_data": performance_summary.get('data_points_collected', 0) > 10,
        "recent_activity": len(observer_analysis.get('areas_for_observation', [])) > 0,
        "principles_learned": len(caelum_self_optimizer.overarching_principles) > 0
    }
    
    readiness_score = sum(readiness_factors.values()) / len(readiness_factors)
    
    return {
        "readiness_score": readiness_score,
        "readiness_factors": readiness_factors,
        "status": "ready" if readiness_score > 0.7 else "partial" if readiness_score > 0.4 else "not_ready",
        "recommendations": _generate_readiness_recommendations(readiness_factors)
    }

def _generate_readiness_recommendations(factors: Dict[str, bool]) -> List[str]:
    """Generate recommendations to improve optimization readiness"""
    recommendations = []
    
    if not factors["monitoring_active"]:
        recommendations.append("Activate performance monitoring")
    if not factors["sufficient_data"]:
        recommendations.append("Collect more performance data before optimizing")
    if not factors["recent_activity"]:
        recommendations.append("Increase system usage to generate optimization opportunities")
    if not factors["principles_learned"]:
        recommendations.append("Allow system to learn from initial optimization cycles")
        
    if not recommendations:
        recommendations.append("System is ready for optimization")
        
    return recommendations

def _calculate_sync_efficiency(sync_status: Dict[str, Any]) -> float:
    """Calculate synchronization efficiency score (0.0-1.0)"""
    if not sync_status["sync_active"]:
        return 0.0
        
    connectivity_ratio = sync_status["active_nodes"] / max(1, sync_status["known_nodes"])
    queue_efficiency = 1.0 - min(1.0, sync_status["sync_queue_size"] / 100)  # Penalty for large queue
    
    return (connectivity_ratio * 0.7 + queue_efficiency * 0.3)

def _get_last_successful_sync_time(sync_status: Dict[str, Any]) -> Optional[str]:
    """Get the timestamp of the most recent successful sync"""
    last_sync_times = sync_status.get("last_sync_times", {})
    if not last_sync_times:
        return None
    
    # Return the most recent sync time
    return max(last_sync_times.values())

def _estimate_queue_processing_time(queue_size: int) -> str:
    """Estimate time to process current sync queue"""
    if queue_size == 0:
        return "No items in queue"
    elif queue_size <= 5:
        return "< 1 minute"
    elif queue_size <= 20:
        return "1-5 minutes"
    elif queue_size <= 50:
        return "5-15 minutes"
    else:
        return "15+ minutes"

def _count_high_priority_items() -> int:
    """Count high priority items in sync queue (simulated)"""
    # In real implementation, would query the actual sync queue
    return 0

def _generate_sync_recommendations(sync_status: Dict[str, Any]) -> List[str]:
    """Generate recommendations for LAN synchronization improvement"""
    recommendations = []
    
    if not sync_status["sync_active"]:
        recommendations.append("Activate LAN synchronization to share optimization data")
    
    if sync_status["active_nodes"] == 0:
        recommendations.append("No active cluster nodes detected - check network connectivity")
    elif sync_status["active_nodes"] < sync_status["known_nodes"]:
        recommendations.append(f"Only {sync_status['active_nodes']} of {sync_status['known_nodes']} nodes active - investigate connection issues")
    
    if sync_status["sync_queue_size"] > 50:
        recommendations.append("Large sync queue detected - consider increasing sync frequency")
    elif sync_status["sync_queue_size"] > 20:
        recommendations.append("Moderate sync queue backlog - monitor for performance impact")
    
    if not recommendations:
        recommendations.append("LAN synchronization operating optimally")
    
    return recommendations

async def _generate_system_recommendations(ecosystem_data: Dict[str, Any], 
                                         sync_status: Dict[str, Any], 
                                         performance_dashboard: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate comprehensive system recommendations"""
    recommendations = []
    
    # Architecture recommendations
    if ecosystem_data["ecosystem_overview"]["total_tools"] > 100:
        recommendations.append({
            "category": "architecture",
            "priority": "medium",
            "title": "Consider tool consolidation",
            "description": f"Current tool count ({ecosystem_data['ecosystem_overview']['total_tools']}) may exceed external LLM limits",
            "impact": "Improve external LLM compatibility"
        })
    
    # Performance recommendations
    health_score = performance_dashboard["system_health"]["overall_score"]
    if health_score < 0.7:
        recommendations.append({
            "category": "performance",
            "priority": "high",
            "title": "System health needs attention",
            "description": f"Overall health score is {health_score:.1%} - below optimal threshold",
            "impact": "Improve system reliability and performance"
        })
    
    # Synchronization recommendations
    if sync_status["active_nodes"] == 0:
        recommendations.append({
            "category": "synchronization",
            "priority": "high",
            "title": "Enable LAN synchronization",
            "description": "No cluster nodes detected - optimization data not being shared",
            "impact": "Enable distributed learning and optimization"
        })
    
    # Optimization recommendations
    if performance_dashboard["optimization_insights"]["active_principles"] < 3:
        recommendations.append({
            "category": "optimization",
            "priority": "medium",
            "title": "Build optimization knowledge base",
            "description": "Few optimization principles learned - system needs more experience",
            "impact": "Improve optimization effectiveness over time"
        })
    
    return recommendations