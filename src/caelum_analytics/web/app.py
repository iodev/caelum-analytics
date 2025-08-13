"""FastAPI web application for Caelum Analytics dashboard."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List
import json
import asyncio
import uuid
from datetime import datetime

from ..config import settings
from ..machine_registry import machine_registry
from ..port_registry import port_registry, ServiceType
from ..cluster_protocol import cluster_node, ClusterMessage, MessageType

# Create FastAPI application
app = FastAPI(
    title="Caelum Analytics",
    description="Real-time monitoring and analytics for Caelum MCP Server System",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
templates = Jinja2Templates(directory=settings.templates_dir)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove failed connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Cluster communication server
cluster_server = None


@app.on_event("startup")
async def startup_event():
    """Start the cluster communication server on app startup."""
    global cluster_server
    try:
        # Start cluster communication server on port 8080
        cluster_server = await cluster_node.start_server(host="0.0.0.0")
        print(f"🌐 Cluster communication server started on port 8080")
    except Exception as e:
        print(f"⚠️ Failed to start cluster server: {e}")


@app.on_event("shutdown") 
async def shutdown_event():
    """Clean shutdown of cluster communication."""
    global cluster_server
    if cluster_server:
        cluster_server.close()
        await cluster_server.wait_closed()
        print("🌐 Cluster communication server stopped")


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page with distributed machine monitoring."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Caelum Distributed Analytics Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f8fafc; }
            .header { background: linear-gradient(135deg, #2c3e50, #3498db); color: white; padding: 30px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .header h1 { margin: 0 0 10px 0; font-size: 2.5em; font-weight: 700; }
            .header p { margin: 0; opacity: 0.9; font-size: 1.1em; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px; margin-bottom: 30px; }
            .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border: 1px solid #e1e8ed; }
            .card h3 { margin-top: 0; color: #2c3e50; font-size: 1.3em; display: flex; align-items: center; gap: 10px; }
            .status { display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
            .status.online { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .status.offline { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .status.busy { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
            .metric { display: flex; justify-content: space-between; margin: 12px 0; padding: 8px 0; border-bottom: 1px solid #f1f3f4; }
            .metric:last-child { border-bottom: none; }
            .metric-label { color: #5f6368; font-weight: 500; }
            .metric-value { font-weight: 600; color: #202124; }
            .machine-card { margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #3498db; }
            .machine-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
            .machine-name { font-weight: 600; color: #2c3e50; }
            .resource-bar { width: 100%; height: 8px; background: #e9ecef; border-radius: 4px; margin: 5px 0; overflow: hidden; }
            .resource-fill { height: 100%; background: linear-gradient(90deg, #28a745, #ffc107, #dc3545); transition: width 0.3s ease; }
            .tabs { display: flex; margin: 20px 0; border-bottom: 2px solid #e1e8ed; }
            .tab { padding: 12px 24px; background: none; border: none; cursor: pointer; font-weight: 500; color: #5f6368; border-bottom: 3px solid transparent; transition: all 0.2s; }
            .tab.active { color: #3498db; border-bottom-color: #3498db; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            #realtime-data { background: white; border-radius: 12px; padding: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            #live-log { background: #1a1a1a; color: #00ff41; padding: 15px; height: 250px; overflow-y: scroll; font-family: 'Courier New', monospace; border-radius: 8px; font-size: 13px; line-height: 1.4; }
            .btn { padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; margin: 5px; transition: background 0.2s; }
            .btn:hover { background: #2980b9; }
            .btn-success { background: #28a745; }
            .btn-success:hover { background: #218838; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌐 Caelum Distributed Analytics</h1>
            <p>Real-time monitoring for distributed MCP server ecosystem • Phase 1 Implementation</p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">📊 Overview</button>
            <button class="tab" onclick="showTab('machines')">🖥️ Machines</button>
            <button class="tab" onclick="showTab('servers')">🔧 MCP Servers</button>
            <button class="tab" onclick="showTab('cluster')">🌐 Cluster</button>
            <button class="tab" onclick="showTab('network')">📡 Network</button>
        </div>

        <div id="overview" class="tab-content active">
            <div class="grid">
                <div class="card">
                    <h3>📊 System Overview</h3>
                    <div class="metric">
                        <span class="metric-label">Total Machines</span>
                        <span class="metric-value" id="total-machines">Loading...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Online Machines</span>
                        <span class="metric-value" id="online-machines">0</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">MCP Servers</span>
                        <span class="metric-value" id="server-count">20</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Active Services</span>
                        <span class="metric-value" id="active-services">0</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🏗️ Distributed Resources</h3>
                    <div class="metric">
                        <span class="metric-label">Total CPU Cores</span>
                        <span class="metric-value" id="total-cpu">--</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total Memory</span>
                        <span class="metric-value" id="total-memory">-- GB</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Available Memory</span>
                        <span class="metric-value" id="available-memory">-- GB</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">GPU Count</span>
                        <span class="metric-value" id="gpu-count">--</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📈 Performance Status</h3>
                    <div class="metric">
                        <span class="metric-label">Cluster Health</span>
                        <span class="metric-value status online" id="cluster-health">ONLINE</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Avg Response Time</span>
                        <span class="metric-value" id="avg-response">-- ms</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Network Latency</span>
                        <span class="metric-value" id="network-latency">-- ms</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Task Queue</span>
                        <span class="metric-value" id="task-queue">0 pending</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>⚡ Quick Actions</h3>
                    <a href="/api/docs" class="btn">📖 API Docs</a>
                    <a href="/api/v1/machines" class="btn">🖥️ Machines API</a>
                    <button class="btn btn-success" onclick="discoverMachines()">🔍 Discover Machines</button>
                    <button class="btn" onclick="connectWebSocket()">🔴 Connect Live</button>
                </div>
            </div>
        </div>

        <div id="machines" class="tab-content">
            <div class="card">
                <h3>🖥️ Network Machines</h3>
                <div id="machines-list">Loading machine topology...</div>
            </div>
        </div>

        <div id="servers" class="tab-content">
            <div class="card">
                <h3>🔧 MCP Server Status</h3>
                <div id="server-list">Loading MCP servers...</div>
            </div>
        </div>

        <div id="cluster" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h3>🌐 Cluster Communication</h3>
                    <div class="metric">
                        <span class="metric-label">Cluster Server</span>
                        <span class="metric-value status" id="cluster-server-status">Loading...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Connected Machines</span>
                        <span class="metric-value" id="connected-machines">0</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Discovered Machines</span>
                        <span class="metric-value" id="discovered-machines">0</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Pending Tasks</span>
                        <span class="metric-value" id="pending-tasks">0</span>
                    </div>
                    <button class="btn btn-success" onclick="discoverClusterMachines()">🔍 Discover Network</button>
                    <button class="btn" onclick="testClusterCommunication()">📡 Test Communication</button>
                </div>
                
                <div class="card">
                    <h3>🔗 Machine Connections</h3>
                    <div id="cluster-connections">No connections established</div>
                    <div style="margin-top: 15px;">
                        <input type="text" id="connect-host" placeholder="Machine IP address" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin-right: 10px;">
                        <button class="btn" onclick="connectToMachine()">Connect</button>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📋 Distributed Tasks</h3>
                    <div id="distributed-tasks">No active tasks</div>
                    <div style="margin-top: 15px;">
                        <select id="task-type" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin-right: 10px;">
                            <option value="code_analysis">Code Analysis</option>
                            <option value="integration_testing">Integration Testing</option>
                            <option value="ai_inference">AI Inference</option>
                            <option value="data_processing">Data Processing</option>
                        </select>
                        <button class="btn btn-success" onclick="distributeTask()">Distribute Task</button>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🏗️ Resource Reservations</h3>
                    <div id="resource-reservations">No active reservations</div>
                </div>
            </div>
        </div>

        <div id="network" class="tab-content">
            <div class="card">
                <h3>📡 Network Topology</h3>
                <p><strong>Phase 1 Week 2:</strong> Cross-machine communication protocol implemented!</p>
                <div id="network-topology">
                    <div class="metric">
                        <span class="metric-label">🔧 WebSocket Cluster Communication</span>
                        <span class="metric-value">Port 8080 • Ready</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">🗄️ Redis Work Queue</span>
                        <span class="metric-value">Port 6379 • Coordination</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">📊 Analytics Dashboard</span>
                        <span class="metric-value">Port 8090 • Monitoring</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">🔍 Service Discovery</span>
                        <span class="metric-value">Auto-detection • Active</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="realtime-data">
            <h3>🔴 Live System Updates</h3>
            <div id="live-log"></div>
        </div>

        <script>
            let ws = null;
            let machineData = {};
            
            function showTab(tabName) {
                // Hide all tabs
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.remove('active');
                });
                document.querySelectorAll('.tab').forEach(btn => {
                    btn.classList.remove('active');
                });
                
                // Show selected tab
                document.getElementById(tabName).classList.add('active');
                event.target.classList.add('active');
                
                // Load tab-specific data
                if (tabName === 'machines') {
                    loadMachines();
                } else if (tabName === 'servers') {
                    loadServers();
                } else if (tabName === 'cluster') {
                    loadClusterStatus();
                }
            }
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const host = window.location.host;
                ws = new WebSocket(`${protocol}//${host}/ws/live`);
                
                ws.onopen = function(event) {
                    addLog("✅ Connected to distributed analytics");
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addLog(`📡 ${data.type}: ${JSON.stringify(data.data).substring(0, 100)}...`);
                    updateDashboard(data);
                };
                
                ws.onclose = function(event) {
                    addLog("❌ WebSocket connection closed");
                };
                
                ws.onerror = function(error) {
                    addLog("⚠️ WebSocket error occurred");
                };
            }
            
            function addLog(message) {
                const log = document.getElementById('live-log');
                const time = new Date().toLocaleTimeString();
                log.innerHTML += `[${time}] ${message}\\n`;
                log.scrollTop = log.scrollHeight;
            }
            
            async function loadMachines() {
                try {
                    const response = await fetch('/api/v1/machines');
                    const data = await response.json();
                    machineData = data;
                    updateMachineDisplay(data);
                    updateOverviewMetrics(data);
                } catch (error) {
                    addLog(`❌ Failed to load machines: ${error.message}`);
                }
            }
            
            async function loadServers() {
                try {
                    const response = await fetch('/api/v1/servers');
                    const data = await response.json();
                    updateServerDisplay(data);
                } catch (error) {
                    addLog(`❌ Failed to load servers: ${error.message}`);
                }
            }
            
            function updateMachineDisplay(data) {
                const container = document.getElementById('machines-list');
                if (data.machines && data.machines.length > 0) {
                    container.innerHTML = data.machines.map(machine => `
                        <div class="machine-card">
                            <div class="machine-header">
                                <div class="machine-name">${machine.hostname} (${machine.primary_ip})</div>
                                <span class="status ${machine.status}">${machine.status.toUpperCase()}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">CPU Usage</span>
                                <span class="metric-value">${machine.resources.cpu_usage_percent.toFixed(1)}%</span>
                            </div>
                            <div class="resource-bar">
                                <div class="resource-fill" style="width: ${machine.resources.cpu_usage_percent}%"></div>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Memory</span>
                                <span class="metric-value">${machine.resources.memory_available_gb.toFixed(1)}GB / ${machine.resources.memory_total_gb.toFixed(1)}GB</span>
                            </div>
                            <div class="resource-bar">
                                <div class="resource-fill" style="width: ${machine.resources.memory_usage_percent}%"></div>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Services</span>
                                <span class="metric-value">${machine.running_services.length} running</span>
                            </div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<p>No machines discovered. Local machine registration in progress...</p>';
                }
            }
            
            function updateServerDisplay(data) {
                const container = document.getElementById('server-list');
                if (data.servers) {
                    container.innerHTML = data.servers.map(server => `
                        <div class="metric">
                            <span class="metric-label">${server.name}</span>
                            <span class="status ${server.status}">${server.status.toUpperCase()}</span>
                        </div>
                    `).join('');
                }
            }
            
            function updateOverviewMetrics(data) {
                if (data.total_resources) {
                    document.getElementById('total-machines').textContent = data.total_machines;
                    document.getElementById('online-machines').textContent = data.online_machines;
                    document.getElementById('total-cpu').textContent = data.total_resources.cpu_cores;
                    document.getElementById('total-memory').textContent = data.total_resources.memory_total_gb.toFixed(1) + ' GB';
                    document.getElementById('available-memory').textContent = data.total_resources.memory_available_gb.toFixed(1) + ' GB';
                    document.getElementById('gpu-count').textContent = data.total_resources.gpu_count || 0;
                    
                    // Update active services count
                    const totalServices = data.machines.reduce((sum, machine) => sum + machine.running_services.length, 0);
                    document.getElementById('active-services').textContent = totalServices;
                }
            }
            
            function updateDashboard(data) {
                if (data.type === 'machine_update') {
                    updateOverviewMetrics(data.data);
                    if (document.getElementById('machines').classList.contains('active')) {
                        updateMachineDisplay(data.data);
                    }
                }
            }
            
            async function loadClusterStatus() {
                try {
                    const response = await fetch('/api/v1/cluster/status');
                    const data = await response.json();
                    updateClusterDisplay(data);
                    
                    // Load tasks
                    const tasksResponse = await fetch('/api/v1/cluster/tasks');
                    const tasksData = await tasksResponse.json();
                    updateTasksDisplay(tasksData);
                } catch (error) {
                    addLog(`❌ Failed to load cluster status: ${error.message}`);
                }
            }
            
            function updateClusterDisplay(data) {
                document.getElementById('cluster-server-status').textContent = 
                    data.cluster_server_running ? 'ONLINE' : 'OFFLINE';
                document.getElementById('cluster-server-status').className = 
                    'metric-value status ' + (data.cluster_server_running ? 'online' : 'offline');
                
                document.getElementById('connected-machines').textContent = data.connected_machines.length;
                document.getElementById('discovered-machines').textContent = data.discovered_machines.length;
                document.getElementById('pending-tasks').textContent = data.pending_tasks;
                
                // Update connections display
                const connectionsDiv = document.getElementById('cluster-connections');
                if (data.connected_machines.length > 0) {
                    connectionsDiv.innerHTML = data.connected_machines.map(machine => 
                        `<div class="metric"><span class="metric-label">${machine}</span><span class="status online">CONNECTED</span></div>`
                    ).join('');
                } else {
                    connectionsDiv.innerHTML = 'No connections established';
                }
            }
            
            function updateTasksDisplay(data) {
                const tasksDiv = document.getElementById('distributed-tasks');
                const reservationsDiv = document.getElementById('resource-reservations');
                
                if (data.pending_tasks.length > 0) {
                    tasksDiv.innerHTML = data.pending_tasks.map(task => 
                        `<div class="metric">
                            <span class="metric-label">${task.task_type}</span>
                            <span class="metric-value">Priority ${task.priority}</span>
                        </div>`
                    ).join('');
                } else {
                    tasksDiv.innerHTML = 'No active tasks';
                }
                
                if (data.resource_reservations.length > 0) {
                    reservationsDiv.innerHTML = data.resource_reservations.map(res => 
                        `<div class="metric">
                            <span class="metric-label">CPU: ${res.cpu_cores || 0}, RAM: ${res.memory_gb || 0}GB</span>
                            <span class="metric-value">${res.machine_id}</span>
                        </div>`
                    ).join('');
                } else {
                    reservationsDiv.innerHTML = 'No active reservations';
                }
            }
            
            async function discoverClusterMachines() {
                try {
                    addLog("🔍 Starting cluster network discovery...");
                    const response = await fetch('/api/v1/cluster/discover', { method: 'POST' });
                    const data = await response.json();
                    addLog(`📡 Discovery broadcast sent to ${data.connected_machines} machines`);
                    
                    // Refresh cluster status after discovery
                    setTimeout(loadClusterStatus, 2000);
                } catch (error) {
                    addLog(`❌ Failed to trigger discovery: ${error.message}`);
                }
            }
            
            async function connectToMachine() {
                const host = document.getElementById('connect-host').value;
                if (!host) {
                    addLog("⚠️ Please enter a machine IP address");
                    return;
                }
                
                try {
                    addLog(`🔗 Connecting to ${host}:8080...`);
                    const response = await fetch('/api/v1/cluster/connect', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ host: host, port: 8080 })
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        addLog(`✅ Connected to ${host}`);
                        document.getElementById('connect-host').value = '';
                        loadClusterStatus();
                    } else {
                        addLog(`❌ Failed to connect to ${host}`);
                    }
                } catch (error) {
                    addLog(`❌ Connection error: ${error.message}`);
                }
            }
            
            async function testClusterCommunication() {
                try {
                    addLog("📡 Testing cluster communication...");
                    const response = await fetch('/api/v1/cluster/broadcast', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            message_type: 'PING',
                            payload: { test_message: 'Hello from Analytics Dashboard!' }
                        })
                    });
                    const data = await response.json();
                    addLog(`📡 Broadcast sent to ${data.recipients} machines`);
                } catch (error) {
                    addLog(`❌ Communication test failed: ${error.message}`);
                }
            }
            
            async function distributeTask() {
                const taskType = document.getElementById('task-type').value;
                
                try {
                    addLog(`📋 Distributing ${taskType} task...`);
                    const response = await fetch('/api/v1/cluster/task/distribute', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            task_type: taskType,
                            service_name: 'caelum-code-analysis',
                            payload: { 
                                test_task: true,
                                description: `Distributed ${taskType} task from Analytics Dashboard`
                            },
                            priority: 7,
                            estimated_duration: 120
                        })
                    });
                    const data = await response.json();
                    addLog(`✅ Task distributed to ${data.recipients} machines (ID: ${data.task_id.substring(0, 8)}...)`);
                    
                    // Refresh cluster status
                    setTimeout(loadClusterStatus, 1000);
                } catch (error) {
                    addLog(`❌ Task distribution failed: ${error.message}`);
                }
            }
            
            function discoverMachines() {
                addLog("🔍 Starting machine discovery...");
                loadMachines();
                addLog("🖥️ Local machine registered");
            }
            
            // Auto-load on page load
            window.onload = function() {
                connectWebSocket();
                loadMachines();
                
                // Auto-refresh every 30 seconds
                setInterval(loadMachines, 30000);
                setInterval(loadClusterStatus, 30000);
            };
        </script>
    </body>
    </html>
    """


@app.get("/api/v1/servers")
async def get_servers():
    """Get list of all MCP servers and their status."""
    servers = settings.get_mcp_servers_list()
    return {
        "servers": [
            {
                "name": server,
                "status": "online" if i < 16 else "offline",  # Simulated data
                "response_time": f"{(i * 10) + 20}ms",
                "last_check": "2025-08-13T21:30:00Z"
            }
            for i, server in enumerate(servers)
        ],
        "summary": {
            "total": len(servers),
            "online": 16,
            "offline": 4
        }
    }


@app.get("/api/v1/machines")
async def get_machines():
    """Get list of all machines in the distributed network."""
    # Register local machine if not already done
    if machine_registry.local_machine_id is None:
        local_machine = machine_registry.get_local_machine_info()
        machine_registry.register_machine(local_machine)
    
    # Sync port registry with machine registry
    port_registry.update_from_machine_registry(machine_registry)
    
    return machine_registry.get_machine_summary()


@app.get("/api/v1/machines/{machine_id}")
async def get_machine_details(machine_id: str):
    """Get detailed information about a specific machine."""
    if machine_id in machine_registry.machines:
        return machine_registry.machines[machine_id].to_dict()
    else:
        return {"error": "Machine not found"}


@app.post("/api/v1/machines/register")
async def register_machine(machine_data: dict):
    """Register a new machine in the network."""
    try:
        machine = machine_registry.MachineNode.from_dict(machine_data)
        machine_registry.register_machine(machine)
        return {"status": "success", "machine_id": machine.machine_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/v1/machines/{machine_id}/heartbeat")
async def machine_heartbeat(machine_id: str):
    """Update heartbeat for a machine."""
    machine_registry.update_machine_heartbeat(machine_id)
    return {"status": "success", "timestamp": datetime.now().isoformat()}


@app.get("/api/v1/services/discovery")
async def service_discovery():
    """Get service discovery information for the distributed network."""
    # Sync registries
    port_registry.update_from_machine_registry(machine_registry)
    
    return {
        "distributed_services": port_registry.get_distributed_service_map(),
        "service_endpoints": {
            "databases": port_registry.find_service_endpoints(ServiceType.DATABASE),
            "apis": port_registry.find_service_endpoints(ServiceType.API),
            "websockets": port_registry.find_service_endpoints(ServiceType.WEBSOCKET),
            "mcp_servers": port_registry.find_service_endpoints(ServiceType.MCP_SERVER),
            "monitoring": port_registry.find_service_endpoints(ServiceType.MONITORING)
        }
    }


@app.get("/api/v1/services/{service_name}/location")
async def get_service_location(service_name: str):
    """Find where a specific service is running."""
    location = port_registry.get_service_location(service_name)
    if location:
        return {
            "service_name": service_name,
            "port": location.port,
            "machine_id": location.machine_id,
            "ip_address": location.ip_address,
            "endpoint": f"{location.ip_address}:{location.port}" if location.ip_address else None,
            "status": location.status
        }
    else:
        return {"error": "Service not found"}


@app.get("/api/v1/ports/distributed")
async def get_distributed_port_map():
    """Get the enhanced port allocation map with machine assignments."""
    # Sync registries first
    port_registry.update_from_machine_registry(machine_registry)
    
    return {
        "port_allocations": {
            str(port): {
                "service_name": alloc.service_name,
                "service_type": alloc.service_type.value,
                "project": alloc.project,
                "purpose": alloc.purpose,
                "machine_id": alloc.machine_id,
                "ip_address": alloc.ip_address,
                "endpoint": f"{alloc.ip_address}:{alloc.port}" if alloc.ip_address else None,
                "status": alloc.status
            }
            for port, alloc in port_registry.get_all_allocations().items()
        },
        "machine_services": port_registry.get_distributed_service_map(),
        "summary": {
            "total_ports": len(port_registry.get_all_allocations()),
            "assigned_to_machines": len([a for a in port_registry.get_all_allocations().values() if a.machine_id]),
            "available_for_assignment": len([a for a in port_registry.get_all_allocations().values() if not a.machine_id])
        }
    }


@app.get("/api/v1/cluster/status")
async def get_cluster_status():
    """Get cluster communication status and connected machines."""
    return {
        "cluster_server_running": cluster_server is not None,
        "local_machine_id": cluster_node.machine_id,
        "connected_machines": list(cluster_node.connections.keys()),
        "discovered_machines": list(cluster_node.discovered_machines.keys()),
        "pending_tasks": len(cluster_node.pending_tasks),
        "resource_reservations": len(cluster_node.resource_reservations),
        "communication_port": 8080,
        "message_handlers": len(cluster_node.message_handlers)
    }


@app.post("/api/v1/cluster/connect")
async def connect_to_machine(request: dict):
    """Connect to another machine in the cluster."""
    host = request.get('host')
    port = request.get('port', 8080)
    
    if not host:
        return {"error": "Host is required"}
    
    success = await cluster_node.connect_to_machine(host, port)
    return {
        "success": success,
        "message": f"{'Connected to' if success else 'Failed to connect to'} {host}:{port}"
    }


@app.post("/api/v1/cluster/discover")
async def discover_network_machines():
    """Trigger network discovery for Caelum machines."""
    # Send discovery broadcast
    message = ClusterMessage(
        message_id=str(uuid.uuid4()),
        message_type=MessageType.MACHINE_DISCOVER,
        source_machine=cluster_node.machine_id or "unknown",
        payload={"discovery_request": True}
    )
    
    await cluster_node.broadcast_message(message)
    
    return {
        "status": "discovery_initiated",
        "message": "Network discovery broadcast sent",
        "connected_machines": len(cluster_node.connections),
        "discovered_machines": len(cluster_node.discovered_machines)
    }


@app.post("/api/v1/cluster/broadcast")
async def broadcast_message(request: dict):
    """Broadcast a custom message to all cluster machines."""
    message_type = request.get('message_type', 'STATUS_BROADCAST')
    payload = request.get('payload', {})
    
    try:
        msg_type = MessageType(message_type)
    except ValueError:
        return {"error": f"Invalid message type: {message_type}"}
    
    message = ClusterMessage(
        message_id=str(uuid.uuid4()),
        message_type=msg_type,
        source_machine=cluster_node.machine_id or "unknown",
        payload=payload
    )
    
    await cluster_node.broadcast_message(message)
    
    return {
        "status": "message_broadcast",
        "message_id": message.message_id,
        "recipients": len(cluster_node.connections)
    }


@app.get("/api/v1/cluster/tasks")
async def get_distributed_tasks():
    """Get current distributed tasks and their status."""
    return {
        "pending_tasks": [
            {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "service_name": task.service_name,
                "source_machine": task.source_machine,
                "assigned_machines": task.assigned_machines,
                "priority": task.priority,
                "estimated_duration": task.estimated_duration,
                "created_at": task.created_at.isoformat()
            }
            for task in cluster_node.pending_tasks.values()
        ],
        "resource_reservations": [
            {
                "reservation_id": res.reservation_id,
                "machine_id": res.machine_id,
                "cpu_cores": res.cpu_cores,
                "memory_gb": res.memory_gb,
                "gpu_count": res.gpu_count,
                "duration_seconds": res.duration_seconds,
                "task_id": res.task_id,
                "reserved_at": res.reserved_at.isoformat()
            }
            for res in cluster_node.resource_reservations.values()
        ]
    }


@app.post("/api/v1/cluster/task/distribute")
async def distribute_task(request: dict):
    """Distribute a task across the cluster."""
    from ..cluster_protocol import TaskDistribution
    
    task_data = {
        'task_id': str(uuid.uuid4()),
        'task_type': request.get('task_type', 'unknown'),
        'service_name': request.get('service_name', 'caelum-code-analysis'),
        'source_machine': cluster_node.machine_id or "unknown",
        'assigned_machines': request.get('assigned_machines', []),
        'payload': request.get('payload', {}),
        'priority': request.get('priority', 5),
        'estimated_duration': request.get('estimated_duration', 60)
    }
    
    task = TaskDistribution(**task_data)
    cluster_node.pending_tasks[task.task_id] = task
    
    # Broadcast task distribution message
    message = ClusterMessage(
        message_id=str(uuid.uuid4()),
        message_type=MessageType.TASK_DISTRIBUTE,
        source_machine=cluster_node.machine_id or "unknown",
        payload={'task': task_data}
    )
    
    await cluster_node.broadcast_message(message)
    
    return {
        "status": "task_distributed",
        "task_id": task.task_id,
        "recipients": len(cluster_node.connections)
    }


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        # Send initial data
        await websocket.send_text(json.dumps({
            "type": "connection",
            "data": {"message": "Connected to Caelum Analytics"}
        }))
        
        # Keep connection alive and send periodic updates
        while True:
            # This would be replaced with real data collection
            await asyncio.sleep(5)
            await websocket.send_text(json.dumps({
                "type": "heartbeat",
                "data": {"timestamp": "2025-08-13T21:30:00Z"}
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def start_server():
    """Start the development server."""
    uvicorn.run(
        "caelum_analytics.web.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    start_server()