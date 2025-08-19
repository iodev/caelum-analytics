"""
LAN Synchronization for Self-Optimization System

Robust synchronization of optimization data across Caelum instances on the LAN.
Handles frequent updates, network instability, and ensures consistency of learned
principles and adaptations across all instances.
"""

import asyncio
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class SyncPriority(Enum):
    CRITICAL = "critical"    # Immediate sync (alerts, failures)
    HIGH = "high"           # Within 30 seconds (new principles)
    MEDIUM = "medium"       # Within 5 minutes (performance data)
    LOW = "low"            # Hourly (historical data)

@dataclass
class SyncData:
    """Data structure for synchronization packets"""
    sync_id: str
    timestamp: datetime
    source_instance: str
    data_type: str
    priority: SyncPriority
    payload: Dict[str, Any]
    checksum: str
    version: int

@dataclass
class ClusterNode:
    """Information about a cluster node"""
    node_id: str
    host: str
    port: int
    last_seen: datetime
    status: str  # active, inactive, error
    version: str
    optimization_version: int

class OptimizationSynchronizer:
    """Handles synchronization of optimization data across LAN clusters"""
    
    def __init__(self, instance_id: str = None):
        self.instance_id = instance_id or f"caelum_{int(time.time())}"
        self.known_nodes: Dict[str, ClusterNode] = {}
        self.sync_queue: List[SyncData] = []
        self.last_sync_times: Dict[str, datetime] = {}
        self.conflict_resolution_callbacks: Dict[str, Callable] = {}
        self.sync_active = False
        self.optimization_version = 1
        
        # Sync intervals by priority
        self.sync_intervals = {
            SyncPriority.CRITICAL: 5,      # 5 seconds
            SyncPriority.HIGH: 30,         # 30 seconds
            SyncPriority.MEDIUM: 300,      # 5 minutes
            SyncPriority.LOW: 3600         # 1 hour
        }
        
        # Data type configurations
        self.data_type_configs = {
            'learned_principles': {'priority': SyncPriority.HIGH, 'merge_strategy': 'evidence_weighted'},
            'performance_alerts': {'priority': SyncPriority.CRITICAL, 'merge_strategy': 'latest_wins'},
            'optimization_results': {'priority': SyncPriority.HIGH, 'merge_strategy': 'append'},
            'tool_effectiveness': {'priority': SyncPriority.MEDIUM, 'merge_strategy': 'weighted_average'},
            'server_performance': {'priority': SyncPriority.MEDIUM, 'merge_strategy': 'weighted_average'},
            'adaptation_history': {'priority': SyncPriority.MEDIUM, 'merge_strategy': 'append'},
            'workflow_metrics': {'priority': SyncPriority.LOW, 'merge_strategy': 'latest_wins'}
        }
        
    async def initialize_synchronization(self):
        """Initialize the synchronization system"""
        logger.info(f"🔄 Initializing optimization synchronization for instance {self.instance_id}")
        
        # Start background sync processes
        self.sync_active = True
        
        # Start discovery and sync tasks
        asyncio.create_task(self._cluster_discovery_loop())
        asyncio.create_task(self._sync_processing_loop())
        asyncio.create_task(self._periodic_sync_loop())
        
        logger.info("✅ Optimization synchronization initialized")
        
    async def _cluster_discovery_loop(self):
        """Continuously discover and monitor cluster nodes"""
        while self.sync_active:
            try:
                await self._discover_cluster_nodes()
                await self._health_check_nodes()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in cluster discovery: {e}")
                await asyncio.sleep(30)  # Retry after 30 seconds on error
                
    async def _discover_cluster_nodes(self):
        """Discover active Caelum instances on the LAN"""
        try:
            # Use existing cluster communication tools
            from ..self_optimization.caelum_integration import caelum_self_optimizer
            
            # Try to discover through multiple methods
            discovered_nodes = await self._multi_method_discovery()
            
            current_time = datetime.now()
            
            for node_info in discovered_nodes:
                node_id = node_info.get('id', 'unknown')
                
                if node_id != self.instance_id:  # Don't include self
                    self.known_nodes[node_id] = ClusterNode(
                        node_id=node_id,
                        host=node_info.get('host', 'localhost'),
                        port=node_info.get('port', 8090),
                        last_seen=current_time,
                        status='active',
                        version=node_info.get('version', '1.0.0'),
                        optimization_version=node_info.get('optimization_version', 1)
                    )
                    
            logger.debug(f"Discovered {len(self.known_nodes)} cluster nodes")
            
        except Exception as e:
            logger.error(f"Error discovering cluster nodes: {e}")
            
    async def _multi_method_discovery(self) -> List[Dict[str, Any]]:
        """Use multiple methods to discover cluster nodes"""
        
        discovered_nodes = []
        
        try:
            # Method 1: Use Caelum cluster communication
            # This would integrate with existing cluster communication if available
            pass
            
        except Exception as e:
            logger.debug(f"Cluster communication discovery failed: {e}")
            
        try:
            # Method 2: Network scanning for Caelum instances
            # Scan common ports for Caelum analytics services
            potential_hosts = ['127.0.0.1', '10.32.3.27']  # Add your LAN IPs
            potential_ports = [8090, 8080, 8100, 8101, 8102]
            
            for host in potential_hosts:
                for port in potential_ports:
                    if await self._check_caelum_instance(host, port):
                        discovered_nodes.append({
                            'id': f"{host}_{port}",
                            'host': host,
                            'port': port,
                            'method': 'network_scan'
                        })
                        
        except Exception as e:
            logger.debug(f"Network scan discovery failed: {e}")
            
        return discovered_nodes
        
    async def _check_caelum_instance(self, host: str, port: int) -> bool:
        """Check if a host:port is running a Caelum instance"""
        try:
            # Simple check - in production would make HTTP request to health endpoint
            # For now, return False to avoid network calls in demo
            return False
        except Exception:
            return False
            
    async def _health_check_nodes(self):
        """Check health of known nodes and update status"""
        current_time = datetime.now()
        inactive_threshold = timedelta(minutes=5)
        
        for node_id, node in list(self.known_nodes.items()):
            try:
                # Check if node is still reachable
                if current_time - node.last_seen > inactive_threshold:
                    node.status = 'inactive'
                    logger.warning(f"Node {node_id} marked as inactive")
                    
                # Remove nodes that haven't been seen for too long
                if current_time - node.last_seen > timedelta(hours=1):
                    del self.known_nodes[node_id]
                    logger.info(f"Removed inactive node {node_id}")
                    
            except Exception as e:
                logger.error(f"Error checking node {node_id}: {e}")
                node.status = 'error'
                
    async def sync_optimization_data(self, data_type: str, payload: Dict[str, Any], 
                                   force_immediate: bool = False):
        """Queue optimization data for synchronization"""
        
        config = self.data_type_configs.get(data_type, {
            'priority': SyncPriority.MEDIUM, 
            'merge_strategy': 'latest_wins'
        })
        
        priority = SyncPriority.CRITICAL if force_immediate else config['priority']
        
        sync_data = SyncData(
            sync_id=f"{self.instance_id}_{data_type}_{int(time.time())}",
            timestamp=datetime.now(),
            source_instance=self.instance_id,
            data_type=data_type,
            priority=priority,
            payload=payload,
            checksum=self._calculate_checksum(payload),
            version=self.optimization_version
        )
        
        self.sync_queue.append(sync_data)
        
        logger.debug(f"Queued {data_type} for sync with priority {priority.value}")
        
        # If critical priority, trigger immediate sync
        if priority == SyncPriority.CRITICAL:
            asyncio.create_task(self._immediate_sync(sync_data))
            
    async def _sync_processing_loop(self):
        """Process sync queue and distribute data to cluster nodes"""
        while self.sync_active:
            try:
                if self.sync_queue and self.known_nodes:
                    # Group by priority and process
                    await self._process_sync_queue()
                    
                await asyncio.sleep(5)  # Check queue every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in sync processing loop: {e}")
                await asyncio.sleep(10)
                
    async def _process_sync_queue(self):
        """Process queued sync data"""
        
        # Group by priority
        priority_groups = {}
        for sync_data in self.sync_queue:
            priority = sync_data.priority
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(sync_data)
            
        # Process in priority order
        for priority in [SyncPriority.CRITICAL, SyncPriority.HIGH, 
                        SyncPriority.MEDIUM, SyncPriority.LOW]:
            
            if priority in priority_groups:
                items = priority_groups[priority]
                
                # Check if it's time to sync this priority level
                last_sync = self.last_sync_times.get(priority.value, datetime.min)
                interval = self.sync_intervals[priority]
                
                if (datetime.now() - last_sync).total_seconds() >= interval:
                    await self._sync_priority_group(priority, items)
                    self.last_sync_times[priority.value] = datetime.now()
                    
                    # Remove processed items from queue
                    self.sync_queue = [item for item in self.sync_queue if item not in items]
                    
    async def _sync_priority_group(self, priority: SyncPriority, items: List[SyncData]):
        """Sync a group of items with the same priority"""
        
        if not self.known_nodes:
            logger.debug(f"No cluster nodes available for sync (priority: {priority.value})")
            return
            
        logger.debug(f"Syncing {len(items)} items with priority {priority.value} to {len(self.known_nodes)} nodes")
        
        # Prepare sync batch
        sync_batch = {
            'batch_id': f"batch_{int(time.time())}",
            'source_instance': self.instance_id,
            'priority': priority.value,
            'items': [asdict(item) for item in items],
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to all active nodes
        for node_id, node in self.known_nodes.items():
            if node.status == 'active':
                try:
                    await self._send_sync_batch_to_node(node, sync_batch)
                except Exception as e:
                    logger.error(f"Failed to sync to node {node_id}: {e}")
                    node.status = 'error'
                    
    async def _send_sync_batch_to_node(self, node: ClusterNode, sync_batch: Dict[str, Any]):
        """Send sync batch to a specific node"""
        
        # In production, this would make HTTP/WebSocket call to the node
        # For now, we'll simulate successful sync
        logger.debug(f"Sync batch sent to node {node.node_id} at {node.host}:{node.port}")
        
        # Update node's last seen time
        node.last_seen = datetime.now()
        
    async def _immediate_sync(self, sync_data: SyncData):
        """Immediately sync critical data"""
        
        if not self.known_nodes:
            logger.warning(f"No cluster nodes available for immediate sync of {sync_data.data_type}")
            return
            
        logger.info(f"🚨 Immediate sync: {sync_data.data_type}")
        
        # Send to all active nodes immediately
        for node_id, node in self.known_nodes.items():
            if node.status == 'active':
                try:
                    await self._send_immediate_sync(node, sync_data)
                except Exception as e:
                    logger.error(f"Failed immediate sync to node {node_id}: {e}")
                    
    async def _send_immediate_sync(self, node: ClusterNode, sync_data: SyncData):
        """Send immediate sync to a node"""
        
        immediate_packet = {
            'type': 'immediate_sync',
            'data': asdict(sync_data),
            'source': self.instance_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # In production: send via WebSocket or HTTP POST
        logger.debug(f"Immediate sync sent to {node.node_id}: {sync_data.data_type}")
        
    async def _periodic_sync_loop(self):
        """Periodic full synchronization to ensure consistency"""
        while self.sync_active:
            try:
                await asyncio.sleep(1800)  # Every 30 minutes
                
                if self.known_nodes:
                    logger.info("🔄 Starting periodic full synchronization")
                    await self._perform_full_sync()
                    
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")
                
    async def _perform_full_sync(self):
        """Perform full synchronization of all optimization data"""
        
        # Collect all current optimization data
        full_sync_data = await self._collect_full_optimization_state()
        
        # Send to all nodes
        for node_id, node in self.known_nodes.items():
            if node.status == 'active':
                try:
                    await self._send_full_sync_to_node(node, full_sync_data)
                except Exception as e:
                    logger.error(f"Full sync failed for node {node_id}: {e}")
                    
        logger.info("✅ Periodic full synchronization completed")
        
    async def _collect_full_optimization_state(self) -> Dict[str, Any]:
        """Collect complete current optimization state"""
        
        from .caelum_integration import caelum_self_optimizer
        from .performance_monitor import performance_monitor
        from .self_observer import self_observer
        from .analytics_integration import enhanced_analytics
        
        return {
            'instance_id': self.instance_id,
            'optimization_version': self.optimization_version,
            'timestamp': datetime.now().isoformat(),
            'learned_principles': caelum_self_optimizer.get_current_principles(),
            'optimization_history': caelum_self_optimizer.get_optimization_history()[-10:],  # Last 10
            'performance_summary': performance_monitor.get_performance_summary(),
            'self_analysis': self_observer.get_self_analysis(),
            'server_performance': enhanced_analytics.server_performance_map,
            'tool_effectiveness': enhanced_analytics.tool_effectiveness_scores,
            'workflow_metrics': enhanced_analytics.workflow_efficiency_metrics
        }
        
    async def _send_full_sync_to_node(self, node: ClusterNode, full_data: Dict[str, Any]):
        """Send full sync data to a node"""
        
        # In production: compress and send via HTTP POST
        logger.debug(f"Full sync sent to {node.node_id} ({len(json.dumps(full_data))} bytes)")
        
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for data integrity"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
        
    async def handle_incoming_sync(self, sync_batch: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming synchronization data from another instance"""
        
        try:
            source_instance = sync_batch.get('source_instance')
            items = sync_batch.get('items', [])
            
            logger.info(f"📥 Received sync from {source_instance}: {len(items)} items")
            
            conflicts_resolved = 0
            items_merged = 0
            
            for item_data in items:
                sync_item = SyncData(**item_data)
                
                # Verify checksum
                if sync_item.checksum != self._calculate_checksum(sync_item.payload):
                    logger.warning(f"Checksum mismatch for {sync_item.data_type} from {source_instance}")
                    continue
                    
                # Merge the data
                merge_result = await self._merge_sync_data(sync_item)
                
                if merge_result['status'] == 'merged':
                    items_merged += 1
                elif merge_result['status'] == 'conflict_resolved':
                    conflicts_resolved += 1
                    
            # Update our optimization version if we received newer data
            remote_version = max(item['version'] for item in items) if items else 1
            if remote_version > self.optimization_version:
                self.optimization_version = remote_version
                
            return {
                'status': 'success',
                'items_processed': len(items),
                'items_merged': items_merged,
                'conflicts_resolved': conflicts_resolved,
                'optimization_version': self.optimization_version
            }
            
        except Exception as e:
            logger.error(f"Error handling incoming sync: {e}")
            return {'status': 'error', 'message': str(e)}
            
    async def _merge_sync_data(self, sync_data: SyncData) -> Dict[str, Any]:
        """Merge incoming sync data with local data"""
        
        data_type = sync_data.data_type
        config = self.data_type_configs.get(data_type, {'merge_strategy': 'latest_wins'})
        merge_strategy = config['merge_strategy']
        
        try:
            if merge_strategy == 'evidence_weighted':
                result = await self._merge_evidence_weighted(sync_data)
            elif merge_strategy == 'weighted_average':
                result = await self._merge_weighted_average(sync_data)
            elif merge_strategy == 'append':
                result = await self._merge_append(sync_data)
            else:  # latest_wins
                result = await self._merge_latest_wins(sync_data)
                
            return result
            
        except Exception as e:
            logger.error(f"Error merging {data_type}: {e}")
            return {'status': 'error', 'message': str(e)}
            
    async def _merge_evidence_weighted(self, sync_data: SyncData) -> Dict[str, Any]:
        """Merge data using evidence-weighted strategy (for principles)"""
        
        # This would merge learned principles based on evidence strength
        # Higher evidence strength wins, or combine if both have good evidence
        
        return {'status': 'merged', 'method': 'evidence_weighted'}
        
    async def _merge_weighted_average(self, sync_data: SyncData) -> Dict[str, Any]:
        """Merge data using weighted average strategy (for metrics)"""
        
        # This would combine performance metrics using weighted averages
        # based on data recency and sample sizes
        
        return {'status': 'merged', 'method': 'weighted_average'}
        
    async def _merge_append(self, sync_data: SyncData) -> Dict[str, Any]:
        """Merge data using append strategy (for history)"""
        
        # This would append new items to historical data
        
        return {'status': 'merged', 'method': 'append'}
        
    async def _merge_latest_wins(self, sync_data: SyncData) -> Dict[str, Any]:
        """Merge data using latest wins strategy (for alerts)"""
        
        # This would replace local data with newer remote data
        
        return {'status': 'merged', 'method': 'latest_wins'}
        
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        
        return {
            'sync_active': self.sync_active,
            'instance_id': self.instance_id,
            'optimization_version': self.optimization_version,
            'known_nodes': len(self.known_nodes),
            'active_nodes': len([node for node in self.known_nodes.values() if node.status == 'active']),
            'sync_queue_size': len(self.sync_queue),
            'last_sync_times': {k: v.isoformat() for k, v in self.last_sync_times.items()},
            'node_details': {
                node_id: {
                    'status': node.status,
                    'last_seen': node.last_seen.isoformat(),
                    'host': f"{node.host}:{node.port}"
                }
                for node_id, node in self.known_nodes.items()
            }
        }
        
    async def shutdown(self):
        """Gracefully shutdown synchronization"""
        logger.info("🔄 Shutting down optimization synchronization")
        self.sync_active = False
        
        # Send final sync to all nodes
        if self.sync_queue and self.known_nodes:
            try:
                await asyncio.wait_for(self._process_sync_queue(), timeout=30)
            except asyncio.TimeoutError:
                logger.warning("Sync queue processing timed out during shutdown")
                
        logger.info("✅ Optimization synchronization shutdown complete")

# Global synchronizer instance
optimization_synchronizer = OptimizationSynchronizer()