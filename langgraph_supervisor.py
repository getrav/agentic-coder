from typing import Dict, List, Any, Optional, Callable, TypedDict
from dataclasses import dataclass
from enum import Enum
import asyncio
from recovery_loop import RecoveryLoop, RecoveryStrategy

class AgentState(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class WorkflowNode:
    agent_name: str
    state: AgentState = AgentState.PENDING
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class WorkflowEdge:
    from_node: str
    to_node: str
    condition: str = "always"

class WorkflowGraph:
    def __init__(self):
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: List[WorkflowEdge] = []
        self.start_node: Optional[str] = None
        
    def add_node(self, name: str):
        self.nodes[name] = WorkflowNode(agent_name=name)
        
    def add_edge(self, from_node: str, to_node: str, condition: str = "always"):
        self.edges.append(WorkflowEdge(from_node, to_node, condition))
        
    def set_start_node(self, name: str):
        self.start_node = name
        if name not in self.nodes:
            self.add_node(name)

class LangGraphSupervisorAgent:
    def __init__(self, enable_recovery: bool = True, recovery_config: Optional[Dict[str, Any]] = None):
        self.agents: Dict[str, Callable] = {}
        self.graph = WorkflowGraph()
        self.workflow_state: Dict[str, Any] = {}
        self.alternative_agents: Dict[str, Callable] = {}
        
        # Initialize RecoveryLoop
        self.enable_recovery = enable_recovery
        if enable_recovery:
            recovery_config = recovery_config or {}
            self.recovery_loop = RecoveryLoop(
                max_retries=recovery_config.get('max_retries', 3),
                default_strategy=RecoveryStrategy(recovery_config.get('default_strategy', 'exponential_backoff')),
                base_delay_ms=recovery_config.get('base_delay_ms', 1000),
                max_delay_ms=recovery_config.get('max_delay_ms', 30000),
                circuit_breaker_threshold=recovery_config.get('circuit_breaker_threshold', 3)
            )
        else:
            self.recovery_loop = None
        
    def register_agent(self, name: str, agent_func: Callable, is_fallback: bool = False):
        """Register an agent with the supervisor"""
        if is_fallback:
            self.alternative_agents[name] = agent_func
        else:
            self.agents[name] = agent_func
            # Register circuit breaker for primary agents if recovery is enabled
            if self.enable_recovery and self.recovery_loop:
                self.recovery_loop.register_circuit_breaker(name)
        
    def create_workflow(self):
        """Create a sample workflow graph"""
        # Create nodes
        self.graph.add_node("input_processing")
        self.graph.add_node("analysis")
        self.graph.add_node("decision")
        self.graph.add_node("execution")
        self.graph.add_node("validation")
        self.graph.add_node("output")
        
        # Set start node
        self.graph.set_start_node("input_processing")
        
        # Create edges (workflow connections)
        self.graph.add_edge("input_processing", "analysis", "input_valid")
        self.graph.add_edge("analysis", "decision", "analysis_complete")
        self.graph.add_edge("decision", "execution", "requires_execution")
        self.graph.add_edge("decision", "output", "ready_for_output")
        self.graph.add_edge("execution", "validation", "execution_complete")
        self.graph.add_edge("validation", "output", "validation_passed")
        self.graph.add_edge("validation", "analysis", "validation_failed")
        
    def evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate edge condition"""
        if condition == "always":
            return True
        elif condition == "input_valid":
            return context.get("input_valid", True)
        elif condition == "analysis_complete":
            return context.get("analysis_complete", True)
        elif condition == "requires_execution":
            return context.get("requires_execution", True)
        elif condition == "ready_for_output":
            return context.get("ready_for_output", False)
        elif condition == "execution_complete":
            return context.get("execution_complete", False)
        elif condition == "validation_passed":
            return context.get("validation_passed", True)
        elif condition == "validation_failed":
            return not context.get("validation_passed", False)
        return False
    
    def get_next_nodes(self, current_node: str) -> List[str]:
        """Get next nodes based on current node and conditions"""
        next_nodes = []
        for edge in self.graph.edges:
            if edge.from_node == current_node:
                if self.evaluate_condition(edge.condition, self.workflow_state):
                    next_nodes.append(edge.to_node)
        return next_nodes
    
    async def execute_node(self, node_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node/agent with recovery if enabled"""
        node = self.graph.nodes[node_name]
        node.state = AgentState.RUNNING
        node.input_data = input_data
        
        try:
            if node_name not in self.agents:
                raise Exception(f"Agent {node_name} not found")
            
            agent_func = self.agents[node_name]
            
            # Use recovery loop if enabled
            if self.enable_recovery and self.recovery_loop:
                recovery_strategies = [
                    RecoveryStrategy.EXPONENTIAL_BACKOFF,
                    RecoveryStrategy.ALTERNATIVE_AGENT,
                    RecoveryStrategy.FALLBACK_DEFAULT
                ]
                
                fallback_result = {"status": "fallback_executed", "data": input_data}
                
                result = await self.recovery_loop.execute_with_recovery(
                    agent_name=node_name,
                    agent_func=agent_func,
                    input_data=input_data,
                    strategies=recovery_strategies,
                    alternative_agents=self.alternative_agents,
                    fallback_result=fallback_result
                )
                
                # Update node state based on recovery result
                if result.get("status") == "success":
                    node.state = AgentState.COMPLETED
                    node.output_data = result["result"]
                    return result["result"]
                elif result.get("status") == "fallback":
                    node.state = AgentState.COMPLETED
                    node.output_data = result["result"]
                    return result["result"]
                else:
                    node.state = AgentState.FAILED
                    node.error = result.get("error", "Recovery failed")
                    raise Exception(node.error)
            else:
                # Original execution logic without recovery
                if asyncio.iscoroutinefunction(agent_func):
                    result = await agent_func(input_data)
                else:
                    result = agent_func(input_data)
                
                node.output_data = result
                node.state = AgentState.COMPLETED
                return result
                
        except Exception as e:
            node.state = AgentState.FAILED
            node.error = str(e)
            raise
    
    async def run_workflow(self, initial_input: Dict[str, Any], max_iterations: int = 20) -> Dict[str, Any]:
        """Run the workflow using LangGraph-style execution"""
        if not self.graph.nodes:
            self.create_workflow()
            
        self.workflow_state = initial_input.copy()
        execution_log = []
        completed_nodes = set()
        
        if self.graph.start_node is None:
            raise ValueError("No start node defined in workflow graph")
        
        current_nodes: List[str] = [self.graph.start_node]
        iteration = 0
        
        while current_nodes and iteration < max_iterations:
            iteration += 1
            next_nodes: List[str] = []
            
            for node_name in current_nodes:
                if node_name in completed_nodes:
                    continue
                    
                try:
                    # Execute current node
                    result = await self.execute_node(node_name, self.workflow_state)
                    
                    # Update workflow state
                    self.workflow_state[f"{node_name}_result"] = result
                    execution_log.append({
                        "iteration": iteration,
                        "node": node_name,
                        "status": "completed",
                        "result": result
                    })
                    
                    completed_nodes.add(node_name)
                    
                    # Get next nodes
                    next_candidates = self.get_next_nodes(node_name)
                    for next_node in next_candidates:
                        if next_node not in completed_nodes:
                            next_nodes.append(next_node)
                            
                except Exception as e:
                    execution_log.append({
                        "iteration": iteration,
                        "node": node_name,
                        "status": "failed",
                        "error": str(e)
                    })
                    # Don't stop execution on failure when recovery is enabled - continue with other nodes
                    if not self.enable_recovery:
                        break
            
            # Remove duplicates from next nodes
            current_nodes = list(set(next_nodes))
            
            # If no next nodes, workflow is complete
            if not current_nodes:
                break
        
        return {
            "workflow_state": self.workflow_state,
            "execution_log": execution_log,
            "completed_nodes": list(completed_nodes),
            "total_iterations": iteration,
            "recovery_stats": self.get_recovery_stats() if self.enable_recovery else None
        }
    
    def get_recovery_stats(self) -> Optional[Dict[str, Any]]:
        """Get recovery statistics if recovery is enabled"""
        if self.enable_recovery and self.recovery_loop:
            return self.recovery_loop.get_recovery_stats()
        return None
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers"""
        if self.enable_recovery and self.recovery_loop:
            self.recovery_loop.reset_circuit_breakers()

# Example agents for the workflow
def input_processing_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process and validate input data"""
    print("🔄 Input Processing: Processing input data...")
    
    # Simulate input validation
    raw_input = input_data.get("data", {})
    processed = {
        "validated": True,
        "normalized": True,
        "data_type": "structured",
        "quality_score": 0.85
    }
    
    input_data["input_valid"] = True
    input_data["data_quality"] = "good"
    
    return {"processed_input": processed}

def analysis_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the processed input"""
    print("🔍 Analysis: Analyzing data...")
    
    analysis = {
        "complexity": "medium",
        "risk_level": "low",
        "insights": ["pattern_detected", "outliers_found"],
        "confidence": 0.92
    }
    
    input_data["analysis_complete"] = True
    input_data["requires_execution"] = True
    
    return {"analysis_result": analysis}

def decision_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Make decisions based on analysis"""
    print("🤔 Decision: Making workflow decisions...")
    
    decision = {
        "action": "execute",
        "priority": "high",
        "estimated_duration": 5,
        "resources_needed": ["cpu", "memory"]
    }
    
    return {"decision": decision}

def execution_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the main task"""
    print("⚡ Execution: Running main task...")
    
    execution = {
        "output_items": 10,
        "success_rate": 0.98,
        "processing_time": 4.2,
        "status": "completed"
    }
    
    input_data["execution_complete"] = True
    input_data["ready_for_output"] = True
    
    return {"execution_result": execution}

def validation_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate execution results"""
    print("✅ Validation: Validating results...")
    
    validation = {
        "is_valid": True,
        "accuracy": 0.96,
        "completeness": 1.0,
        "issues_found": []
    }
    
    input_data["validation_passed"] = True
    
    return {"validation_result": validation}

def output_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate final output"""
    print("📤 Output: Generating final output...")
    
    output = {
        "status": "success",
        "summary": "Workflow completed successfully",
        "results": {
            "total_items_processed": 10,
            "success_rate": 0.98,
            "execution_time": 4.2
        }
    }
    
    return {"final_output": output}

# Fallback agents for recovery
def input_processing_fallback_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback input processing agent"""
    print("🔄 Input Processing (Fallback): Using simplified processing...")
    
    processed = {
        "validated": True,
        "normalized": False,  # Simplified processing
        "data_type": "basic",
        "quality_score": 0.6  # Lower quality for fallback
    }
    
    return {"processed_input": processed}

def analysis_fallback_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback analysis agent"""
    print("🔍 Analysis (Fallback): Using basic analysis...")
    
    analysis = {
        "complexity": "low",
        "risk_level": "unknown",
        "insights": ["basic_analysis_only"],
        "confidence": 0.5  # Lower confidence for fallback
    }
    
    return {"analysis_result": analysis}

async def main():
    # Create LangGraph-style Supervisor Agent
    supervisor = LangGraphSupervisorAgent(enable_recovery=True)
    
    # Register all agents
    supervisor.register_agent("input_processing", input_processing_agent)
    supervisor.register_agent("analysis", analysis_agent)
    supervisor.register_agent("decision", decision_agent)
    supervisor.register_agent("execution", execution_agent)
    supervisor.register_agent("validation", validation_agent)
    supervisor.register_agent("output", output_agent)
    
    # Register some fallback agents
    supervisor.register_agent("input_processing_fallback", input_processing_fallback_agent, is_fallback=True)
    supervisor.register_agent("analysis_fallback", analysis_fallback_agent, is_fallback=True)
    
    # Create workflow graph
    supervisor.create_workflow()
    
    # Run the workflow
    initial_input = {
        "task": "process_complex_data",
        "data": {"sample": "test_data", "format": "json"},
        "priority": "high"
    }
    
    print("🚀 Starting LangGraph-style Supervised Workflow with Recovery...")
    result = await supervisor.run_workflow(initial_input)
    
    print("\n" + "="*50)
    print("📋 WORKFLOW EXECUTION SUMMARY")
    print("="*50)
    
    print(f"✅ Completed Nodes: {len(result['completed_nodes'])}")
    print(f"🔄 Total Iterations: {result['total_iterations']}")
    print(f"📊 Execution Log Entries: {len(result['execution_log'])}")
    
    # Print recovery stats if available
    if result.get('recovery_stats'):
        stats = result['recovery_stats']
        print(f"🛟 Recovery Attempts: {stats['total_attempts']}")
        print(f"🛟 Recovery Success Rate: {stats['success_rate']:.2%}")
    
    print("\n🔍 Execution Details:")
    for log_entry in result['execution_log']:
        status_icon = "✅" if log_entry['status'] == 'completed' else "❌"
        print(f"  {status_icon} Iteration {log_entry['iteration']}: {log_entry['node']} - {log_entry['status']}")
    
    print("\n🎯 Final Workflow State:")
    for key, value in result['workflow_state'].items():
        if not key.startswith('_'):
            print(f"  {key}: {value}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())