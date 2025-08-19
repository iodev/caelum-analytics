"""
Caelum Cluster Monitoring Dashboard

This module provides monitoring capabilities for the distributed Caelum MCP server ecosystem.
It observes and reports on the health, performance, and optimization activities of 
Caelum MCP servers across the LAN without participating in the optimization itself.

Architecture:
- caelum-analytics: Single monitoring dashboard (this)  
- caelum repo: Distributed MCP servers with 5-workflow architecture
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cluster-monitor", tags=["Caelum Cluster Monitor"])

class CaelumClusterMonitor:
    """Monitor distributed Caelum MCP servers"""
    
    def __init__(self):
        self.known_servers: Dict[str, Dict[str, Any]] = {}
        self.last_discovery_time = None
        
    async def discover_caelum_servers(self) -> List[Dict[str, Any]]:
        """Discover active Caelum MCP servers on the LAN"""
        
        discovered_servers = []
        
        # Common Caelum server ports and endpoints
        caelum_server_configs = [
            # Workflow servers (5-workflow architecture)
            {"name": "caelum-development-workflow", "port": 8100, "type": "workflow"},
            {"name": "caelum-business-workflow", "port": 8101, "type": "workflow"}, 
            {"name": "caelum-infrastructure-workflow", "port": 8102, "type": "workflow"},
            {"name": "caelum-communication-workflow", "port": 8103, "type": "workflow"},
            {"name": "caelum-security-workflow", "port": 8104, "type": "workflow"},
            
            # Individual MCP servers
            {"name": "ai-code-analysis-server", "port": 8105, "type": "individual"},
            {"name": "business-intelligence-aggregation-server", "port": 8106, "type": "individual"},
            {"name": "cluster-communication-server", "port": 8107, "type": "individual"},
            {"name": "deployment-infrastructure-server", "port": 8108, "type": "individual"},
            {"name": "device-orchestration-server", "port": 8109, "type": "individual"},
            {"name": "intelligence-hub-server", "port": 8110, "type": "individual"},
            {"name": "knowledge-management-server", "port": 8111, "type": "individual"},
            {"name": "opportunity-discovery-server", "port": 8112, "type": "individual"},
            {"name": "performance-optimization-server", "port": 8113, "type": "individual"},
            {"name": "project-intelligence-server", "port": 8114, "type": "individual"},
            {"name": "security-compliance-server", "port": 8115, "type": "individual"},
            {"name": "security-management-server", "port": 8116, "type": "individual"},
            {"name": "user-profile-server", "port": 8117, "type": "individual"},
            {"name": "workflow-orchestration-server", "port": 8118, "type": "individual"},
        ]
        
        # Check localhost and common LAN IPs
        hosts_to_check = ["127.0.0.1", "10.32.3.27"]
        
        timeout = aiohttp.ClientTimeout(total=5)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for host in hosts_to_check:
                for server_config in caelum_server_configs:
                    try:
                        # Check MCP server health endpoint
                        health_url = f"http://{host}:{server_config['port']}/health"
                        async with session.get(health_url) as response:
                            if response.status == 200:
                                health_data = await response.json()
                                
                                server_info = {
                                    **server_config,
                                    "host": host,
                                    "status": "active",
                                    "health_data": health_data,
                                    "last_seen": datetime.now().isoformat(),
                                    "endpoint": f"http://{host}:{server_config['port']}"
                                }
                                
                                discovered_servers.append(server_info)
                                logger.debug(f"✅ Found {server_config['name']} at {host}:{server_config['port']}")
                                
                    except (aiohttp.ClientError, asyncio.TimeoutError):
                        # Server not available at this host:port
                        continue
                    except Exception as e:
                        logger.debug(f"Error checking {server_config['name']} at {host}:{server_config['port']}: {e}")
        
        self.known_servers = {server["name"]: server for server in discovered_servers}
        self.last_discovery_time = datetime.now()
        
        logger.info(f"🔍 Discovered {len(discovered_servers)} active Caelum servers")
        return discovered_servers
    
    async def get_server_metrics(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get performance metrics from a specific Caelum server"""
        
        server_info = self.known_servers.get(server_name)
        if not server_info:
            return None
            
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                
                # Try different metrics endpoints
                metrics_endpoints = [
                    f"{server_info['endpoint']}/metrics",
                    f"{server_info['endpoint']}/api/metrics", 
                    f"{server_info['endpoint']}/health/metrics",
                    f"{server_info['endpoint']}/status"
                ]
                
                for endpoint in metrics_endpoints:
                    try:
                        async with session.get(endpoint) as response:
                            if response.status == 200:
                                metrics_data = await response.json()
                                
                                return {
                                    "server_name": server_name,
                                    "timestamp": datetime.now().isoformat(),
                                    "metrics": metrics_data,
                                    "response_time": response.headers.get("X-Response-Time"),
                                    "endpoint_used": endpoint
                                }
                    except (aiohttp.ClientError, asyncio.TimeoutError):
                        continue
                        
        except Exception as e:
            logger.error(f"Error getting metrics from {server_name}: {e}")
            
        return None
    
    async def get_cluster_optimization_status(self) -> Dict[str, Any]:
        """Get optimization status from the distributed Caelum cluster"""
        
        if not self.known_servers:
            await self.discover_caelum_servers()
            
        optimization_status = {
            "cluster_overview": {
                "total_servers": len(self.known_servers),
                "workflow_servers": len([s for s in self.known_servers.values() if s["type"] == "workflow"]),
                "individual_servers": len([s for s in self.known_servers.values() if s["type"] == "individual"]),
                "last_discovery": self.last_discovery_time.isoformat() if self.last_discovery_time else None
            },
            "server_status": {},
            "optimization_insights": {
                "active_optimizers": 0,
                "recent_optimizations": [],
                "learned_principles": [],
                "performance_trends": {}
            }
        }
        
        # Get status from each server
        for server_name, server_info in self.known_servers.items():
            try:
                # Try to get optimization status from the server
                status_endpoint = f"{server_info['endpoint']}/api/optimization/status"
                
                timeout = aiohttp.ClientTimeout(total=8)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    try:
                        async with session.get(status_endpoint) as response:
                            if response.status == 200:
                                server_opt_status = await response.json()
                                optimization_status["server_status"][server_name] = {
                                    "status": "active",
                                    "optimization_data": server_opt_status,
                                    "last_updated": datetime.now().isoformat()
                                }
                                
                                # Aggregate optimization insights
                                if server_opt_status.get("system_active"):
                                    optimization_status["optimization_insights"]["active_optimizers"] += 1
                                    
                            else:
                                optimization_status["server_status"][server_name] = {
                                    "status": "no_optimization_api",
                                    "last_updated": datetime.now().isoformat()
                                }
                    except (aiohttp.ClientError, asyncio.TimeoutError):
                        optimization_status["server_status"][server_name] = {
                            "status": "unreachable",
                            "last_updated": datetime.now().isoformat()
                        }
                        
            except Exception as e:
                logger.error(f"Error getting optimization status from {server_name}: {e}")
                optimization_status["server_status"][server_name] = {
                    "status": "error",
                    "error": str(e),
                    "last_updated": datetime.now().isoformat()
                }
        
        return optimization_status

# Global cluster monitor instance
cluster_monitor = CaelumClusterMonitor()

@router.get("/discover")
async def discover_cluster() -> Dict[str, Any]:
    """Discover active Caelum MCP servers on the LAN"""
    try:
        servers = await cluster_monitor.discover_caelum_servers()
        return {
            "status": "success",
            "servers_discovered": len(servers),
            "servers": servers,
            "discovery_time": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cluster-status")
async def get_cluster_status() -> Dict[str, Any]:
    """Get comprehensive status of the Caelum cluster"""
    try:
        status = await cluster_monitor.get_cluster_optimization_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/server/{server_name}/metrics")
async def get_server_metrics(server_name: str) -> Dict[str, Any]:
    """Get metrics from a specific Caelum server"""
    try:
        metrics = await cluster_monitor.get_server_metrics(server_name)
        if metrics is None:
            raise HTTPException(status_code=404, detail=f"Server {server_name} not found or unreachable")
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow-architecture")
async def get_workflow_architecture_status() -> Dict[str, Any]:
    """Get status of the 5-workflow architecture"""
    try:
        if not cluster_monitor.known_servers:
            await cluster_monitor.discover_caelum_servers()
            
        workflow_servers = {
            name: info for name, info in cluster_monitor.known_servers.items()
            if info["type"] == "workflow"
        }
        
        architecture_status = {
            "architecture_type": "5-workflow distributed MCP servers",
            "workflow_servers": workflow_servers,
            "total_workflow_servers": len(workflow_servers),
            "expected_workflow_servers": 5,
            "status": "healthy" if len(workflow_servers) >= 4 else "degraded" if len(workflow_servers) >= 2 else "critical"
        }
        
        return architecture_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-summary")
async def get_cluster_performance_summary() -> Dict[str, Any]:
    """Get performance summary of the entire Caelum cluster"""
    try:
        if not cluster_monitor.known_servers:
            await cluster_monitor.discover_caelum_servers()
            
        performance_data = {
            "cluster_health": {
                "total_servers": len(cluster_monitor.known_servers),
                "active_servers": len([s for s in cluster_monitor.known_servers.values() if s["status"] == "active"]),
                "last_discovery": cluster_monitor.last_discovery_time.isoformat() if cluster_monitor.last_discovery_time else None
            },
            "server_performance": {},
            "aggregated_metrics": {
                "avg_response_time": 0.0,
                "total_tools_available": 0,
                "cluster_uptime": "monitoring_active"
            }
        }
        
        # Get performance data from each server
        total_response_time = 0
        active_servers = 0
        
        for server_name in cluster_monitor.known_servers.keys():
            metrics = await cluster_monitor.get_server_metrics(server_name)
            if metrics:
                performance_data["server_performance"][server_name] = metrics
                
                # Extract response time if available
                if metrics.get("response_time"):
                    try:
                        response_time = float(metrics["response_time"])
                        total_response_time += response_time
                        active_servers += 1
                    except (ValueError, TypeError):
                        pass
        
        if active_servers > 0:
            performance_data["aggregated_metrics"]["avg_response_time"] = total_response_time / active_servers
            
        return performance_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))