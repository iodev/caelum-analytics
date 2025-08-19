#!/usr/bin/env python3
"""
Demonstration of Caelum Self-Optimization System

This script demonstrates the complete self-optimization cycle and shows how
overarching principles are learned and applied.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def demonstrate_self_optimization():
    """Demonstrate the complete self-optimization system"""
    
    print("🚀 Caelum Self-Optimization System Demonstration")
    print("=" * 60)
    
    try:
        # Import the self-optimization system
        from caelum_analytics.self_optimization import (
            start_self_optimization, 
            get_current_principles, 
            get_optimization_status,
            get_system_insights,
            trigger_optimization_cycle,
            OVERARCHING_PRINCIPLES
        )
        
        print("\n📚 OVERARCHING PRINCIPLES LEARNED:")
        print("-" * 40)
        
        for principle_name, principle_data in OVERARCHING_PRINCIPLES.items():
            print(f"\n🎯 {principle_name}")
            print(f"   Description: {principle_data['description']}")
            print(f"   Key Insight: {principle_data['key_insight']}")
        
        print("\n" + "=" * 60)
        print("🔧 INITIALIZING SELF-OPTIMIZATION SYSTEM")
        print("=" * 60)
        
        # Initialize the system
        init_result = await start_self_optimization()
        
        if init_result["status"] == "started":
            print("✅ System started successfully!")
            print(f"   Components: {', '.join(init_result['system_components'].keys())}")
            print(f"   Principles loaded: {init_result['principles_loaded']}")
            
            # Show current principles with evidence
            print("\n📊 CURRENT PRINCIPLES WITH EVIDENCE:")
            print("-" * 50)
            
            principles = get_current_principles()
            
            for principle_id, principle in principles['principles'].items():
                print(f"\n🔬 {principle['title']}")
                print(f"   Category: {principle['category']}")
                print(f"   Evidence Strength: {principle['evidence_strength']:.2f}")
                print(f"   Conditions: {', '.join(principle['conditions'][:2])}")  # Show first 2
                
            print(f"\n📈 Average Evidence Strength: {principles['avg_evidence_strength']:.2f}")
            
            # Show system status
            print("\n⚡ SYSTEM STATUS:")
            print("-" * 30)
            
            status = get_optimization_status()
            print(f"   System Active: {'✅ Yes' if status['system_active'] else '❌ No'}")
            print(f"   Monitoring Status: {status['current_performance']['monitoring_status']}")
            print(f"   Total Principles: {status['principles']['total_learned']}")
            
            # Demonstrate optimization cycle
            print("\n🔄 TRIGGERING OPTIMIZATION CYCLE:")
            print("-" * 40)
            
            optimization_result = await trigger_optimization_cycle()
            
            if optimization_result["status"] == "completed":
                print("✅ Optimization cycle completed!")
                phases = optimization_result["results"]["phases"]
                
                print(f"\n📋 PHASES EXECUTED:")
                for phase_name, phase_result in phases.items():
                    if isinstance(phase_result, dict):
                        if phase_name == "observation":
                            tools_count = len(phase_result.get("tools_analyzed", []))
                            print(f"   🔍 {phase_name.title()}: {tools_count} tools analyzed")
                        elif phase_name == "monitoring":
                            alerts = phase_result.get("active_alerts", 0) 
                            print(f"   📊 {phase_name.title()}: {alerts} alerts processed")
                        elif phase_name == "suggestions":
                            suggestions_count = len(phase_result) if isinstance(phase_result, list) else 0
                            print(f"   💡 {phase_name.title()}: {suggestions_count} suggestions generated")
                        elif phase_name == "implementation":
                            implemented = phase_result.get("implemented", 0)
                            total = phase_result.get("total_suggestions", 0)
                            print(f"   🔧 {phase_name.title()}: {implemented}/{total} implemented")
                        elif phase_name == "evaluation":
                            success_rate = phase_result.get("success_rate", 0)
                            print(f"   📈 {phase_name.title()}: {success_rate:.1%} success rate")
                            
                # Show principles learned
                principles_learned = optimization_result["results"].get("principles_learned", [])
                if principles_learned:
                    print(f"\n🎓 PRINCIPLES LEARNED: {len(principles_learned)}")
                    for principle_id in principles_learned:
                        print(f"   📜 {principle_id}")
            else:
                print(f"❌ Optimization failed: {optimization_result.get('error', 'Unknown error')}")
            
            # Generate insights
            print("\n🧠 SYSTEM INSIGHTS:")
            print("-" * 30)
            
            insights = get_system_insights()
            
            if insights["key_learnings"]:
                print("   Key Learnings:")
                for learning in insights["key_learnings"]:
                    print(f"   • {learning}")
                    
            if insights["success_patterns"]:
                print("   Success Patterns:")
                for pattern in insights["success_patterns"]:
                    print(f"   • {pattern}")
                    
            # Show principle effectiveness
            print("\n🎯 PRINCIPLE EFFECTIVENESS:")
            print("-" * 35)
            
            for principle_id, effectiveness in insights["principle_effectiveness"].items():
                recommendation = effectiveness["recommendation"].replace("_", " ").title()
                score = effectiveness["effectiveness_score"]
                print(f"   {effectiveness['title'][:30]:<30} {score:.2f} ({recommendation})")
            
        else:
            print(f"❌ Failed to start system: {init_result.get('message', 'Unknown error')}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   The self-optimization system may not be properly installed.")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        
    finally:
        print("\n" + "=" * 60)
        print("🏁 DEMONSTRATION COMPLETE")
        print("=" * 60)
        
        print("\n📖 SUMMARY OF OVERARCHING PRINCIPLES:")
        print("   1. Workflow-Centric Organization")
        print("   2. External LLM Compatibility First") 
        print("   3. Intelligence-Driven Decisions")
        print("   4. Dynamic Adaptation")
        print("   5. Hierarchical Tool Organization")
        
        print("\n🎯 These principles emerged from implementing the 5-workflow")
        print("   architecture and solving real constraints like GitHub Copilot's")
        print("   100-tool limit. They now guide all optimization decisions.")

if __name__ == "__main__":
    asyncio.run(demonstrate_self_optimization())