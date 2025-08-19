"""
Claude CLI Integration with Pre-hook System

Automatically intercepts external LLM requests and pre-screens tools
to stay within provider limits (e.g., GitHub Copilot's 100 tool limit).
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess
import sys

from .llm_prehook import llm_prehook
from .tool_prescreener import tool_prescreener
import logging

logger = logging.getLogger(__name__)

class ClaudeCLIIntegration:
    """
    Integration layer for Claude CLI that automatically applies
    tool pre-screening for external LLM providers
    """
    
    def __init__(self):
        self.prehook = llm_prehook
        self.claude_config_path = Path.home() / ".claude" / "claude_desktop_config.json"
        self.original_config = None
        self.providers_with_limits = {
            "github-copilot": 100,
            "openai-assistant": 128,
            "azure-openai": 100
        }
        
    async def initialize(self):
        """Initialize the Claude CLI integration"""
        await self.prehook.initialize()
        await self._backup_original_config()
        logger.info("Claude CLI integration initialized")
        
    async def _backup_original_config(self):
        """Backup the original Claude configuration"""
        if self.claude_config_path.exists():
            with open(self.claude_config_path, 'r') as f:
                self.original_config = json.load(f)
                
            backup_path = self.claude_config_path.parent / "claude_desktop_config.backup.json"
            with open(backup_path, 'w') as f:
                json.dump(self.original_config, f, indent=2)
                
            logger.info(f"Backed up original Claude config to {backup_path}")
    
    async def create_optimized_config_for_provider(self, provider: str, user_query: str = "") -> Path:
        """
        Create an optimized Claude configuration for a specific provider
        with pre-screened tools
        """
        if not self.original_config:
            raise ValueError("Original Claude config not found. Run initialize() first.")
            
        max_tools = self.providers_with_limits.get(provider, 100)
        
        # Get all available tools from original config
        all_tools = await self._extract_available_tools()
        
        # Pre-screen tools for this query and provider
        if user_query:
            optimized_request = await self.prehook.intercept_external_llm_request(
                llm_provider=provider,
                query=user_query,
                available_tools=all_tools
            )
            
            relevant_tool_names = {tool["name"] for tool in optimized_request["tools"]}
        else:
            # Default to core tools if no query provided
            relevant_tool_names = set()
            for tool in all_tools:
                if any(keyword in tool.get("description", "").lower() 
                      for keyword in ["core", "file", "read", "write", "edit"]):
                    relevant_tool_names.add(tool["name"])
                if len(relevant_tool_names) >= max_tools:
                    break
        
        # Create optimized config
        optimized_config = self._create_filtered_config(relevant_tool_names)
        
        # Save optimized config
        optimized_path = self.claude_config_path.parent / f"claude_config_{provider}_optimized.json"
        with open(optimized_path, 'w') as f:
            json.dump(optimized_config, f, indent=2)
            
        logger.info(f"Created optimized config for {provider}: {len(relevant_tool_names)} tools → {optimized_path}")
        
        return optimized_path
    
    async def _extract_available_tools(self) -> List[Dict[str, Any]]:
        """Extract all available tools from MCP server configs"""
        tools = []
        
        # Built-in Claude Code tools
        builtin_tools = [
            {"name": "Read", "description": "Read file contents", "server": "claude-code"},
            {"name": "Write", "description": "Write file contents", "server": "claude-code"},
            {"name": "Edit", "description": "Edit file contents", "server": "claude-code"},
            {"name": "Bash", "description": "Execute bash commands", "server": "claude-code"},
            {"name": "Grep", "description": "Search file contents", "server": "claude-code"},
            {"name": "Glob", "description": "Find files by pattern", "server": "claude-code"},
            {"name": "TodoWrite", "description": "Manage todo lists", "server": "claude-code"}
        ]
        tools.extend(builtin_tools)
        
        # MCP server tools (from config)
        if "mcpServers" in self.original_config:
            for server_name, server_config in self.original_config["mcpServers"].items():
                # Estimate tools based on server type
                estimated_tools = self._estimate_server_tools(server_name, server_config)
                tools.extend(estimated_tools)
                
        return tools
    
    def _estimate_server_tools(self, server_name: str, server_config: Dict) -> List[Dict[str, Any]]:
        """Estimate available tools for a given MCP server"""
        # This is a simplified estimation - in practice, you'd query the server
        server_tool_estimates = {
            "caelum-code-analysis": [
                {"name": "analyze_code", "description": "Analyze code quality and security"},
                {"name": "search_similar_code", "description": "Find similar code patterns"},
                {"name": "get_code_statistics", "description": "Get code metrics"}
            ],
            "caelum-business-intelligence": [
                {"name": "research_market", "description": "Market research and analysis"}
            ],
            "caelum-ollama-pool": [
                {"name": "route_llm_request", "description": "Route requests to optimal LLM"},
                {"name": "get_pool_health_status", "description": "Check pool health"},
                {"name": "optimize_model_distribution", "description": "Optimize model distribution"}
            ],
            "caelum-project-intelligence": [
                {"name": "analyze_project", "description": "Analyze project structure"},
                {"name": "list_projects", "description": "List analyzed projects"},
                {"name": "get_project_details", "description": "Get project details"}
            ],
            "caelum-notifications": [
                {"name": "send_notification", "description": "Send notifications"},
                {"name": "list_notifications", "description": "List notifications"},
                {"name": "get_notification_status", "description": "Get notification status"}
            ],
            "filesystem": [
                {"name": "read_text_file", "description": "Read text files"},
                {"name": "write_file", "description": "Write files"},
                {"name": "list_directory", "description": "List directory contents"},
                {"name": "search_files", "description": "Search for files"}
            ]
        }
        
        estimated = server_tool_estimates.get(server_name, [
            {"name": f"{server_name}_default", "description": f"Default tool for {server_name}"}
        ])
        
        # Add server context to each tool
        for tool in estimated:
            tool["server"] = server_name
            
        return estimated
    
    def _create_filtered_config(self, relevant_tool_names: set) -> Dict[str, Any]:
        """Create a filtered Claude configuration with only relevant tools"""
        if not self.original_config:
            return {}
            
        # Start with original config
        filtered_config = self.original_config.copy()
        
        # Filter MCP servers to only include those with relevant tools
        if "mcpServers" in filtered_config:
            servers_to_keep = {}
            
            for server_name, server_config in self.original_config["mcpServers"].items():
                # Check if this server has relevant tools
                server_tools = self._estimate_server_tools(server_name, server_config)
                has_relevant_tools = any(
                    tool["name"] in relevant_tool_names 
                    for tool in server_tools
                )
                
                if has_relevant_tools or server_name in ["filesystem"]:  # Always keep filesystem
                    servers_to_keep[server_name] = server_config
                    
            filtered_config["mcpServers"] = servers_to_keep
            
        return filtered_config
    
    async def run_claude_with_provider(
        self, 
        provider: str, 
        query: str,
        additional_args: List[str] = None
    ) -> subprocess.CompletedProcess:
        """
        Run Claude CLI with optimized configuration for specific provider
        """
        # Create optimized config for this provider and query
        optimized_config_path = await self.create_optimized_config_for_provider(provider, query)
        
        # Prepare Claude CLI command
        cmd = [
            "claude-code",
            "--config", str(optimized_config_path)
        ]
        
        if additional_args:
            cmd.extend(additional_args)
            
        # Add the query
        cmd.append(query)
        
        logger.info(f"Running Claude CLI with {provider} optimization: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Log the result
            await self._log_claude_execution(provider, query, result)
            
            return result
            
        except subprocess.TimeoutExpired:
            logger.error(f"Claude CLI execution timed out for provider {provider}")
            raise
        except Exception as e:
            logger.error(f"Error running Claude CLI with {provider}: {e}")
            raise
    
    async def _log_claude_execution(
        self, 
        provider: str, 
        query: str, 
        result: subprocess.CompletedProcess
    ):
        """Log Claude CLI execution for monitoring"""
        execution_data = {
            "provider": provider,
            "query_length": len(query),
            "return_code": result.returncode,
            "stdout_length": len(result.stdout) if result.stdout else 0,
            "stderr_length": len(result.stderr) if result.stderr else 0,
            "success": result.returncode == 0
        }
        
        if result.returncode == 0:
            logger.info(f"Claude CLI execution successful for {provider}")
        else:
            logger.error(f"Claude CLI execution failed for {provider}: {result.stderr}")
    
    async def create_provider_wrapper_script(self, provider: str) -> Path:
        """
        Create a wrapper script for easy provider-specific Claude CLI usage
        """
        wrapper_script = f"""#!/bin/bash
# Auto-generated wrapper for Claude CLI with {provider} optimization
# Automatically pre-screens tools to stay within {self.providers_with_limits.get(provider, 100)} tool limit

QUERY="$*"
if [ -z "$QUERY" ]; then
    echo "Usage: claude-{provider} <your query>"
    exit 1
fi

# Use Python to create optimized config and run Claude
python3 -c "
import asyncio
import sys
sys.path.append('{Path(__file__).parent}')
from claude_cli_integration import ClaudeCLIIntegration

async def main():
    integration = ClaudeCLIIntegration()
    await integration.initialize()
    result = await integration.run_claude_with_provider('{provider}', '$QUERY')
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)

asyncio.run(main())
"
"""
        
        wrapper_path = Path.home() / ".local" / "bin" / f"claude-{provider}"
        wrapper_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(wrapper_path, 'w') as f:
            f.write(wrapper_script)
            
        # Make executable
        wrapper_path.chmod(0o755)
        
        logger.info(f"Created wrapper script: {wrapper_path}")
        return wrapper_path

# Global integration instance
claude_cli_integration = ClaudeCLIIntegration()