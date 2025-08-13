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

from ..config import settings

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


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Caelum Analytics Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .status { display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            .status.online { background: #2ecc71; color: white; }
            .status.offline { background: #e74c3c; color: white; }
            .status.unknown { background: #95a5a6; color: white; }
            #realtime-data { margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Caelum Analytics Dashboard</h1>
            <p>Real-time monitoring for 20+ MCP servers</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📊 System Overview</h3>
                <p>MCP Servers: <span id="server-count">Loading...</span></p>
                <p>Online: <span id="online-count" class="status online">0</span></p>
                <p>Offline: <span id="offline-count" class="status offline">0</span></p>
            </div>
            
            <div class="card">
                <h3>🔄 Real-time Status</h3>
                <div id="server-list">Loading servers...</div>
            </div>
            
            <div class="card">
                <h3>📈 Performance Metrics</h3>
                <p>Avg Response Time: <span id="avg-response">-- ms</span></p>
                <p>Total Requests: <span id="total-requests">--</span></p>
                <p>Error Rate: <span id="error-rate">--%</span></p>
            </div>
            
            <div class="card">
                <h3>⚡ Quick Actions</h3>
                <p><a href="/api/docs">API Documentation</a></p>
                <p><a href="/api/v1/servers">Server Status API</a></p>
                <p><a href="#" onclick="connectWebSocket()">Connect Real-time</a></p>
            </div>
        </div>
        
        <div id="realtime-data">
            <h3>🔴 Live Updates</h3>
            <div id="live-log" style="background: black; color: #00ff00; padding: 10px; height: 200px; overflow-y: scroll; font-family: monospace;"></div>
        </div>

        <script>
            let ws = null;
            
            function connectWebSocket() {
                ws = new WebSocket(`ws://localhost:${window.location.port}/ws/live`);
                
                ws.onopen = function(event) {
                    addLog("✅ Connected to real-time updates");
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addLog(`📡 ${data.type}: ${JSON.stringify(data.data)}`);
                    updateDashboard(data);
                };
                
                ws.onclose = function(event) {
                    addLog("❌ Connection closed");
                };
            }
            
            function addLog(message) {
                const log = document.getElementById('live-log');
                const time = new Date().toLocaleTimeString();
                log.innerHTML += `[${time}] ${message}\\n`;
                log.scrollTop = log.scrollHeight;
            }
            
            function updateDashboard(data) {
                if (data.type === 'server_status') {
                    document.getElementById('server-count').textContent = data.data.total || '20';
                    document.getElementById('online-count').textContent = data.data.online || '0';
                    document.getElementById('offline-count').textContent = data.data.offline || '0';
                }
            }
            
            // Auto-connect on page load
            window.onload = function() {
                connectWebSocket();
                
                // Simulate some initial data
                setTimeout(() => {
                    updateDashboard({
                        type: 'server_status',
                        data: { total: 20, online: 16, offline: 4 }
                    });
                }, 1000);
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