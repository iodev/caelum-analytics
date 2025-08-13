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

```bash
# Start web dashboard
uv run caelum-dashboard

# Start data collectors (separate terminal)
uv run caelum-collector

# Development mode with hot reload
uv run uvicorn caelum_analytics.web.app:app --reload --host 0.0.0.0 --port 8080
```

## 📊 Features

### Real-time MCP Server Monitoring

- ✅ Health status for all 20+ MCP servers
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
CAELUM_ANALYTICS_PORT=8080
DEBUG=false

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

## 🔗 MCP Server Integration

### Supported Caelum Servers

The dashboard monitors all 20+ MCP servers:

- `analytics-metrics-server` - Primary metrics source
- `api-gateway-server` - API routing and auth
- `business-intelligence-aggregation-server` - BI insights
- `cluster-communication-server` - Cluster status
- `device-orchestration-server` - Device management
- `ollama-pool-integration-server` - LLM integration
- `project-intelligence-server` - Code analysis
- `user-profile-server` - User management
- `workflow-orchestration-server` - Workflow tracking
- And 11+ additional specialized servers...

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
docker build -t caelum-analytics .
docker run -d -p 8080:8090 --name caelum-analytics caelum-analytics

# Note: The application runs on port 8090 internally to avoid conflict with
# the cluster communication server on port 8080. The Docker command maps
# host port 8080 to container port 8090 for convenience.

# Or with systemd service
sudo cp scripts/caelum-analytics.service /etc/systemd/system/
sudo systemctl enable caelum-analytics
sudo systemctl start caelum-analytics
```

## 📖 API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

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