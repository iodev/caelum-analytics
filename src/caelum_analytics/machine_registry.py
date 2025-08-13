"""Machine discovery and registry for distributed Caelum MCP servers."""

import asyncio
import json
import socket
import psutil
import platform
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

from .port_registry import port_registry


class MachineStatus(Enum):
    """Machine status states."""
    ONLINE = "online"
    OFFLINE = "offline" 
    BUSY = "busy"
    MAINTENANCE = "maintenance"


@dataclass
class ResourceInfo:
    """System resource information."""
    cpu_cores: int
    cpu_usage_percent: float
    memory_total_gb: float
    memory_available_gb: float
    memory_usage_percent: float
    disk_total_gb: float
    disk_available_gb: float
    disk_usage_percent: float
    gpu_info: Optional[List[dict]] = None


@dataclass
class NetworkInfo:
    """Network interface information."""
    hostname: str
    ip_addresses: List[str]
    mac_addresses: List[str]
    network_interfaces: List[dict]


@dataclass
class MachineNode:
    """Represents a machine in the distributed Caelum network."""
    machine_id: str
    hostname: str
    primary_ip: str
    network_info: NetworkInfo
    resources: ResourceInfo
    status: MachineStatus
    running_services: List[dict]
    available_ports: List[int]
    last_heartbeat: datetime
    caelum_version: str = "0.1.0"
    platform_info: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['last_heartbeat'] = self.last_heartbeat.isoformat()
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MachineNode':
        """Create from dictionary."""
        data['status'] = MachineStatus(data['status'])
        data['last_heartbeat'] = datetime.fromisoformat(data['last_heartbeat'])
        data['network_info'] = NetworkInfo(**data['network_info'])
        data['resources'] = ResourceInfo(**data['resources'])
        return cls(**data)


class MachineRegistry:
    """Registry for discovering and managing machines in the Caelum network."""
    
    def __init__(self):
        self.machines: Dict[str, MachineNode] = {}
        self.local_machine_id: Optional[str] = None
        self.heartbeat_interval = 30  # seconds
        self.offline_threshold = 90   # seconds
        
    def get_local_machine_info(self) -> MachineNode:
        """Get information about the local machine."""
        hostname = socket.gethostname()
        
        # Get network information
        ip_addresses = []
        mac_addresses = []
        interfaces = []
        
        for interface, addrs in psutil.net_if_addrs().items():
            interface_info = {"name": interface, "addresses": []}
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip_addresses.append(addr.address)
                    interface_info["addresses"].append({
                        "type": "ipv4",
                        "address": addr.address,
                        "netmask": addr.netmask
                    })
                elif addr.family == psutil.AF_LINK:
                    mac_addresses.append(addr.address)
                    interface_info["addresses"].append({
                        "type": "mac",
                        "address": addr.address
                    })
            interfaces.append(interface_info)
        
        primary_ip = self._get_primary_ip(ip_addresses)
        
        network_info = NetworkInfo(
            hostname=hostname,
            ip_addresses=ip_addresses,
            mac_addresses=mac_addresses,
            network_interfaces=interfaces
        )
        
        # Get resource information
        cpu_count = psutil.cpu_count()
        cpu_usage = psutil.cpu_percent(interval=1)
        
        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        
        disk = psutil.disk_usage('/')
        disk_total_gb = disk.total / (1024**3)
        disk_available_gb = disk.free / (1024**3)
        
        resources = ResourceInfo(
            cpu_cores=cpu_count,
            cpu_usage_percent=cpu_usage,
            memory_total_gb=round(memory_total_gb, 2),
            memory_available_gb=round(memory_available_gb, 2),
            memory_usage_percent=memory.percent,
            disk_total_gb=round(disk_total_gb, 2),
            disk_available_gb=round(disk_available_gb, 2),
            disk_usage_percent=disk.percent,
            gpu_info=self._get_gpu_info()
        )
        
        # Get running services (ports in use)
        running_services = self._get_running_services()
        available_ports = self._get_available_ports()
        
        # Create machine ID from MAC address
        machine_id = self._generate_machine_id(mac_addresses)
        
        platform_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
        
        machine = MachineNode(
            machine_id=machine_id,
            hostname=hostname,
            primary_ip=primary_ip,
            network_info=network_info,
            resources=resources,
            status=MachineStatus.ONLINE,
            running_services=running_services,
            available_ports=available_ports,
            last_heartbeat=datetime.now(timezone.utc),
            platform_info=platform_info
        )
        
        self.local_machine_id = machine_id
        return machine
    
    def _get_primary_ip(self, ip_addresses: List[str]) -> str:
        """Get the primary IP address for the machine."""
        # Filter out localhost
        external_ips = [ip for ip in ip_addresses if not ip.startswith('127.')]
        
        # Prefer private network IPs
        private_ips = [ip for ip in external_ips 
                      if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.')]
        
        if private_ips:
            return private_ips[0]
        elif external_ips:
            return external_ips[0]
        else:
            return '127.0.0.1'
    
    def _get_gpu_info(self) -> Optional[List[dict]]:
        """Get GPU information if available."""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            return [
                {
                    "id": gpu.id,
                    "name": gpu.name,
                    "memory_total": gpu.memoryTotal,
                    "memory_used": gpu.memoryUsed,
                    "memory_free": gpu.memoryFree,
                    "load": gpu.load,
                    "temperature": gpu.temperature
                }
                for gpu in gpus
            ]
        except ImportError:
            # GPUtil not available, try nvidia-ml-py
            try:
                import pynvml
                pynvml.nvmlInit()
                gpu_count = pynvml.nvmlDeviceGetCount()
                gpus = []
                for i in range(gpu_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpus.append({
                        "id": i,
                        "name": name,
                        "memory_total": memory_info.total // (1024**2),  # MB
                        "memory_used": memory_info.used // (1024**2),
                        "memory_free": memory_info.free // (1024**2)
                    })
                return gpus
            except (ImportError, Exception):
                return None
    
    def _get_running_services(self) -> List[dict]:
        """Get list of running services on known Caelum ports."""
        services = []
        
        # Check known Caelum ports from port registry
        for port, allocation in port_registry.get_all_allocations().items():
            if self._is_port_in_use(port):
                services.append({
                    "port": port,
                    "service_name": allocation.service_name,
                    "service_type": allocation.service_type.value,
                    "purpose": allocation.purpose,
                    "status": "running"
                })
        
        return services
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result == 0
        except Exception:
            return False
    
    def _get_available_ports(self) -> List[int]:
        """Get list of available ports in Caelum ranges."""
        available = []
        
        # Check MCP server range (8100-8199)
        for port in range(8100, 8200):
            if not self._is_port_in_use(port):
                available.append(port)
        
        # Check additional ranges
        for port in range(8400, 8500):
            if not self._is_port_in_use(port):
                available.append(port)
        
        return available[:20]  # Limit to first 20 available ports
    
    def _generate_machine_id(self, mac_addresses: List[str]) -> str:
        """Generate a unique machine ID from MAC addresses."""
        if mac_addresses:
            # Use first MAC address as base
            primary_mac = mac_addresses[0].replace(':', '').replace('-', '').lower()
            return f"caelum-{primary_mac[-8:]}"
        else:
            # Fallback to hostname
            return f"caelum-{socket.gethostname().lower()}"
    
    def register_machine(self, machine: MachineNode) -> None:
        """Register a machine in the network."""
        self.machines[machine.machine_id] = machine
    
    def update_machine_heartbeat(self, machine_id: str) -> None:
        """Update the heartbeat timestamp for a machine."""
        if machine_id in self.machines:
            self.machines[machine_id].last_heartbeat = datetime.now(timezone.utc)
            self.machines[machine_id].status = MachineStatus.ONLINE
    
    def get_online_machines(self) -> List[MachineNode]:
        """Get list of currently online machines."""
        now = datetime.now(timezone.utc)
        online_machines = []
        
        for machine in self.machines.values():
            time_since_heartbeat = (now - machine.last_heartbeat).total_seconds()
            if time_since_heartbeat <= self.offline_threshold:
                machine.status = MachineStatus.ONLINE
                online_machines.append(machine)
            else:
                machine.status = MachineStatus.OFFLINE
        
        return online_machines
    
    def get_machine_summary(self) -> dict:
        """Get summary statistics for all machines."""
        online_machines = self.get_online_machines()
        total_machines = len(self.machines)
        online_count = len(online_machines)
        
        total_resources = {
            "cpu_cores": sum(m.resources.cpu_cores for m in online_machines),
            "memory_total_gb": sum(m.resources.memory_total_gb for m in online_machines),
            "memory_available_gb": sum(m.resources.memory_available_gb for m in online_machines),
            "disk_total_gb": sum(m.resources.disk_total_gb for m in online_machines),
            "disk_available_gb": sum(m.resources.disk_available_gb for m in online_machines),
            "gpu_count": sum(len(m.resources.gpu_info) if m.resources.gpu_info else 0 for m in online_machines)
        }
        
        return {
            "total_machines": total_machines,
            "online_machines": online_count,
            "offline_machines": total_machines - online_count,
            "total_resources": total_resources,
            "machines": [m.to_dict() for m in online_machines]
        }
    
    def discover_network_machines(self, ip_range: str = "192.168.1.0/24") -> List[str]:
        """Discover potential Caelum machines on the network."""
        # This would implement network scanning for Caelum Analytics endpoints
        # For now, return empty list - would be implemented in Phase 1 Week 2
        return []


# Global machine registry instance
machine_registry = MachineRegistry()