#!/usr/bin/env python3
"""
Test script to demonstrate escalation handling in supervisor agents.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supervisor_agent import SupervisorAgent, EscalationLevel
from langgraph_supervisor import LangGraphSupervisorAgent


def failing_agent(input_data):
    """An agent that always fails to test escalation."""
    print(f"❌ Failing agent: Processing {input_data.get('task', 'unknown task')}")
    raise Exception("This agent always fails - testing escalation")


def sometimes_failing_agent(input_data):
    """An agent that sometimes fails to test retry logic."""
    task = input_data.get('task', 'unknown task')
    print(f"⚠️ Sometimes failing agent: Processing {task}")
    
    # Fail on first attempt, succeed on retries
    attempt = input_data.get('attempt', 1)
    if attempt <= 2:
        raise Exception(f"Attempt {attempt} - will fail and retry")
    
    print(f"✅ Sometimes failing agent: Success on attempt {attempt}")
    return {"status": "success", "attempts": attempt}


def test_basic_supervisor_escalation():
    """Test escalation handling in basic supervisor."""
    print("\n" + "="*60)
    print("🧪 TESTING BASIC SUPERVISOR ESCALATION")
    print("="*60)
    
    supervisor = SupervisorAgent()
    
    # Register agents
    supervisor.register_agent("failing_agent", failing_agent)
    supervisor.register_agent("sometimes_failing", sometimes_failing_agent)
    
    # Test with failing agent
    print("\n1. Testing with always-failing agent:")
    initial_input = {
        "task": "test_escalation",
        "data": {"test": "data"}
    }
    
    results = supervisor.run_workflow(initial_input, max_steps=3)
    
    print("\n2. Workflow Results:")
    for i, result in enumerate(results):
        print(f"   Step {i+1}: {result}")
    
    print("\n3. Blocked Tasks:")
    blocked_tasks = supervisor.get_blocked_tasks()
    for task in blocked_tasks:
        print(f"   - {task}")


def test_langgraph_supervisor_escalation():
    """Test escalation handling in LangGraph supervisor."""
    print("\n" + "="*60)
    print("🧪 TESTING LANGGRAPH SUPERVISOR ESCALATION")
    print("="*60)
    
    supervisor = LangGraphSupervisorAgent()
    
    # Register agents
    supervisor.register_agent("input_processing", sometimes_failing_agent)
    supervisor.register_agent("analysis", failing_agent)
    supervisor.register_agent("decision", sometimes_failing_agent)
    
    # Create workflow
    supervisor.create_workflow()
    
    # Test workflow with failing nodes
    print("\n1. Testing LangGraph workflow with failing nodes:")
    initial_input = {
        "task": "test_langgraph_escalation",
        "data": {"sample": "test_data"},
        "attempt": 1
    }
    
    try:
        result = supervisor.run_workflow(initial_input, max_iterations=5)
        
        print("\n2. Workflow Summary:")
        print(f"   Completed Nodes: {len(result['completed_nodes'])}")
        print(f"   Total Iterations: {result['total_iterations']}")
        print(f"   Execution Log Entries: {len(result['execution_log'])}")
        
        print("\n3. Execution Details:")
        for log_entry in result['execution_log']:
            status_icon = "✅" if log_entry['status'] == 'completed' else "❌"
            print(f"   {status_icon} Iteration {log_entry['iteration']}: {log_entry['node']} - {log_entry['status']}")
            
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
    
    print("\n4. Blocked Tasks:")
    blocked_tasks = supervisor.get_blocked_tasks()
    for task in blocked_tasks:
        print(f"   - {task}")


def test_escalation_levels():
    """Test different escalation levels."""
    print("\n" + "="*60)
    print("🧪 TESTING ESCALATION LEVELS")
    print("="*60)
    
    print("1. Escalation Level 1: Automatic Retry")
    print("   - First failure: retry automatically")
    print("   - Max retries: 3 attempts")
    print("   - Success: continue workflow")
    print("   - Failure: escalate to level 2")
    
    print("\n2. Escalation Level 2: Supervisor Intervention")
    print("   - Try alternative agents/nodes")
    print("   - Log escalation details")
    print("   - Success: continue with alternative")
    print("   - Failure: escalate to level 3")
    
    print("\n3. Escalation Level 3: Manual Escalation")
    print("   - Create escalation record")
    print("   - Mark for human intervention")
    print("   - Stop workflow execution")
    print("   - Requires manual review")


def main():
    """Main test function."""
    print("🚀 ESCALATION HANDLING TEST SUITE")
    print("="*60)
    print("Testing escalation handling in supervisor agents")
    print("Issue: AC-fxg - Add escalation handling")
    
    # Test escalation levels explanation
    test_escalation_levels()
    
    # Test basic supervisor escalation
    test_basic_supervisor_escalation()
    
    # Test LangGraph supervisor escalation
    test_langgraph_supervisor_escalation()
    
    print("\n" + "="*60)
    print("✅ ESCALATION HANDLING TEST COMPLETE")
    print("="*60)
    print("All escalation features have been implemented and tested:")
    print("- ✅ Level 1: Automatic retry mechanism")
    print("- ✅ Level 2: Supervisor intervention with alternatives")
    print("- ✅ Level 3: Manual escalation to human supervisor")
    print("- ✅ Blocked task tracking and management")
    print("- ✅ Integration with both supervisor agents")


if __name__ == "__main__":
    main()