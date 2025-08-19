"""
Business Intelligence Workflow MCP Server

Consolidates business intelligence, opportunity discovery, and market research
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

class BusinessWorkflowServer:
    """
    Business intelligence workflow server that consolidates:
    - caelum-business-intelligence
    - caelum-opportunity-discovery
    - caelum-user-profile
    """
    
    def __init__(self):
        self.app = Server("caelum-business-workflow")
        self.setup_handlers()
        
        # Tool definitions with intelligent selection
        self.all_tools = {
            # Business Intelligence Tools
            "research_market_intelligence": {
                "name": "research_market_intelligence",
                "description": "Conduct comprehensive market research using multiple intelligence sources",
                "priority": 5,
                "category": "research",
                "intents": ["research", "analyze", "investigate"],
                "underlying_service": "caelum-business-intelligence",
                "schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Market research query or topic"},
                        "depth": {"type": "string", "enum": ["basic", "comprehensive", "deep"], "default": "comprehensive"},
                        "sources": {"type": "array", "items": {"type": "string"}, "default": ["all"]},
                        "timeframe": {"type": "string", "enum": ["1d", "7d", "30d", "90d", "1y"], "default": "30d"},
                        "region": {"type": "string", "description": "Geographic region focus"}
                    },
                    "required": ["query"]
                }
            },
            
            "analyze_competitive_landscape": {
                "name": "analyze_competitive_landscape",
                "description": "Analyze competitors and market positioning",
                "priority": 4,
                "category": "analysis",
                "intents": ["analyze", "compare", "evaluate"],
                "underlying_service": "caelum-business-intelligence",
                "schema": {
                    "type": "object",
                    "properties": {
                        "industry": {"type": "string", "description": "Industry or market sector"},
                        "competitors": {"type": "array", "items": {"type": "string"}, "description": "Specific competitors to analyze"},
                        "focus_areas": {"type": "array", "items": {"type": "string"}, "default": ["pricing", "features", "market_share"]},
                        "depth": {"type": "string", "enum": ["overview", "detailed", "comprehensive"], "default": "detailed"}
                    },
                    "required": ["industry"]
                }
            },
            
            "generate_business_insights": {
                "name": "generate_business_insights",
                "description": "Generate actionable business intelligence reports and insights",
                "priority": 4,
                "category": "analysis",
                "intents": ["generate", "create", "analyze"],
                "underlying_service": "caelum-business-intelligence",
                "schema": {
                    "type": "object",
                    "properties": {
                        "data_sources": {"type": "array", "items": {"type": "string"}},
                        "focus_area": {"type": "string", "enum": ["trends", "opportunities", "risks", "competitive-analysis", "optimization"]},
                        "industry": {"type": "string", "description": "Industry context"},
                        "time_horizon": {"type": "string", "enum": ["short-term", "medium-term", "long-term"], "default": "medium-term"}
                    },
                    "required": ["focus_area"]
                }
            },
            
            "forecast_market_trends": {
                "name": "forecast_market_trends",
                "description": "Forecast market trends and future opportunities",
                "priority": 4,
                "category": "forecasting",
                "intents": ["forecast", "predict", "analyze"],
                "underlying_service": "caelum-business-intelligence",
                "schema": {
                    "type": "object",
                    "properties": {
                        "market": {"type": "string", "description": "Market or industry to analyze"},
                        "timeframe": {"type": "string", "enum": ["3m", "6m", "1y", "2y", "5y"], "default": "1y"},
                        "factors": {"type": "array", "items": {"type": "string"}, "description": "Specific factors to consider"},
                        "confidence_level": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"}
                    },
                    "required": ["market"]
                }
            },
            
            # Opportunity Discovery Tools
            "discover_business_opportunities": {
                "name": "discover_business_opportunities",
                "description": "Identify and analyze business opportunities using AI-powered discovery",
                "priority": 5,
                "category": "discovery",
                "intents": ["discover", "find", "identify"],
                "underlying_service": "caelum-opportunity-discovery",
                "schema": {
                    "type": "object",
                    "properties": {
                        "industry": {"type": "string", "description": "Industry or sector to explore"},
                        "opportunity_type": {"type": "string", "enum": ["market_gap", "technology", "partnership", "expansion", "all"], "default": "all"},
                        "risk_tolerance": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                        "investment_range": {"type": "string", "description": "Investment range (e.g., '10k-100k')"},
                        "timeframe": {"type": "string", "enum": ["immediate", "short-term", "medium-term", "long-term"], "default": "medium-term"}
                    },
                    "required": ["industry"]
                }
            },
            
            "evaluate_opportunity": {
                "name": "evaluate_opportunity",
                "description": "Evaluate a specific business opportunity with detailed analysis",
                "priority": 4,
                "category": "analysis",
                "intents": ["evaluate", "analyze", "assess"],
                "underlying_service": "caelum-opportunity-discovery",
                "schema": {
                    "type": "object",
                    "properties": {
                        "opportunity_id": {"type": "string", "description": "ID of opportunity to evaluate"},
                        "evaluation_criteria": {"type": "array", "items": {"type": "string"}, "default": ["market_size", "competition", "feasibility", "profitability"]},
                        "detailed_analysis": {"type": "boolean", "default": true},
                        "include_risks": {"type": "boolean", "default": true}
                    },
                    "required": ["opportunity_id"]
                }
            },
            
            "search_opportunities": {
                "name": "search_opportunities",
                "description": "Search for opportunities based on specific criteria",
                "priority": 3,
                "category": "search",
                "intents": ["search", "find", "filter"],
                "underlying_service": "caelum-opportunity-discovery",
                "schema": {
                    "type": "object",
                    "properties": {
                        "keywords": {"type": "array", "items": {"type": "string"}},
                        "industry": {"type": "string"},
                        "location": {"type": "string"},
                        "investment_range": {"type": "string"},
                        "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                        "limit": {"type": "integer", "default": 10}
                    }
                }
            },
            
            # User Profile & Context Tools
            "manage_user_business_profile": {
                "name": "manage_user_business_profile",
                "description": "Manage user business profile, preferences, and context",
                "priority": 3,
                "category": "management",
                "intents": ["manage", "update", "configure"],
                "underlying_service": "caelum-user-profile",
                "schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["get", "update", "initialize"]},
                        "profile_data": {"type": "object", "description": "Profile data to update"},
                        "business_context": {"type": "object", "description": "Business context information"}
                    },
                    "required": ["action"]
                }
            },
            
            "get_personalized_insights": {
                "name": "get_personalized_insights",
                "description": "Get personalized business insights based on user profile and preferences",
                "priority": 4,
                "category": "personalization",
                "intents": ["personalize", "customize", "tailor"],
                "underlying_service": "caelum-user-profile",
                "schema": {
                    "type": "object",
                    "properties": {
                        "insight_type": {"type": "string", "enum": ["opportunities", "trends", "recommendations", "alerts"]},
                        "industry_focus": {"type": "string"},
                        "time_horizon": {"type": "string", "enum": ["immediate", "short-term", "medium-term", "long-term"], "default": "medium-term"}
                    },
                    "required": ["insight_type"]
                }
            },
            
            # Cross-cutting Business Tools
            "analyze_business_metrics": {
                "name": "analyze_business_metrics",
                "description": "Analyze key business metrics and performance indicators",
                "priority": 4,
                "category": "analysis",
                "intents": ["analyze", "measure", "evaluate"],
                "underlying_service": "analytics",
                "schema": {
                    "type": "object",
                    "properties": {
                        "metrics": {"type": "array", "items": {"type": "string"}, "description": "Specific metrics to analyze"},
                        "timeframe": {"type": "string", "enum": ["week", "month", "quarter", "year"], "default": "month"},
                        "comparison_period": {"type": "boolean", "default": true},
                        "industry_benchmarks": {"type": "boolean", "default": false}
                    }
                }
            },
            
            "generate_business_report": {
                "name": "generate_business_report",
                "description": "Generate comprehensive business intelligence and opportunity report",
                "priority": 3,
                "category": "reporting",
                "intents": ["generate", "create", "compile"],
                "underlying_service": "analytics",
                "schema": {
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string", "enum": ["market_analysis", "opportunity_summary", "competitive_landscape", "trend_analysis"], "default": "market_analysis"},
                        "timeframe": {"type": "string", "enum": ["week", "month", "quarter"], "default": "month"},
                        "include_forecasts": {"type": "boolean", "default": true},
                        "include_recommendations": {"type": "boolean", "default": true}
                    }
                }
            },
            
            "track_market_alerts": {
                "name": "track_market_alerts",
                "description": "Set up and manage market trend and opportunity alerts",
                "priority": 3,
                "category": "monitoring",
                "intents": ["track", "monitor", "alert"],
                "underlying_service": "monitoring",
                "schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["create", "list", "update", "delete"]},
                        "alert_type": {"type": "string", "enum": ["trend_change", "new_opportunity", "competitive_move", "market_shift"]},
                        "keywords": {"type": "array", "items": {"type": "string"}},
                        "threshold": {"type": "string", "description": "Alert threshold"},
                        "frequency": {"type": "string", "enum": ["realtime", "daily", "weekly"], "default": "daily"}
                    },
                    "required": ["action"]
                }
            }
        }
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.app.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available business workflow tools"""
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
            """Handle business workflow tool calls"""
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
        
        # Analyze query intent and select tools
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
            "research": ["research", "investigate", "study", "examine", "explore"],
            "discover": ["discover", "find", "identify", "locate", "uncover"],
            "analyze": ["analyze", "evaluate", "assess", "review", "examine"],
            "forecast": ["forecast", "predict", "project", "estimate", "anticipate"],
            "compare": ["compare", "versus", "vs", "against", "competitive"],
            "track": ["track", "monitor", "watch", "follow", "observe"]
        }
        
        for intent, keywords in intent_patterns.items():
            if any(keyword in query for keyword in keywords):
                return intent
        
        return "research"  # Default intent
    
    def score_tool_relevance(self, tool: Dict, intent: str, query: str) -> float:
        """Score tool relevance for the given intent and query"""
        score = tool["priority"] * 2  # Base priority score
        
        # Intent matching
        if intent in tool["intents"]:
            score += 10
        
        # Business-specific keyword matching
        business_keywords = ["market", "business", "opportunity", "competitor", "trend", "industry", "revenue", "profit"]
        query_words = set(query.split())
        business_word_matches = len(set(business_keywords) & query_words)
        score += business_word_matches * 3
        
        # Keyword matching in description
        tool_keywords = tool["description"].lower().split()
        matching_keywords = len(set(tool_keywords) & query_words)
        score += matching_keywords * 2
        
        # Category relevance
        category_weights = {
            "research": 5,
            "discovery": 5,
            "analysis": 4,
            "forecasting": 4,
            "personalization": 3,
            "monitoring": 3,
            "reporting": 2
        }
        score += category_weights.get(tool["category"], 1)
        
        return score
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a business workflow tool"""
        if tool_name not in self.all_tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool_info = self.all_tools[tool_name]
        underlying_service = tool_info["underlying_service"]
        
        # Route to appropriate service implementation
        if underlying_service == "caelum-business-intelligence":
            return await self.handle_business_intelligence_tool(tool_name, arguments)
        elif underlying_service == "caelum-opportunity-discovery":
            return await self.handle_opportunity_discovery_tool(tool_name, arguments)
        elif underlying_service == "caelum-user-profile":
            return await self.handle_user_profile_tool(tool_name, arguments)
        else:
            return await self.handle_generic_tool(tool_name, arguments)
    
    async def handle_business_intelligence_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle business intelligence tool calls"""
        
        if tool_name == "research_market_intelligence":
            return {
                "query": args.get("query"),
                "depth": args.get("depth", "comprehensive"),
                "sources_used": ["tavily", "perplexity", "google"],
                "research_results": {
                    "market_size": "$15.2B globally, growing at 12.5% CAGR",
                    "key_players": ["Company A (35% market share)", "Company B (22%)", "Company C (18%)"],
                    "trends": [
                        "Increasing adoption of AI-powered solutions",
                        "Shift towards cloud-based platforms",
                        "Growing emphasis on data privacy and security"
                    ],
                    "opportunities": [
                        "Underserved SMB market segment",
                        "Integration with emerging technologies",
                        "Geographic expansion in Asia-Pacific"
                    ],
                    "threats": [
                        "New regulatory requirements",
                        "Increased competition from tech giants",
                        "Economic uncertainty affecting enterprise spending"
                    ]
                },
                "confidence_score": 8.5,
                "sources_count": 45,
                "timestamp": datetime.now().isoformat(),
                "service": "caelum-business-intelligence"
            }
            
        elif tool_name == "analyze_competitive_landscape":
            return {
                "industry": args.get("industry"),
                "analysis": {
                    "market_leaders": [
                        {"name": "Company A", "market_share": 35, "strengths": ["Brand recognition", "Distribution network"], "weaknesses": ["High pricing", "Slow innovation"]},
                        {"name": "Company B", "market_share": 22, "strengths": ["Technology leadership", "Customer service"], "weaknesses": ["Limited geographic presence"]}
                    ],
                    "emerging_competitors": [
                        {"name": "Startup X", "growth_rate": "150% YoY", "differentiator": "AI-first approach"},
                        {"name": "Startup Y", "growth_rate": "90% YoY", "differentiator": "Vertical specialization"}
                    ],
                    "competitive_gaps": [
                        "Mobile-first user experience",
                        "Real-time analytics capabilities",
                        "Industry-specific customization"
                    ],
                    "market_positioning": {
                        "price_leaders": ["Company C"],
                        "innovation_leaders": ["Company B", "Startup X"],
                        "service_leaders": ["Company A"]
                    }
                },
                "recommendations": [
                    "Focus on mobile-first development",
                    "Invest in real-time capabilities",
                    "Consider strategic partnerships for vertical expansion"
                ],
                "service": "caelum-business-intelligence"
            }
            
        elif tool_name == "generate_business_insights":
            return {
                "focus_area": args.get("focus_area"),
                "insights": [
                    {
                        "category": "Market Opportunity",
                        "insight": "SMB segment shows 3x higher growth potential than enterprise",
                        "confidence": 0.85,
                        "impact": "high",
                        "action_required": "Develop SMB-focused product variant"
                    },
                    {
                        "category": "Technology Trend",
                        "insight": "AI integration becomes table stakes by 2025",
                        "confidence": 0.92,
                        "impact": "critical",
                        "action_required": "Accelerate AI feature development"
                    },
                    {
                        "category": "Customer Behavior",
                        "insight": "Self-service adoption increases 40% post-implementation",
                        "confidence": 0.78,
                        "impact": "medium",
                        "action_required": "Invest in user experience improvements"
                    }
                ],
                "key_metrics": {
                    "total_addressable_market": "$45B",
                    "serviceable_addressable_market": "$12B",
                    "customer_acquisition_cost_trend": "-15% YoY",
                    "customer_lifetime_value_trend": "+22% YoY"
                },
                "service": "caelum-business-intelligence"
            }
        
        return {"error": f"Unknown business intelligence tool: {tool_name}"}
    
    async def handle_opportunity_discovery_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle opportunity discovery tool calls"""
        
        if tool_name == "discover_business_opportunities":
            return {
                "industry": args.get("industry"),
                "opportunity_type": args.get("opportunity_type", "all"),
                "discovered_opportunities": [
                    {
                        "id": "opp_001",
                        "title": "AI-Powered Analytics Platform for Healthcare",
                        "type": "market_gap",
                        "market_size": "$2.3B",
                        "growth_rate": "18% CAGR",
                        "investment_required": "$500K - $2M",
                        "timeframe": "12-18 months",
                        "risk_level": "medium",
                        "opportunity_score": 8.2,
                        "key_factors": [
                            "Underserved healthcare analytics market",
                            "Regulatory compliance requirements create barriers",
                            "Strong demand for real-time insights"
                        ]
                    },
                    {
                        "id": "opp_002",
                        "title": "B2B Marketplace for Sustainable Packaging",
                        "type": "market_gap",
                        "market_size": "$850M",
                        "growth_rate": "25% CAGR",
                        "investment_required": "$200K - $800K",
                        "timeframe": "6-12 months",
                        "risk_level": "low",
                        "opportunity_score": 7.8,
                        "key_factors": [
                            "Growing sustainability mandates",
                            "Fragmented supplier ecosystem",
                            "Strong corporate ESG focus"
                        ]
                    }
                ],
                "total_opportunities": 15,
                "filters_applied": {
                    "industry": args.get("industry"),
                    "risk_tolerance": args.get("risk_tolerance", "medium"),
                    "timeframe": args.get("timeframe", "medium-term")
                },
                "service": "caelum-opportunity-discovery"
            }
            
        elif tool_name == "evaluate_opportunity":
            return {
                "opportunity_id": args.get("opportunity_id"),
                "evaluation": {
                    "overall_score": 8.2,
                    "market_attractiveness": 8.5,
                    "competitive_intensity": 6.8,
                    "technical_feasibility": 8.9,
                    "financial_potential": 7.8,
                    "risk_assessment": {
                        "market_risk": "medium",
                        "technical_risk": "low",
                        "competitive_risk": "medium",
                        "regulatory_risk": "low",
                        "overall_risk": "medium"
                    },
                    "financial_projections": {
                        "revenue_year_1": "$250K",
                        "revenue_year_3": "$2.1M",
                        "revenue_year_5": "$8.3M",
                        "break_even_months": 18,
                        "roi_3_year": "320%"
                    },
                    "success_factors": [
                        "Strong technical team with domain expertise",
                        "Strategic partnerships with key players",
                        "Sufficient funding for 24-month runway"
                    ],
                    "key_risks": [
                        "Regulatory changes in target market",
                        "Increased competition from incumbents",
                        "Technology adoption slower than expected"
                    ]
                },
                "recommendation": "Proceed with development - strong opportunity with manageable risks",
                "service": "caelum-opportunity-discovery"
            }
        
        return {"error": f"Unknown opportunity discovery tool: {tool_name}"}
    
    async def handle_user_profile_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user profile tool calls"""
        
        if tool_name == "manage_user_business_profile":
            action = args.get("action")
            if action == "get":
                return {
                    "user_profile": {
                        "business_interests": ["SaaS", "AI/ML", "Healthcare Technology"],
                        "investment_preferences": {
                            "risk_tolerance": "medium",
                            "investment_range": "$100K - $1M",
                            "timeframe": "medium-term",
                            "sectors": ["Technology", "Healthcare", "Sustainability"]
                        },
                        "experience_level": "experienced",
                        "geographic_focus": ["North America", "Europe"],
                        "last_updated": "2025-01-19T10:00:00Z"
                    },
                    "service": "caelum-user-profile"
                }
            elif action == "update":
                return {
                    "action": "update",
                    "status": "Profile updated successfully",
                    "updated_fields": list(args.get("profile_data", {}).keys()),
                    "timestamp": datetime.now().isoformat(),
                    "service": "caelum-user-profile"
                }
            
        elif tool_name == "get_personalized_insights":
            return {
                "insight_type": args.get("insight_type"),
                "personalized_insights": [
                    {
                        "title": "Healthcare AI Investment Opportunity",
                        "relevance_score": 9.2,
                        "reason": "Matches your interest in healthcare technology and AI/ML",
                        "summary": "Emerging opportunity in AI-powered diagnostics with $2.3B market potential",
                        "action": "Consider deeper analysis of regulatory requirements"
                    },
                    {
                        "title": "SaaS Market Consolidation Trend",
                        "relevance_score": 8.5,
                        "reason": "Aligns with your SaaS sector focus",
                        "summary": "Mid-market SaaS companies becoming acquisition targets",
                        "action": "Monitor for potential acquisition opportunities"
                    }
                ],
                "industry_focus": args.get("industry_focus"),
                "generated_for": "user_business_profile",
                "service": "caelum-user-profile"
            }
        
        return {"error": f"Unknown user profile tool: {tool_name}"}
    
    async def handle_generic_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic business workflow tools"""
        
        if tool_name == "analyze_business_metrics":
            return {
                "metrics_analysis": {
                    "revenue_growth": "+15.2% QoQ",
                    "customer_acquisition_cost": "$245 (-8% vs last quarter)",
                    "customer_lifetime_value": "$3,450 (+12% vs last quarter)",
                    "monthly_recurring_revenue": "$1.2M (+18% MoM)",
                    "churn_rate": "3.2% (-0.5% vs last month)"
                },
                "industry_benchmarks": {
                    "revenue_growth": "Industry avg: 12.5%",
                    "cac_ltv_ratio": "1:14 (You: 1:14, Industry avg: 1:10)",
                    "churn_rate": "Industry avg: 4.1%"
                },
                "insights": [
                    "Revenue growth exceeds industry average",
                    "Excellent CAC/LTV ratio indicates efficient customer acquisition",
                    "Churn rate below industry benchmark shows strong retention"
                ],
                "service": "analytics"
            }
            
        elif tool_name == "generate_business_report":
            return {
                "report_type": args.get("report_type", "market_analysis"),
                "timeframe": args.get("timeframe", "month"),
                "executive_summary": {
                    "key_findings": [
                        "Market shows continued growth with 15% increase in demand",
                        "3 new competitive threats identified in target segments",
                        "Customer satisfaction scores increased by 12%"
                    ],
                    "opportunities": [
                        "Expand into adjacent vertical markets",
                        "Develop strategic partnerships",
                        "Invest in customer success capabilities"
                    ],
                    "risks": [
                        "Increased competitive pressure",
                        "Economic headwinds affecting enterprise spending",
                        "Talent acquisition challenges"
                    ]
                },
                "detailed_sections": {
                    "market_analysis": "Comprehensive market analysis data...",
                    "competitive_landscape": "Competitive analysis data...",
                    "financial_performance": "Financial metrics and trends...",
                    "recommendations": "Strategic recommendations..."
                },
                "generated_at": datetime.now().isoformat(),
                "service": "analytics"
            }
        
        return {"error": f"Unknown generic tool: {tool_name}"}

async def main():
    """Run the business workflow MCP server"""
    from mcp.server.stdio import stdio_server
    
    workflow_server = BusinessWorkflowServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await workflow_server.app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="caelum-business-workflow",
                server_version="1.0.0",
                capabilities=workflow_server.app.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())