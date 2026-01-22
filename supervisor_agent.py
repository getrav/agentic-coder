from typing import Dict, List, Any, Optional, Callable

class SupervisorAgent:
    def __init__(self):
        self.agents = {}
        self.workflow = []
        
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
        """Run the supervised workflow"""
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
                break
            if result.get("result", {}).get("completed"):
                break
        
        return results

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