"""Configuration management for Caelum Analytics."""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings
from .port_registry import port_registry


class Settings(BaseSettings):
    """Application settings and configuration."""

    # Core Application Settings
    host: str = Field(default="0.0.0.0", env="CAELUM_ANALYTICS_HOST")
    port: int = Field(
        default=8090, env="CAELUM_ANALYTICS_PORT"
    )  # Moved from 8080 to avoid cluster communication conflict
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="info", env="LOG_LEVEL")

    # Caelum Integration
    caelum_base_url: str = Field(default="http://localhost:3000", env="CAELUM_BASE_URL")
    caelum_api_key: Optional[str] = Field(default=None, env="CAELUM_API_KEY")
    mcp_servers_config_path: str = Field(
        default="/root/.claude/claude_desktop_config.json",
        env="MCP_SERVERS_CONFIG_PATH",
    )

    # Database Configuration
    influxdb_url: str = Field(default="http://10.32.3.27:8086", env="INFLUXDB_URL")
    influxdb_token: str = Field(default="", env="INFLUXDB_TOKEN")
    influxdb_org: str = Field(default="caelum", env="INFLUXDB_ORG")
    influxdb_bucket: str = Field(default="metrics", env="INFLUXDB_BUCKET")

    redis_url: str = Field(default="redis://10.32.3.27:6379", env="REDIS_URL")
    postgres_url: str = Field(
        default="postgresql://user:password@10.32.3.27:5432/caelum_analytics",
        env="POSTGRES_URL",
    )

    # External Services
    prometheus_url: str = Field(default="http://10.32.3.27:9090", env="PROMETHEUS_URL")
    grafana_url: str = Field(default="http://10.32.3.27:3000", env="GRAFANA_URL")

    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production", env="SECRET_KEY"
    )
    access_token_expire_minutes: int = Field(
        default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")

    # Data Collection
    collection_interval_seconds: int = Field(
        default=30, env="COLLECTION_INTERVAL_SECONDS"
    )
    retention_days: int = Field(default=90, env="RETENTION_DAYS")
    max_concurrent_collectors: int = Field(default=10, env="MAX_CONCURRENT_COLLECTORS")

    # WebSocket Configuration
    ws_max_connections: int = Field(default=100, env="WS_MAX_CONNECTIONS")
    ws_heartbeat_interval: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")

    # Cluster Communication
    cluster_communication_port: int = Field(default=8081, env="CLUSTER_COMMUNICATION_PORT")

    # Notification Services (Optional)
    pushover_user_key: Optional[str] = Field(default=None, env="PUSHOVER_USER_KEY")
    pushover_api_token: Optional[str] = Field(default=None, env="PUSHOVER_API_TOKEN")
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")

    # Development Settings
    reload: bool = Field(default=False, env="RELOAD")
    auto_reload_dirs: List[str] = Field(
        default=["src/caelum_analytics", "templates", "static"], env="AUTO_RELOAD_DIRS"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    @property
    def static_dir(self) -> Path:
        """Get the static files directory."""
        return self.project_root / "static"

    @property
    def templates_dir(self) -> Path:
        """Get the templates directory."""
        return self.project_root / "templates"

    def get_mcp_servers_list(self) -> List[str]:
        """Get list of MCP server names from configuration."""
        # This will be implemented to read from MCP config file
        return [
            "caelum-analytics-metrics",
            "caelum-api-gateway",
            "caelum-business-intelligence",
            "caelum-cluster-communication",
            "caelum-code-analysis",
            "caelum-cross-device-notifications",
            "caelum-deployment-infrastructure",
            "caelum-development-session",
            "caelum-device-orchestration",
            "caelum-integration-testing",
            "caelum-intelligence-hub",
            "caelum-knowledge-management",
            "caelum-ollama-pool",
            "caelum-opportunity-discovery",
            "caelum-performance-optimization",
            "caelum-project-intelligence",
            "caelum-security-compliance",
            "caelum-security-management",
            "caelum-user-profile",
            "caelum-workflow-orchestration",
        ]

    def validate_port_allocation(self) -> bool:
        """Validate that this service's port doesn't conflict with other Caelum services."""
        allocation = port_registry.get_allocation(self.port)
        if allocation and allocation.service_name != "analytics-dashboard":
            raise ValueError(
                f"Port {self.port} is already allocated to {allocation.service_name} "
                f"({allocation.purpose}). Please use a different port."
            )
        return True

    def get_port_registry_report(self) -> str:
        """Get a comprehensive port allocation report for the Caelum ecosystem."""
        return port_registry.generate_port_map_report()


# Global settings instance
settings = Settings()
