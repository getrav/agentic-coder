#!/usr/bin/env python3
"""
Test script for RecoveryLoop functionality
Tests various failure scenarios and recovery strategies
"""

import asyncio
from langgraph_supervisor import LangGraphSupervisorAgent, decision_agent, validation_agent, output_agent
from recovery_loop import RecoveryStrategy

# Test agents that can fail
def unreliable_input_processing_agent(input_data):
    """Input processing agent that sometimes fails"""
    import random
    
    print("🔄 Input Processing: Processing input data...")
    
    # 30% chance of failure
    if random.random() < 0.3:
        raise Exception("Network timeout during input processing")
    
    processed = {
        "validated": True,
        "normalized": True,
        "data_type": "structured",
        "quality_score": 0.85
    }
    
    input_data["input_valid"] = True
    input_data["data_quality"] = "good"
    
    return {"processed_input": processed}

def flaky_analysis_agent(input_data):
    """Analysis agent that frequently fails"""
    import random
    
    print("🔍 Analysis: Analyzing data...")
    
    # 50% chance of failure
    if random.random() < 0.5:
        raise Exception("Analysis service unavailable")
    
    analysis = {
        "complexity": "medium",
        "risk_level": "low",
        "insights": ["pattern_detected", "outliers_found"],
        "confidence": 0.92
    }
    
    input_data["analysis_complete"] = True
    input_data["requires_execution"] = True
    
    return {"analysis_result": analysis}

def crash_prone_execution_agent(input_data):
    """Execution agent that often crashes"""
    import random
    
    print("⚡ Execution: Running main task...")
    
    # 60% chance of failure
    if random.random() < 0.6:
        raise Exception("Memory allocation failed")
    
    execution = {
        "output_items": 10,
        "success_rate": 0.98,
        "processing_time": 4.2,
        "status": "completed"
    }
    
    input_data["execution_complete"] = True
    input_data["ready_for_output"] = True
    
    return {"execution_result": execution}

async def test_recovery_loop():
    """Test the RecoveryLoop with failing agents"""
    print("🧪 Testing RecoveryLoop with Failing Agents")
    print("="*50)
    
    # Create supervisor with recovery enabled
    recovery_config = {
        "max_retries": 3,
        "default_strategy": "exponential_backoff",
        "base_delay_ms": 500,  # Faster for testing
        "max_delay_ms": 2000,
        "circuit_breaker_threshold": 2
    }
    
    supervisor = LangGraphSupervisorAgent(
        enable_recovery=True, 
        recovery_config=recovery_config
    )
    
    # Register unreliable agents
    supervisor.register_agent("input_processing", unreliable_input_processing_agent)
    supervisor.register_agent("analysis", flaky_analysis_agent)
    supervisor.register_agent("execution", crash_prone_execution_agent)
    supervisor.register_agent("decision", decision_agent)  # Add this
    supervisor.register_agent("validation", validation_agent)  # Add this
    supervisor.register_agent("output", output_agent)  # Add this
    
    # Register fallback agents
    supervisor.register_agent("input_processing_fallback", reliable_input_processing_agent, is_fallback=True)
    supervisor.register_agent("analysis_fallback", reliable_analysis_agent, is_fallback=True)
    supervisor.register_agent("execution_fallback", reliable_execution_agent, is_fallback=True)
    
    # Create workflow
    supervisor.create_workflow()
    
    # Test data
    test_input = {
        "task": "stress_test_recovery",
        "data": {"test": "recovery_scenarios"},
        "priority": "high"
    }
    
    print("🚀 Starting workflow with recovery...")
    result = await supervisor.run_workflow(test_input)
    
    # Print results
    print(f"\n✅ Completed Nodes: {len(result['completed_nodes'])}")
    print(f"🔄 Total Iterations: {result['total_iterations']}")
    print(f"📊 Execution Log Entries: {len(result['execution_log'])}")
    
    if result.get('recovery_stats'):
        stats = result['recovery_stats']
        print(f"\n🛟 RECOVERY STATISTICS:")
        print(f"   Total Recovery Attempts: {stats['total_attempts']}")
        print(f"   Successful Recoveries: {stats['successful_attempts']}")
        print(f"   Failed Recoveries: {stats['failed_attempts']}")
        print(f"   Recovery Success Rate: {stats['success_rate']:.2%}")
        print(f"   Average Recovery Time: {stats['average_duration_ms']:.2f}ms")
        
        print(f"\n🔧 Strategies Used:")
        for strategy, count in stats['strategies_used'].items():
            print(f"   {strategy}: {count} attempts")
        
        if stats['circuit_breakers']:
            print(f"\n⚡ Circuit Breaker Status:")
            for agent, cb_stats in stats['circuit_breakers'].items():
                status = "🔴 OPEN" if cb_stats['circuit_open'] else "🟢 CLOSED"
                print(f"   {agent}: {status} (failures: {cb_stats['failure_count']})")
    
    print(f"\n📋 Execution Details:")
    for log_entry in result['execution_log']:
        status_icon = "✅" if log_entry['status'] == 'completed' else "❌"
        print(f"   {status_icon} Iteration {log_entry['iteration']}: {log_entry['node']} - {log_entry['status']}")
        if 'error' in log_entry:
            print(f"      Error: {log_entry['error']}")

# Reliable fallback agents
def reliable_input_processing_agent(input_data):
    """Reliable fallback input processing agent"""
    print("🔄 Input Processing (Fallback): Using reliable processing...")
    
    processed = {
        "validated": True,
        "normalized": True,
        "data_type": "structured",
        "quality_score": 0.75
    }
    
    input_data["input_valid"] = True
    input_data["data_quality"] = "good"
    
    return {"processed_input": processed}

def reliable_analysis_agent(input_data):
    """Reliable fallback analysis agent"""
    print("🔍 Analysis (Fallback): Using reliable analysis...")
    
    analysis = {
        "complexity": "low",
        "risk_level": "low",
        "insights": ["basic_analysis"],
        "confidence": 0.8
    }
    
    input_data["analysis_complete"] = True
    input_data["requires_execution"] = True
    
    return {"analysis_result": analysis}

def reliable_execution_agent(input_data):
    """Reliable fallback execution agent"""
    print("⚡ Execution (Fallback): Using reliable execution...")
    
    execution = {
        "output_items": 8,
        "success_rate": 0.95,
        "processing_time": 6.0,
        "status": "completed"
    }
    
    input_data["execution_complete"] = True
    input_data["ready_for_output"] = True
    
    return {"execution_result": execution}

async def test_circuit_breaker():
    """Test circuit breaker functionality"""
    print("\n🔌 Testing Circuit Breaker")
    print("="*30)
    
    from recovery_loop import RecoveryLoop
    
    recovery_loop = RecoveryLoop(max_retries=1, circuit_breaker_threshold=2)
    recovery_loop.register_circuit_breaker("test_agent")
    
    def failing_agent(input_data):
        raise Exception("Always fails")
    
    # Trigger circuit breaker
    for i in range(3):
        result = await recovery_loop.execute_with_recovery(
            "test_agent",
            failing_agent,
            {"test": "data"},
            strategies=[RecoveryStrategy.EXPONENTIAL_BACKOFF]
        )
        print(f"Attempt {i+1}: {result['status']}")
    
    # Check circuit breaker stats
    stats = recovery_loop.get_recovery_stats()
    print(f"Circuit breaker open: {stats['circuit_breakers']['test_agent']['circuit_open']}")
    print(f"Failure count: {stats['circuit_breakers']['test_agent']['failure_count']}")

if __name__ == "__main__":
    async def run_all_tests():
        await test_recovery_loop()
        await test_circuit_breaker()
    
    asyncio.run(run_all_tests())