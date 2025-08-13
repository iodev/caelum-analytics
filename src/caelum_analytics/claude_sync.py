"""Claude configuration synchronization between Caelum cluster machines.

This module handles synchronization of Claude hooks, user configurations, 
and system prompts across different machines and environments in a Caelum cluster.
"""

import asyncio
import json
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

from .machine_registry import machine_registry
from .cluster_protocol import cluster_node, ClusterMessage, MessageType

logger = logging.getLogger(__name__)


@dataclass
class ClaudeConfig:
    """Claude configuration data structure."""
    
    config_type: str  # "hooks", "desktop_config", "system_prompts", "user_profile"
    config_name: str  # e.g., "user-prompt-submit-hook", "claude_desktop_config.json"
    content: str      # The actual configuration content
    file_path: str    # Original file path
    checksum: str     # SHA256 checksum for change detection
    last_modified: str  # ISO timestamp
    machine_id: str   # Source machine ID
    environment: str  # "wsl", "windows", "linux", "macos"


@dataclass
class ConfigSyncRequest:
    """Request for configuration synchronization."""
    
    request_id: str
    source_machine: str
    target_machines: List[str]  # Empty = broadcast to all
    config_types: List[str]     # Types to sync
    sync_direction: str         # "push", "pull", "bidirectional"
    conflict_resolution: str    # "source_wins", "target_wins", "merge", "prompt"


class ClaudeSyncManager:
    """Manages synchronization of Claude configurations across cluster machines."""
    
    def __init__(self):
        self.local_configs: Dict[str, ClaudeConfig] = {}
        self.sync_requests: Dict[str, ConfigSyncRequest] = {}
        self.config_paths = {
            "hooks": [
                "~/.claude/hooks/",
                "~/.claude/hooks.d/", 
                "~/.config/claude/hooks/"
            ],
            "desktop_config": [
                "~/.claude/claude_desktop_config.json",
                "~/AppData/Roaming/Claude/claude_desktop_config.json",  # Windows
                "~/.config/claude/claude_desktop_config.json"
            ],
            "system_prompts": [
                "~/.claude/system_prompts/",
                "~/.config/claude/system_prompts/",
                "~/.claude/prompts/"
            ],
            "user_profile": [
                "~/.claude/profile.json",
                "~/.claude/CLAUDE.md",
                "~/.config/claude/profile/"
            ]
        }
        
        # Environment detection
        self.environment = self._detect_environment()
        
    def _detect_environment(self) -> str:
        """Detect the current environment (WSL, Windows, Linux, macOS)."""
        import platform
        import subprocess
        
        system = platform.system().lower()
        
        if system == "linux":
            # Check if running in WSL
            try:
                with open("/proc/version", "r") as f:
                    if "microsoft" in f.read().lower():
                        return "wsl"
            except:
                pass
            return "linux"
        elif system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        else:
            return system

    def _calculate_checksum(self, content: str) -> str:
        """Calculate SHA256 checksum of configuration content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _find_config_files(self, config_type: str) -> List[Path]:
        """Find all configuration files of a given type."""
        files = []
        paths = self.config_paths.get(config_type, [])
        
        for path_str in paths:
            path = Path(path_str).expanduser()
            
            if path.is_file():
                files.append(path)
            elif path.is_dir():
                # Recursively find configuration files in directory
                if config_type == "hooks":
                    files.extend(path.glob("**/*.sh"))
                    files.extend(path.glob("**/*.py"))
                    files.extend(path.glob("**/*.js"))
                    files.extend(path.glob("**/*.json"))
                elif config_type == "system_prompts":
                    files.extend(path.glob("**/*.md"))
                    files.extend(path.glob("**/*.txt"))
                    files.extend(path.glob("**/*.json"))
                elif config_type == "user_profile":
                    files.extend(path.glob("**/*.json"))
                    files.extend(path.glob("**/*.md"))
                    
        return [f for f in files if f.exists()]

    def scan_local_configs(self) -> Dict[str, ClaudeConfig]:
        """Scan and catalog all local Claude configurations."""
        configs = {}
        
        for config_type in self.config_paths.keys():
            try:
                files = self._find_config_files(config_type)
                
                for file_path in files:
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        checksum = self._calculate_checksum(content)
                        
                        config = ClaudeConfig(
                            config_type=config_type,
                            config_name=file_path.name,
                            content=content,
                            file_path=str(file_path),
                            checksum=checksum,
                            last_modified=datetime.fromtimestamp(
                                file_path.stat().st_mtime, tz=timezone.utc
                            ).isoformat(),
                            machine_id=machine_registry.local_machine_id or "unknown",
                            environment=self.environment
                        )
                        
                        config_key = f"{config_type}:{file_path.name}"
                        configs[config_key] = config
                        
                    except Exception as e:
                        logger.warning(f"Failed to read config file {file_path}: {e}")
                        
            except Exception as e:
                logger.error(f"Failed to scan {config_type} configs: {e}")
        
        self.local_configs = configs
        logger.info(f"Scanned {len(configs)} local Claude configurations")
        return configs

    async def sync_config_to_cluster(self, config_types: List[str] = None, 
                                   target_machines: List[str] = None) -> str:
        """Sync local configurations to cluster machines."""
        if not cluster_node:
            raise ValueError("Cluster node not initialized")
            
        if config_types is None:
            config_types = list(self.config_paths.keys())
            
        # Scan local configs
        local_configs = self.scan_local_configs()
        
        # Filter by requested types
        configs_to_sync = {
            k: v for k, v in local_configs.items() 
            if any(v.config_type == ct for ct in config_types)
        }
        
        if not configs_to_sync:
            logger.warning(f"No configurations found for types: {config_types}")
            return "no_configs_found"
            
        request_id = f"sync_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{machine_registry.local_machine_id}"
        
        # Create sync request
        sync_request = ConfigSyncRequest(
            request_id=request_id,
            source_machine=machine_registry.local_machine_id or "unknown",
            target_machines=target_machines or [],
            config_types=config_types,
            sync_direction="push",
            conflict_resolution="source_wins"  # Default - can be configured
        )
        
        self.sync_requests[request_id] = sync_request
        
        # Send sync message to cluster
        message = ClusterMessage(
            message_id=request_id,
            message_type=MessageType.STATUS_BROADCAST,  # We'll add CLAUDE_CONFIG_SYNC later
            source_machine=machine_registry.local_machine_id or "unknown",
            target_machines=target_machines,
            payload={
                "message_subtype": "CLAUDE_CONFIG_SYNC",
                "sync_request": asdict(sync_request),
                "configurations": {k: asdict(v) for k, v in configs_to_sync.items()},
                "config_count": len(configs_to_sync),
                "environments_included": list(set(c.environment for c in configs_to_sync.values()))
            }
        )
        
        await cluster_node.broadcast_message(message)
        
        logger.info(f"Initiated Claude config sync {request_id} for {len(configs_to_sync)} configurations")
        return request_id

    async def receive_config_sync(self, message: ClusterMessage) -> bool:
        """Handle incoming configuration sync from another machine."""
        try:
            payload = message.payload
            sync_data = payload.get("sync_request", {})
            configurations = payload.get("configurations", {})
            
            if not configurations:
                logger.warning("Received empty config sync")
                return False
                
            # Process each configuration
            applied_configs = []
            for config_key, config_data in configurations.items():
                try:
                    config = ClaudeConfig(**config_data)
                    if await self._apply_config(config):
                        applied_configs.append(config_key)
                except Exception as e:
                    logger.error(f"Failed to apply config {config_key}: {e}")
            
            if applied_configs:
                logger.info(f"Applied {len(applied_configs)} Claude configurations from {message.source_machine}")
                
                # Send acknowledgment
                ack_message = ClusterMessage(
                    message_id=f"ack_{message.message_id}",
                    message_type=MessageType.STATUS_BROADCAST,
                    source_machine=machine_registry.local_machine_id or "unknown",
                    target_machines=[message.source_machine],
                    payload={
                        "message_subtype": "CLAUDE_CONFIG_SYNC_ACK",
                        "original_request_id": message.message_id,
                        "applied_configs": applied_configs,
                        "target_environment": self.environment
                    }
                )
                
                await cluster_node.broadcast_message(ack_message)
                return True
                
        except Exception as e:
            logger.error(f"Failed to process config sync: {e}")
            
        return False

    async def _apply_config(self, config: ClaudeConfig) -> bool:
        """Apply a configuration to the local system."""
        try:
            # Determine target path based on config type and environment
            target_path = self._get_target_path(config)
            if not target_path:
                logger.warning(f"No target path for {config.config_name} in {self.environment}")
                return False
                
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file already exists and compare checksums
            if target_path.exists():
                existing_content = target_path.read_text(encoding='utf-8')
                existing_checksum = self._calculate_checksum(existing_content)
                
                if existing_checksum == config.checksum:
                    logger.debug(f"Config {config.config_name} is already up to date")
                    return True
                    
                # Create backup of existing file
                backup_path = target_path.with_suffix(f"{target_path.suffix}.backup")
                backup_path.write_text(existing_content, encoding='utf-8')
                logger.info(f"Backed up existing config to {backup_path}")
            
            # Write new configuration
            target_path.write_text(config.content, encoding='utf-8')
            
            # Set executable permissions for hook files
            if config.config_type == "hooks" and target_path.suffix in ['.sh', '.py']:
                os.chmod(target_path, 0o755)
            
            logger.info(f"Applied Claude config: {config.config_name} -> {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply config {config.config_name}: {e}")
            return False

    def _get_target_path(self, config: ClaudeConfig) -> Optional[Path]:
        """Determine the target path for a configuration based on current environment."""
        config_type = config.config_type
        config_name = config.config_name
        
        # Get environment-appropriate paths
        paths = self.config_paths.get(config_type, [])
        
        for path_str in paths:
            path = Path(path_str).expanduser()
            
            # For directory paths, append the config name
            if path_str.endswith("/"):
                target_path = path / config_name
            else:
                target_path = path
                
            # Check if this path is appropriate for current environment
            if self._is_path_appropriate(target_path, self.environment):
                return target_path
                
        return None

    def _is_path_appropriate(self, path: Path, environment: str) -> bool:
        """Check if a path is appropriate for the current environment."""
        path_str = str(path)
        
        if environment == "windows":
            return "AppData" in path_str or path_str.startswith("C:\\")
        elif environment in ["linux", "wsl", "macos"]:
            return not ("AppData" in path_str or path_str.startswith("C:\\"))
            
        return True

    def get_sync_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a configuration sync request."""
        if request_id not in self.sync_requests:
            return None
            
        sync_request = self.sync_requests[request_id]
        return {
            "request_id": request_id,
            "sync_request": asdict(sync_request),
            "status": "completed",  # This would be tracked properly in a full implementation
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global Claude sync manager instance
claude_sync = ClaudeSyncManager()