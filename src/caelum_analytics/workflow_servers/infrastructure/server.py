"""
Infrastructure Workflow MCP Server

Consolidates device orchestration, cluster communication, and workflow orchestration
into a single infrastructure-focused server with intelligent tool selection.
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

class InfrastructureWorkflowServer:
    """
    Infrastructure workflow server that consolidates:
    - caelum-device-orchestration
    - caelum-cluster-communication
    - caelum-workflow-orchestration
    """
    
    def __init__(self):
        self.app = Server("caelum-infrastructure-workflow")
        self.setup_handlers()
        
        # Tool definitions with intelligent selection
        self.all_tools = {
            # Device Orchestration Tools
            "orchestrate_multi_device": {
                "name": "orchestrate_multi_device",
                "description": "Coordinate tasks and configurations across multiple devices",
                "priority": 5,
                "category": "orchestration",
                "intents": ["orchestrate", "coordinate", "manage"],
                "underlying_service": "caelum-device-orchestration",
                "schema": {
                    "type": "object",
                    "properties": {
                        "devices": {"type": "array", "items": {"type": "string"}, "description": "Device IDs to orchestrate"},
                        "task": {"type": "string", "description": "Task to execute across devices"},
                        "execution_strategy": {"type": "string", "enum": ["parallel", "sequential", "conditional"], "default": "parallel"},
                        "timeout": {"type": "integer", "default": 300, "description": "Timeout in seconds"}
                    },
                    "required": ["devices", "task"]
                }
            },
            
            "list_devices": {
                "name": "list_devices",
                "description": "List all registered devices and their status",
                "priority": 4,
                "category": "discovery",
                "intents": ["list", "discover", "inventory"],
                "underlying_service": "caelum-device-orchestration",
                "schema": {
                    "type": "object",
                    "properties": {
                        "status_filter": {"type": "string", "enum": ["online", "offline", "error", "all"], "default": "all"},
                        "device_type": {"type": "string", "description": "Filter by device type"},
                        "location": {"type": "string", "description": "Filter by location"}
                    }
                }
            },
            
            "register_device": {
                "name": "register_device",
                "description": "Register a new device in the orchestration system",
                "priority": 3,
                "category": "management",
                "intents": ["register", "add", "configure"],
                "underlying_service": "caelum-device-orchestration",
                "schema": {
                    "type": "object",
                    "properties": {
                        "device_name": {"type": "string", "description": "Device name"},
                        "device_type": {"type": "string", "description": "Type of device"},
                        "capabilities": {"type": "array", "items": {"type": "string"}},
                        "location": {"type": "string", "description": "Device location"},
                        "metadata": {"type": "object", "description": "Additional device metadata"}
                    },
                    "required": ["device_name", "device_type"]
                }
            },
            
            "execute_remote_command": {
                "name": "execute_remote_command",
                "description": "Execute commands on remote devices",
                "priority": 4,
                "category": "execution",
                "intents": ["execute", "run", "command"],
                "underlying_service": "caelum-device-orchestration",
                "schema": {
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "Target device ID"},
                        "command": {"type": "string", "description": "Command to execute"},
                        "working_directory": {"type": "string", "description": "Working directory"},
                        "environment": {"type": "object", "description": "Environment variables"},
                        "timeout": {"type": "integer", "default": 60}
                    },
                    "required": ["device_id", "command"]
                }
            },
            
            # Cluster Communication Tools  
            "manage_cluster_communication": {
                "name": "manage_cluster_communication",
                "description": "Manage inter-cluster communication and coordination",
                "priority": 5,
                "category": "communication",
                "intents": ["communicate", "coordinate", "sync"],
                "underlying_service": "caelum-cluster-communication",
                "schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["broadcast", "send", "subscribe", "status"]},
                        "message": {"type": "string", "description": "Message content"},
                        "target_cluster": {"type": "string", "description": "Target cluster ID"},
                        "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"], "default": "normal"}
                    },
                    "required": ["action"]
                }
            },
            
            "get_cluster_status": {
                "name": "get_cluster_status", 
                "description": "Get status of all clusters in the network",
                "priority": 4,
                "category": "monitoring",
                "intents": ["monitor", "status", "health"],
                "underlying_service": "caelum-cluster-communication",
                "schema": {
                    "type": "object",
                    "properties": {
                        "cluster_id": {"type": "string", "description": "Specific cluster to check"},
                        "detailed": {"type": "boolean", "default": false, "description": "Include detailed metrics"}
                    }
                }
            },
            
            "find_best_cluster": {
                "name": "find_best_cluster",
                "description": "Find the optimal cluster for specific workload requirements",
                "priority": 4,
                "category": "optimization",
                "intents": ["optimize", "find", "select"],
                "underlying_service": "caelum-cluster-communication", 
                "schema": {
                    "type": "object",
                    "properties": {
                        "capability": {"type": "string", "description": "Required capability"},
                        "priority": {"type": "number", "minimum": 0, "maximum": 10, "description": "Priority level"},
                        "context": {"type": "string", "description": "Security context requirement"},
                        "exclude_cluster": {"type": "string", "description": "Cluster to exclude"}
                    }
                }
            },
            
            # Workflow Orchestration Tools
            "create_infrastructure_workflow": {
                "name": "create_infrastructure_workflow",
                "description": "Create automated infrastructure workflows",
                "priority": 4,
                "category": "orchestration",
                "intents": ["create", "automate", "orchestrate"],
                "underlying_service": "caelum-workflow-orchestration",
                "schema": {
                    "type": "object",
                    "properties": {
                        "workflow_name": {"type": "string", "description": "Workflow name"},
                        "description": {"type": "string", "description": "Workflow description"},
                        "steps": {"type": "array", "items": {"type": "object"}, "description": "Workflow steps"},
                        "triggers": {"type": "array", "items": {"type": "string"}, "description": "Workflow triggers"},
                        "target_devices": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["workflow_name", "steps"]
                }
            },
            
            "execute_distributed_workflow": {
                "name": "execute_distributed_workflow",
                "description": "Execute workflows across distributed infrastructure",
                "priority": 5,
                "category": "execution",
                "intents": ["execute", "run", "deploy"],
                "underlying_service": "caelum-workflow-orchestration",
                "schema": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {"type": "string", "description": "Workflow to execute"},
                        "parameters": {"type": "object", "description": "Workflow parameters"},
                        "target_clusters": {"type": "array", "items": {"type": "string"}},
                        "execution_mode": {"type": "string", "enum": ["test", "production"], "default": "production"}
                    },
                    "required": ["workflow_id"]
                }
            },
            
            "get_workflow_status": {
                "name": "get_workflow_status",
                "description": "Get status of workflow executions",
                "priority": 3,
                "category": "monitoring",
                "intents": ["monitor", "status", "track"],
                "underlying_service": "caelum-workflow-orchestration",
                "schema": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {"type": "string", "description": "Workflow ID"},
                        "execution_id": {"type": "string", "description": "Specific execution ID"},
                        "include_logs": {"type": "boolean", "default": false}
                    }
                }
            },
            
            # Deployment Tools
            "deploy_infrastructure": {
                "name": "deploy_infrastructure",
                "description": "Deploy infrastructure components and services",
                "priority": 4,
                "category": "deployment",
                "intents": ["deploy", "install", "setup"],
                "underlying_service": "deployment",
                "schema": {
                    "type": "object",
                    "properties": {
                        "component": {"type": "string", "description": "Component to deploy"},
                        "target_environment": {"type": "string", "enum": ["development", "staging", "production"]},
                        "configuration": {"type": "object", "description": "Deployment configuration"},
                        "rollback_enabled": {"type": "boolean", "default": true}
                    },
                    "required": ["component", "target_environment"]
                }
            },
            
            "monitor_system_health": {
                "name": "monitor_system_health",
                "description": "Monitor overall infrastructure system health and performance",
                "priority": 4,
                "category": "monitoring",
                "intents": ["monitor", "health", "performance"],
                "underlying_service": "monitoring",
                "schema": {
                    "type": "object",
                    "properties": {
                        "scope": {"type": "string", "enum": ["devices", "clusters", "workflows", "all"], "default": "all"},
                        "metrics": {"type": "array", "items": {"type": "string"}},
                        "time_range": {"type": "string", "enum": ["1h", "6h", "24h", "7d"], "default": "1h"}
                    }
                }
            },
            
            "scale_resources": {
                "name": "scale_resources",
                "description": "Scale infrastructure resources based on demand",
                "priority": 3,
                "category": "scaling",
                "intents": ["scale", "resize", "optimize"],
                "underlying_service": "orchestration",
                "schema": {
                    "type": "object",
                    "properties": {
                        "resource_type": {"type": "string", "enum": ["compute", "storage", "network", "services"]},
                        "target_capacity": {"type": "number", "description": "Target capacity percentage"},
                        "scaling_policy": {"type": "string", "enum": ["immediate", "gradual", "scheduled"]},
                        "constraints": {"type": "object", "description": "Scaling constraints"}
                    },
                    "required": ["resource_type", "target_capacity"]
                }
            }
        }
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.app.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available infrastructure workflow tools"""
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
            """Handle infrastructure workflow tool calls"""
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
            "deploy": ["deploy", "install", "setup", "provision"],
            "orchestrate": ["orchestrate", "coordinate", "manage", "automate"],
            "monitor": ["monitor", "status", "health", "check", "watch"],
            "execute": ["execute", "run", "start", "launch"],
            "scale": ["scale", "resize", "expand", "shrink"],
            "communicate": ["communicate", "send", "broadcast", "sync"]
        }
        
        for intent, keywords in intent_patterns.items():
            if any(keyword in query for keyword in keywords):
                return intent
        
        return "orchestrate"  # Default intent
    
    def score_tool_relevance(self, tool: Dict, intent: str, query: str) -> float:
        """Score tool relevance for the given intent and query"""
        score = tool["priority"] * 2  # Base priority score
        
        # Intent matching
        if intent in tool["intents"]:
            score += 10
        
        # Infrastructure-specific keyword matching
        infra_keywords = ["deploy", "infrastructure", "cluster", "device", "workflow", "orchestration", "scale", "monitor"]
        query_words = set(query.split())
        infra_word_matches = len(set(infra_keywords) & query_words)
        score += infra_word_matches * 3
        
        # Keyword matching in description
        tool_keywords = tool["description"].lower().split()
        matching_keywords = len(set(tool_keywords) & query_words)
        score += matching_keywords * 2
        
        # Category relevance
        category_weights = {
            "orchestration": 5,
            "deployment": 5,
            "execution": 4,
            "monitoring": 4,
            "communication": 3,
            "scaling": 3,
            "discovery": 2
        }
        score += category_weights.get(tool["category"], 1)
        
        return score
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an infrastructure workflow tool"""
        if tool_name not in self.all_tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool_info = self.all_tools[tool_name]
        underlying_service = tool_info["underlying_service"]
        
        # Route to appropriate service implementation
        if underlying_service == "caelum-device-orchestration":
            return await self.handle_device_orchestration_tool(tool_name, arguments)
        elif underlying_service == "caelum-cluster-communication":
            return await self.handle_cluster_communication_tool(tool_name, arguments)
        elif underlying_service == "caelum-workflow-orchestration":
            return await self.handle_workflow_orchestration_tool(tool_name, arguments)
        else:
            return await self.handle_generic_tool(tool_name, arguments)
    
    async def handle_device_orchestration_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle device orchestration tool calls"""
        
        if tool_name == "orchestrate_multi_device":
            return {
                "orchestration_id": f"orch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "devices": args.get("devices", []),
                "task": args.get("task"),
                "execution_strategy": args.get("execution_strategy", "parallel"),
                "status": "initiated",
                "device_status": {
                    device: "queued" for device in args.get("devices", [])
                },
                "estimated_completion": "5-10 minutes",
                "service": "caelum-device-orchestration"
            }
            
        elif tool_name == "list_devices":
            return {
                "devices": [
                    {
                        "id": "dev_workstation_001",
                        "name": "Primary Development Machine",
                        "type": "workstation", 
                        "status": "online",
                        "location": "home_office",
                        "capabilities": ["development", "testing", "deployment"],
                        "last_seen": "2025-01-19T10:30:00Z"
                    },
                    {
                        "id": "dev_server_001",
                        "name": "Production Server",
                        "type": "server",
                        "status": "online",
                        "location": "data_center",
                        "capabilities": ["hosting", "database", "api"],
                        "last_seen": "2025-01-19T10:29:45Z"
                    },
                    {
                        "id": "dev_mobile_001", 
                        "name": "Mobile Development Device",
                        "type": "mobile",
                        "status": "offline",
                        "location": "remote",
                        "capabilities": ["testing", "development"],
                        "last_seen": "2025-01-18T15:22:10Z"
                    }
                ],
                "total_devices": 3,
                "status_filter": args.get("status_filter", "all"),
                "service": "caelum-device-orchestration"
            }
            
        elif tool_name == "execute_remote_command":
            return {
                "execution_id": f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "device_id": args.get("device_id"),
                "command": args.get("command"),
                "status": "executing",
                "output": "Command initiated successfully",
                "exit_code": None,
                "execution_time": None,
                "service": "caelum-device-orchestration"
            }
        
        return {"error": f"Unknown device orchestration tool: {tool_name}"}
    
    async def handle_cluster_communication_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cluster communication tool calls"""
        
        if tool_name == "manage_cluster_communication":
            action = args.get("action")
            if action == "broadcast":
                return {
                    "action": "broadcast",
                    "message_id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "message": args.get("message"),
                    "priority": args.get("priority", "normal"),
                    "delivered_to": ["cluster_001", "cluster_002", "cluster_003"],
                    "delivery_status": "delivered",
                    "timestamp": datetime.now().isoformat(),
                    "service": "caelum-cluster-communication"
                }
            elif action == "status":
                return {
                    "communication_status": {
                        "active_connections": 3,
                        "message_queue_size": 5,
                        "last_heartbeat": "2025-01-19T10:30:15Z",
                        "network_latency_avg": "15ms",
                        "error_rate": "0.01%"
                    },
                    "service": "caelum-cluster-communication"
                }
                
        elif tool_name == "get_cluster_status":
            return {
                "clusters": [
                    {
                        "id": "cluster_001",
                        "name": "Primary Cluster",
                        "status": "healthy",
                        "load": 0.65,
                        "capacity": "78%",
                        "services": 12,
                        "last_update": "2025-01-19T10:29:45Z"
                    },
                    {
                        "id": "cluster_002", 
                        "name": "Secondary Cluster",
                        "status": "degraded",
                        "load": 0.85,
                        "capacity": "92%",
                        "services": 8,
                        "last_update": "2025-01-19T10:28:30Z"
                    }
                ],
                "overall_health": "warning",
                "service": "caelum-cluster-communication"
            }
        
        return {"error": f"Unknown cluster communication tool: {tool_name}"}
    
    async def handle_workflow_orchestration_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow orchestration tool calls"""
        
        if tool_name == "create_infrastructure_workflow":
            return {
                "workflow_id": f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "workflow_name": args.get("workflow_name"),
                "description": args.get("description", ""),
                "steps_count": len(args.get("steps", [])),
                "target_devices": args.get("target_devices", []),
                "status": "created",
                "created_at": datetime.now().isoformat(),
                "service": "caelum-workflow-orchestration"
            }
            
        elif tool_name == "execute_distributed_workflow":
            return {
                "execution_id": f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "workflow_id": args.get("workflow_id"),
                "execution_mode": args.get("execution_mode", "production"),
                "target_clusters": args.get("target_clusters", []),
                "status": "running",
                "progress": {
                    "total_steps": 5,
                    "completed_steps": 1,
                    "current_step": "Infrastructure validation",
                    "estimated_completion": "8 minutes"
                },
                "started_at": datetime.now().isoformat(),
                "service": "caelum-workflow-orchestration"
            }
            
        elif tool_name == "get_workflow_status":
            return {
                "workflow_id": args.get("workflow_id"),
                "execution_id": args.get("execution_id"),
                "status": "completed",
                "progress": {
                    "total_steps": 5,
                    "completed_steps": 5,
                    "success_rate": "100%"
                },
                "execution_time": "6 minutes 32 seconds",
                "results": {
                    "deployed_components": 3,
                    "configured_devices": 5,
                    "tests_passed": 12
                },
                "service": "caelum-workflow-orchestration"
            }
        
        return {"error": f"Unknown workflow orchestration tool: {tool_name}"}
    
    async def handle_generic_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic infrastructure tools"""
        
        if tool_name == "deploy_infrastructure":
            return {
                "deployment_id": f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "component": args.get("component"),
                "target_environment": args.get("target_environment"),
                "status": "deploying",
                "phases": {
                    "preparation": "completed",
                    "deployment": "in_progress",
                    "validation": "pending",
                    "activation": "pending"
                },
                "estimated_completion": "12 minutes",
                "rollback_plan": "Available" if args.get("rollback_enabled", True) else "Disabled",
                "service": "deployment"
            }
            
        elif tool_name == "monitor_system_health":
            return {
                "overall_health": "healthy",
                "scope": args.get("scope", "all"),
                "health_metrics": {
                    "devices": {
                        "total": 15,
                        "online": 13,
                        "offline": 2,
                        "health_score": 0.87
                    },
                    "clusters": {
                        "total": 3,
                        "healthy": 2,
                        "degraded": 1,
                        "health_score": 0.75
                    },
                    "workflows": {
                        "active": 5,
                        "successful_24h": 45,
                        "failed_24h": 2,
                        "success_rate": 0.96
                    }
                },
                "alerts": [
                    {
                        "level": "warning",
                        "component": "cluster_002",
                        "message": "High CPU utilization (92%)",
                        "timestamp": "2025-01-19T10:25:00Z"
                    }
                ],
                "service": "monitoring"
            }
            
        elif tool_name == "scale_resources":
            return {
                "scaling_id": f"scale_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "resource_type": args.get("resource_type"),
                "current_capacity": "75%",
                "target_capacity": f"{args.get('target_capacity', 80)}%",
                "scaling_policy": args.get("scaling_policy", "gradual"),
                "status": "scaling",
                "estimated_completion": "3-5 minutes",
                "affected_resources": [
                    "compute_cluster_001",
                    "storage_pool_002"
                ],
                "service": "orchestration"
            }
        
        return {"error": f"Unknown generic tool: {tool_name}"}

async def main():
    """Run the infrastructure workflow MCP server"""
    from mcp.server.stdio import stdio_server
    
    workflow_server = InfrastructureWorkflowServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await workflow_server.app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="caelum-infrastructure-workflow",
                server_version="1.0.0",
                capabilities=workflow_server.app.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())