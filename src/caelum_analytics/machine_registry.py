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
    cluster_id: Optional[str] = None  # Unique cluster identifier
    cluster_name: Optional[str] = None  # Human-readable cluster name
    machine_role: str = "node"  # node, coordinator, hybrid

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["last_heartbeat"] = self.last_heartbeat.isoformat()
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "MachineNode":
        """Create from dictionary."""
        data["status"] = MachineStatus(data["status"])
        data["last_heartbeat"] = datetime.fromisoformat(data["last_heartbeat"])
        data["network_info"] = NetworkInfo(**data["network_info"])
        data["resources"] = ResourceInfo(**data["resources"])
        return cls(**data)


class MachineRegistry:
    """Registry for discovering and managing machines in the Caelum network."""

    def __init__(self):
        self.machines: Dict[str, MachineNode] = {}
        self.local_machine_id: Optional[str] = None
        self.heartbeat_interval = 30  # seconds
        self.offline_threshold = 90  # seconds
        self.cluster_id = self._generate_cluster_id()
        self.cluster_name = self._get_cluster_name()

    def _generate_cluster_id(self) -> str:
        """Generate a unique cluster identifier."""
        import uuid
        import os

        # Try to load existing cluster ID from file
        cluster_file = os.path.expanduser("~/.caelum/cluster_id")
        if os.path.exists(cluster_file):
            try:
                with open(cluster_file, "r") as f:
                    return f.read().strip()
            except Exception:
                pass

        # Generate new cluster ID
        cluster_id = str(uuid.uuid4())

        # Save cluster ID
        try:
            os.makedirs(os.path.dirname(cluster_file), exist_ok=True)
            with open(cluster_file, "w") as f:
                f.write(cluster_id)
        except Exception:
            pass

        return cluster_id

    def _get_cluster_name(self) -> str:
        """Get cluster name from environment or generate one."""
        import os

        # Check environment variable first
        cluster_name = os.getenv("CAELUM_CLUSTER_NAME")
        if cluster_name:
            return cluster_name

        # Try to load from config file
        cluster_file = os.path.expanduser("~/.caelum/cluster_name")
        if os.path.exists(cluster_file):
            try:
                with open(cluster_file, "r") as f:
                    return f.read().strip()
            except Exception:
                pass

        # Generate descriptive name based on hostname and location
        hostname = socket.gethostname()
        primary_ip = self._get_primary_ip([])

        # Create a readable cluster name
        cluster_name = f"caelum-{hostname.lower()}-{primary_ip.split('.')[-1]}"

        # Save cluster name
        try:
            os.makedirs(os.path.dirname(cluster_file), exist_ok=True)
            with open(cluster_file, "w") as f:
                f.write(cluster_name)
        except Exception:
            pass

        return cluster_name

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
                    interface_info["addresses"].append(
                        {
                            "type": "ipv4",
                            "address": addr.address,
                            "netmask": addr.netmask,
                        }
                    )
                elif addr.family == psutil.AF_LINK:
                    mac_addresses.append(addr.address)
                    interface_info["addresses"].append(
                        {"type": "mac", "address": addr.address}
                    )
            interfaces.append(interface_info)

        primary_ip = self._get_primary_ip(ip_addresses)

        network_info = NetworkInfo(
            hostname=hostname,
            ip_addresses=ip_addresses,
            mac_addresses=mac_addresses,
            network_interfaces=interfaces,
        )

        # Get resource information
        cpu_count = psutil.cpu_count()
        cpu_usage = psutil.cpu_percent(interval=1)

        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024**3)
        memory_available_gb = memory.available / (1024**3)

        disk = psutil.disk_usage("/")
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
            gpu_info=self._get_gpu_info(),
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
            "processor": platform.processor(),
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
            platform_info=platform_info,
            cluster_id=self.cluster_id,
            cluster_name=self.cluster_name,
            machine_role="coordinator",  # This machine is running the analytics dashboard
        )

        self.local_machine_id = machine_id
        return machine

    def _get_primary_ip(self, ip_addresses: List[str]) -> str:
        """Get the primary IP address for the machine."""
        # Filter out localhost
        external_ips = [ip for ip in ip_addresses if not ip.startswith("127.")]

        # Prioritize network selection for real hardware-to-hardware discovery
        # 1. VPN networks (10.x.x.x range) - for real machine discovery
        # 2. Common private networks (192.168.x.x, 172.16-31.x.x)  
        # 3. WSL/Docker internal networks (172.17+.x.x) - lowest priority
        
        # VPN networks (10.x.x.x range) - highest priority for hardware discovery
        vpn_ips = [ip for ip in external_ips if ip.startswith("10.")]
        if vpn_ips:
            return vpn_ips[0]
        
        # Standard private networks
        standard_private_ips = [ip for ip in external_ips if ip.startswith("192.168.")]
        if standard_private_ips:
            return standard_private_ips[0]
            
        # Private 172.x networks, but prefer lower ranges (172.16-31 over 172.17+)
        private_172_ips = [ip for ip in external_ips if ip.startswith("172.")]
        if private_172_ips:
            # Sort to prefer 172.16-31.x.x (standard private) over 172.17+.x.x (Docker/WSL)
            private_172_ips.sort(key=lambda ip: int(ip.split('.')[1]))
            return private_172_ips[0]

        # Fallback to any remaining external IP
        if external_ips:
            return external_ips[0]
        else:
            return "127.0.0.1"

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
                    "temperature": gpu.temperature,
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
                    name = pynvml.nvmlDeviceGetName(handle).decode("utf-8")
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpus.append(
                        {
                            "id": i,
                            "name": name,
                            "memory_total": memory_info.total // (1024**2),  # MB
                            "memory_used": memory_info.used // (1024**2),
                            "memory_free": memory_info.free // (1024**2),
                        }
                    )
                return gpus
            except (ImportError, Exception):
                return None

    def _get_running_services(self) -> List[dict]:
        """Get list of running services on known Caelum ports."""
        services = []

        # Check known Caelum ports from port registry
        for port, allocation in port_registry.get_all_allocations().items():
            if self._is_port_in_use(port):
                services.append(
                    {
                        "port": port,
                        "service_name": allocation.service_name,
                        "service_type": allocation.service_type.value,
                        "purpose": allocation.purpose,
                        "status": "running",
                    }
                )

        return services

    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(("localhost", port))
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
            primary_mac = mac_addresses[0].replace(":", "").replace("-", "").lower()
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
            "memory_total_gb": sum(
                m.resources.memory_total_gb for m in online_machines
            ),
            "memory_available_gb": sum(
                m.resources.memory_available_gb for m in online_machines
            ),
            "disk_total_gb": sum(m.resources.disk_total_gb for m in online_machines),
            "disk_available_gb": sum(
                m.resources.disk_available_gb for m in online_machines
            ),
            "gpu_count": sum(
                len(m.resources.gpu_info) if m.resources.gpu_info else 0
                for m in online_machines
            ),
        }

        return {
            "total_machines": total_machines,
            "online_machines": online_count,
            "offline_machines": total_machines - online_count,
            "total_resources": total_resources,
            "machines": [m.to_dict() for m in online_machines],
        }

    async def discover_network_machines(self, ip_range: str = None) -> List[str]:
        """Discover potential Caelum machines on the network."""
        import subprocess
        import ipaddress
        from concurrent.futures import ThreadPoolExecutor

        discovered = []

        if ip_range is None:
            # Auto-detect network range from primary interface
            ip_range = self._get_network_range()

        if not ip_range:
            return []

        try:
            # Parse the network range
            network = ipaddress.IPv4Network(ip_range, strict=False)

            # Limit scan to reasonable range for faster discovery
            hosts_to_scan = list(network.hosts())[:100]  # Limit to first 100 IPs

            # Scan for machines with Caelum Analytics endpoints
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = []
                for ip in hosts_to_scan:
                    if str(ip) != self._get_primary_ip([]):  # Skip self
                        futures.append(
                            executor.submit(self._check_caelum_endpoint, str(ip))
                        )

                for future in futures:
                    result = future.result()
                    if result:
                        discovered.append(result)

        except Exception as e:
            print(f"Network discovery error: {e}")

        return discovered

    def _get_network_range(self) -> Optional[str]:
        """Get the network range for the primary interface."""
        try:
            # Get the primary IP and determine network
            primary_ip = None
            netmask = None

            for interface, addrs in psutil.net_if_addrs().items():
                if interface.startswith(("lo", "docker", "br-")):
                    continue

                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        ip = addr.address
                        if not ip.startswith("127.") and addr.netmask:
                            primary_ip = ip
                            netmask = addr.netmask
                            break
                if primary_ip:
                    break

            if primary_ip and netmask:
                import ipaddress

                network = ipaddress.IPv4Network(f"{primary_ip}/{netmask}", strict=False)
                return str(network.network_address) + "/" + str(network.prefixlen)

        except Exception as e:
            print(f"Error detecting network range: {e}")

        return None

    def _check_caelum_endpoint(self, ip: str) -> Optional[str]:
        """Check if an IP has a Caelum Analytics endpoint."""
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        # Ports to check for Caelum services
        caelum_ports = [8090, 8080, 8100, 8101, 8102, 8103, 8104, 8105]

        for port in caelum_ports:
            try:
                # Quick connection check first
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(0.3)  # Shorter timeout
                    if sock.connect_ex((ip, port)) != 0:
                        continue

                # Try to get Caelum identification
                session = requests.Session()
                retry_strategy = Retry(total=1, backoff_factor=0.1)
                adapter = HTTPAdapter(max_retries=retry_strategy)
                session.mount("http://", adapter)

                urls_to_try = [
                    f"http://{ip}:{port}/api/v1/machines",
                    f"http://{ip}:{port}/api/v1/cluster/status",
                    f"http://{ip}:{port}/",
                ]

                for url in urls_to_try:
                    try:
                        response = session.get(url, timeout=1)  # Shorter timeout
                        if response.status_code == 200:
                            # Check if response indicates Caelum system
                            content = response.text.lower()
                            if any(
                                keyword in content
                                for keyword in ["caelum", "mcp", "analytics", "cluster"]
                            ):
                                return f"{ip}:{port}"
                    except:
                        continue

            except Exception:
                continue

        return None

    def get_cluster_info(self) -> dict:
        """Get information about this cluster."""
        return {
            "cluster_id": self.cluster_id,
            "cluster_name": self.cluster_name,
            "total_machines": len(self.machines),
            "online_machines": len(self.get_online_machines()),
            "coordinator_machine": self.local_machine_id,
        }

    def get_discovered_clusters(self) -> Dict[str, dict]:
        """Get information about discovered clusters."""
        clusters = {}

        for machine in self.machines.values():
            if machine.cluster_id and machine.cluster_id != self.cluster_id:
                cluster_id = machine.cluster_id
                if cluster_id not in clusters:
                    clusters[cluster_id] = {
                        "cluster_id": cluster_id,
                        "cluster_name": machine.cluster_name
                        or f"Unknown-{cluster_id[:8]}",
                        "machines": [],
                        "total_resources": {
                            "cpu_cores": 0,
                            "memory_total_gb": 0,
                            "memory_available_gb": 0,
                            "disk_total_gb": 0,
                            "disk_available_gb": 0,
                            "gpu_count": 0,
                        },
                    }

                clusters[cluster_id]["machines"].append(machine.to_dict())
                # Aggregate resources
                res = clusters[cluster_id]["total_resources"]
                res["cpu_cores"] += machine.resources.cpu_cores
                res["memory_total_gb"] += machine.resources.memory_total_gb
                res["memory_available_gb"] += machine.resources.memory_available_gb
                res["disk_total_gb"] += machine.resources.disk_total_gb
                res["disk_available_gb"] += machine.resources.disk_available_gb
                res["gpu_count"] += (
                    len(machine.resources.gpu_info) if machine.resources.gpu_info else 0
                )

        return clusters


# Global machine registry instance
machine_registry = MachineRegistry()
