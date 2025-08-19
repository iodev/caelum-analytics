"""
Development Workflow MCP Server

Consolidates code analysis, project intelligence, and development session management
into a single workflow-focused server with intelligent tool selection.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp import types

logger = logging.getLogger(__name__)

class DevelopmentWorkflowServer:
    """
    Development workflow server that consolidates:
    - caelum-code-analysis
    - caelum-project-intelligence  
    - caelum-development-session
    """
    
    def __init__(self):
        self.app = Server("caelum-development-workflow")
        self.setup_handlers()
        
        # Tool definitions with intelligent selection
        self.all_tools = {
            # Code Analysis Tools
            "analyze_code_quality": {
                "name": "analyze_code_quality",
                "description": "Analyze code for quality, security, and performance issues",
                "priority": 5,
                "category": "analysis",
                "intents": ["analyze", "review", "check"],
                "underlying_service": "caelum-code-analysis",
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to analyze"},
                        "language": {"type": "string", "description": "Programming language"},
                        "analysis_type": {"type": "string", "enum": ["security", "quality", "performance", "all"], "default": "all"}
                    },
                    "required": ["code", "language"]
                }
            },
            
            "search_code_patterns": {
                "name": "search_code_patterns",
                "description": "Find similar code patterns and examples across projects",
                "priority": 4,
                "category": "analysis", 
                "intents": ["search", "find", "discover"],
                "underlying_service": "caelum-code-analysis",
                "schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "Code pattern to search for"},
                        "language": {"type": "string", "description": "Programming language"},
                        "limit": {"type": "integer", "default": 5, "description": "Max results"}
                    },
                    "required": ["pattern", "language"]
                }
            },
            
            "get_code_statistics": {
                "name": "get_code_statistics", 
                "description": "Get comprehensive code metrics and statistics",
                "priority": 3,
                "category": "monitoring",
                "intents": ["monitor", "track", "measure"],
                "underlying_service": "caelum-code-analysis",
                "schema": {
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string", "description": "Path to project"}
                    }
                }
            },
            
            # Project Intelligence Tools
            "analyze_project_structure": {
                "name": "analyze_project_structure",
                "description": "Analyze project structure, dependencies, and architecture",
                "priority": 4,
                "category": "analysis",
                "intents": ["analyze", "understand", "explore"],
                "underlying_service": "caelum-project-intelligence",
                "schema": {
                    "type": "object", 
                    "properties": {
                        "path": {"type": "string", "description": "Project path to analyze"},
                        "include_metrics": {"type": "boolean", "default": true},
                        "use_ai": {"type": "boolean", "default": false}
                    },
                    "required": ["path"]
                }
            },
            
            "list_projects": {
                "name": "list_projects",
                "description": "List analyzed projects with filtering options",
                "priority": 3,
                "category": "management",
                "intents": ["list", "browse", "explore"],
                "underlying_service": "caelum-project-intelligence", 
                "schema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 10},
                        "status": {"type": "string", "enum": ["healthy", "warning", "critical"]},
                        "type": {"type": "string"}
                    }
                }
            },
            
            "get_project_details": {
                "name": "get_project_details",
                "description": "Get detailed information about a specific project",
                "priority": 4,
                "category": "analysis",
                "intents": ["analyze", "inspect", "examine"],
                "underlying_service": "caelum-project-intelligence",
                "schema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "Project ID"}
                    },
                    "required": ["project_id"]
                }
            },
            
            # Development Session Tools
            "track_development_session": {
                "name": "track_development_session",
                "description": "Track development time and productivity metrics",
                "priority": 3,
                "category": "management",
                "intents": ["track", "monitor", "manage"],
                "underlying_service": "caelum-development-session",
                "schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["start", "stop", "pause", "resume"]},
                        "project": {"type": "string", "description": "Project name"},
                        "description": {"type": "string", "description": "Session description"}
                    },
                    "required": ["action"]
                }
            },
            
            "get_development_metrics": {
                "name": "get_development_metrics",
                "description": "Get development productivity and time tracking metrics",
                "priority": 3,
                "category": "monitoring",
                "intents": ["monitor", "measure", "analyze"],
                "underlying_service": "caelum-development-session",
                "schema": {
                    "type": "object",
                    "properties": {
                        "timeframe": {"type": "string", "enum": ["day", "week", "month"], "default": "week"},
                        "project": {"type": "string", "description": "Filter by project"}
                    }
                }
            },
            
            # Cross-cutting Tools
            "optimize_development_workflow": {
                "name": "optimize_development_workflow",
                "description": "Optimize development workflow based on analytics and patterns",
                "priority": 4,
                "category": "optimization",
                "intents": ["optimize", "improve", "enhance"],
                "underlying_service": "workflow-orchestration",
                "schema": {
                    "type": "object",
                    "properties": {
                        "focus_area": {"type": "string", "enum": ["productivity", "quality", "performance", "all"], "default": "all"},
                        "project_path": {"type": "string"}
                    }
                }
            },
            
            "generate_development_report": {
                "name": "generate_development_report",
                "description": "Generate comprehensive development progress and quality report",
                "priority": 3,
                "category": "reporting",
                "intents": ["generate", "create", "report"],
                "underlying_service": "analytics",
                "schema": {
                    "type": "object",
                    "properties": {
                        "timeframe": {"type": "string", "enum": ["day", "week", "month"], "default": "week"},
                        "include_code_analysis": {"type": "boolean", "default": true},
                        "include_project_metrics": {"type": "boolean", "default": true}
                    }
                }
            }
        }
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.app.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available development workflow tools"""
            # Get tools based on context (for now, return all)
            selected_tools = await self.select_tools_for_context()
            
            return [
                types.Tool(
                    name=tool_data["name"],
                    description=tool_data["description"], 
                    inputSchema=tool_data["schema"]
                )
                for tool_name, tool_data in selected_tools.items()
            ]
        
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle development workflow tool calls"""
            try:
                result = await self.execute_tool(name, arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                error_result = {
                    "error": str(e),
                    "tool": name,
                    "timestamp": datetime.now().isoformat()
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    async def select_tools_for_context(self, query: str = "", max_tools: int = 15) -> Dict[str, Dict]:
        """Select most relevant tools based on query context"""
        if not query:
            # Return high-priority tools if no context
            high_priority_tools = {
                name: tool for name, tool in self.all_tools.items() 
                if tool["priority"] >= 4
            }
            return dict(list(high_priority_tools.items())[:max_tools])
        
        # Analyze query intent
        query_lower = query.lower()
        intent = self.detect_intent(query_lower)
        
        # Score and select tools
        scored_tools = []
        for name, tool in self.all_tools.items():
            score = self.score_tool_relevance(tool, intent, query_lower)
            scored_tools.append((name, tool, score))
        
        # Sort by score and return top tools
        scored_tools.sort(key=lambda x: x[2], reverse=True)
        selected = {name: tool for name, tool, _ in scored_tools[:max_tools]}
        
        return selected
    
    def detect_intent(self, query: str) -> str:
        """Detect primary intent from query"""
        intent_patterns = {
            "analyze": ["analyze", "review", "check", "examine", "inspect"],
            "create": ["create", "generate", "build", "make", "develop"],
            "search": ["search", "find", "discover", "locate", "lookup"],
            "track": ["track", "monitor", "measure", "time", "productivity"],
            "optimize": ["optimize", "improve", "enhance", "speed up", "performance"],
            "manage": ["manage", "organize", "control", "handle"]
        }
        
        for intent, keywords in intent_patterns.items():
            if any(keyword in query for keyword in keywords):
                return intent
                
        return "analyze"  # Default intent
    
    def score_tool_relevance(self, tool: Dict, intent: str, query: str) -> float:
        """Score tool relevance for the given intent and query"""
        score = tool["priority"] * 2  # Base priority score
        
        # Intent matching
        if intent in tool["intents"]:
            score += 10
        
        # Keyword matching in description
        tool_keywords = tool["description"].lower().split()
        query_words = set(query.split())
        matching_keywords = len(set(tool_keywords) & query_words)
        score += matching_keywords * 2
        
        # Category relevance
        category_weights = {
            "analysis": 5,
            "management": 4,
            "monitoring": 3,
            "optimization": 4,
            "reporting": 2
        }
        score += category_weights.get(tool["category"], 1)
        
        return score
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a development workflow tool"""
        if tool_name not in self.all_tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool_info = self.all_tools[tool_name]
        underlying_service = tool_info["underlying_service"]
        
        # Route to appropriate service implementation
        if underlying_service == "caelum-code-analysis":
            return await self.handle_code_analysis_tool(tool_name, arguments)
        elif underlying_service == "caelum-project-intelligence":
            return await self.handle_project_intelligence_tool(tool_name, arguments)
        elif underlying_service == "caelum-development-session":
            return await self.handle_development_session_tool(tool_name, arguments)
        else:
            return await self.handle_generic_tool(tool_name, arguments)
    
    async def handle_code_analysis_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code analysis tool calls"""
        # This would integrate with the actual caelum-code-analysis MCP server
        # For now, return structured mock data
        
        if tool_name == "analyze_code_quality":
            return {
                "analysis_type": args.get("analysis_type", "all"),
                "language": args.get("language"),
                "code_length": len(args.get("code", "")),
                "findings": {
                    "security_issues": 2,
                    "quality_issues": 3,
                    "performance_issues": 1,
                    "suggestions": [
                        "Consider using parameterized queries to prevent SQL injection",
                        "Add input validation for user data",
                        "Optimize database query with proper indexing"
                    ]
                },
                "overall_score": 7.5,
                "timestamp": datetime.now().isoformat(),
                "service": "caelum-code-analysis"
            }
            
        elif tool_name == "search_code_patterns":
            return {
                "pattern": args.get("pattern"),
                "language": args.get("language"), 
                "results": [
                    {"file": "src/utils/database.py", "line": 45, "similarity": 0.85},
                    {"file": "src/models/user.py", "line": 123, "similarity": 0.72}
                ],
                "total_found": 2,
                "service": "caelum-code-analysis"
            }
            
        elif tool_name == "get_code_statistics":
            return {
                "project_path": args.get("project_path", ""),
                "statistics": {
                    "total_lines": 15420,
                    "code_lines": 12330,
                    "comment_lines": 2180,
                    "blank_lines": 910,
                    "files_count": 85,
                    "languages": {"Python": 60, "TypeScript": 30, "JSON": 10}
                },
                "quality_metrics": {
                    "code_coverage": 78.5,
                    "cyclomatic_complexity": 3.2,
                    "maintainability_index": 82
                },
                "service": "caelum-code-analysis"
            }
        
        return {"error": f"Unknown code analysis tool: {tool_name}"}
    
    async def handle_project_intelligence_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle project intelligence tool calls"""
        
        if tool_name == "analyze_project_structure":
            return {
                "path": args.get("path"),
                "analysis": {
                    "project_type": "Python Web Application",
                    "framework": "FastAPI",
                    "architecture_pattern": "MVC with Services",
                    "dependencies": {
                        "total": 45,
                        "direct": 12,
                        "outdated": 3,
                        "security_vulnerabilities": 1
                    },
                    "structure_quality": "Good",
                    "recommendations": [
                        "Update outdated dependencies",
                        "Add integration tests",
                        "Consider dependency injection for better testability"
                    ]
                },
                "timestamp": datetime.now().isoformat(),
                "service": "caelum-project-intelligence"
            }
            
        elif tool_name == "list_projects":
            return {
                "projects": [
                    {
                        "id": "proj_001",
                        "name": "caelum-analytics",
                        "type": "Python Web App",
                        "health": "healthy",
                        "last_analyzed": "2025-01-19T10:30:00Z"
                    },
                    {
                        "id": "proj_002", 
                        "name": "workflow-servers",
                        "type": "TypeScript MCP Servers",
                        "health": "warning",
                        "last_analyzed": "2025-01-19T09:15:00Z"
                    }
                ],
                "total_count": 2,
                "service": "caelum-project-intelligence"
            }
            
        elif tool_name == "get_project_details":
            return {
                "project_id": args.get("project_id"),
                "details": {
                    "name": "caelum-analytics",
                    "path": "/mnt/d/swdatasci/caelum-analytics",
                    "type": "Python Web Application",
                    "created": "2025-01-15T00:00:00Z",
                    "last_modified": "2025-01-19T10:30:00Z",
                    "metrics": {
                        "lines_of_code": 15420,
                        "test_coverage": 78.5,
                        "maintainability": 82,
                        "complexity": 3.2
                    },
                    "dependencies": {
                        "python": "3.11",
                        "frameworks": ["FastAPI", "SQLAlchemy", "Pydantic"],
                        "total_dependencies": 45
                    }
                },
                "service": "caelum-project-intelligence"
            }
        
        return {"error": f"Unknown project intelligence tool: {tool_name}"}
    
    async def handle_development_session_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle development session tool calls"""
        
        if tool_name == "track_development_session":
            action = args.get("action")
            return {
                "action": action,
                "project": args.get("project", "default"),
                "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "status": f"Session {action}ed successfully",
                "service": "caelum-development-session"
            }
            
        elif tool_name == "get_development_metrics":
            return {
                "timeframe": args.get("timeframe", "week"),
                "project": args.get("project", "all"),
                "metrics": {
                    "total_hours": 32.5,
                    "coding_hours": 24.2,
                    "debugging_hours": 5.5, 
                    "meeting_hours": 2.8,
                    "productivity_score": 8.2,
                    "sessions_count": 15,
                    "average_session_length": 2.17,
                    "most_productive_time": "10:00-12:00",
                    "projects_worked_on": ["caelum-analytics", "workflow-servers"]
                },
                "trends": {
                    "productivity_trend": "increasing",
                    "focus_improvement": 15.5
                },
                "service": "caelum-development-session"
            }
        
        return {"error": f"Unknown development session tool: {tool_name}"}
    
    async def handle_generic_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic workflow tools"""
        
        if tool_name == "optimize_development_workflow":
            return {
                "focus_area": args.get("focus_area", "all"),
                "optimizations": [
                    {
                        "area": "Code Quality",
                        "suggestion": "Implement automated code review hooks",
                        "impact": "high",
                        "effort": "medium"
                    },
                    {
                        "area": "Productivity", 
                        "suggestion": "Set up dedicated focus time blocks",
                        "impact": "medium",
                        "effort": "low"
                    },
                    {
                        "area": "Performance",
                        "suggestion": "Add performance monitoring to CI/CD",
                        "impact": "high",
                        "effort": "high"
                    }
                ],
                "estimated_improvement": "25-40% productivity increase",
                "service": "workflow-orchestration"
            }
            
        elif tool_name == "generate_development_report":
            return {
                "timeframe": args.get("timeframe", "week"),
                "report": {
                    "summary": {
                        "total_commits": 23,
                        "lines_added": 1240,
                        "lines_removed": 320,
                        "files_modified": 45,
                        "issues_closed": 8,
                        "overall_productivity": 8.5
                    },
                    "code_quality": {
                        "quality_score": 8.2,
                        "security_score": 9.1,
                        "test_coverage": 78.5,
                        "code_duplication": 2.1
                    },
                    "time_tracking": {
                        "total_hours": 32.5,
                        "focused_hours": 28.2,
                        "efficiency": 86.8
                    },
                    "recommendations": [
                        "Increase test coverage to 85%",
                        "Reduce code duplication in utility modules",
                        "Schedule regular code review sessions"
                    ]
                },
                "generated_at": datetime.now().isoformat(),
                "service": "analytics"
            }
        
        return {"error": f"Unknown generic tool: {tool_name}"}

async def main():
    """Run the development workflow MCP server"""
    from mcp.server.stdio import stdio_server
    
    workflow_server = DevelopmentWorkflowServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await workflow_server.app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="caelum-development-workflow",
                server_version="1.0.0",
                capabilities=workflow_server.app.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())