# Caelum Analytics LAN Distribution Guide

## Overview

This guide explains how to distribute and run Caelum Analytics across multiple machines on your LAN, with automatic discovery between Caelum Analytics instances and regular Caelum cluster nodes.

## Network Discovery Architecture

### Port Configuration
- **Caelum Analytics**:
  - UDP 8181: Analytics beacon broadcasts/listening
  - UDP 8083+: Cluster beacon listening (fallback ports if 8081 busy)
  - TCP 8095+: WebSocket cluster communication (configurable)
  
- **Caelum Cluster**:
  - UDP 8081: Cluster beacon broadcasts/listening  
  - UDP 8181: Analytics beacon listening (updated)
  - TCP 8080: WebSocket cluster communication

### Cross-Discovery Features
✅ **Caelum Analytics** can discover other **Caelum Analytics** instances
✅ **Caelum Analytics** can discover **Caelum Cluster** nodes
✅ **Caelum Cluster** can discover **Caelum Analytics** instances
✅ **Caelum Cluster** can discover other **Caelum Cluster** nodes

## Distribution Options

### Option 1: Docker Deployment (Recommended)

#### Build and Distribute
```bash
# On development machine
docker build -t caelum-analytics .
docker save caelum-analytics > caelum-analytics.tar

# Transfer to target machines and load
docker load < caelum-analytics.tar

# Run on each machine (different ports for multiple instances)
docker run -d -p 8095:8090 --name caelum-analytics-1 caelum-analytics
docker run -d -p 8096:8090 --name caelum-analytics-2 caelum-analytics
```

#### Beacon-Only Mode
For lightweight monitoring nodes:
```bash
# Create beacon-only script on target machine
cat > start-beacon.sh << 'EOF'
#!/bin/bash
docker run -d --network host --name caelum-beacon \
  caelum-analytics python beacon_only.py --port 8095
EOF

chmod +x start-beacon.sh
./start-beacon.sh
```

### Option 2: Python Direct Install

#### Prerequisites
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone <repository-url> caelum-analytics
cd caelum-analytics
```

#### Installation
```bash
# Install dependencies
uv sync

# Run full analytics dashboard
uv run uvicorn caelum_analytics.web.app:app --host 0.0.0.0 --port 8095

# OR run beacon-only mode
uv run beacon_only.py --port 8095
```

### Option 3: Standalone Beacon Distribution

For machines that only need to be discoverable (no analytics dashboard):

#### Create Beacon Package
```bash
# On development machine
mkdir caelum-beacon-dist
cp beacon_only.py caelum-beacon-dist/
cp -r src/ caelum-beacon-dist/
cp pyproject.toml caelum-beacon-dist/
cp uv.lock caelum-beacon-dist/

# Create simple launcher
cat > caelum-beacon-dist/start-beacon.sh << 'EOF'
#!/bin/bash
uv sync
exec uv run beacon_only.py --port ${BEACON_PORT:-8095}
EOF

chmod +x caelum-beacon-dist/start-beacon.sh

# Package for distribution
tar -czf caelum-beacon.tar.gz caelum-beacon-dist/
```

#### Deploy on Target Machines
```bash
# Extract and run
tar -xzf caelum-beacon.tar.gz
cd caelum-beacon-dist
BEACON_PORT=8095 ./start-beacon.sh
```

## Network Configuration

### Port Management
Each machine should use different WebSocket ports to avoid conflicts:

| Machine | WebSocket Port | Purpose |
|---------|---------------|---------|
| Machine A | 8095 | Full Analytics Dashboard |
| Machine B | 8096 | Full Analytics Dashboard |
| Machine C | 8097 | Beacon-Only Node |
| Machine D | 8098 | Beacon-Only Node |

### Firewall Configuration
Ensure these ports are open on all machines:
```bash
# Ubuntu/Debian
sudo ufw allow 8181/udp  # Analytics beacons
sudo ufw allow 8083/udp  # Cluster beacon listener
sudo ufw allow 8095:8099/tcp  # WebSocket communication range

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8181/udp
sudo firewall-cmd --permanent --add-port=8083/udp  
sudo firewall-cmd --permanent --add-port=8095-8099/tcp
sudo firewall-cmd --reload
```

## Testing Network Discovery

### Verify Beacon Broadcasting
```bash
# Listen for analytics beacons on another machine
sudo tcpdump -i any -A port 8181

# Listen for cluster beacons
sudo tcpdump -i any -A port 8081
```

### Check Discovery Status
```bash
# Via API (if running full dashboard)
curl http://localhost:8095/api/discovered-machines

# Via logs
docker logs caelum-analytics | grep "UDP discovered"
```

## Deployment Scenarios

### Scenario 1: Mixed Caelum Environment
- 2x Caelum Cluster nodes (existing)
- 3x Caelum Analytics instances (new)

All instances will automatically discover each other via UDP beacons.

### Scenario 2: Analytics-Only Network
- 5x Caelum Analytics instances
- No existing Caelum clusters

Perfect for monitoring-focused deployments.

### Scenario 3: Development Lab
- 1x Full Caelum Analytics (main dashboard)
- 4x Beacon-only nodes (lightweight monitoring)

Minimal resource usage while maintaining network visibility.

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep 809

# Kill conflicting processes
sudo kill $(sudo lsof -t -i:8095)
```

#### Discovery Not Working
```bash
# Check UDP beacon broadcasts
sudo tcpdump -i any port 8181 or port 8081

# Verify firewall
sudo ufw status
iptables -L

# Check application logs
docker logs caelum-analytics
```

#### Network Segmentation
If machines are on different subnets, beacons may not cross network boundaries:
```bash
# Enable IP forwarding (router/gateway)
echo 1 > /proc/sys/net/ipv4/ip_forward

# Or use specific broadcast addresses in beacon code
```

## Security Considerations

### Network Security
- Use private network ranges (192.168.x.x, 10.x.x.x)
- Consider VPN for remote access
- Implement firewall rules for production

### Authentication
- WebSocket communication uses machine IDs for identification
- No authentication implemented by default
- Add authentication layer for production use

## Performance Optimization

### Resource Allocation
- **Full Analytics**: 512MB RAM minimum, 1GB recommended
- **Beacon-Only**: 128MB RAM minimum, 256MB recommended
- **CPU**: Minimal requirements, single core sufficient

### Network Optimization
- Beacon interval: 15 seconds (configurable)
- Discovery timeout: 60 seconds (configurable)
- Use multicast where possible to reduce network traffic

## Maintenance

### Health Monitoring
```bash
# Check beacon status
curl http://localhost:8095/health

# Monitor discovery
tail -f /var/log/caelum-analytics/discovery.log
```

### Updates
```bash
# Update Docker image
docker pull caelum-analytics:latest
docker stop caelum-analytics
docker rm caelum-analytics
docker run -d -p 8095:8090 --name caelum-analytics caelum-analytics:latest

# Update Python installation
cd caelum-analytics
git pull
uv sync
sudo systemctl restart caelum-analytics
```

## Support

For issues with network discovery or deployment:
1. Check logs: `docker logs caelum-analytics`
2. Verify network connectivity: `ping <target-machine>`
3. Test UDP connectivity: `nc -u <target-machine> 8181`
4. Review firewall settings
5. Check for port conflicts

---

**Note**: This cross-discovery system allows seamless integration between existing Caelum clusters and new Caelum Analytics instances, providing unified network visibility across your entire infrastructure.