#!/usr/bin/env python3
"""Pre-startup port validation script."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from caelum_analytics.port_enforcer import PortEnforcer

def main():
    print("🔍 Validating port usage before startup...")
    
    # Check Docker configuration
    dockerfile = Path(__file__).parent / "Dockerfile"
    if dockerfile.exists():
        if not PortEnforcer.validate_before_docker(str(dockerfile), "analytics-dashboard"):
            print("❌ Dockerfile validation failed")
            sys.exit(1)
        print("✅ Dockerfile port configuration valid")
    
    # Check critical ports
    critical_ports = [
        (8090, "analytics-dashboard"),
        (8080, "cluster-websocket"),
    ]
    
    for port, service in critical_ports:
        can_use, message = PortEnforcer.check_port(port, service)
        if service == "analytics-dashboard" and not can_use:
            print(f"❌ {message}")
            suggested = PortEnforcer.suggest_alternative(service)
            print(f"💡 Consider updating configuration to use port {suggested}")
        elif service == "cluster-websocket" and not can_use and port == 8080:
            print(f"⚠️  Port 8080 is in use but should be reserved for cluster WebSocket")
        else:
            print(f"✅ {message}")
    
    print("\n🎯 Port validation complete!")

if __name__ == "__main__":
    main()