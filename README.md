# Caelum Analytics - Real-time Monitoring Dashboard

A comprehensive Python-based monitoring, analytics, and visualization system for the Caelum MCP Server ecosystem.

## 🎯 Project Overview

Caelum Analytics provides real-time monitoring, usage analytics, and graphical visualizations for all 20+ MCP servers in the Caelum ecosystem. Built with modern Python tools using `uv` for dependency management.

## 🏗️ Architecture

### Core Components

- **Web Dashboard**: FastAPI + WebSocket real-time interface
- **Data Collectors**: Automated metrics gathering from MCP servers  
- **Analytics Engine**: Data processing and pattern analysis
- **Visualization Layer**: Interactive charts, graphs, and diagrams
- **Integration APIs**: Connects to existing Caelum infrastructure

### Technology Stack

- **Package Management**: `uv` for fast, reliable dependencies
- **Web Framework**: FastAPI + Uvicorn for high-performance APIs
- **Real-time**: WebSockets + Socket.IO for live updates
- **Data Storage**: InfluxDB (time-series) + Redis (caching) + PostgreSQL
- **Visualization**: Plotly + Streamlit + Matplotlib + Seaborn
- **Monitoring**: Prometheus + psutil + docker integration

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- `uv` package manager
- Access to Caelum MCP servers
- InfluxDB, Redis, PostgreSQL (optional for full features)

### Installation

```bash
# Clone repository
git clone https://github.com/caelum-team/caelum-analytics.git
cd caelum-analytics

# Install with uv
uv sync

# Install development dependencies
uv sync --dev

# Set up environment
cp .env.example .env
# Edit .env with your configuration
```

### Running the Dashboard

#### Quick Start (Recommended)
```bash
# Start the analytics server (production-ready)
uv run uvicorn caelum_analytics.web.app:app --host 0.0.0.0 --port 8090

# Development mode with hot reload
uv run uvicorn caelum_analytics.web.app:app --reload --host 0.0.0.0 --port 8090
```

#### Starting & Stopping the Server

**Start the Server:**
```bash
# Method 1: Production mode
uv run uvicorn caelum_analytics.web.app:app --host 0.0.0.0 --port 8090

# Method 2: Development mode (with auto-reload)
uv run uvicorn caelum_analytics.web.app:app --reload --host 0.0.0.0 --port 8090

# Method 3: Background mode
nohup uv run uvicorn caelum_analytics.web.app:app --host 0.0.0.0 --port 8090 > logs/server.log 2>&1 &
```

**Stop the Server:**
```bash
# Find and kill the server process
ps aux | grep "uvicorn.*caelum_analytics" | grep -v grep
kill <PID>

# Or kill all uvicorn processes (be careful!)
pkill -f "uvicorn.*caelum_analytics"

# Or use Ctrl+C if running in foreground
```

**Check Server Status:**
```bash
# Check if server is running
curl http://localhost:8090/health

# Check what's using port 8090
lsof -i :8090

# View server logs (if running in background)
tail -f logs/server.log
```

#### Docker Deployment (Alternative)

**Option 1: Docker Compose (Recommended)**
```bash
# Development mode (with auto-reload and mounted source)
docker-compose up -d

# Production mode (optimized, stable)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f caelum-analytics

# Stop services
docker-compose down
```

**Option 2: Direct Docker**
```bash
# Build and run with Docker
docker build -t caelum-analytics .
docker stop caelum-analytics 2>/dev/null && docker rm caelum-analytics 2>/dev/null
docker run -d -p 8090:8090 --name caelum-analytics caelum-analytics
```

**Docker Configuration Files:**
- `docker-compose.yml` - Base configuration with supporting services
- `docker-compose.override.yml` - Development overrides (auto-applied)
- `docker-compose.prod.yml` - Production optimizations
- `.env.example` - Environment variable template

#### Additional Components (Optional)
```bash
# Start data collectors (separate terminal)
uv run caelum-collector

# Start other services if needed
# Note: Main dashboard includes basic monitoring by default
```

## 📊 Features

### Real-time MCP Server Monitoring

- ✅ Health status for all 20+ MCP servers with automatic port checking (8100-8119)
- ✅ Connection health percentage display (e.g., "15/20 servers online - 75%")
- ✅ Connection status, response times, error rates
- ✅ Resource usage (CPU, memory, disk, network)
- ✅ Tool usage statistics and patterns
- ✅ Alert notifications for failures/anomalies

### Analytics & Metrics

- 📈 Historical performance trends
- 📊 Usage pattern analysis  
- 🔍 Bottleneck identification
- 📋 Custom dashboard creation
- 💡 Predictive analytics and recommendations

### Graphical Visualizations

- 🌐 System architecture diagrams
- 📈 Real-time performance charts
- 🔄 Data flow visualizations
- 🎯 Interactive drill-down capabilities
- 📱 Mobile-responsive interface

### Integration Points

- **Data Sources**: analytics-metrics-server, cluster-communication-server
- **APIs**: api-gateway-server for routing and authentication
- **Diagramming**: AgenticWorkflow MCP server integration
- **Notifications**: cross-device-notification-server alerts
- **Intelligence**: business-intelligence-aggregation-server insights

## 🔧 Configuration

### Environment Variables

```bash
# Core Settings
CAELUM_ANALYTICS_HOST=0.0.0.0
CAELUM_ANALYTICS_PORT=8090  # Changed from 8080 to avoid conflicts
DEBUG=false
CLUSTER_COMMUNICATION_PORT=8081  # WebSocket cluster communication

# Caelum Integration
CAELUM_BASE_URL=http://localhost:3000
CAELUM_API_KEY=your-api-key
MCP_SERVERS_CONFIG_PATH=/path/to/mcp/config.json

# Database Connections
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-influxdb-token
INFLUXDB_ORG=caelum
INFLUXDB_BUCKET=metrics

REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://user:pass@localhost:5432/caelum_analytics

# External Services
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
```

## 📁 Project Structure

```
caelum-analytics/
├── pyproject.toml              # uv project configuration
├── src/caelum_analytics/       # Main package
│   ├── __init__.py
│   ├── cli.py                  # Command-line interface
│   ├── config.py               # Configuration management
│   ├── web/                    # Web dashboard
│   │   ├── app.py              # FastAPI application
│   │   ├── routes/             # API routes
│   │   ├── websocket.py        # Real-time updates
│   │   └── middleware.py       # Authentication, CORS, etc.
│   ├── collectors/             # Data collection
│   │   ├── mcp_collector.py    # MCP server metrics
│   │   ├── system_collector.py # System resource metrics
│   │   └── main.py             # Collector orchestration
│   ├── analytics/              # Data processing
│   │   ├── metrics_processor.py
│   │   ├── pattern_analyzer.py
│   │   └── predictive_models.py
│   ├── visualizations/         # Charts and graphs
│   │   ├── dashboards.py       # Dashboard generators
│   │   ├── charts.py           # Chart configurations
│   │   └── diagrams.py         # System diagrams
│   └── integrations/           # External integrations
│       ├── caelum_api.py       # Caelum MCP integration
│       ├── influxdb_client.py  # Time-series data
│       └── notification_client.py
├── static/                     # Frontend assets
│   ├── css/                    # Stylesheets
│   ├── js/                     # JavaScript
│   └── images/                 # Static images
├── templates/                  # HTML templates
├── tests/                      # Test suite
├── docs/                       # Documentation
└── scripts/                    # Utility scripts
```

## 🌐 Clusters vs Machines

### Understanding the Architecture

- **Machine**: An individual host/computer in the network. Each machine has its own resources (CPU, memory, etc.) and can run multiple MCP servers.
- **Cluster**: A logical group of machines working together. Machines in the same cluster share a cluster ID and can coordinate tasks.

### Current Implementation

- Each machine initially forms its own cluster (1:1 relationship)
- Machines can join existing clusters through network discovery
- Clusters enable distributed task execution and resource sharing
- The dashboard shows both cluster-level and machine-level metrics

## 🔗 MCP Server Integration

### Supported Caelum Servers

The dashboard monitors all 20+ MCP servers with automatic port checking:

| Server Name | Default Port | Purpose |
|------------|--------------|---------|
| `caelum-analytics-metrics` | 8100 | Primary metrics source |
| `caelum-api-gateway` | 8101 | API routing and auth |
| `caelum-business-intelligence` | 8102 | BI insights |
| `caelum-cluster-communication` | 8103 | Cluster status |
| `caelum-code-analysis` | 8104 | Code analysis |
| `caelum-cross-device-notifications` | 8105 | Notifications |
| `caelum-deployment-infrastructure` | 8106 | Deployment |
| `caelum-development-session` | 8107 | Dev sessions |
| `caelum-device-orchestration` | 8108 | Device management |
| `caelum-integration-testing` | 8109 | Testing |
| `caelum-intelligence-hub` | 8110 | AI hub |
| `caelum-knowledge-management` | 8111 | Knowledge base |
| `caelum-ollama-pool` | 8112 | LLM integration |
| `caelum-opportunity-discovery` | 8113 | Opportunities |
| `caelum-performance-optimization` | 8114 | Performance |
| `caelum-project-intelligence` | 8115 | Project analysis |
| `caelum-security-compliance` | 8116 | Security |
| `caelum-user-profile` | 8117 | User management |
| `caelum-vector-database` | 8118 | Vector DB |
| `caelum-workflow-automation` | 8119 | Workflow tracking |

### Data Collection Methods

1. **Direct API Calls**: REST endpoints on MCP servers
2. **WebSocket Subscriptions**: Real-time event streams  
3. **InfluxDB Queries**: Historical time-series data
4. **Prometheus Scraping**: Standard metrics collection
5. **Log File Parsing**: Error detection and analysis

## 🚀 Deployment

### Development

```bash
# Start all services
uv run scripts/start-dev.sh

# Run tests
uv run pytest

# Format code  
uv run black src/ tests/
uv run isort src/ tests/

# Type checking
uv run mypy src/
```

### Production

```bash
# Build distribution
uv build

# Deploy with Docker
# Build fresh image
docker build -t caelum-analytics .

# Stop and remove existing container, then run new one
docker stop caelum-analytics 2>/dev/null && docker rm caelum-analytics 2>/dev/null; docker run -d -p 8090:8090 --name caelum-analytics caelum-analytics

# Note: The application runs on port 8090 to avoid conflict with
# the cluster communication server on port 8080.

# Or with systemd service
sudo cp scripts/caelum-analytics.service /etc/systemd/system/
sudo systemctl enable caelum-analytics
sudo systemctl start caelum-analytics
```

## 📖 API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8090/docs`
- ReDoc: `http://localhost:8090/redoc`

### Key Endpoints

- `GET /api/v1/servers` - List all MCP server statuses
- `GET /api/v1/metrics/{server_id}` - Get server metrics
- `WebSocket /ws/live` - Real-time updates stream
- `GET /api/v1/analytics/dashboard` - Dashboard data
- `POST /api/v1/alerts/configure` - Set up alerts

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- **[Caelum MCP Servers](https://github.com/caelum-team/caelum)** - Core MCP server ecosystem
- **[AgenticWorkflow](https://github.com/caelum-team/agentic-workflow)** - Workflow diagramming
- **[Project Intelligence](https://github.com/caelum-team/project-intelligence)** - Code analysis

---

**Plan ↔ Project ↔ Path Association:**
- **Plan**: Caelum Analytics Monitoring Dashboard  
- **Project**: caelum-analytics
- **Path**: `/home/rford/dev/caelum-analytics`