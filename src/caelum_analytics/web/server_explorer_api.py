"""
API endpoints for dynamic server exploration in Caelum Analytics web interface
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
import asyncio

from ..dynamic_server_explorer import dynamic_explorer

router = APIRouter(prefix="/api/servers", tags=["Server Explorer"])

@router.on_event("startup")
async def startup_event():
    """Initialize the dynamic explorer on startup"""
    await dynamic_explorer.initialize()

@router.get("/hierarchy")
async def get_server_hierarchy(
    expand_tools: bool = Query(False, description="Include detailed tool information")
) -> Dict[str, Any]:
    """Get hierarchical view of all MCP servers with optional tool expansion"""
    try:
        return dynamic_explorer.get_server_hierarchy(expand_tools=expand_tools)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ecosystem-map")
async def get_ecosystem_map() -> Dict[str, Any]:
    """Get complete ecosystem map with relationships and statistics"""
    try:
        return dynamic_explorer.generate_ecosystem_map()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_by_capability(
    capability: str = Query(..., description="Capability to search for")
) -> Dict[str, Any]:
    """Search servers, tools, and workflows by capability"""
    try:
        return dynamic_explorer.search_by_capability(capability)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/{tool_name}")
async def get_tool_details(
    tool_name: str,
    include_related: bool = Query(True, description="Include related tools")
) -> Dict[str, Any]:
    """Get detailed information about a specific tool"""
    try:
        result = dynamic_explorer.get_tool_details(tool_name, include_related=include_related)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/{workflow_name}")
async def get_workflow_details(workflow_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific workflow"""
    try:
        result = dynamic_explorer.get_workflow_details(workflow_name)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows")
async def list_workflows() -> Dict[str, Any]:
    """List all available workflows with descriptions"""
    try:
        return {
            "workflows": [
                {
                    "name": name,
                    "description": info.description,
                    "complexity": info.complexity,
                    "servers_count": len(info.servers_involved),
                    "tools_count": info.tools_count,
                    "use_cases": info.use_cases
                }
                for name, info in dynamic_explorer.workflows.items()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/servers/{server_name}")
async def get_server_details(
    server_name: str,
    include_tools: bool = Query(False, description="Include tool details")
) -> Dict[str, Any]:
    """Get detailed information about a specific server"""
    try:
        if server_name not in dynamic_explorer.servers:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")
        
        server_info = dynamic_explorer.servers[server_name]
        result = {
            "name": server_info.name,
            "type": server_info.type,
            "description": server_info.description,
            "status": server_info.status,
            "tool_count": server_info.tool_count,
            "capabilities": server_info.capabilities,
            "workflows": server_info.workflows,
            "underlying_services": server_info.underlying_services,
            "last_updated": server_info.last_updated.isoformat()
        }
        
        if include_tools:
            server_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category,
                    "priority": tool.priority,
                    "workflow_context": tool.workflow_context
                }
                for tool_name, tool in dynamic_explorer.tools.items()
                if tool.underlying_service == server_name
            ]
            result["tools"] = server_tools
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities")
async def list_capabilities() -> Dict[str, Any]:
    """List all capabilities across the ecosystem"""
    try:
        capability_matrix = dynamic_explorer._generate_capability_matrix()
        return {
            "capabilities": [
                {
                    "name": capability,
                    "servers": servers,
                    "server_count": len(servers)
                }
                for capability, servers in capability_matrix.items()
            ],
            "total_capabilities": len(capability_matrix)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_ecosystem_statistics() -> Dict[str, Any]:
    """Get comprehensive ecosystem statistics"""
    try:
        tool_distribution = dynamic_explorer._generate_tool_distribution()
        
        # Server type distribution
        server_types = {}
        for server in dynamic_explorer.servers.values():
            server_types[server.type] = server_types.get(server.type, 0) + 1
        
        # Workflow complexity distribution
        workflow_complexity = {}
        for workflow in dynamic_explorer.workflows.values():
            workflow_complexity[workflow.complexity] = workflow_complexity.get(workflow.complexity, 0) + 1
        
        return {
            "server_statistics": {
                "total_servers": len(dynamic_explorer.servers),
                "by_type": server_types,
                "average_tools_per_server": sum(s.tool_count for s in dynamic_explorer.servers.values()) / len(dynamic_explorer.servers)
            },
            "tool_statistics": {
                "total_tools": len(dynamic_explorer.tools),
                "by_category": tool_distribution,
                "external_llm_compatible_count": 80  # Based on 5-workflow architecture
            },
            "workflow_statistics": {
                "total_workflows": len(dynamic_explorer.workflows),
                "by_complexity": workflow_complexity,
                "average_tools_per_workflow": sum(w.tools_count for w in dynamic_explorer.workflows.values()) / len(dynamic_explorer.workflows) if dynamic_explorer.workflows else 0
            },
            "architecture_benefits": {
                "tool_reduction_percentage": 52.7,  # (169-80)/169 * 100
                "external_llm_compatibility": True,
                "github_copilot_compatible": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh")
async def refresh_explorer() -> Dict[str, str]:
    """Refresh the server explorer data"""
    try:
        await dynamic_explorer.initialize()
        return {"status": "success", "message": "Server explorer data refreshed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))