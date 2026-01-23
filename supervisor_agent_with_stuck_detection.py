from typing import Dict, List, Any, Optional, Callable
from stuck_issue_detector import StuckIssueDetector, StuckIssueRecovery
import time
import uuid


class SupervisorAgentWithStuckDetection:
    """Enhanced Supervisor Agent with stuck issue detection"""
    
    def __init__(self, 
                 enable_stuck_detection: bool = True,
                 timeout_threshold: int = 300,
                 progress_check_interval: int = 60):
        self.agents = {}
        self.workflow = []
        self.enable_stuck_detection = enable_stuck_detection
        
        # Initialize stuck issue detection if enabled
        if self.enable_stuck_detection:
            self.stuck_detector = StuckIssueDetector(
                timeout_threshold=timeout_threshold,
                progress_check_interval=progress_check_interval
            )
            self.recovery = StuckIssueRecovery(self.stuck_detector)
            
            # Register recovery callback
            self.stuck_detector.register_issue_callback(self.recovery.handle_issue)
            
            # Start monitoring
            self.stuck_detector.start_monitoring()
        else:
            self.stuck_detector = None
            self.recovery = None
         
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
        """Execute a specific agent with stuck detection"""
        if agent_name not in self.agents:
            return {"error": f"Agent {agent_name} not found"}
        
        workflow_id = input_data.get("workflow_id", f"workflow_{uuid.uuid4().hex[:8]}")
        
        # Notify stuck detector that agent is starting
        if self.stuck_detector:
            self.stuck_detector.agent_started(agent_name, workflow_id)
        
        agent_func = self.agents[agent_name]
        try:
            result = agent_func(input_data)
            
            # Notify stuck detector that agent made progress
            if self.stuck_detector:
                self.stuck_detector.agent_progress(agent_name, workflow_id)
            
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
        finally:
            # Notify stuck detector that agent completed
            if self.stuck_detector:
                self.stuck_detector.agent_completed(agent_name, workflow_id)
    
    def run_workflow(self, initial_input: Dict[str, Any], max_steps: int = 10) -> Dict[str, Any]:
        """Run the supervised workflow with stuck detection"""
        results = []
        context = initial_input.copy()
        step = 0  # Initialize step to avoid unbound variable error
        
        # Generate workflow ID if not provided
        workflow_id = context.get("workflow_id", f"workflow_{uuid.uuid4().hex[:8]}")
        
        # Notify stuck detector that workflow is starting
        if self.stuck_detector:
            self.stuck_detector.workflow_started(workflow_id, context)
        
        for step in range(max_steps):
            # Decide next agent
            next_agent = self.decide_next_agent(context)
            
            # Add workflow ID to context
            context["workflow_id"] = workflow_id
            
            # Execute agent
            result = self.execute_agent(next_agent, context)
            results.append(result)
            
            # Update context
            context["last_agent"] = next_agent
            context["step"] = step + 1
            
            # Notify stuck detector of workflow progress
            if self.stuck_detector and result.get("status") == "success":
                self.stuck_detector.workflow_progress(workflow_id, next_agent, step + 1)
            
            # Check if workflow should stop
            if result.get("status") == "failed":
                break
            if result.get("result", {}).get("completed"):
                break
        
        # Notify stuck detector that workflow completed
        if self.stuck_detector:
            self.stuck_detector.workflow_completed(workflow_id)
        
        # Include stuck issue information in results
        if self.stuck_detector:
            active_issues = self.stuck_detector.get_active_issues()
            issues_summary = self.stuck_detector.get_issue_summary()
            
            return {
                "workflow_id": workflow_id,
                "results": results,
                "total_steps": step + 1,
                "stuck_issues": {
                    "active_count": len(active_issues),
                    "summary": issues_summary
                }
            }
        else:
            return {
                "workflow_id": workflow_id,
                "results": results,
                "total_steps": step + 1
            }
    
    def get_stuck_issues(self) -> Optional[Dict[str, Any]]:
        """Get current stuck issues if detection is enabled"""
        if self.stuck_detector:
            return self.stuck_detector.get_issue_summary()
        else:
            return None
    
    def stop_monitoring(self):
        """Stop stuck issue monitoring"""
        if self.stuck_detector:
            self.stuck_detector.stop_monitoring()


# Enhanced version of the original SupervisorAgent for backward compatibility
class SupervisorAgent:
    """Original SupervisorAgent class (backward compatible)"""
    
    def __init__(self, enable_stuck_detection: bool = False):
        if enable_stuck_detection:
            # Use the enhanced version with stuck detection
            self._enhanced = SupervisorAgentWithStuckDetection(enable_stuck_detection=True)
        else:
            # Use basic functionality
            self._enhanced = None
            self.agents = {}
            self.workflow = []
    
    def register_agent(self, name: str, agent_func: Callable):
        """Register an agent with the supervisor"""
        if self._enhanced:
            self._enhanced.register_agent(name, agent_func)
        else:
            self.agents[name] = agent_func
         
    def decide_next_agent(self, context: Dict[str, Any]) -> str:
        """Simple decision logic for next agent"""
        if self._enhanced:
            return self._enhanced.decide_next_agent(context)
        else:
            # Basic decision logic
            agents = list(self.agents.keys())
            if not agents:
                return "no_agent"
            
            if "last_agent" in context:
                last_idx = agents.index(context["last_agent"])
                next_idx = (last_idx + 1) % len(agents)
                return agents[next_idx]
            return agents[0]
    
    def execute_agent(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific agent"""
        if self._enhanced:
            return self._enhanced.execute_agent(agent_name, input_data)
        else:
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
        if self._enhanced:
            result = self._enhanced.run_workflow(initial_input, max_steps)
            # Return only results for backward compatibility
            return result.get("results", [])
        else:
            # Original implementation
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


# Example agents for testing
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

def slow_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Agent that simulates slow execution (for testing stuck detection)"""
    print("Slow agent: Processing slowly...")
    time.sleep(6)  # Will trigger timeout if threshold is 5 seconds
    return {"slow_result": "completed_after_delay"}


if __name__ == "__main__":
    # Demonstration with stuck detection enabled
    print("🚀 Supervisor Agent with Stuck Detection Demo")
    print("=" * 50)
    
    # Create enhanced supervisor with stuck detection
    supervisor = SupervisorAgentWithStuckDetection(
        enable_stuck_detection=True,
        timeout_threshold=5,  # 5 seconds for demo
        progress_check_interval=1  # Check every second
    )
    
    # Register agents
    supervisor.register_agent("analyzer", analysis_agent)
    supervisor.register_agent("processor", processing_agent)
    supervisor.register_agent("validator", validation_agent)
    supervisor.register_agent("slow_agent", slow_agent)  # Will timeout
    
    # Run workflow
    initial_input = {
        "task": "process_sample_data",
        "data": {"sample": "test_data"}
    }
    
    print("🔄 Running workflow (includes slow agent that will timeout)...")
    result = supervisor.run_workflow(initial_input, max_steps=5)
    
    print("\n📊 Workflow Results:")
    print(f"Workflow ID: {result['workflow_id']}")
    print(f"Total steps: {result['total_steps']}")
    
    print("\n🔍 Agent Execution Results:")
    for i, agent_result in enumerate(result['results']):
        status_icon = "✅" if agent_result.get("status") == "success" else "❌"
        agent_name = agent_result.get("agent", "unknown")
        print(f"  {status_icon} Step {i+1}: {agent_name}")
    
    # Show stuck issues
    if "stuck_issues" in result:
        issues = result["stuck_issues"]
        print(f"\n🚨 Stuck Issues Detected: {issues['active_count']}")
        
        if issues['active_count'] > 0:
            print("Issue Summary:")
            for issue_type, count in issues['summary']['by_type'].items():
                print(f"  - {issue_type}: {count}")
    
    # Get current stuck issues
    current_issues = supervisor.get_stuck_issues()
    if current_issues and current_issues.get("total_issues", 0) > 0:
        print(f"\n📋 Detailed Issues:")
        for issue in current_issues['issues']:
            print(f"  - {issue['issue_type']} ({issue['severity']}): {issue['description']}")
    
    # Stop monitoring
    supervisor.stop_monitoring()
    
    print("\n✅ Demo completed!")