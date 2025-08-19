#!/usr/bin/env python3
"""
Workflow Server Runner

Runs individual workflow servers for testing and development.
Usage: python run_workflow_server.py <workflow_name>
"""

import sys
import asyncio
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from caelum_analytics.workflow_servers import (
    DevelopmentWorkflowServer,
    BusinessWorkflowServer,
    InfrastructureWorkflowServer,
    CommunicationWorkflowServer,
    SecurityWorkflowServer
)

WORKFLOW_SERVERS = {
    "development": DevelopmentWorkflowServer,
    "business": BusinessWorkflowServer,
    "infrastructure": InfrastructureWorkflowServer,
    "communication": CommunicationWorkflowServer,
    "security": SecurityWorkflowServer
}

async def main():
    if len(sys.argv) != 2 or sys.argv[1] not in WORKFLOW_SERVERS:
        print(f"Usage: {sys.argv[0]} <workflow_name>")
        print(f"Available workflows: {', '.join(WORKFLOW_SERVERS.keys())}")
        sys.exit(1)
    
    workflow_name = sys.argv[1]
    server_class = WORKFLOW_SERVERS[workflow_name]
    
    print(f"Starting {workflow_name} workflow server...")
    
    # Create and run the server
    server = server_class()
    
    from mcp.server.stdio import stdio_server
    from mcp.server.models import InitializationOptions
    
    async with stdio_server() as (read_stream, write_stream):
        await server.app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=f"caelum-{workflow_name}-workflow",
                server_version="1.0.0",
                capabilities=server.app.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())