"""
Template for Workflow-Based MCP Server

This template shows how to create a workflow server that:
1. Exposes only relevant tools based on context
2. Routes internally to multiple underlying services
3. Stays within external LLM tool limits
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
import asyncio
import json

class QueryIntent(Enum):
    """Common query intents across workflows"""
    ANALYZE = "analyze"
    CREATE = "create"
    MANAGE = "manage"
    MONITOR = "monitor"
    OPTIMIZE = "optimize"
    RESEARCH = "research"

class WorkflowContext:
    """Context for workflow tool selection"""
    def __init__(self, intent: QueryIntent, complexity: str, entities: List[str]):
        self.intent = intent
        self.complexity = complexity  # simple, moderate, complex
        self.entities = entities
        self.max_tools = 20  # Default max tools to expose

class WorkflowTool:
    """Represents a workflow tool with metadata"""
    def __init__(self, name: str, description: str, category: str, priority: int, underlying_service: str):
        self.name = name
        self.description = description
        self.category = category
        self.priority = priority  # 1-5, 5 = highest
        self.underlying_service = underlying_service

class BaseWorkflowServer(ABC):
    """Base class for all workflow servers"""
    
    def __init__(self, name: str):
        self.name = name
        self.all_tools: Dict[str, WorkflowTool] = {}
        self.service_clients: Dict[str, Any] = {}
        
    @abstractmethod
    async def register_tools(self):
        """Register all available tools for this workflow"""
        pass
    
    @abstractmethod
    async def initialize_services(self):
        """Initialize connections to underlying services"""
        pass
    
    def analyze_query_context(self, query: str) -> WorkflowContext:
        """Analyze query to determine context and intent"""
        query_lower = query.lower()
        
        # Simple intent detection
        if any(word in query_lower for word in ["analyze", "review", "check", "examine"]):
            intent = QueryIntent.ANALYZE
        elif any(word in query_lower for word in ["create", "build", "generate", "make"]):
            intent = QueryIntent.CREATE
        elif any(word in query_lower for word in ["manage", "organize", "handle"]):
            intent = QueryIntent.MANAGE
        elif any(word in query_lower for word in ["monitor", "track", "watch"]):
            intent = QueryIntent.MONITOR
        elif any(word in query_lower for word in ["optimize", "improve", "enhance"]):
            intent = QueryIntent.OPTIMIZE
        elif any(word in query_lower for word in ["research", "find", "discover"]):
            intent = QueryIntent.RESEARCH
        else:
            intent = QueryIntent.ANALYZE  # Default
            
        # Assess complexity
        complexity = "complex" if len(query.split()) > 20 else "moderate" if len(query.split()) > 10 else "simple"
        
        # Extract entities (simplified)
        entities = []
        
        return WorkflowContext(intent, complexity, entities)
    
    def select_relevant_tools(self, context: WorkflowContext) -> List[WorkflowTool]:
        """Select relevant tools based on query context"""
        scored_tools = []
        
        for tool in self.all_tools.values():
            score = self._score_tool_relevance(tool, context)
            if score > 0:
                scored_tools.append((tool, score))
                
        # Sort by score and take top tools
        scored_tools.sort(key=lambda x: x[1], reverse=True)
        selected = [tool for tool, _ in scored_tools[:context.max_tools]]
        
        return selected
    
    def _score_tool_relevance(self, tool: WorkflowTool, context: WorkflowContext) -> float:
        """Score tool relevance for the given context"""
        score = tool.priority * 2  # Base priority score
        
        # Intent-based scoring
        intent_tool_mapping = {
            QueryIntent.ANALYZE: ["analyze", "review", "check", "scan"],
            QueryIntent.CREATE: ["create", "generate", "build", "make"],
            QueryIntent.MANAGE: ["manage", "organize", "handle", "control"],
            QueryIntent.MONITOR: ["monitor", "track", "watch", "observe"],
            QueryIntent.OPTIMIZE: ["optimize", "improve", "enhance", "boost"],
            QueryIntent.RESEARCH: ["research", "find", "discover", "search"]
        }
        
        intent_keywords = intent_tool_mapping.get(context.intent, [])
        if any(keyword in tool.name.lower() or keyword in tool.description.lower() for keyword in intent_keywords):
            score += 5
            
        return score
    
    async def route_to_service(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Route tool call to appropriate underlying service"""
        if tool_name not in self.all_tools:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        tool = self.all_tools[tool_name]
        service = self.service_clients.get(tool.underlying_service)
        
        if not service:
            raise ValueError(f"Service not available: {tool.underlying_service}")
            
        # This would call the actual underlying service
        # For now, return mock response
        return {
            "tool": tool_name,
            "service": tool.underlying_service,
            "result": f"Mock result from {tool.underlying_service} for {tool_name}",
            "args": args
        }

class DevelopmentWorkflowServer(BaseWorkflowServer):
    """Development workflow server implementation"""
    
    def __init__(self):
        super().__init__("caelum-development-workflow")
        
    async def register_tools(self):
        """Register development workflow tools"""
        self.all_tools = {
            "analyze_code_quality": WorkflowTool(
                "analyze_code_quality",
                "Analyze code for quality, security, and performance issues",
                "analysis",
                5,
                "caelum-code-analysis"
            ),
            "analyze_project_structure": WorkflowTool(
                "analyze_project_structure", 
                "Analyze project structure and dependencies",
                "analysis",
                4,
                "caelum-project-intelligence"
            ),
            "track_development_session": WorkflowTool(
                "track_development_session",
                "Track development time and productivity metrics", 
                "management",
                3,
                "caelum-development-session"
            ),
            "search_code_patterns": WorkflowTool(
                "search_code_patterns",
                "Find similar code patterns across projects",
                "analysis", 
                4,
                "caelum-code-analysis"
            ),
            "get_development_metrics": WorkflowTool(
                "get_development_metrics",
                "Get development progress and productivity statistics",
                "monitoring",
                3,
                "caelum-development-session"
            ),
            "optimize_code_performance": WorkflowTool(
                "optimize_code_performance",
                "Get performance optimization suggestions",
                "optimization",
                4,
                "caelum-code-analysis"
            ),
            "create_project_template": WorkflowTool(
                "create_project_template",
                "Create new project from template",
                "creation",
                3,
                "caelum-project-intelligence"
            ),
            "review_code_changes": WorkflowTool(
                "review_code_changes", 
                "Review code changes for quality and security",
                "analysis",
                5,
                "caelum-code-analysis"
            ),
            "manage_project_dependencies": WorkflowTool(
                "manage_project_dependencies",
                "Manage and update project dependencies",
                "management",
                4,
                "caelum-project-intelligence"
            ),
            "generate_development_report": WorkflowTool(
                "generate_development_report",
                "Generate comprehensive development progress report",
                "reporting", 
                3,
                "caelum-development-session"
            )
        }
        
    async def initialize_services(self):
        """Initialize connections to underlying development services"""
        self.service_clients = {
            "caelum-code-analysis": "MockCodeAnalysisClient()",
            "caelum-project-intelligence": "MockProjectIntelligenceClient()",
            "caelum-development-session": "MockDevelopmentSessionClient()"
        }

class BusinessWorkflowServer(BaseWorkflowServer):
    """Business intelligence workflow server implementation"""
    
    def __init__(self):
        super().__init__("caelum-business-workflow")
        
    async def register_tools(self):
        """Register business workflow tools"""
        self.all_tools = {
            "research_market_intelligence": WorkflowTool(
                "research_market_intelligence",
                "Conduct comprehensive market research and analysis",
                "research",
                5,
                "caelum-business-intelligence"
            ),
            "discover_business_opportunities": WorkflowTool(
                "discover_business_opportunities",
                "Identify and analyze business opportunities",
                "research",
                5,
                "caelum-opportunity-discovery"
            ),
            "analyze_competitive_landscape": WorkflowTool(
                "analyze_competitive_landscape",
                "Analyze competitors and market positioning",
                "analysis",
                4,
                "caelum-business-intelligence"
            ),
            "generate_business_insights": WorkflowTool(
                "generate_business_insights",
                "Generate actionable business intelligence reports",
                "analysis",
                4,
                "caelum-business-intelligence"
            ),
            "track_user_preferences": WorkflowTool(
                "track_user_preferences",
                "Manage user profiles and preferences",
                "management",
                3,
                "caelum-user-profile"
            ),
            "forecast_market_trends": WorkflowTool(
                "forecast_market_trends",
                "Forecast market trends and opportunities",
                "analysis",
                4,
                "caelum-business-intelligence"
            )
        }
        
    async def initialize_services(self):
        """Initialize connections to underlying business services"""
        self.service_clients = {
            "caelum-business-intelligence": "MockBusinessIntelligenceClient()",
            "caelum-opportunity-discovery": "MockOpportunityDiscoveryClient()",
            "caelum-user-profile": "MockUserProfileClient()"
        }

# Example usage
async def demo_workflow_server():
    """Demonstrate workflow server functionality"""
    
    # Create development workflow server
    dev_server = DevelopmentWorkflowServer()
    await dev_server.register_tools()
    await dev_server.initialize_services()
    
    # Test query analysis and tool selection
    test_queries = [
        "analyze the security vulnerabilities in my Python code",
        "create a new React project with TypeScript", 
        "track my development productivity this week",
        "optimize the performance of my database queries"
    ]
    
    for query in test_queries:
        print(f"\n=== Query: {query} ===")
        
        context = dev_server.analyze_query_context(query)
        print(f"Intent: {context.intent.value}")
        print(f"Complexity: {context.complexity}")
        
        relevant_tools = dev_server.select_relevant_tools(context)
        print(f"Selected {len(relevant_tools)} tools:")
        
        for tool in relevant_tools[:5]:  # Show top 5
            print(f"  • {tool.name} - {tool.description}")

if __name__ == "__main__":
    asyncio.run(demo_workflow_server())