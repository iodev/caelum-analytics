"""Command-line interface for Caelum Analytics."""

import click
import uvicorn
from .config import settings
from .web.app import app
from .port_enforcer import require_port


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
    # CRITICAL: Check port availability BEFORE starting
    require_port(port, "analytics-dashboard")

    click.echo(f"🚀 Starting Caelum Analytics Dashboard on http://{host}:{port}")
    click.echo(f"📊 Monitoring {len(settings.get_mcp_servers_list())} MCP servers")

    uvicorn.run(
        "caelum_analytics.web.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower(),
    )


@main.command()
def status():
    """Check the status of all MCP servers."""
    click.echo("🔍 Checking MCP server status...")
    servers = settings.get_mcp_servers_list()

    online_count = 0
    for server in servers:
        # Check if server is actually running by attempting to connect to its port
        from .port_registry import port_registry

        allocation = port_registry.get_service_location(server)
        is_online = False

        if allocation:
            import socket

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex(("localhost", allocation.port))
                    is_online = result == 0
            except Exception:
                is_online = False

        status = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
        click.echo(f"  {server}: {status}")

        if is_online:
            online_count += 1

    click.echo(f"\n📊 Summary: {online_count}/{len(servers)} servers online")


@main.command()
def collect():
    """Start the data collection service."""
    click.echo("📡 Starting data collection for MCP servers...")
    click.echo("⚠️  Data collection service not yet implemented")
    # This would start the actual data collectors


@main.command()
def ports():
    """Show the Caelum ecosystem port allocation map."""
    click.echo("🌐 Caelum Ecosystem Port Registry")
    click.echo("=" * 50)
    click.echo()

    # Validate current port
    try:
        settings.validate_port_allocation()
        click.echo(f"✅ Analytics dashboard port {settings.port} is properly allocated")
    except ValueError as e:
        click.echo(f"⚠️  {e}")

    click.echo()
    click.echo(settings.get_port_registry_report())


if __name__ == "__main__":
    main()
