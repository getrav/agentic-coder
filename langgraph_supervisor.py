from typing import Dict, List, Any, Optional, Callable, TypedDict
from dataclasses import dataclass
from enum import Enum

class AgentState(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class EscalationLevel(Enum):
    """Escalation levels for blocked tasks."""
    LEVEL_1 = "level_1"  # Automatic retry
    LEVEL_2 = "level_2"  # Supervisor intervention
    LEVEL_3 = "level_3"  # Manual escalation

@dataclass
class BlockedTask:
    """Represents a blocked task that needs escalation."""
    task_id: str
    agent_name: str
    error: str
    escalation_level: EscalationLevel
    retry_count: int = 0
    max_retries: int = 3
    context: Optional[Dict[str, Any]] = None

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
        self.blocked_tasks: List[BlockedTask] = []
        self.escalation_handlers: Dict[EscalationLevel, Callable] = {}
        self._setup_default_escalation_handlers()
    
    def _setup_default_escalation_handlers(self):
        """Setup default escalation handlers."""
        self.escalation_handlers[EscalationLevel.LEVEL_1] = self._handle_level1_escalation
        self.escalation_handlers[EscalationLevel.LEVEL_2] = self._handle_level2_escalation
        self.escalation_handlers[EscalationLevel.LEVEL_3] = self._handle_level3_escalation
        
    def register_agent(self, name: str, agent_func: Callable):
        """Register an agent with the supervisor"""
        self.agents[name] = agent_func
        
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
        
        try:
            if node_name in self.agents:
                result = self.agents[node_name](input_data)
                node.output_data = result
                node.state = AgentState.COMPLETED
                return result
            else:
                raise Exception(f"Agent {node_name} not found")
        except Exception as e:
            node.state = AgentState.BLOCKED
            node.error = str(e)
            # Handle blocked task with escalation
            task_id = f"node_{node_name}"
            escalation_result = self.handle_blocked_task(task_id, node_name, str(e), input_data)
            # Return escalation result instead of raising exception
            return escalation_result
    
    def handle_blocked_task(self, task_id: str, agent_name: str, error: str, 
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a blocked task by escalating it appropriately."""
        # Create blocked task record
        blocked_task = BlockedTask(
            task_id=task_id,
            agent_name=agent_name,
            error=error,
            escalation_level=EscalationLevel.LEVEL_1,
            context=context
        )
        
        # Add to blocked tasks list
        self.blocked_tasks.append(blocked_task)
        
        # Handle escalation
        return self._escalate_task(blocked_task)
    
    def _escalate_task(self, blocked_task: BlockedTask) -> Dict[str, Any]:
        """Escalate a blocked task using appropriate handler."""
        handler = self.escalation_handlers.get(blocked_task.escalation_level)
        if handler:
            return handler(blocked_task)
        else:
            return {
                "status": "failed",
                "error": f"No escalation handler for level {blocked_task.escalation_level}",
                "task_id": blocked_task.task_id
            }
    
    def _handle_level1_escalation(self, blocked_task: BlockedTask) -> Dict[str, Any]:
        """Level 1 escalation: Automatic retry with limited attempts."""
        if blocked_task.retry_count < blocked_task.max_retries:
            blocked_task.retry_count += 1
            print(f"🔄 Retrying blocked node {blocked_task.task_id} (attempt {blocked_task.retry_count})")
            
            # Try to execute the agent again
            try:
                result = self.agents[blocked_task.agent_name](blocked_task.context or {})
                
                if result:
                    # Remove from blocked tasks if successful
                    if blocked_task in self.blocked_tasks:
                        self.blocked_tasks.remove(blocked_task)
                    print(f"✅ Node {blocked_task.task_id} unblocked after retry")
                    return {"status": "success", "result": result, "retry_success": True}
            except Exception as e:
                print(f"❌ Retry failed for node {blocked_task.task_id}: {e}")
            
            # Escalate to next level if retry failed
            blocked_task.escalation_level = EscalationLevel.LEVEL_2
            return self._escalate_task(blocked_task)
        else:
            # Max retries reached, escalate to level 2
            blocked_task.escalation_level = EscalationLevel.LEVEL_2
            return self._escalate_task(blocked_task)
    
    def _handle_level2_escalation(self, blocked_task: BlockedTask) -> Dict[str, Any]:
        """Level 2 escalation: Supervisor intervention and alternative routing."""
        print(f"⚠️ Supervisor intervention for blocked node {blocked_task.task_id}")
        print(f"   Error: {blocked_task.error}")
        print(f"   Node: {blocked_task.agent_name}")
        
        # Try to find an alternative node/path
        alternative_nodes = [name for name in self.agents.keys() 
                           if name != blocked_task.agent_name]
        
        if alternative_nodes:
            # Try the first alternative node
            alternative_node = alternative_nodes[0]
            print(f"   Trying alternative node: {alternative_node}")
            
            try:
                result = self.agents[alternative_node](blocked_task.context or {})
                if result:
                    if blocked_task in self.blocked_tasks:
                        self.blocked_tasks.remove(blocked_task)
                    print(f"✅ Node {blocked_task.task_id} completed with alternative")
                    return {"status": "success", "result": result, "alternative_used": alternative_node}
            except Exception as e:
                print(f"   Alternative node also failed: {e}")
        
        # If alternative nodes fail, escalate to level 3
        blocked_task.escalation_level = EscalationLevel.LEVEL_3
        return self._escalate_task(blocked_task)
    
    def _handle_level3_escalation(self, blocked_task: BlockedTask) -> Dict[str, Any]:
        """Level 3 escalation: Manual escalation to human supervisor."""
        print(f"🚨 CRITICAL: Node {blocked_task.task_id} requires manual intervention")
        print(f"   Node ID: {blocked_task.task_id}")
        print(f"   Original Node: {blocked_task.agent_name}")
        print(f"   Error: {blocked_task.error}")
        print(f"   Context: {blocked_task.context}")
        
        # Create escalation record for manual review
        escalation_record = {
            "node_id": blocked_task.task_id,
            "agent_name": blocked_task.agent_name,
            "error": blocked_task.error,
            "escalation_level": blocked_task.escalation_level.value,
            "timestamp": "manual",
            "status": "awaiting_human_intervention",
            "requires_manual_review": True
        }
        
        return {
            "status": "escalated",
            "escalation_record": escalation_record,
            "message": f"Node {blocked_task.task_id} escalated for manual review"
        }
    
    def get_blocked_tasks(self) -> List[Dict[str, Any]]:
        """Get list of currently blocked tasks."""
        return [
            {
                "task_id": task.task_id,
                "agent_name": task.agent_name,
                "error": task.error,
                "escalation_level": task.escalation_level.value,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries
            }
            for task in self.blocked_tasks
        ]
    
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
        
        return {
            "workflow_state": self.workflow_state,
            "execution_log": execution_log,
            "completed_nodes": list(completed_nodes),
            "total_iterations": iteration
        }

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
    
    print("🚀 Starting LangGraph-style Supervised Workflow...")
    result = supervisor.run_workflow(initial_input)
    
    print("\n" + "="*50)
    print("📋 WORKFLOW EXECUTION SUMMARY")
    print("="*50)
    
    print(f"✅ Completed Nodes: {len(result['completed_nodes'])}")
    print(f"🔄 Total Iterations: {result['total_iterations']}")
    print(f"📊 Execution Log Entries: {len(result['execution_log'])}")
    
    print("\n🔍 Execution Details:")
    for log_entry in result['execution_log']:
        status_icon = "✅" if log_entry['status'] == 'completed' else "❌"
        print(f"  {status_icon} Iteration {log_entry['iteration']}: {log_entry['node']} - {log_entry['status']}")
    
    print("\n🎯 Final Workflow State:")
    for key, value in result['workflow_state'].items():
        if not key.startswith('_'):
            print(f"  {key}: {value}")