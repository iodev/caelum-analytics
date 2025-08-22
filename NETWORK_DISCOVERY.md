# Caelum Analytics - Network Discovery Setup

## Overview

The Caelum Analytics system uses a combination of UDP beacons and WebSocket cluster communication to automatically discover other machines running Caelum services on your local network.

## How Network Discovery Works

### 1. UDP Beacon System
- **Broadcasts**: Each machine broadcasts UDP beacons every 15 seconds on port **8181**
- **Multicast Group**: Uses `239.255.43.21` for efficient network discovery
- **Beacon Content**: Machine ID, hostname, primary IP, services, and WebSocket port

### 2. WebSocket Cluster Communication
- **Port**: Each machine listens on port **8080** for cluster communication
- **Protocol**: Custom cluster protocol for machine registration and task distribution
- **Auto-connection**: When a UDP beacon is received, the system automatically attempts WebSocket connection

## Network Requirements

### Firewall Configuration
Ensure these ports are open on all machines:
- **Port 8080**: WebSocket cluster communication (TCP)
- **Port 8181**: UDP beacon discovery (UDP)
- **Port 8090**: Analytics web interface (TCP) - only needed on dashboard machine

### Network Topology
- All machines must be on the same LAN/subnet
- Current known machines: `10.32.3.27`, `10.32.3.44`, `10.32.3.58`
- Broadcast and multicast traffic must be allowed

## Setup Instructions

### Option 1: Full Analytics Dashboard
Run this on machines where you want the full web interface:

```bash
# Clone the repository
git clone <repo-url> caelum-analytics
cd caelum-analytics

# Install dependencies
uv sync

# Run the full analytics dashboard
uv run uvicorn caelum_analytics.web.app:app --host 0.0.0.0 --port 8090
```

Access the dashboard at: `http://10.32.3.58:8090` (or your machine's IP)

### Option 2: Beacon-Only Mode (Recommended for Remote Machines)
Run this on machines that should be discoverable but don't need the dashboard:

```bash
# Clone the repository
git clone <repo-url> caelum-analytics
cd caelum-analytics

# Install dependencies
uv sync

# Run beacon-only mode
python beacon_only.py --host 0.0.0.0 --port 8080
```

### Option 3: Docker Deployment
```bash
# Build the Docker image
docker build -t caelum-analytics .

# Run full dashboard
docker run -d -p 8090:8090 -p 8080:8080 -p 8181:8181/udp --name caelum-analytics caelum-analytics

# Or run beacon-only mode
docker run -d -p 8080:8080 -p 8181:8181/udp --name caelum-beacon caelum-analytics python beacon_only.py
```

## Using Network Discovery

### From the Web Interface
1. Open the analytics dashboard: `http://10.32.3.58:8090`
2. Navigate to the "Cluster Status" section
3. Click the **"🔍 Discover Network"** button
4. Watch the discovery log for results

### Expected Results
When discovery works correctly, you should see:
- **UDP Discovery**: "UDP discovered new Caelum machine: hostname (IP)"
- **Connection Attempts**: Success/failure for each discovered machine
- **Cluster Status**: Connected machines appear in the cluster overview

## Troubleshooting

### No Machines Discovered
1. **Check if services are running** on target machines:
   ```bash
   ps aux | grep -E "(caelum|analytics|beacon)"
   ```

2. **Verify ports are listening**:
   ```bash
   netstat -tuln | grep -E "(8080|8090|8181)"
   ```

3. **Test UDP connectivity**:
   ```bash
   # From another machine, test if UDP port 8181 is reachable
   nc -u 10.32.3.58 8181
   ```

4. **Check firewall rules**:
   ```bash
   sudo ufw status
   # Ensure ports 8080, 8181, and 8090 are allowed
   ```

### Common Issues

#### "Cluster node not initialized"
- The analytics service isn't fully started
- Wait a few seconds and try again

#### "Connection refused" for WebSocket
- Target machine isn't running caelum-analytics or beacon-only mode
- Firewall is blocking port 8080

#### "No UDP beacons received"
- Target machines aren't broadcasting (not running caelum services)
- Network doesn't allow multicast/broadcast traffic
- Wrong network interface (check your IP range)

### Network Debugging
```bash
# Check your network interface and IP
ip addr show

# Monitor UDP traffic (run while clicking "Discover Network")
sudo tcpdump -i any -n port 8181

# Check if beacons are being sent
sudo tcpdump -i any -n dst port 8181

# Test WebSocket connectivity
telnet 10.32.3.27 8080
```

## Architecture

### Service Discovery Flow
1. **Beacon Broadcast**: Machine A sends UDP beacon to `239.255.43.21:8181`
2. **Beacon Reception**: Machine B receives beacon, extracts machine info
3. **WebSocket Connection**: Machine B connects to Machine A on port 8080
4. **Registration Exchange**: Machines exchange full machine information
5. **Cluster Formation**: Both machines are now aware of each other

### Port Allocation
- **8080**: Cluster WebSocket communication
- **8090**: Analytics web dashboard  
- **8181**: UDP beacon discovery
- **8100-8199**: Reserved for MCP servers (20 slots)

## Development Notes

### Key Files
- `src/caelum_analytics/udp_beacon.py`: UDP beacon system implementation
- `src/caelum_analytics/cluster_protocol.py`: WebSocket cluster communication
- `src/caelum_analytics/web/app.py`: Web dashboard with discovery endpoint
- `beacon_only.py`: Lightweight beacon-only deployment

### Extending Discovery
To add more discovery methods:
1. Implement new discovery in `cluster_protocol.py`
2. Add endpoint handler in `web/app.py` 
3. Update the discovery UI to show new method results

## Security Considerations

### Current Security Model
- **Open Network**: Currently assumes trusted LAN environment
- **No Authentication**: WebSocket connections are not authenticated
- **Plain Text**: All communication is unencrypted

### Production Hardening (Future)
- Add TLS encryption for WebSocket connections
- Implement machine authentication tokens
- Network access control lists
- Rate limiting for discovery requests

## Monitoring

### Log Locations
- **Application Logs**: Console output from uvicorn/python
- **Discovery Events**: Look for "🎯 UDP discovered" messages
- **Connection Events**: WebSocket connection success/failure logs

### Health Checks
- **UDP Beacon Status**: Check if beacons are being sent every 15 seconds
- **WebSocket Connections**: Monitor active cluster connections
- **Discovery Performance**: Track discovery success rates

---

For additional support, check the main `CLAUDE.md` file or examine the source code in `src/caelum_analytics/`.