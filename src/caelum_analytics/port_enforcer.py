"""Port Enforcer - Actually prevents port conflicts by checking before binding."""

import socket
import subprocess
import sys
import json
from typing import Optional, Dict, Any, Tuple
from pathlib import Path


class PortEnforcer:
    """Enforces port usage rules BEFORE services start."""

    # Core reserved ports that MUST NOT be used by other services
    RESERVED_PORTS = {
        8080: "cluster-websocket",  # Critical: WebSocket cluster communication
        8090: "analytics-dashboard",  # Analytics web UI
        5432: "postgresql",
        6379: "redis",
        8086: "influxdb",
        9090: "prometheus",
        3000: "grafana",
        8000: "api-gateway",
    }

    @classmethod
    def check_port(cls, port: int, service_name: str) -> Tuple[bool, str]:
        """
        Check if a port can be used by a service.
        Returns (can_use, message)
        """
        # Check reserved ports
        if port in cls.RESERVED_PORTS:
            reserved_for = cls.RESERVED_PORTS[port]
            if service_name != reserved_for:
                return (
                    False,
                    f"Port {port} is reserved for {reserved_for}. Cannot use for {service_name}.",
                )

        # Check if port is actually in use
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            result = sock.connect_ex(("0.0.0.0", port))
            sock.close()

            if result == 0:
                # Port is in use, try to identify what's using it
                try:
                    cmd = f"lsof -i :{port} -t 2>/dev/null | head -1"
                    pid = subprocess.check_output(cmd, shell=True, text=True).strip()
                    if pid:
                        cmd = f"ps -p {pid} -o comm= 2>/dev/null"
                        process = subprocess.check_output(
                            cmd, shell=True, text=True
                        ).strip()
                        return (
                            False,
                            f"Port {port} is already in use by {process} (PID: {pid})",
                        )
                except:
                    pass
                return False, f"Port {port} is already in use"

            return True, f"Port {port} is available for {service_name}"

        except Exception as e:
            return True, f"Port {port} appears available (check failed: {e})"

    @classmethod
    def enforce_port(
        cls, port: int, service_name: str, exit_on_conflict: bool = True
    ) -> bool:
        """
        Enforce port usage rules.
        If exit_on_conflict is True, will exit the program on conflict.
        Returns True if port can be used, False otherwise.
        """
        can_use, message = cls.check_port(port, service_name)

        if not can_use:
            print(f"❌ PORT CONFLICT: {message}", file=sys.stderr)

            # Suggest alternative
            alternative = cls.suggest_alternative(service_name)
            print(f"💡 Suggestion: Use port {alternative} instead", file=sys.stderr)

            if exit_on_conflict:
                sys.exit(1)
            return False

        print(f"✅ {message}")
        return True

    @classmethod
    def suggest_alternative(cls, service_name: str) -> int:
        """Suggest an alternative port based on service type."""
        if "web" in service_name or "dashboard" in service_name:
            return cls.find_free_port(8091, 8099)
        elif "api" in service_name:
            return cls.find_free_port(8001, 8099)
        elif "mcp" in service_name:
            return cls.find_free_port(8100, 8199)
        else:
            return cls.find_free_port(8200, 8999)

    @classmethod
    def find_free_port(cls, start: int, end: int) -> int:
        """Find a free port in the given range."""
        for port in range(start, end + 1):
            if port in cls.RESERVED_PORTS:
                continue

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                result = sock.connect_ex(("0.0.0.0", port))
                sock.close()
                if result != 0:
                    return port
            except:
                return port

        return start  # Fallback

    @classmethod
    def validate_before_docker(
        cls, dockerfile_path: str, service_name: str = "unknown"
    ) -> bool:
        """Validate port usage before Docker build/run."""
        # Parse Dockerfile for EXPOSE directives
        exposed_ports = []
        if Path(dockerfile_path).exists():
            with open(dockerfile_path, "r") as f:
                for line in f:
                    if line.strip().startswith("EXPOSE"):
                        port = int(line.split()[1])
                        exposed_ports.append(port)

        for port in exposed_ports:
            if port in cls.RESERVED_PORTS:
                reserved_for = cls.RESERVED_PORTS[port]
                if service_name != reserved_for:
                    print(
                        f"❌ Dockerfile exposes port {port} reserved for {reserved_for}, but service is {service_name}",
                        file=sys.stderr,
                    )
                    return False

        return True

    @classmethod
    def get_safe_port_for_service(
        cls, service_name: str, preferred_port: Optional[int] = None
    ) -> int:
        """
        Get a safe port for a service, checking preferred port first.
        Always returns a usable port.
        """
        if preferred_port:
            can_use, _ = cls.check_port(preferred_port, service_name)
            if can_use:
                return preferred_port

        # Find alternative
        return cls.suggest_alternative(service_name)


def require_port(port: int, service_name: str) -> None:
    """
    Decorator/function to require a specific port before service starts.
    Will exit if port cannot be used.
    """
    PortEnforcer.enforce_port(port, service_name, exit_on_conflict=True)


def check_port_safe(port: int, service_name: str) -> bool:
    """
    Check if a port is safe to use without exiting.
    Returns True if safe, False otherwise.
    """
    return PortEnforcer.enforce_port(port, service_name, exit_on_conflict=False)


if __name__ == "__main__":
    # CLI usage
    if len(sys.argv) < 3:
        print("Usage: python port_enforcer.py <port> <service_name>")
        sys.exit(1)

    port = int(sys.argv[1])
    service = sys.argv[2]

    PortEnforcer.enforce_port(port, service)
