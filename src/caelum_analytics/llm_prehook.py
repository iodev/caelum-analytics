"""
Pre-hook System for External LLM Integration

Intelligently filters MCP tools before sending to external LLMs like GitHub Copilot
that have tool count limits (e.g., 100 tools max).
"""

from typing import Dict, List, Any, Optional, Callable
import asyncio
import json
from datetime import datetime
from pathlib import Path

from .tool_prescreener import tool_prescreener, QueryAnalysis
from .evolutionary_monitor import evolutionary_monitor
import logging

logger = logging.getLogger(__name__)

class LLMPreHook:
    """
    Pre-hook system that intercepts requests to external LLMs
    and pre-screens tools to stay within limits
    """
    
    def __init__(self):
        self.prescreener = tool_prescreener
        self.monitor = evolutionary_monitor
        self.hook_enabled = True
        self.external_llm_configs = {
            "github-copilot": {
                "max_tools": 100,
                "priority_categories": ["core", "analysis", "development"],
                "cost_per_request": 0.002  # Estimated
            },
            "openai-gpt4": {
                "max_tools": 128,
                "priority_categories": ["core", "analysis", "business"],
                "cost_per_request": 0.03
            },
            "anthropic-claude": {
                "max_tools": 200,  # Higher limit
                "priority_categories": ["core", "analysis", "development", "business"],
                "cost_per_request": 0.015
            }
        }
        
    async def initialize(self):
        """Initialize the pre-hook system"""
        await self.prescreener.initialize_tool_registry()
        logger.info("LLM Pre-hook system initialized")
        
    async def intercept_external_llm_request(
        self, 
        llm_provider: str,
        query: str, 
        available_tools: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Intercept and pre-process external LLM requests
        
        Args:
            llm_provider: Provider name (github-copilot, openai-gpt4, etc.)
            query: User query
            available_tools: All available tools
            context: Additional context
            
        Returns:
            Modified request with filtered tools and metadata
        """
        if not self.hook_enabled:
            return {
                "query": query,
                "tools": available_tools,
                "modified": False
            }
            
        start_time = datetime.utcnow()
        
        # Get LLM configuration
        llm_config = self.external_llm_configs.get(llm_provider, {
            "max_tools": 100,
            "priority_categories": ["core"],
            "cost_per_request": 0.01
        })
        
        # Update prescreener max tools for this provider
        self.prescreener.max_tools = llm_config["max_tools"]
        
        try:
            # Pre-screen tools
            relevant_tool_keys = await self.prescreener.prescreen_tools(query, context)
            
            # Filter available tools to only relevant ones
            filtered_tools = []
            tool_name_map = {tool.get("name", ""): tool for tool in available_tools}
            
            for tool_key in relevant_tool_keys:
                tool_name = tool_key.split("::")[-1]  # Extract tool name
                if tool_name in tool_name_map:
                    filtered_tools.append(tool_name_map[tool_name])
                    
            # Calculate cost savings
            original_count = len(available_tools)
            filtered_count = len(filtered_tools)
            cost_savings = self._calculate_cost_savings(
                original_count, 
                filtered_count, 
                llm_config["cost_per_request"]
            )
            
            # Log the optimization
            await self._log_optimization(
                llm_provider=llm_provider,
                query=query,
                original_tools=original_count,
                filtered_tools=filtered_count,
                cost_savings=cost_savings,
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
            
            return {
                "query": query,
                "tools": filtered_tools,
                "modified": True,
                "optimization_metadata": {
                    "original_tool_count": original_count,
                    "filtered_tool_count": filtered_count,
                    "reduction_percentage": round((1 - filtered_count / original_count) * 100, 1),
                    "cost_savings_estimate": cost_savings,
                    "llm_provider": llm_provider,
                    "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds()
                }
            }
            
        except Exception as e:
            logger.error(f"Pre-hook processing failed: {e}")
            # Fallback: return original request
            return {
                "query": query,
                "tools": available_tools[:llm_config["max_tools"]],  # Simple truncation
                "modified": True,
                "error": str(e)
            }
    
    def _calculate_cost_savings(self, original_count: int, filtered_count: int, cost_per_request: float) -> float:
        """Calculate estimated cost savings from tool reduction"""
        if original_count <= 100:
            return 0.0  # No savings if already under limit
            
        # Assume cost scales with tool count complexity
        original_cost = cost_per_request * (original_count / 100)
        filtered_cost = cost_per_request * (filtered_count / 100)
        
        return max(0, original_cost - filtered_cost)
    
    async def _log_optimization(
        self, 
        llm_provider: str,
        query: str,
        original_tools: int,
        filtered_tools: int,
        cost_savings: float,
        processing_time: float
    ):
        """Log optimization metrics for monitoring"""
        optimization_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "llm_provider": llm_provider,
            "query_length": len(query),
            "original_tool_count": original_tools,
            "filtered_tool_count": filtered_tools,
            "reduction_percentage": round((1 - filtered_tools / original_tools) * 100, 1),
            "cost_savings": cost_savings,
            "processing_time_seconds": processing_time,
            "efficiency_ratio": filtered_tools / max(original_tools, 1)
        }
        
        # Log to evolutionary monitor for tracking
        if hasattr(self.monitor, 'log_cost_optimization'):
            await self.monitor.log_cost_optimization(optimization_data)
            
        logger.info(f"LLM Pre-hook: {llm_provider} - Reduced {original_tools} → {filtered_tools} tools ({optimization_data['reduction_percentage']}% reduction)")
        
    async def get_optimization_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate optimization report for the specified time period"""
        # This would integrate with evolutionary_monitor to get historical data
        return {
            "period_hours": hours,
            "total_optimizations": 0,  # Would be populated from historical data
            "average_reduction_percentage": 0,
            "total_cost_savings": 0,
            "top_providers": {},
            "optimization_trends": []
        }
    
    def configure_llm_provider(
        self, 
        provider: str, 
        max_tools: int, 
        cost_per_request: float,
        priority_categories: List[str] = None
    ):
        """Configure settings for a specific LLM provider"""
        self.external_llm_configs[provider] = {
            "max_tools": max_tools,
            "priority_categories": priority_categories or ["core"],
            "cost_per_request": cost_per_request
        }
        logger.info(f"Configured LLM provider: {provider} (max_tools: {max_tools})")
        
    def enable_hook(self):
        """Enable the pre-hook system"""
        self.hook_enabled = True
        logger.info("LLM Pre-hook system enabled")
        
    def disable_hook(self):
        """Disable the pre-hook system"""
        self.hook_enabled = False
        logger.info("LLM Pre-hook system disabled")

# Global pre-hook instance
llm_prehook = LLMPreHook()