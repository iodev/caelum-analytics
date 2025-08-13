"""Caelum Port Registry - Centralized port management for the entire ecosystem."""

from typing import Dict, List, Optional, NamedTuple
from enum import Enum
from dataclasses import dataclass


class ServiceType(Enum):
    """Types of services in the Caelum ecosystem."""
    DATABASE = "database"
    WEB_UI = "web_ui" 
    API = "api"
    WEBSOCKET = "websocket"
    MONITORING = "monitoring"
    COMMUNICATION = "communication"
    MCP_SERVER = "mcp_server"
    ANALYTICS = "analytics"


@dataclass
class PortAllocation:
    """Represents a port allocation in the Caelum ecosystem."""
    port: int
    service_name: str
    service_type: ServiceType
    project: str
    purpose: str
    protocol: str = "TCP"
    status: str = "active"  # active, reserved, deprecated
    machine_id: Optional[str] = None  # Which machine is running this service
    ip_address: Optional[str] = None  # IP address where service is running
    
    def __str__(self) -> str:
        location = f" on {self.machine_id}({self.ip_address})" if self.machine_id else ""
        return f"{self.port}: {self.service_name} ({self.service_type.value}) - {self.purpose}{location}"


class CaelumPortRegistry:
    """Central registry for all port allocations in the Caelum ecosystem."""
    
    def __init__(self):
        self._allocations: Dict[int, PortAllocation] = {}
        self._initialize_core_allocations()
    
    def _initialize_core_allocations(self):
        """Initialize known port allocations for core Caelum infrastructure."""
        core_ports = [
            # Database Layer
            PortAllocation(5432, "postgresql", ServiceType.DATABASE, "caelum-core", "Primary database"),
            PortAllocation(6379, "redis", ServiceType.DATABASE, "caelum-core", "Cache and message broker"),
            PortAllocation(8086, "influxdb", ServiceType.DATABASE, "caelum-core", "Time-series metrics storage"),
            
            # Monitoring & Observability
            PortAllocation(9090, "prometheus", ServiceType.MONITORING, "caelum-monitoring", "Metrics collection"),
            PortAllocation(3000, "grafana", ServiceType.MONITORING, "caelum-monitoring", "Metrics visualization"),
            
            # Core Communication
            PortAllocation(8080, "cluster-communication", ServiceType.WEBSOCKET, "caelum-core", "Inter-cluster WebSocket communication"),
            
            # Analytics Platform (moved from 8080)
            PortAllocation(8090, "analytics-dashboard", ServiceType.WEB_UI, "caelum-analytics", "Real-time monitoring dashboard"),
            
            # API Gateway
            PortAllocation(8000, "api-gateway", ServiceType.API, "caelum-core", "Main API gateway"),
            
            # MCP Server Port Ranges (8100-8199 reserved for MCP servers)
            PortAllocation(8100, "caelum-analytics-metrics", ServiceType.MCP_SERVER, "caelum-analytics", "Analytics MCP server"),
            PortAllocation(8101, "caelum-business-intelligence", ServiceType.MCP_SERVER, "caelum-bi", "BI MCP server"),
            PortAllocation(8102, "caelum-code-analysis", ServiceType.MCP_SERVER, "caelum-dev", "Code analysis MCP server"),
            PortAllocation(8103, "caelum-deployment-infrastructure", ServiceType.MCP_SERVER, "caelum-ops", "Deployment MCP server"),
            PortAllocation(8104, "caelum-device-orchestration", ServiceType.MCP_SERVER, "caelum-core", "Device orchestration MCP server"),
            PortAllocation(8105, "caelum-intelligence-hub", ServiceType.MCP_SERVER, "caelum-ai", "Intelligence hub MCP server"),
            PortAllocation(8106, "caelum-knowledge-management", ServiceType.MCP_SERVER, "caelum-knowledge", "Knowledge management MCP server"),
            PortAllocation(8107, "caelum-opportunity-discovery", ServiceType.MCP_SERVER, "caelum-business", "Opportunity discovery MCP server"),
            PortAllocation(8108, "caelum-performance-optimization", ServiceType.MCP_SERVER, "caelum-ops", "Performance optimization MCP server"),
            PortAllocation(8109, "caelum-project-intelligence", ServiceType.MCP_SERVER, "caelum-pm", "Project intelligence MCP server"),
            PortAllocation(8110, "caelum-security-compliance", ServiceType.MCP_SERVER, "caelum-security", "Security compliance MCP server"),
            PortAllocation(8111, "caelum-security-management", ServiceType.MCP_SERVER, "caelum-security", "Security management MCP server"),
            PortAllocation(8112, "caelum-user-profile", ServiceType.MCP_SERVER, "caelum-user", "User profile MCP server"),
            PortAllocation(8113, "caelum-workflow-orchestration", ServiceType.MCP_SERVER, "caelum-workflow", "Workflow orchestration MCP server"),
            PortAllocation(8114, "caelum-cross-device-notifications", ServiceType.MCP_SERVER, "caelum-notifications", "Cross-device notifications MCP server"),
            PortAllocation(8115, "caelum-development-session", ServiceType.MCP_SERVER, "caelum-dev", "Development session MCP server"),
            PortAllocation(8116, "caelum-integration-testing", ServiceType.MCP_SERVER, "caelum-testing", "Integration testing MCP server"),
            PortAllocation(8117, "caelum-ollama-pool", ServiceType.MCP_SERVER, "caelum-ai", "Ollama pool MCP server"),
            
            # Additional Infrastructure
            PortAllocation(8200, "streamlit-apps", ServiceType.WEB_UI, "caelum-analytics", "Streamlit visualization apps"),
            PortAllocation(8300, "jupyter-lab", ServiceType.WEB_UI, "caelum-analytics", "Jupyter analysis environment"),
        ]
        
        for allocation in core_ports:
            self._allocations[allocation.port] = allocation
    
    def register_port(self, allocation: PortAllocation) -> bool:
        """Register a new port allocation."""
        if allocation.port in self._allocations:
            return False
        self._allocations[allocation.port] = allocation
        return True
    
    def get_allocation(self, port: int) -> Optional[PortAllocation]:
        """Get allocation info for a specific port."""
        return self._allocations.get(port)
    
    def find_available_port(self, start_range: int = 8400, end_range: int = 8500) -> Optional[int]:
        """Find the next available port in a given range."""
        for port in range(start_range, end_range + 1):
            if port not in self._allocations:
                return port
        return None
    
    def list_by_project(self, project: str) -> List[PortAllocation]:
        """List all port allocations for a specific project."""
        return [alloc for alloc in self._allocations.values() if alloc.project == project]
    
    def list_by_service_type(self, service_type: ServiceType) -> List[PortAllocation]:
        """List all port allocations for a specific service type."""
        return [alloc for alloc in self._allocations.values() if alloc.service_type == service_type]
    
    def get_all_allocations(self) -> Dict[int, PortAllocation]:
        """Get all current port allocations."""
        return self._allocations.copy()
    
    def is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        return port not in self._allocations
    
    def generate_port_map_report(self) -> str:
        """Generate a human-readable port allocation report."""
        lines = ["Caelum Ecosystem Port Allocation Map", "=" * 40, ""]
        
        # Group by project
        projects = {}
        for alloc in self._allocations.values():
            if alloc.project not in projects:
                projects[alloc.project] = []
            projects[alloc.project].append(alloc)
        
        for project, allocations in sorted(projects.items()):
            lines.append(f"\n📁 {project.upper()}")
            lines.append("-" * 30)
            for alloc in sorted(allocations, key=lambda x: x.port):
                lines.append(f"  {alloc}")
        
        return "\n".join(lines)
    
    def assign_service_to_machine(self, port: int, machine_id: str, ip_address: str) -> bool:
        """Assign a service port to a specific machine."""
        if port in self._allocations:
            self._allocations[port].machine_id = machine_id
            self._allocations[port].ip_address = ip_address
            return True
        return False
    
    def get_services_on_machine(self, machine_id: str) -> List[PortAllocation]:
        """Get all services running on a specific machine."""
        return [alloc for alloc in self._allocations.values() if alloc.machine_id == machine_id]
    
    def get_service_location(self, service_name: str) -> Optional[PortAllocation]:
        """Find where a specific service is running."""
        for alloc in self._allocations.values():
            if alloc.service_name == service_name:
                return alloc
        return None
    
    def update_from_machine_registry(self, machine_registry) -> None:
        """Update port assignments based on machine registry information."""
        # This will be called to sync with the machine registry
        for machine in machine_registry.machines.values():
            for service in machine.running_services:
                self.assign_service_to_machine(
                    service['port'], 
                    machine.machine_id, 
                    machine.primary_ip
                )
    
    def get_distributed_service_map(self) -> Dict[str, List[PortAllocation]]:
        """Get a map of services organized by machine for distributed coordination."""
        machine_services = {}
        for alloc in self._allocations.values():
            if alloc.machine_id:
                if alloc.machine_id not in machine_services:
                    machine_services[alloc.machine_id] = []
                machine_services[alloc.machine_id].append(alloc)
        return machine_services
    
    def find_service_endpoints(self, service_type: ServiceType) -> List[str]:
        """Find all endpoints for a specific type of service across the network."""
        endpoints = []
        for alloc in self._allocations.values():
            if alloc.service_type == service_type and alloc.ip_address:
                endpoints.append(f"{alloc.ip_address}:{alloc.port}")
        return endpoints


# Global registry instance
port_registry = CaelumPortRegistry()