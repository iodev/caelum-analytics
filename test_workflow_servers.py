#!/usr/bin/env python3
"""
Comprehensive test suite for 5-workflow architecture MCP servers
"""

import sys
import asyncio
import json
from pathlib import Path
import importlib.util
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_import_all_servers():
    """Test that all workflow servers can be imported without errors"""
    print("🧪 Testing server imports...")
    
    try:
        from caelum_analytics.workflow_servers import (
            DevelopmentWorkflowServer,
            BusinessWorkflowServer,
            InfrastructureWorkflowServer,
            CommunicationWorkflowServer,
            SecurityWorkflowServer
        )
        print("✅ All workflow servers imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_server_initialization():
    """Test server initialization without MCP dependencies"""
    print("\n🧪 Testing server initialization...")
    
    try:
        from caelum_analytics.workflow_servers.development.server import DevelopmentWorkflowServer
        from caelum_analytics.workflow_servers.business.server import BusinessWorkflowServer
        from caelum_analytics.workflow_servers.infrastructure.server import InfrastructureWorkflowServer
        from caelum_analytics.workflow_servers.communication.server import CommunicationWorkflowServer
        from caelum_analytics.workflow_servers.security.server import SecurityWorkflowServer
        
        servers = [
            ("Development", DevelopmentWorkflowServer),
            ("Business", BusinessWorkflowServer),
            ("Infrastructure", InfrastructureWorkflowServer),
            ("Communication", CommunicationWorkflowServer),
            ("Security", SecurityWorkflowServer)
        ]
        
        for name, ServerClass in servers:
            try:
                server = ServerClass()
                print(f"✅ {name} workflow server initialized")
                
                # Test that all_tools is populated
                if hasattr(server, 'all_tools') and server.all_tools:
                    print(f"   📊 {len(server.all_tools)} tools registered")
                else:
                    print(f"   ⚠️  No tools found in {name} server")
                    
            except Exception as e:
                print(f"❌ {name} server initialization failed: {e}")
                return False
                
        return True
    except Exception as e:
        print(f"❌ Server initialization error: {e}")
        return False

def test_tool_definitions():
    """Test that tool definitions are properly structured"""
    print("\n🧪 Testing tool definitions...")
    
    try:
        from caelum_analytics.workflow_servers.development.server import DevelopmentWorkflowServer
        
        server = DevelopmentWorkflowServer()
        
        required_fields = ["name", "description", "priority", "category", "intents", "underlying_service", "schema"]
        
        for tool_name, tool_def in server.all_tools.items():
            for field in required_fields:
                if field not in tool_def:
                    print(f"❌ Tool {tool_name} missing field: {field}")
                    return False
                    
            # Test schema structure
            schema = tool_def["schema"]
            if "type" not in schema:
                print(f"❌ Tool {tool_name} schema missing type")
                return False
                
        print(f"✅ All {len(server.all_tools)} development tools properly defined")
        return True
        
    except Exception as e:
        print(f"❌ Tool definition test error: {e}")
        return False

async def test_tool_execution():
    """Test tool execution logic"""
    print("\n🧪 Testing tool execution...")
    
    try:
        from caelum_analytics.workflow_servers.development.server import DevelopmentWorkflowServer
        
        server = DevelopmentWorkflowServer()
        
        # Test analyze_code_quality tool
        result = await server.execute_tool("analyze_code_quality", {
            "code": "print('hello world')",
            "language": "python"
        })
        
        if "analysis_type" in result and "findings" in result:
            print("✅ Development tool execution working")
        else:
            print(f"❌ Unexpected tool result: {result}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Tool execution test error: {e}")
        return False

async def test_tool_selection():
    """Test intelligent tool selection"""
    print("\n🧪 Testing intelligent tool selection...")
    
    try:
        from caelum_analytics.workflow_servers.development.server import DevelopmentWorkflowServer
        
        server = DevelopmentWorkflowServer()
        
        # Test with security-focused query
        selected = await server.select_tools_for_context("analyze security vulnerabilities in my code", max_tools=5)
        
        if len(selected) > 0:
            print(f"✅ Tool selection working - selected {len(selected)} tools")
            for tool_name in list(selected.keys())[:3]:
                print(f"   🔧 {tool_name}")
        else:
            print("❌ No tools selected")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Tool selection test error: {e}")
        return False

async def test_dynamic_explorer():
    """Test dynamic server explorer"""
    print("\n🧪 Testing dynamic server explorer...")
    
    try:
        from caelum_analytics.dynamic_server_explorer import dynamic_explorer
        
        # Test initialization
        await dynamic_explorer.initialize()
        
        if len(dynamic_explorer.servers) > 0:
            print(f"✅ Dynamic explorer initialized - {len(dynamic_explorer.servers)} servers")
        else:
            print("❌ No servers found in explorer")
            return False
            
        # Test hierarchy generation
        hierarchy = dynamic_explorer.get_server_hierarchy()
        
        if "workflow_servers" in hierarchy and "summary" in hierarchy:
            print("✅ Server hierarchy generation working")
        else:
            print("❌ Hierarchy generation failed")
            return False
            
        # Test search
        search_results = dynamic_explorer.search_by_capability("analysis")
        
        if len(search_results["servers"]) > 0 or len(search_results["tools"]) > 0:
            print("✅ Capability search working")
        else:
            print("❌ Search functionality failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Dynamic explorer test error: {e}")
        return False

def test_claude_config():
    """Test Claude configuration file"""
    print("\n🧪 Testing Claude configuration...")
    
    try:
        config_path = Path("claude_config_5workflow_optimized.json")
        
        if not config_path.exists():
            print("❌ Optimized Claude config not found")
            return False
            
        with open(config_path) as f:
            config = json.load(f)
            
        if "mcpServers" not in config:
            print("❌ Invalid Claude config structure")
            return False
            
        workflow_servers = [
            "caelum-development-workflow",
            "caelum-business-workflow", 
            "caelum-infrastructure-workflow",
            "caelum-communication-workflow",
            "caelum-security-workflow"
        ]
        
        found_servers = 0
        for server in workflow_servers:
            if server in config["mcpServers"]:
                found_servers += 1
                print(f"   ✅ {server} configured")
            else:
                print(f"   ❌ {server} missing from config")
                
        if found_servers == len(workflow_servers):
            print(f"✅ All {found_servers} workflow servers in Claude config")
            return True
        else:
            print(f"❌ Only {found_servers}/{len(workflow_servers)} workflow servers configured")
            return False
            
    except Exception as e:
        print(f"❌ Claude config test error: {e}")
        return False

async def test_pre_hook_system():
    """Test the pre-hook system for external LLMs"""
    print("\n🧪 Testing pre-hook system...")
    
    try:
        from caelum_analytics.tool_prescreener import tool_prescreener
        from caelum_analytics.llm_prehook import llm_prehook
        
        # Test tool prescreener initialization
        await tool_prescreener.initialize_tool_registry()
        
        if len(tool_prescreener.tool_registry) > 0:
            print(f"✅ Tool prescreener initialized - {len(tool_prescreener.tool_registry)} tools registered")
        else:
            print("❌ Tool prescreener failed to initialize")
            return False
            
        # Test query analysis
        query = "analyze the security of my Python application"
        analysis = await tool_prescreener.analyze_query(query)
        
        if analysis.intent and analysis.complexity:
            print(f"✅ Query analysis working - Intent: {analysis.intent}, Complexity: {analysis.complexity}")
        else:
            print("❌ Query analysis failed")
            return False
            
        # Test tool pre-screening
        selected_tools = await tool_prescreener.prescreen_tools(query)
        
        if len(selected_tools) <= 100:  # GitHub Copilot limit
            print(f"✅ Tool pre-screening working - {len(selected_tools)} tools (under GitHub Copilot limit)")
            return True
        else:
            print(f"❌ Too many tools selected: {len(selected_tools)} (exceeds limit)")
            return False
            
    except Exception as e:
        print(f"❌ Pre-hook system test error: {e}")
        return False

async def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 Starting comprehensive 5-workflow architecture tests...\n")
    
    tests = [
        ("Import Tests", test_import_all_servers),
        ("Initialization Tests", test_server_initialization), 
        ("Tool Definition Tests", test_tool_definitions),
        ("Tool Execution Tests", test_tool_execution),
        ("Tool Selection Tests", test_tool_selection),
        ("Dynamic Explorer Tests", test_dynamic_explorer),
        ("Claude Config Tests", test_claude_config),
        ("Pre-hook System Tests", test_pre_hook_system)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("🎯 TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - 5-workflow architecture ready for deployment!")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed - please address issues before deployment")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)