from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass

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

class SupervisorAgent:
    def __init__(self):
        self.agents = {}
        self.workflow = []
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
        
    def decide_next_agent(self, context: Dict[str, Any]) -> str:
        """Simple decision logic for next agent"""
        # Basic decision logic - could be enhanced with AI/ML
        agents = list(self.agents.keys())
        if not agents:
            return "no_agent"
        
        # Simple round-robin or context-based selection
        if "last_agent" in context:
            last_idx = agents.index(context["last_agent"])
            next_idx = (last_idx + 1) % len(agents)
            return agents[next_idx]
        return agents[0]
    
    def execute_agent(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific agent"""
        if agent_name not in self.agents:
            return {"error": f"Agent {agent_name} not found"}
        
        agent_func = self.agents[agent_name]
        try:
            result = agent_func(input_data)
            return {
                "agent": agent_name,
                "result": result,
                "status": "success"
            }
        except Exception as e:
            return {
                "agent": agent_name,
                "error": str(e),
                "status": "failed"
            }
    
    def run_workflow(self, initial_input: Dict[str, Any], max_steps: int = 10) -> List[Dict[str, Any]]:
        """Run the supervised workflow with escalation handling"""
        results = []
        context = initial_input.copy()
        
        for step in range(max_steps):
            # Decide next agent
            next_agent = self.decide_next_agent(context)
            
            # Execute agent
            result = self.execute_agent(next_agent, context)
            results.append(result)
            
            # Update context
            context["last_agent"] = next_agent
            context["step"] = step + 1
            
            # Check if workflow should stop
            if result.get("status") == "failed":
                # Handle blocked task with escalation
                task_id = f"task_{step}_{next_agent}"
                error = result.get("error", "Unknown error")
                escalation_result = self.handle_blocked_task(task_id, next_agent, error, context)
                results.append(escalation_result)
                
                # Stop workflow if manual intervention is required
                if escalation_result.get("status") == "escalated":
                    print(f"🚨 Workflow stopped: Task {task_id} requires manual intervention")
                    break
                
            if result.get("result", {}).get("completed"):
                break
        
        return results
    
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
            print(f"🔄 Retrying blocked task {blocked_task.task_id} (attempt {blocked_task.retry_count})")
            
            # Try to execute the agent again
            result = self.execute_agent(blocked_task.agent_name, blocked_task.context or {})
            
            if result.get("status") == "success":
                # Remove from blocked tasks if successful
                self.blocked_tasks.remove(blocked_task)
                print(f"✅ Task {blocked_task.task_id} unblocked after retry")
                return result
            else:
                # Escalate to next level if retry failed
                blocked_task.escalation_level = EscalationLevel.LEVEL_2
                return self._escalate_task(blocked_task)
        else:
            # Max retries reached, escalate to level 2
            blocked_task.escalation_level = EscalationLevel.LEVEL_2
            return self._escalate_task(blocked_task)
    
    def _handle_level2_escalation(self, blocked_task: BlockedTask) -> Dict[str, Any]:
        """Level 2 escalation: Supervisor intervention and alternative routing."""
        print(f"⚠️ Supervisor intervention for blocked task {blocked_task.task_id}")
        print(f"   Error: {blocked_task.error}")
        print(f"   Agent: {blocked_task.agent_name}")
        
        # Try to find an alternative agent
        alternative_agents = [name for name in self.agents.keys() 
                            if name != blocked_task.agent_name]
        
        if alternative_agents:
            # Try the first alternative agent
            alternative_agent = alternative_agents[0]
            print(f"   Trying alternative agent: {alternative_agent}")
            
            try:
                result = self.execute_agent(alternative_agent, blocked_task.context or {})
                if result.get("status") == "success":
                    self.blocked_tasks.remove(blocked_task)
                    print(f"✅ Task {blocked_task.task_id} completed with alternative agent")
                    return result
            except Exception as e:
                print(f"   Alternative agent also failed: {e}")
        
        # If alternative agents fail, escalate to level 3
        blocked_task.escalation_level = EscalationLevel.LEVEL_3
        return self._escalate_task(blocked_task)
    
    def _handle_level3_escalation(self, blocked_task: BlockedTask) -> Dict[str, Any]:
        """Level 3 escalation: Manual escalation to human supervisor."""
        print(f"🚨 CRITICAL: Task {blocked_task.task_id} requires manual intervention")
        print(f"   Task ID: {blocked_task.task_id}")
        print(f"   Original Agent: {blocked_task.agent_name}")
        print(f"   Error: {blocked_task.error}")
        print(f"   Context: {blocked_task.context}")
        
        # Create escalation record for manual review
        escalation_record = {
            "task_id": blocked_task.task_id,
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
            "message": f"Task {blocked_task.task_id} escalated for manual review"
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

# Example agents
def analysis_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Agent that analyzes input data"""
    print("Analysis agent: Analyzing input data...")
    # Simulate analysis
    analysis_result = {
        "data_quality": "good",
        "complexity": "medium",
        "recommendations": ["proceed_with_processing", "requires_validation"]
    }
    return {"analysis": analysis_result}

def processing_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Agent that processes data"""
    print("Processing agent: Processing data...")
    # Simulate processing
    processing_result = {
        "processed_items": 5,
        "success_rate": 0.95,
        "output_format": "structured"
    }
    return {"processing": processing_result}

def validation_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Agent that validates results"""
    print("Validation agent: Validating results...")
    # Simulate validation
    validation_result = {
        "is_valid": True,
        "confidence": 0.92,
        "completed": True
    }
    return {"validation": validation_result}

if __name__ == "__main__":
    # Create and configure supervisor
    supervisor = SupervisorAgent()
    
    # Register agents
    supervisor.register_agent("analyzer", analysis_agent)
    supervisor.register_agent("processor", processing_agent)
    supervisor.register_agent("validator", validation_agent)
    
    # Run workflow
    initial_input = {
        "task": "process_sample_data",
        "data": {"sample": "test_data"}
    }
    
    print("Starting supervised workflow...")
    results = supervisor.run_workflow(initial_input)
    
    print("\nWorkflow Results:")
    for i, result in enumerate(results):
        print(f"Step {i+1}: {result}")