from typing import Dict, List, Any, Optional, Callable, TypedDict
from dataclasses import dataclass
from enum import Enum
from structured_logger import get_logger, LogLevel

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
    def __init__(self):
        self.agents: Dict[str, Callable] = {}
        self.graph = WorkflowGraph()
        self.workflow_state: Dict[str, Any] = {}
        self.logger = get_logger("langgraph_supervisor")
        
    def register_agent(self, name: str, agent_func: Callable):
        """Register an agent with the supervisor"""
        self.agents[name] = agent_func
        self.logger.debug("Agent registered", agent_name=name)
        
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
    
    def execute_node(self, node_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node/agent"""
        node = self.graph.nodes[node_name]
        node.state = AgentState.RUNNING
        node.input_data = input_data
        
        self.logger.info("Executing node", 
                        node_name=node_name, 
                        state="running",
                        input_keys=list(input_data.keys()))
        
        try:
            if node_name in self.agents:
                result = self.agents[node_name](input_data)
                node.output_data = result
                node.state = AgentState.COMPLETED
                self.logger.debug("Node execution completed", 
                                 node_name=node_name,
                                 state="completed")
                return result
            else:
                raise Exception(f"Agent {node_name} not found")
        except Exception as e:
            node.state = AgentState.FAILED
            node.error = str(e)
            self.logger.error("Node execution failed", 
                            node_name=node_name,
                            state="failed",
                            error=str(e))
            raise
    
    def run_workflow(self, initial_input: Dict[str, Any], max_iterations: int = 20) -> Dict[str, Any]:
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
        
        self.logger.info("Starting workflow execution",
                        start_node=self.graph.start_node,
                        initial_input_keys=list(initial_input.keys()),
                        max_iterations=max_iterations)
        
        while current_nodes and iteration < max_iterations:
            iteration += 1
            next_nodes: List[str] = []
            
            for node_name in current_nodes:
                if node_name in completed_nodes:
                    continue
                    
                try:
                    # Execute current node
                    result = self.execute_node(node_name, self.workflow_state)
                    
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
                    # Stop execution on failure
                    break
            
            # Remove duplicates from next nodes
            current_nodes = list(set(next_nodes))
            
            # If no next nodes, workflow is complete
            if not current_nodes:
                break
        
        result = {
            "workflow_state": self.workflow_state,
            "execution_log": execution_log,
            "completed_nodes": list(completed_nodes),
            "total_iterations": iteration
        }
        
        self.logger.info("Workflow execution completed",
                        completed_nodes_count=len(completed_nodes),
                        total_iterations=iteration,
                        execution_log_entries=len(execution_log))
        
        return result

# Example agents for the workflow
def input_processing_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process and validate input data"""
    logger = get_logger("input_processing_agent")
    logger.info("Processing input data", 
               input_keys=list(input_data.keys()))
    
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
    
    logger.debug("Input processing completed", 
                processed_keys=list(processed.keys()),
                quality_score=processed["quality_score"])
    
    return {"processed_input": processed}

def analysis_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the processed input"""
    logger = get_logger("analysis_agent")
    logger.info("Analyzing input data")
    
    analysis = {
        "complexity": "medium",
        "risk_level": "low",
        "insights": ["pattern_detected", "outliers_found"],
        "confidence": 0.92
    }
    
    input_data["analysis_complete"] = True
    input_data["requires_execution"] = True
    
    logger.debug("Analysis completed", 
                complexity=analysis["complexity"],
                risk_level=analysis["risk_level"],
                confidence=analysis["confidence"])
    
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
    logger = get_logger("execution_agent")
    logger.info("Executing main task")
    
    execution = {
        "output_items": 10,
        "success_rate": 0.98,
        "processing_time": 4.2,
        "status": "completed"
    }
    
    input_data["execution_complete"] = True
    input_data["ready_for_output"] = True
    
    logger.debug("Task execution completed", 
                output_items=execution["output_items"],
                success_rate=execution["success_rate"],
                processing_time=execution["processing_time"])
    
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

if __name__ == "__main__":
    # Create LangGraph-style Supervisor Agent
    supervisor = LangGraphSupervisorAgent()
    
    # Register all agents
    supervisor.register_agent("input_processing", input_processing_agent)
    supervisor.register_agent("analysis", analysis_agent)
    supervisor.register_agent("decision", decision_agent)
    supervisor.register_agent("execution", execution_agent)
    supervisor.register_agent("validation", validation_agent)
    supervisor.register_agent("output", output_agent)
    
    # Create workflow graph
    supervisor.create_workflow()
    
    # Run the workflow
    initial_input = {
        "task": "process_complex_data",
        "data": {"sample": "test_data", "format": "json"},
        "priority": "high"
    }
    
    logger = get_logger("demo")
    logger.info("Starting LangGraph-style Supervised Workflow",
               demo_type="langgraph_supervisor")
    
    result = supervisor.run_workflow(initial_input)
    
    logger.info("Workflow execution summary",
               completed_nodes_count=len(result['completed_nodes']),
               total_iterations=result['total_iterations'],
               execution_log_entries=len(result['execution_log']))
    
    # Log execution details
    for log_entry in result['execution_log']:
        logger.debug("Execution detail",
                    iteration=log_entry['iteration'],
                    node=log_entry['node'],
                    status=log_entry['status'])
    
    logger.info("Final workflow state",
               state_keys=[k for k in result['workflow_state'].keys() if not k.startswith('_')])
    
    print("\n" + "="*50)
    print("📋 WORKFLOW EXECUTION SUMMARY")
    print("="*50)
    print(f"✅ Completed Nodes: {len(result['completed_nodes'])}")
    print(f"🔄 Total Iterations: {result['total_iterations']}")
    print(f"📊 Execution Log Entries: {len(result['execution_log'])}")