"""
Dynamic Server Explorer for Caelum Analytics

Provides dynamic presentation of MCP servers with expandable tool hierarchies,
purposes, and workflow relationships. Essential for managing complex server ecosystems.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class ToolInfo:
    """Information about a single MCP tool"""
    name: str
    description: str
    category: str
    priority: int
    underlying_service: str
    workflow_context: List[str]
    use_cases: List[str]
    parameters: Dict[str, Any]
    related_tools: List[str]
    
@dataclass
class ServerInfo:
    """Information about an MCP server"""
    name: str
    type: str  # workflow, individual, legacy
    description: str
    status: str  # active, inactive, error
    tool_count: int
    underlying_services: List[str]
    workflows: List[str]
    capabilities: List[str]
    last_updated: datetime

@dataclass
class WorkflowInfo:
    """Information about a workflow"""
    name: str
    description: str
    servers_involved: List[str]
    tools_count: int
    complexity: str  # simple, moderate, complex
    use_cases: List[str]
    dependencies: List[str]

class DynamicServerExplorer:
    """
    Dynamic exploration and presentation of MCP server ecosystem
    """
    
    def __init__(self):
        self.servers: Dict[str, ServerInfo] = {}
        self.tools: Dict[str, ToolInfo] = {}
        self.workflows: Dict[str, WorkflowInfo] = {}
        self.tool_relationships: Dict[str, List[str]] = {}
        
    async def initialize(self):
        """Initialize the server explorer with current ecosystem data"""
        await self._discover_servers()
        await self._analyze_tool_relationships()
        await self._map_workflows()
        logger.info(f"Initialized explorer: {len(self.servers)} servers, {len(self.tools)} tools, {len(self.workflows)} workflows")
    
    async def _discover_servers(self):
        """Discover and catalog all MCP servers"""
        # Workflow servers (new architecture)
        workflow_servers = {
            "caelum-development-workflow": {
                "description": "Complete development lifecycle management",
                "underlying_services": ["caelum-code-analysis", "caelum-project-intelligence", "caelum-development-session"],
                "tools": [
                    {"name": "analyze_code_quality", "category": "analysis", "priority": 5},
                    {"name": "search_code_patterns", "category": "analysis", "priority": 4},
                    {"name": "analyze_project_structure", "category": "analysis", "priority": 4},
                    {"name": "track_development_session", "category": "management", "priority": 3},
                    {"name": "optimize_development_workflow", "category": "optimization", "priority": 4},
                ],
                "capabilities": ["Code Analysis", "Project Intelligence", "Session Tracking", "Workflow Optimization"],
                "workflows": ["development-lifecycle", "code-review", "project-analysis"]
            },
            
            "caelum-business-workflow": {
                "description": "Business intelligence and market research",
                "underlying_services": ["caelum-business-intelligence", "caelum-opportunity-discovery", "caelum-user-profile"],
                "tools": [
                    {"name": "research_market_intelligence", "category": "research", "priority": 5},
                    {"name": "discover_business_opportunities", "category": "discovery", "priority": 5},
                    {"name": "analyze_competitive_landscape", "category": "analysis", "priority": 4},
                    {"name": "generate_business_insights", "category": "analysis", "priority": 4},
                    {"name": "get_personalized_insights", "category": "personalization", "priority": 4},
                ],
                "capabilities": ["Market Research", "Opportunity Discovery", "Competitive Analysis", "Business Intelligence"],
                "workflows": ["market-research", "opportunity-analysis", "competitive-intelligence"]
            },
            
            "caelum-infrastructure-workflow": {
                "description": "Infrastructure and deployment management",
                "underlying_services": ["caelum-device-orchestration", "caelum-cluster-communication", "caelum-workflow-orchestration"],
                "tools": [
                    {"name": "orchestrate_multi_device", "category": "orchestration", "priority": 5},
                    {"name": "manage_cluster_communication", "category": "communication", "priority": 5},
                    {"name": "execute_distributed_workflow", "category": "execution", "priority": 5},
                    {"name": "deploy_infrastructure", "category": "deployment", "priority": 4},
                    {"name": "monitor_system_health", "category": "monitoring", "priority": 4},
                ],
                "capabilities": ["Device Orchestration", "Cluster Communication", "Workflow Execution", "Infrastructure Deployment"],
                "workflows": ["deployment-pipeline", "infrastructure-management", "distributed-processing"]
            },
            
            "caelum-communication-workflow": {
                "description": "Communication and knowledge management",
                "underlying_services": ["caelum-notifications", "caelum-intelligence-hub", "caelum-knowledge-management"],
                "tools": [
                    {"name": "send_smart_notification", "category": "messaging", "priority": 5},
                    {"name": "aggregate_intelligence", "category": "intelligence", "priority": 4},
                    {"name": "manage_knowledge_base", "category": "knowledge", "priority": 4},
                    {"name": "search_knowledge_graph", "category": "search", "priority": 4},
                    {"name": "sync_cross_device", "category": "synchronization", "priority": 3},
                ],
                "capabilities": ["Smart Notifications", "Intelligence Aggregation", "Knowledge Management", "Cross-device Sync"],
                "workflows": ["notification-delivery", "knowledge-curation", "intelligence-synthesis"]
            },
            
            "caelum-security-workflow": {
                "description": "Security, compliance, and optimization", 
                "underlying_services": ["caelum-security-compliance", "caelum-security-management"],
                "tools": [
                    {"name": "scan_security_vulnerabilities", "category": "scanning", "priority": 5},
                    {"name": "manage_api_keys", "category": "key_management", "priority": 5},
                    {"name": "check_compliance_status", "category": "compliance", "priority": 4},
                    {"name": "encrypt_sensitive_data", "category": "encryption", "priority": 4},
                    {"name": "review_access_controls", "category": "access_control", "priority": 4},
                ],
                "capabilities": ["Vulnerability Scanning", "Compliance Checking", "API Key Management", "Access Control"],
                "workflows": ["security-audit", "compliance-assessment", "access-review"]
            }
        }
        
        # Individual servers (legacy/specialized)
        individual_servers = {
            "caelum-ollama-pool": {
                "description": "Tier1 LLM integration with cost optimization",
                "type": "individual",
                "underlying_services": ["ollama-pool"],
                "tools": [
                    {"name": "route_llm_request", "category": "routing", "priority": 5},
                    {"name": "get_pool_health_status", "category": "monitoring", "priority": 4},
                    {"name": "optimize_model_distribution", "category": "optimization", "priority": 4},
                ],
                "capabilities": ["LLM Routing", "Cost Optimization", "Pool Management"],
                "workflows": ["cost-optimization", "llm-routing"]
            },
            
            "filesystem": {
                "description": "Core filesystem operations",
                "type": "core",
                "underlying_services": ["filesystem"],
                "tools": [
                    {"name": "read_text_file", "category": "io", "priority": 5},
                    {"name": "write_file", "category": "io", "priority": 5},
                    {"name": "list_directory", "category": "io", "priority": 4},
                    {"name": "search_files", "category": "search", "priority": 4},
                ],
                "capabilities": ["File Operations", "Directory Management", "File Search"],
                "workflows": ["file-management", "data-access"]
            }
        }
        
        # Build server registry
        for server_name, server_data in workflow_servers.items():
            self.servers[server_name] = ServerInfo(
                name=server_name,
                type="workflow",
                description=server_data["description"],
                status="active",
                tool_count=len(server_data["tools"]),
                underlying_services=server_data["underlying_services"],
                workflows=server_data["workflows"],
                capabilities=server_data["capabilities"],
                last_updated=datetime.utcnow()
            )
            
            # Register tools
            for tool_data in server_data["tools"]:
                tool_name = f"{server_name}::{tool_data['name']}"
                self.tools[tool_name] = ToolInfo(
                    name=tool_data["name"],
                    description=f"{tool_data['name']} from {server_name}",
                    category=tool_data["category"],
                    priority=tool_data["priority"],
                    underlying_service=server_name,
                    workflow_context=server_data["workflows"],
                    use_cases=[],
                    parameters={},
                    related_tools=[]
                )
        
        for server_name, server_data in individual_servers.items():
            self.servers[server_name] = ServerInfo(
                name=server_name,
                type=server_data["type"],
                description=server_data["description"], 
                status="active",
                tool_count=len(server_data["tools"]),
                underlying_services=server_data["underlying_services"],
                workflows=server_data["workflows"],
                capabilities=server_data["capabilities"],
                last_updated=datetime.utcnow()
            )
    
    async def _analyze_tool_relationships(self):
        """Analyze relationships between tools"""
        # Simple relationship mapping based on categories and workflows
        for tool_name, tool_info in self.tools.items():
            related = []
            for other_name, other_info in self.tools.items():
                if other_name != tool_name:
                    # Same category
                    if tool_info.category == other_info.category:
                        related.append(other_name)
                    # Same workflow context
                    elif set(tool_info.workflow_context) & set(other_info.workflow_context):
                        related.append(other_name)
                        
            self.tool_relationships[tool_name] = related[:5]  # Limit to top 5
    
    async def _map_workflows(self):
        """Map and analyze workflows"""
        workflow_definitions = {
            "development-lifecycle": {
                "description": "Complete software development lifecycle management",
                "servers": ["caelum-development-workflow"],
                "complexity": "complex",
                "use_cases": ["Code development", "Quality assurance", "Project management"],
                "dependencies": []
            },
            "market-research": {
                "description": "Comprehensive market research and competitive analysis",
                "servers": ["caelum-business-workflow"],
                "complexity": "moderate",
                "use_cases": ["Market analysis", "Competitor research", "Opportunity identification"],
                "dependencies": []
            },
            "infrastructure-management": {
                "description": "Infrastructure deployment and orchestration",
                "servers": ["caelum-infrastructure-workflow"],
                "complexity": "complex",
                "use_cases": ["Infrastructure deployment", "Multi-device coordination", "System monitoring"],
                "dependencies": []
            },
            "cost-optimization": {
                "description": "LLM cost optimization and intelligent routing",
                "servers": ["caelum-ollama-pool", "caelum-development-workflow"],
                "complexity": "moderate",
                "use_cases": ["Cost reduction", "Performance optimization", "Resource allocation"],
                "dependencies": []
            },
            "security-audit": {
                "description": "Comprehensive security assessment and compliance",
                "servers": ["caelum-security-workflow"],
                "complexity": "complex",
                "use_cases": ["Vulnerability assessment", "Compliance checking", "Access control"],
                "dependencies": []
            }
        }
        
        for workflow_name, workflow_data in workflow_definitions.items():
            tools_count = sum(
                server.tool_count for server_name, server in self.servers.items()
                if server_name in workflow_data["servers"]
            )
            
            self.workflows[workflow_name] = WorkflowInfo(
                name=workflow_name,
                description=workflow_data["description"],
                servers_involved=workflow_data["servers"],
                tools_count=tools_count,
                complexity=workflow_data["complexity"],
                use_cases=workflow_data["use_cases"],
                dependencies=workflow_data["dependencies"]
            )
    
    def get_server_hierarchy(self, expand_tools: bool = False) -> Dict[str, Any]:
        """Get hierarchical view of all servers"""
        hierarchy = {
            "workflow_servers": {},
            "individual_servers": {},
            "core_servers": {},
            "summary": {
                "total_servers": len(self.servers),
                "total_tools": len(self.tools),
                "total_workflows": len(self.workflows)
            }
        }
        
        for server_name, server_info in self.servers.items():
            server_data = {
                "name": server_name,
                "description": server_info.description,
                "status": server_info.status,
                "tool_count": server_info.tool_count,
                "capabilities": server_info.capabilities,
                "workflows": server_info.workflows,
                "underlying_services": server_info.underlying_services
            }
            
            if expand_tools:
                server_tools = [
                    tool for tool_name, tool in self.tools.items()
                    if tool.underlying_service == server_name
                ]
                server_data["tools"] = [asdict(tool) for tool in server_tools]
            
            if server_info.type == "workflow":
                hierarchy["workflow_servers"][server_name] = server_data
            elif server_info.type == "core":
                hierarchy["core_servers"][server_name] = server_data
            else:
                hierarchy["individual_servers"][server_name] = server_data
        
        return hierarchy
    
    def get_tool_details(self, tool_name: str, include_related: bool = True) -> Dict[str, Any]:
        """Get detailed information about a specific tool"""
        if tool_name not in self.tools:
            # Try to find by short name
            matching_tools = [name for name in self.tools.keys() if name.endswith(f"::{tool_name}")]
            if not matching_tools:
                return {"error": f"Tool '{tool_name}' not found"}
            tool_name = matching_tools[0]
        
        tool_info = self.tools[tool_name]
        result = asdict(tool_info)
        
        if include_related:
            result["related_tools"] = self.tool_relationships.get(tool_name, [])
            
        # Add server context
        server_info = self.servers.get(tool_info.underlying_service)
        if server_info:
            result["server_context"] = {
                "server_name": server_info.name,
                "server_type": server_info.type,
                "server_capabilities": server_info.capabilities
            }
        
        return result
    
    def get_workflow_details(self, workflow_name: str) -> Dict[str, Any]:
        """Get detailed information about a workflow"""
        if workflow_name not in self.workflows:
            return {"error": f"Workflow '{workflow_name}' not found"}
        
        workflow_info = self.workflows[workflow_name]
        result = asdict(workflow_info)
        
        # Add server details
        result["server_details"] = [
            {
                "name": server_name,
                "description": self.servers[server_name].description,
                "tool_count": self.servers[server_name].tool_count,
                "capabilities": self.servers[server_name].capabilities
            }
            for server_name in workflow_info.servers_involved
            if server_name in self.servers
        ]
        
        return result
    
    def search_by_capability(self, capability: str) -> Dict[str, Any]:
        """Search servers and tools by capability"""
        results = {
            "servers": [],
            "tools": [],
            "workflows": []
        }
        
        capability_lower = capability.lower()
        
        # Search servers
        for server_name, server_info in self.servers.items():
            if any(capability_lower in cap.lower() for cap in server_info.capabilities):
                results["servers"].append({
                    "name": server_name,
                    "description": server_info.description,
                    "matching_capabilities": [
                        cap for cap in server_info.capabilities 
                        if capability_lower in cap.lower()
                    ]
                })
        
        # Search tools
        for tool_name, tool_info in self.tools.items():
            if (capability_lower in tool_info.description.lower() or
                capability_lower in tool_info.category.lower()):
                results["tools"].append({
                    "name": tool_info.name,
                    "description": tool_info.description,
                    "server": tool_info.underlying_service,
                    "category": tool_info.category
                })
        
        # Search workflows
        for workflow_name, workflow_info in self.workflows.items():
            if any(capability_lower in use_case.lower() for use_case in workflow_info.use_cases):
                results["workflows"].append({
                    "name": workflow_name,
                    "description": workflow_info.description,
                    "matching_use_cases": [
                        use_case for use_case in workflow_info.use_cases
                        if capability_lower in use_case.lower()
                    ]
                })
        
        return results
    
    def generate_ecosystem_map(self) -> Dict[str, Any]:
        """Generate a complete ecosystem map with relationships"""
        return {
            "ecosystem_overview": {
                "architecture_type": "5-workflow + specialized servers",
                "total_servers": len(self.servers),
                "total_tools": len(self.tools),
                "total_workflows": len(self.workflows),
                "external_llm_compatible": True,
                "max_tools_exposed": 80
            },
            "servers": self.get_server_hierarchy(expand_tools=False),
            "workflows": {name: asdict(info) for name, info in self.workflows.items()},
            "capability_matrix": self._generate_capability_matrix(),
            "tool_distribution": self._generate_tool_distribution()
        }
    
    def _generate_capability_matrix(self) -> Dict[str, List[str]]:
        """Generate a matrix of capabilities to servers"""
        matrix = {}
        for server_name, server_info in self.servers.items():
            for capability in server_info.capabilities:
                if capability not in matrix:
                    matrix[capability] = []
                matrix[capability].append(server_name)
        return matrix
    
    def _generate_tool_distribution(self) -> Dict[str, int]:
        """Generate tool distribution statistics"""
        distribution = {}
        for tool_info in self.tools.values():
            category = tool_info.category
            distribution[category] = distribution.get(category, 0) + 1
        return distribution

# Global explorer instance
dynamic_explorer = DynamicServerExplorer()