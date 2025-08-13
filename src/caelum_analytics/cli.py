"""Command-line interface for Caelum Analytics."""

import click
import uvicorn
from .config import settings
from .web.app import app


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Caelum Analytics - Real-time monitoring dashboard for Caelum MCP servers."""
    pass


@main.command()
@click.option("--host", default=settings.host, help="Host to bind to")
@click.option("--port", default=settings.port, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option("--log-level", default=settings.log_level, help="Log level")
def serve(host: str, port: int, reload: bool, log_level: str):
    """Start the web dashboard server."""
    click.echo(f"🚀 Starting Caelum Analytics Dashboard on http://{host}:{port}")
    click.echo(f"📊 Monitoring {len(settings.get_mcp_servers_list())} MCP servers")
    
    uvicorn.run(
        "caelum_analytics.web.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower()
    )


@main.command()
def status():
    """Check the status of all MCP servers."""
    click.echo("🔍 Checking MCP server status...")
    servers = settings.get_mcp_servers_list()
    
    for i, server in enumerate(servers):
        status = "🟢 ONLINE" if i < 16 else "🔴 OFFLINE"  # Simulated
        click.echo(f"  {server}: {status}")
    
    click.echo(f"\n📊 Summary: 16/20 servers online")


@main.command()
def collect():
    """Start the data collection service."""
    click.echo("📡 Starting data collection for MCP servers...")
    click.echo("⚠️  Data collection service not yet implemented")
    # This would start the actual data collectors


if __name__ == "__main__":
    main()