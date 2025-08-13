# Caelum Analytics - Claude Instructions

## Project Overview
Caelum Analytics is a real-time monitoring and analytics dashboard for the Caelum MCP Server ecosystem. It provides comprehensive monitoring for 20+ MCP servers with real-time WebSocket updates, data visualization, and system health tracking.

## Important Technical Notes

### Port Configuration
- **Web Application**: Runs on port 8090 (not 8080)
- **Cluster Communication**: Uses port 8080 for WebSocket inter-cluster communication
- **Docker Deployment**: Map host port 8080 to container port 8090 (`-p 8080:8090`)

### Development Environment
- Uses `uv` package manager for Python dependencies
- Python 3.11+ required
- Virtual environment managed by `uv` in `.venv` directory

### Running the Application

#### Docker (Recommended)
```bash
# Build fresh image
docker build -t caelum-analytics .

# Stop and remove existing container, then run new one
docker stop caelum-analytics 2>/dev/null && docker rm caelum-analytics 2>/dev/null; docker run -d -p 8090:8090 --name caelum-analytics caelum-analytics
```

#### Local Development
```bash
uv sync
uv run uvicorn caelum_analytics.web.app:app --reload --host 0.0.0.0 --port 8090
```

### Testing
```bash
uv run pytest
uv run pytest --cov
```

### Code Quality
```bash
uv run black src/ tests/
uv run isort src/ tests/
uv run mypy src/
```

## Architecture Components

### Core Modules
- `web/app.py`: FastAPI web application and dashboard
- `cluster_protocol.py`: WebSocket cluster communication protocol
- `collectors/`: Data collection modules for MCP servers
- `analytics/`: Data processing and analysis engines
- `visualizations/`: Chart and diagram generation
- `integrations/`: External service integrations

### Data Storage
- InfluxDB: Time-series metrics
- Redis: Caching and real-time data
- PostgreSQL: Configuration and historical data

## Common Issues & Solutions

### Port Conflicts
If port 8080 is in use, the cluster communication server will conflict. Ensure:
1. Application runs on port 8090
2. Cluster communication uses port 8080
3. Docker maps consistently: `-p 8090:8090`

### WebSocket Connection Issues
- Check CORS settings in `web/app.py`
- Ensure WebSocket upgrade headers are properly handled
- Verify firewall allows WebSocket connections

### MCP Server Integration
- Configuration is in `MCP_SERVERS_CONFIG_PATH` environment variable
- Each MCP server must expose metrics endpoints
- Authentication tokens required for secure connections

## Deployment Checklist
- [ ] Environment variables configured (.env file)
- [ ] Database connections verified (InfluxDB, Redis, PostgreSQL)
- [ ] MCP server configuration loaded
- [ ] Port mappings correct
- [ ] SSL certificates configured (production)
- [ ] Monitoring endpoints accessible
- [ ] WebSocket connections established

## Port Management System

### Active Port Enforcement
The system now includes **active port enforcement** that prevents conflicts BEFORE services start:

#### Port Guardian MCP Server (`/mcp-port-guardian/`)
- TypeScript-based MCP server for real-time port management
- Tools: `check_port`, `claim_port`, `release_port`, `validate_service`, `get_port_status`
- Build: `npm run build` in `mcp-port-guardian/`
- Actively checks port availability and reserves ports

#### Python Port Enforcer (`src/caelum_analytics/port_enforcer.py`)
- Enforces port rules before ANY service startup
- Integrated into CLI, web app, and Docker startup
- Usage: `require_port(8090, "analytics-dashboard")` - exits if conflict
- Alternative: `check_port_safe(8090, "service")` - returns boolean

#### Reserved Port Map
- **8080**: cluster-websocket (WebSocket inter-cluster communication)
- **8090**: analytics-dashboard (Analytics web UI)
- **5432**: postgresql, **6379**: redis, **8086**: influxdb
- **9090**: prometheus, **3000**: grafana, **8000**: api-gateway
- **8100-8199**: MCP servers (20 slots allocated)

#### Pre-startup Validation
```bash
# Validate port configuration before startup
python validate-ports.py

# CLI automatically checks ports
uv run python -m caelum_analytics.cli serve --port 8090

# Docker uses validated startup
CMD ["uv", "run", "python", "-m", "caelum_analytics.cli", "serve", "--host", "0.0.0.0", "--port", "8090"]
```

#### System Integration Points
1. **CLI startup**: Port checked in `cli.py:serve()` 
2. **Web app startup**: Port checked in `web/app.py:start_server()`
3. **Docker container**: Uses CLI which includes port checking
4. **Validation script**: `validate-ports.py` for pre-deployment checks

## Development Guidelines
1. **ALWAYS use port enforcement**: Call `require_port()` before binding to any port
2. Follow existing code patterns and conventions
3. Use type hints for all function parameters and returns
4. Write tests for new features
5. Update documentation for API changes
6. Use structured logging with appropriate log levels
7. Handle WebSocket disconnections gracefully
8. Implement proper error handling and recovery

## Security Considerations
- Never commit API keys or tokens
- Use environment variables for sensitive configuration
- Implement rate limiting on API endpoints
- Validate all WebSocket message payloads
- Use SSL/TLS in production
- Implement proper authentication for admin features

## Performance Optimization
- Use Redis caching for frequently accessed data
- Batch database writes to InfluxDB
- Implement WebSocket message throttling
- Use connection pooling for database connections
- Optimize chart rendering with lazy loading
- Implement pagination for large datasets

## Monitoring & Debugging
- Application logs: Check Docker logs or console output
- WebSocket debugging: Use browser developer tools
- Database queries: Monitor InfluxDB and PostgreSQL logs
- Performance metrics: Available at `/metrics` endpoint
- Health check: Available at `/health` endpoint