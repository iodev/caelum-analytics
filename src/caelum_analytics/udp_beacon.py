"""UDP beacon discovery system for Caelum cluster machines.

This module implements UDP broadcasting for automatic discovery of other Caelum machines
on the local network, complementing the existing WebSocket cluster communication.
"""

import asyncio
import json
import socket
import struct
import time
import ipaddress
from typing import Dict, List, Optional, Set, Callable, Any
from datetime import datetime, timezone
import logging
import threading
from dataclasses import dataclass, asdict

from .machine_registry import machine_registry, MachineNode

logger = logging.getLogger(__name__)

# UDP beacon configuration
BEACON_PORT = 8181
BEACON_MULTICAST_GROUP = '239.255.43.21'  # Local multicast address
BEACON_INTERVAL = 15  # seconds
DISCOVERY_TIMEOUT = 5  # seconds


@dataclass
class BeaconMessage:
    """UDP beacon message format."""
    
    message_type: str
    machine_id: str
    hostname: str
    primary_ip: str
    cluster_id: str
    cluster_name: str
    websocket_port: int = 8080
    services: List[dict] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.services is None:
            self.services = []
    
    def to_json(self) -> bytes:
        """Convert message to JSON bytes for UDP transmission."""
        return json.dumps(asdict(self)).encode('utf-8')
    
    @classmethod
    def from_json(cls, data: bytes) -> "BeaconMessage":
        """Create message from JSON bytes."""
        return cls(**json.loads(data.decode('utf-8')))


class UDPBeaconDiscovery:
    """UDP beacon system for automatic machine discovery."""
    
    def __init__(self):
        self.is_running = False
        self.beacon_socket: Optional[socket.socket] = None
        self.listen_socket: Optional[socket.socket] = None
        self.beacon_thread: Optional[threading.Thread] = None
        self.listen_thread: Optional[threading.Thread] = None
        
        # Discovered machines from UDP beacons
        self.discovered_machines: Dict[str, dict] = {}
        self.last_seen: Dict[str, float] = {}
        
        # Callbacks for when machines are discovered
        self.discovery_callbacks: List[Callable[[dict], None]] = []
        
        # Machine offline threshold
        self.offline_threshold = 60  # seconds
    
    def add_discovery_callback(self, callback: Callable[[dict], None]):
        """Add callback to be called when a machine is discovered."""
        self.discovery_callbacks.append(callback)
    
    def start(self):
        """Start the UDP beacon discovery system."""
        if self.is_running:
            logger.warning("UDP beacon discovery already running")
            return
        
        try:
            self._setup_beacon_socket()
            self._setup_listen_socket()
            
            self.is_running = True
            
            # Start beacon broadcasting thread
            self.beacon_thread = threading.Thread(target=self._beacon_loop, daemon=True)
            self.beacon_thread.start()
            
            # Start listening thread
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listen_thread.start()
            
            logger.info(f"UDP beacon discovery started on port {BEACON_PORT}")
            
        except Exception as e:
            logger.error(f"Failed to start UDP beacon discovery: {e}")
            self.stop()
    
    def stop(self):
        """Stop the UDP beacon discovery system."""
        self.is_running = False
        
        if self.beacon_socket:
            try:
                self.beacon_socket.close()
            except:
                pass
            self.beacon_socket = None
        
        if self.listen_socket:
            try:
                self.listen_socket.close()
            except:
                pass
            self.listen_socket = None
        
        # Wait for threads to finish
        if self.beacon_thread and self.beacon_thread.is_alive():
            self.beacon_thread.join(timeout=2)
        
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2)
        
        logger.info("UDP beacon discovery stopped")
    
    def _setup_beacon_socket(self):
        """Setup UDP socket for broadcasting beacons."""
        self.beacon_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.beacon_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.beacon_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Set up multicast
        try:
            self.beacon_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
            multicast_group = socket.inet_aton(BEACON_MULTICAST_GROUP)
            self.beacon_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                                        multicast_group + socket.inet_aton('0.0.0.0'))
        except Exception as e:
            logger.warning(f"Failed to setup multicast: {e}, using broadcast")
    
    def _setup_listen_socket(self):
        """Setup UDP socket for listening to beacons."""
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            # Bind to the beacon port
            self.listen_socket.bind(('', BEACON_PORT))
            
            # Join multicast group
            multicast_group = socket.inet_aton(BEACON_MULTICAST_GROUP)
            mreq = multicast_group + socket.inet_aton('0.0.0.0')
            self.listen_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            # Set timeout for non-blocking operation
            self.listen_socket.settimeout(1.0)
            
        except Exception as e:
            logger.error(f"Failed to setup listen socket: {e}")
            raise
    
    def _beacon_loop(self):
        """Main beacon broadcasting loop."""
        logger.info("UDP beacon broadcasting started")
        
        while self.is_running:
            try:
                self._send_beacon()
                time.sleep(BEACON_INTERVAL)
            except Exception as e:
                if self.is_running:  # Only log if we're supposed to be running
                    logger.error(f"Error in beacon loop: {e}")
                time.sleep(BEACON_INTERVAL)
    
    def _listen_loop(self):
        """Main beacon listening loop."""
        logger.info("UDP beacon listening started")
        
        while self.is_running:
            try:
                if self.listen_socket:
                    try:
                        data, addr = self.listen_socket.recvfrom(4096)
                        self._handle_beacon_message(data, addr[0])
                    except socket.timeout:
                        # Normal timeout, continue
                        continue
                    except Exception as e:
                        if self.is_running:
                            logger.warning(f"Error receiving beacon: {e}")
                
                # Cleanup old machines
                self._cleanup_offline_machines()
                
            except Exception as e:
                if self.is_running:
                    logger.error(f"Error in listen loop: {e}")
                time.sleep(1)
    
    def _send_beacon(self):
        """Send UDP beacon message."""
        if not machine_registry.local_machine_id:
            return
        
        local_machine = machine_registry.machines.get(machine_registry.local_machine_id)
        if not local_machine:
            return
        
        try:
            beacon = BeaconMessage(
                message_type="CAELUM_BEACON",
                machine_id=local_machine.machine_id,
                hostname=local_machine.hostname,
                primary_ip=local_machine.primary_ip,
                cluster_id=local_machine.cluster_id or "",
                cluster_name=local_machine.cluster_name or "",
                websocket_port=8080,
                services=[{
                    'name': svc['service_name'],
                    'type': svc['service_type'], 
                    'port': svc['port'],
                    'status': svc['status']
                } for svc in local_machine.running_services]
            )
            
            beacon_data = beacon.to_json()
            
            # Send to multicast group
            try:
                self.beacon_socket.sendto(beacon_data, (BEACON_MULTICAST_GROUP, BEACON_PORT))
            except Exception:
                pass  # Multicast might fail, continue with broadcast
            
            # Send to local broadcast
            try:
                self.beacon_socket.sendto(beacon_data, ('255.255.255.255', BEACON_PORT))
            except Exception:
                pass  # Broadcast might fail too
            
            # Send to local network ranges
            self._send_to_local_networks(beacon_data)
            
        except Exception as e:
            logger.error(f"Failed to send beacon: {e}")
    
    def _send_to_local_networks(self, beacon_data: bytes):
        """Send beacon to common local network broadcast addresses."""
        local_networks = [
            '192.168.1.255',   # Common home network
            '192.168.0.255',   # Common home network  
            '10.0.0.255',      # Common private network
            '172.16.255.255',  # Common private network
        ]
        
        # Try to detect actual local network
        try:
            local_machine = machine_registry.machines.get(machine_registry.local_machine_id)
            if local_machine:
                for ip_addr in local_machine.network_info.ip_addresses:
                    if not ip_addr.startswith('127.'):
                        try:
                            # Calculate broadcast address
                            network = ipaddress.IPv4Network(f"{ip_addr}/24", strict=False)
                            broadcast_addr = str(network.broadcast_address)
                            local_networks.append(broadcast_addr)
                        except:
                            continue
        except Exception:
            pass
        
        # Send to all network addresses
        for addr in set(local_networks):  # Remove duplicates
            try:
                self.beacon_socket.sendto(beacon_data, (addr, BEACON_PORT))
            except Exception:
                continue  # Silent fail for network sends
    
    def _handle_beacon_message(self, data: bytes, sender_ip: str):
        """Handle received beacon message."""
        try:
            beacon = BeaconMessage.from_json(data)
            
            # Ignore our own beacons
            if beacon.machine_id == machine_registry.local_machine_id:
                return
            
            # Validate beacon
            if beacon.message_type != "CAELUM_BEACON":
                return
            
            current_time = time.time()
            machine_id = beacon.machine_id
            
            # Update discovered machines
            machine_info = {
                'machine_id': beacon.machine_id,
                'hostname': beacon.hostname,
                'primary_ip': beacon.primary_ip,
                'sender_ip': sender_ip,
                'cluster_id': beacon.cluster_id,
                'cluster_name': beacon.cluster_name,
                'websocket_port': beacon.websocket_port,
                'services': beacon.services,
                'last_seen': current_time,
                'discovery_method': 'UDP_BEACON'
            }
            
            # Check if this is a new discovery
            is_new = machine_id not in self.discovered_machines
            
            self.discovered_machines[machine_id] = machine_info
            self.last_seen[machine_id] = current_time
            
            if is_new:
                logger.info(f"🎯 UDP discovered new Caelum machine: {beacon.hostname} ({beacon.primary_ip})")
                
                # Try to create and register MachineNode
                try:
                    # We need more complete information to create a full MachineNode
                    # For now, we'll notify callbacks and let WebSocket handle full registration
                    for callback in self.discovery_callbacks:
                        callback(machine_info)
                        
                except Exception as e:
                    logger.error(f"Failed to register discovered machine: {e}")
            
        except Exception as e:
            logger.warning(f"Invalid beacon message from {sender_ip}: {e}")
    
    def _cleanup_offline_machines(self):
        """Remove machines that haven't sent beacons recently."""
        current_time = time.time()
        offline_machines = []
        
        for machine_id, last_seen in self.last_seen.items():
            if current_time - last_seen > self.offline_threshold:
                offline_machines.append(machine_id)
        
        for machine_id in offline_machines:
            if machine_id in self.discovered_machines:
                machine_info = self.discovered_machines[machine_id]
                logger.info(f"🔴 UDP machine went offline: {machine_info['hostname']} ({machine_info['primary_ip']})")
                
                del self.discovered_machines[machine_id]
                del self.last_seen[machine_id]
    
    def get_discovered_machines(self) -> List[dict]:
        """Get list of machines discovered via UDP beacons."""
        return list(self.discovered_machines.values())
    
    def trigger_discovery(self) -> List[dict]:
        """Trigger immediate discovery by sending beacon and waiting for responses."""
        if not self.is_running:
            return []
        
        # Clear old discoveries for fresh scan
        discovered_before = set(self.discovered_machines.keys())
        
        # Send immediate beacon
        self._send_beacon()
        
        # Wait for responses
        time.sleep(DISCOVERY_TIMEOUT)
        
        # Return newly discovered machines
        discovered_now = set(self.discovered_machines.keys())
        new_machines = discovered_now - discovered_before
        
        return [self.discovered_machines[mid] for mid in new_machines if mid in self.discovered_machines]


# Global UDP beacon discovery instance
udp_beacon = UDPBeaconDiscovery()


def start_udp_beacon_discovery():
    """Start the global UDP beacon discovery system."""
    udp_beacon.start()


def stop_udp_beacon_discovery():
    """Stop the global UDP beacon discovery system."""
    udp_beacon.stop()


def get_udp_discovered_machines() -> List[dict]:
    """Get machines discovered via UDP beacons."""
    return udp_beacon.get_discovered_machines()


def trigger_udp_discovery() -> List[dict]:
    """Trigger immediate UDP discovery."""
    return udp_beacon.trigger_discovery()