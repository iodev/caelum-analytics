#!/usr/bin/env python3
"""
Caelum Analytics - Beacon Only Mode

This script runs only the UDP beacon discovery system without the full web interface.
Use this on machines that should be discoverable but don't need the analytics dashboard.

Usage:
    python beacon_only.py [--port PORT] [--host HOST]
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from caelum_analytics.machine_registry import machine_registry
from caelum_analytics.cluster_protocol import ClusterNode
from caelum_analytics.udp_beacon import start_udp_beacon_discovery, stop_udp_beacon_discovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global cluster node for graceful shutdown
cluster_node = None

async def start_beacon_only_mode(host: str = "0.0.0.0", port: int = 8080):
    """Start beacon-only mode with minimal cluster communication."""
    global cluster_node
    
    logger.info("🚀 Starting Caelum Analytics - Beacon Only Mode")
    
    try:
        # Initialize machine registry
        local_machine = machine_registry.get_local_machine_info()
        machine_registry.register_machine(local_machine)
        logger.info(f"📡 Registered machine: {local_machine.hostname} ({local_machine.machine_id})")
        
        # Create cluster node for WebSocket communication
        cluster_node = ClusterNode(port=port)
        
        # Start cluster communication server
        server = await cluster_node.start_server(host)
        logger.info(f"🌐 Cluster communication server started on {host}:{port}")
        
        logger.info("✅ Beacon-only mode is running. This machine is now discoverable on the network.")
        logger.info("💡 Other Caelum machines can now discover this machine using 'Discover Network'")
        logger.info("🛑 Press Ctrl+C to stop")
        
        # Keep the server running
        await server.wait_closed()
        
    except Exception as e:
        logger.error(f"Failed to start beacon-only mode: {e}")
        raise

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info("🛑 Shutdown signal received")
    
    # Stop UDP beacon discovery
    stop_udp_beacon_discovery()
    
    # TODO: Cleanup cluster node connections
    logger.info("✅ Beacon-only mode shutdown complete")
    sys.exit(0)

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Caelum Analytics - Beacon Only Mode")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port for cluster communication (default: 8080)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await start_beacon_only_mode(args.host, args.port)
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass