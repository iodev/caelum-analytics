"""
Intelligent Tool Pre-screening System for External LLMs

Reduces 100+ tools to relevant subset based on query analysis.
Critical for GitHub Copilot and other tool-limited LLMs.
"""

from typing import Dict, List, Set, Optional, Any
import re
import json
from dataclasses import dataclass
from pathlib import Path
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class ToolMetadata:
    """Metadata for a single MCP tool"""
    name: str
    server: str
    category: str
    keywords: List[str]
    description: str
    parameters: List[str]
    use_cases: List[str]
    priority: int  # 1-5, 5 = highest priority

@dataclass
class QueryAnalysis:
    """Analysis results for a user query"""
    intent: str  # code, business, security, deployment, etc.
    entities: List[str]  # extracted entities
    keywords: Set[str]
    complexity: str  # simple, moderate, complex
    estimated_tools_needed: int

class ToolPreScreener:
    """
    Pre-screens tools for external LLMs with tool count limits
    """
    
    def __init__(self, max_tools: int = 100):
        self.max_tools = max_tools
        self.tool_registry: Dict[str, ToolMetadata] = {}
        self.category_weights = {
            "core": 5,
            "analysis": 4, 
            "development": 4,
            "business": 3,
            "security": 3,
            "infrastructure": 2,
            "monitoring": 1
        }
        self.intent_tool_mapping = {
            "code_analysis": ["caelum-code-analysis", "caelum-project-intelligence"],
            "business_research": ["caelum-business-intelligence", "caelum-opportunity-discovery"],
            "development": ["caelum-development-session", "caelum-code-analysis"],
            "deployment": ["caelum-device-orchestration", "caelum-workflow-orchestration"],
            "security": ["caelum-security-compliance"],
            "communication": ["caelum-notifications", "caelum-cluster-communication"],
            "optimization": ["caelum-ollama-pool", "caelum-performance-optimization"]
        }
        
    async def initialize_tool_registry(self):
        """Initialize the tool registry from MCP server configurations"""
        await self._scan_caelum_tools()
        await self._load_external_tools()
        logger.info(f"Initialized tool registry with {len(self.tool_registry)} tools")
        
    async def _scan_caelum_tools(self):
        """Scan Caelum MCP servers for available tools"""
        caelum_path = Path("/mnt/d/swdatasci/caelum")
        
        # Define tool metadata for key Caelum servers
        caelum_tools = {
            "caelum-code-analysis": {
                "category": "analysis",
                "keywords": ["code", "security", "quality", "performance", "analyze", "review"],
                "tools": ["analyze_code", "get_code_statistics", "search_similar_code"],
                "priority": 5
            },
            "caelum-business-intelligence": {
                "category": "business", 
                "keywords": ["market", "research", "business", "intelligence", "competitor", "analysis"],
                "tools": ["research_market"],
                "priority": 4
            },
            "caelum-ollama-pool": {
                "category": "core",
                "keywords": ["llm", "route", "optimization", "cost", "local", "processing"],
                "tools": ["route_llm_request", "get_pool_health_status", "optimize_model_distribution"],
                "priority": 5
            },
            "caelum-project-intelligence": {
                "category": "development",
                "keywords": ["project", "analyze", "dependencies", "intelligence"],
                "tools": ["analyze_project", "list_projects", "get_project_details"],
                "priority": 4
            },
            "caelum-device-orchestration": {
                "category": "infrastructure",
                "keywords": ["device", "orchestration", "deployment", "infrastructure"],
                "tools": ["list_devices", "register_device", "execute_command", "deploy_mcp_server"],
                "priority": 3
            },
            "caelum-notifications": {
                "category": "communication",
                "keywords": ["notification", "alert", "message", "communication"],
                "tools": ["send_notification", "list_notifications", "get_notification_status"],
                "priority": 3
            },
            "filesystem": {
                "category": "core",
                "keywords": ["file", "directory", "read", "write", "filesystem"],
                "tools": ["read_text_file", "write_file", "list_directory", "search_files"],
                "priority": 5
            }
        }
        
        for server_name, metadata in caelum_tools.items():
            for tool_name in metadata["tools"]:
                self.tool_registry[f"{server_name}::{tool_name}"] = ToolMetadata(
                    name=tool_name,
                    server=server_name,
                    category=metadata["category"],
                    keywords=metadata["keywords"],
                    description=f"{tool_name} from {server_name}",
                    parameters=[],
                    use_cases=[],
                    priority=metadata["priority"]
                )
                
    async def _load_external_tools(self):
        """Load external tools (Claude Code built-ins, etc.)"""
        external_tools = {
            "Read": {"category": "core", "keywords": ["read", "file", "content"], "priority": 5},
            "Write": {"category": "core", "keywords": ["write", "file", "create"], "priority": 5},
            "Edit": {"category": "core", "keywords": ["edit", "modify", "change"], "priority": 5},
            "Bash": {"category": "core", "keywords": ["command", "execute", "shell"], "priority": 5},
            "Grep": {"category": "analysis", "keywords": ["search", "find", "pattern"], "priority": 4},
            "Glob": {"category": "analysis", "keywords": ["file", "pattern", "match"], "priority": 4},
            "TodoWrite": {"category": "development", "keywords": ["todo", "task", "track"], "priority": 3}
        }
        
        for tool_name, metadata in external_tools.items():
            self.tool_registry[f"claude-code::{tool_name}"] = ToolMetadata(
                name=tool_name,
                server="claude-code",
                category=metadata["category"],
                keywords=metadata["keywords"],
                description=f"Claude Code built-in: {tool_name}",
                parameters=[],
                use_cases=[],
                priority=metadata["priority"]
            )
    
    async def analyze_query(self, query: str, context: Dict[str, Any] = None) -> QueryAnalysis:
        """Analyze user query to understand intent and requirements"""
        query_lower = query.lower()
        
        # Intent classification
        intent = self._classify_intent(query_lower)
        
        # Extract entities and keywords
        entities = self._extract_entities(query)
        keywords = set(re.findall(r'\b\w+\b', query_lower))
        
        # Assess complexity
        complexity = self._assess_complexity(query, context or {})
        
        # Estimate tools needed
        estimated_tools = self._estimate_tools_needed(intent, complexity)
        
        return QueryAnalysis(
            intent=intent,
            entities=entities,
            keywords=keywords,
            complexity=complexity,
            estimated_tools_needed=estimated_tools
        )
    
    def _classify_intent(self, query: str) -> str:
        """Classify the primary intent of the query"""
        intent_patterns = {
            "code_analysis": r"\b(analyze|review|code|quality|security|performance|bug|error)\b",
            "business_research": r"\b(market|business|research|competitor|intelligence|opportunity)\b",
            "development": r"\b(develop|create|build|implement|session|time|track)\b",
            "deployment": r"\b(deploy|infrastructure|server|orchestration|device)\b", 
            "security": r"\b(security|compliance|audit|encrypt|vulnerability)\b",
            "communication": r"\b(notify|alert|message|communication|send)\b",
            "optimization": r"\b(optimize|performance|cost|efficiency|local)\b"
        }
        
        for intent, pattern in intent_patterns.items():
            if re.search(pattern, query):
                return intent
                
        return "general"
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract relevant entities from the query"""
        # Simple entity extraction - can be enhanced with NLP
        entities = []
        
        # File extensions
        file_patterns = re.findall(r'\.\w+\b', query)
        entities.extend(file_patterns)
        
        # Technology mentions
        tech_patterns = re.findall(r'\b(python|javascript|typescript|node|react|api|database)\b', query.lower())
        entities.extend(tech_patterns)
        
        return entities
    
    def _assess_complexity(self, query: str, context: Dict[str, Any]) -> str:
        """Assess the complexity of the query"""
        factors = 0
        
        # Length factor
        if len(query.split()) > 20:
            factors += 1
            
        # Multiple intents
        intents_found = sum(1 for pattern in [
            r"\b(and|also|additionally|furthermore)\b",
            r"\b(then|after|next|subsequently)\b"
        ] if re.search(pattern, query.lower()))
        factors += intents_found
        
        # Technical complexity
        if re.search(r"\b(integrate|implement|architecture|system|complex)\b", query.lower()):
            factors += 1
            
        # Context factors
        if context.get("multi_step", False):
            factors += 1
            
        if factors >= 3:
            return "complex"
        elif factors >= 1:
            return "moderate"
        else:
            return "simple"
    
    def _estimate_tools_needed(self, intent: str, complexity: str) -> int:
        """Estimate number of tools needed based on intent and complexity"""
        base_estimates = {
            "code_analysis": 15,
            "business_research": 10,
            "development": 20,
            "deployment": 12,
            "security": 8,
            "communication": 6,
            "optimization": 10,
            "general": 25
        }
        
        complexity_multipliers = {
            "simple": 0.6,
            "moderate": 1.0,
            "complex": 1.5
        }
        
        base = base_estimates.get(intent, 25)
        multiplier = complexity_multipliers.get(complexity, 1.0)
        
        return min(int(base * multiplier), self.max_tools)
    
    async def prescreen_tools(self, query: str, context: Dict[str, Any] = None) -> List[str]:
        """
        Pre-screen tools based on query analysis
        Returns list of relevant tool names within limit
        """
        analysis = await self.analyze_query(query, context)
        
        # Get relevant servers for this intent
        relevant_servers = self.intent_tool_mapping.get(analysis.intent, [])
        
        # Score all tools
        tool_scores = {}
        for tool_key, tool_meta in self.tool_registry.items():
            score = self._score_tool_relevance(tool_meta, analysis, relevant_servers)
            if score > 0:
                tool_scores[tool_key] = score
        
        # Sort by score and take top tools
        sorted_tools = sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
        selected_tools = [tool_key for tool_key, _ in sorted_tools[:analysis.estimated_tools_needed]]
        
        # Always include core tools
        core_tools = [k for k, v in self.tool_registry.items() if v.category == "core"]
        selected_tools.extend([t for t in core_tools if t not in selected_tools])
        
        # Trim to max_tools limit
        final_tools = selected_tools[:self.max_tools]
        
        logger.info(f"Pre-screened {len(self.tool_registry)} tools down to {len(final_tools)} for query intent: {analysis.intent}")
        
        return final_tools
    
    def _score_tool_relevance(self, tool: ToolMetadata, analysis: QueryAnalysis, relevant_servers: List[str]) -> float:
        """Score tool relevance for the given query analysis"""
        score = 0.0
        
        # Base priority score
        score += tool.priority * 2
        
        # Server relevance
        if tool.server in relevant_servers:
            score += 10
            
        # Keyword matching
        keyword_matches = len(set(tool.keywords) & analysis.keywords)
        score += keyword_matches * 3
        
        # Category weight
        score += self.category_weights.get(tool.category, 1)
        
        # Intent-specific boosts
        if analysis.intent == "code_analysis" and "code" in tool.keywords:
            score += 5
        elif analysis.intent == "business_research" and "business" in tool.keywords:
            score += 5
        elif analysis.intent == "security" and "security" in tool.keywords:
            score += 5
            
        return score
    
    async def get_prescreening_report(self, query: str) -> Dict[str, Any]:
        """Generate a detailed pre-screening report"""
        analysis = await self.analyze_query(query)
        selected_tools = await self.prescreen_tools(query)
        
        return {
            "query_analysis": {
                "intent": analysis.intent,
                "complexity": analysis.complexity,
                "estimated_tools_needed": analysis.estimated_tools_needed,
                "entities": analysis.entities,
                "keywords": list(analysis.keywords)[:10]  # Top 10
            },
            "tool_selection": {
                "total_available": len(self.tool_registry),
                "selected_count": len(selected_tools),
                "reduction_percentage": round((1 - len(selected_tools) / len(self.tool_registry)) * 100, 1),
                "selected_tools": selected_tools
            },
            "server_distribution": self._get_server_distribution(selected_tools),
            "recommendations": self._generate_recommendations(analysis, selected_tools)
        }
    
    def _get_server_distribution(self, selected_tools: List[str]) -> Dict[str, int]:
        """Get distribution of tools by server"""
        distribution = {}
        for tool_key in selected_tools:
            server = tool_key.split("::")[0]
            distribution[server] = distribution.get(server, 0) + 1
        return distribution
    
    def _generate_recommendations(self, analysis: QueryAnalysis, selected_tools: List[str]) -> List[str]:
        """Generate recommendations based on tool selection"""
        recommendations = []
        
        if len(selected_tools) > 80:
            recommendations.append("Consider breaking complex query into smaller parts")
            
        if analysis.intent == "development" and "caelum-development-session" not in [t.split("::")[0] for t in selected_tools]:
            recommendations.append("Consider using development session tracking tools")
            
        if analysis.complexity == "complex":
            recommendations.append("Use caelum-workflow-orchestration for multi-step processes")
            
        return recommendations

# Global pre-screener instance
tool_prescreener = ToolPreScreener(max_tools=100)