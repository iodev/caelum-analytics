"""
Self-Optimization System for Caelum Analytics

This module provides a complete self-optimization system that integrates with 
existing Caelum infrastructure to implement the 5-phase optimization cycle:

1. OBSERVE: Track behavior patterns and performance
2. MONITOR: Real-time performance monitoring with alerts  
3. SUGGEST: Intelligence-driven optimization suggestions
4. IMPLEMENT: Execute changes through workflow systems
5. EVALUATE: Measure impact and adapt principles

OVERARCHING PRINCIPLES (learned from implementation):
===============================================

1. WORKFLOW-CENTRIC ORGANIZATION
   - Route all optimizations through the 5-workflow architecture
   - Maintain context boundaries between workflow domains
   - Leverage workflow-specific tool selection

2. EXTERNAL LLM COMPATIBILITY FIRST
   - Always consider tool limits (GitHub Copilot: 100, OpenAI: 128)
   - Use pre-hook filtering for intelligent tool selection
   - Prioritize high-value tools over quantity

3. INTELLIGENCE-DRIVEN DECISIONS
   - Use Caelum's business intelligence for optimization choices
   - Leverage code analysis for technical improvements  
   - Apply market research to optimization strategies

4. DYNAMIC ADAPTATION
   - Continuously adapt based on real-time performance data
   - Learn from successful optimization patterns
   - Adjust strategies based on trend analysis

5. HIERARCHICAL TOOL ORGANIZATION
   - Organize tools by workflow and capability hierarchies
   - Enable dynamic exploration of tool landscapes
   - Support expandable browsing for complex systems

Usage:
------
from caelum_analytics.self_optimization import start_self_optimization, get_current_principles

# Initialize the system
await start_self_optimization()

# Get learned principles
principles = get_current_principles()
"""

import asyncio
import logging
from typing import Dict, Any

from .self_observer import self_observer
from .performance_monitor import performance_monitor
from .change_suggester import change_suggester
from .caelum_integration import caelum_self_optimizer

logger = logging.getLogger(__name__)

# System-wide optimization state
_optimization_active = False
_background_task = None

async def start_self_optimization() -> Dict[str, Any]:
    """
    Initialize and start the complete self-optimization system
    
    This integrates with existing Caelum infrastructure and begins:
    - Self-observation and behavior tracking
    - Performance monitoring with real-time alerts
    - Intelligence-driven optimization suggestions
    - Automated implementation through workflow servers
    - Continuous learning and principle adaptation
    """
    global _optimization_active, _background_task
    
    if _optimization_active:
        return {"status": "already_active", "message": "Self-optimization system is already running"}
        
    try:
        logger.info("🚀 Starting Caelum Self-Optimization System")
        
        # Initialize all components
        await caelum_self_optimizer.initialize_self_optimization()
        
        # Start background optimization cycles
        _background_task = asyncio.create_task(_continuous_optimization_loop())
        _optimization_active = True
        
        # Get initial state
        principles = caelum_self_optimizer.get_current_principles()
        
        return {
            "status": "started",
            "message": "Self-optimization system initialized successfully",
            "principles_loaded": len(principles['principles']),
            "overarching_principles": list(principles['principles'].keys()),
            "system_components": {
                "observer": "active",
                "monitor": "active", 
                "suggester": "ready",
                "workflow_integration": "connected",
                "principle_learning": "enabled"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to start self-optimization system: {e}")
        return {"status": "error", "message": str(e)}

async def _continuous_optimization_loop():
    """Background loop for continuous optimization"""
    global _optimization_active
    
    while _optimization_active:
        try:
            # Run optimization cycle every hour
            await asyncio.sleep(3600)
            
            if _optimization_active:
                logger.info("🔄 Starting scheduled optimization cycle")
                await caelum_self_optimizer.optimize_using_caelum_intelligence()
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in optimization loop: {e}")
            # Continue despite errors
            
async def stop_self_optimization() -> Dict[str, Any]:
    """Stop the self-optimization system"""
    global _optimization_active, _background_task
    
    _optimization_active = False
    
    if _background_task:
        _background_task.cancel()
        try:
            await _background_task
        except asyncio.CancelledError:
            pass
        _background_task = None
        
    performance_monitor.stop_monitoring()
    
    return {"status": "stopped", "message": "Self-optimization system stopped"}

def get_current_principles() -> Dict[str, Any]:
    """
    Get current overarching principles learned by the system
    
    Returns principles with their evidence strength, conditions, and actions.
    These represent the accumulated wisdom from successful optimizations.
    """
    return caelum_self_optimizer.get_current_principles()

def get_optimization_status() -> Dict[str, Any]:
    """Get current status of the optimization system"""
    
    observer_analysis = self_observer.get_self_analysis()
    performance_summary = performance_monitor.get_performance_summary() 
    optimization_history = caelum_self_optimizer.get_optimization_history()
    
    return {
        "system_active": _optimization_active,
        "current_performance": {
            "success_rate": observer_analysis.get('performance_summary', {}).get('success_rate', 0),
            "monitoring_status": performance_summary.get('monitoring_status', 'unknown'),
            "active_alerts": performance_summary.get('recent_alerts', 0)
        },
        "optimization_cycles": {
            "total_completed": len(optimization_history),
            "recent_success_rate": _calculate_recent_success_rate(optimization_history),
            "last_optimization": optimization_history[-1]['timestamp'] if optimization_history else None
        },
        "principles": {
            "total_learned": len(caelum_self_optimizer.overarching_principles),
            "avg_evidence_strength": _calculate_avg_evidence_strength()
        }
    }

def _calculate_recent_success_rate(history: list) -> float:
    """Calculate success rate of recent optimizations"""
    if not history:
        return 0.0
        
    recent = history[-5:]  # Last 5 optimizations
    successful = sum(1 for opt in recent if opt.get('success', False))
    return successful / len(recent)

def _calculate_avg_evidence_strength() -> float:
    """Calculate average evidence strength of principles"""
    principles = caelum_self_optimizer.overarching_principles
    if not principles:
        return 0.0
        
    return sum(p['evidence_strength'] for p in principles.values()) / len(principles)

async def trigger_optimization_cycle() -> Dict[str, Any]:
    """Manually trigger an optimization cycle"""
    logger.info("🎯 Manually triggered optimization cycle")
    return await caelum_self_optimizer.optimize_using_caelum_intelligence()

def get_system_insights() -> Dict[str, Any]:
    """Get insights about system behavior and learned patterns"""
    
    principles = get_current_principles()
    status = get_optimization_status()
    
    # Generate insights based on accumulated data
    insights = {
        "key_learnings": [],
        "success_patterns": [],
        "areas_for_improvement": [],
        "principle_effectiveness": {}
    }
    
    # Analyze principle effectiveness
    for principle_id, principle in principles['principles'].items():
        effectiveness = principle['evidence_strength']
        insights["principle_effectiveness"][principle_id] = {
            "title": principle['title'],
            "effectiveness_score": effectiveness,
            "category": principle['category'],
            "recommendation": "highly_effective" if effectiveness > 0.8 else "moderately_effective" if effectiveness > 0.6 else "needs_validation"
        }
        
    # Generate key learnings
    if status["optimization_cycles"]["recent_success_rate"] > 0.8:
        insights["key_learnings"].append("High optimization success rate indicates effective principle application")
        
    if status["current_performance"]["success_rate"] > 0.9:
        insights["key_learnings"].append("Consistent high performance suggests well-optimized system")
        
    # Identify success patterns
    strongest_principles = principles.get('strongest_principles', [])
    if strongest_principles:
        top_principle = strongest_principles[0]
        insights["success_patterns"].append(f"'{top_principle[1]['title']}' shows strongest evidence ({top_principle[1]['evidence_strength']:.2f})")
        
    return insights

# Export main functions and principles
__all__ = [
    'start_self_optimization',
    'stop_self_optimization', 
    'get_current_principles',
    'get_optimization_status',
    'get_system_insights',
    'trigger_optimization_cycle'
]

# Make principles easily accessible
OVERARCHING_PRINCIPLES = {
    'WORKFLOW_CENTRIC_ORGANIZATION': {
        'description': 'Route all optimizations through the 5-workflow architecture',
        'key_insight': 'Workflow boundaries provide natural optimization domains'
    },
    'EXTERNAL_LLM_COMPATIBILITY_FIRST': {
        'description': 'Always consider tool limits when optimizing for external LLMs',
        'key_insight': 'Pre-hook filtering enables compatibility with constrained LLMs'
    },
    'INTELLIGENCE_DRIVEN_DECISIONS': {
        'description': 'Use Caelum business intelligence for all optimization choices',
        'key_insight': 'Data-driven decisions outperform intuition-based approaches'
    },
    'DYNAMIC_ADAPTATION': {
        'description': 'Continuously adapt based on real-time performance data',
        'key_insight': 'Systems that learn and adapt outperform static configurations'
    },
    'HIERARCHICAL_TOOL_ORGANIZATION': {
        'description': 'Organize tools hierarchically with dynamic exploration capabilities',
        'key_insight': 'Hierarchical organization scales better than flat tool lists'
    }
}