#!/usr/bin/env python3
"""
Integration of Stuck Issue Detection with LangGraph Supervisor

This script demonstrates how to integrate the stuck issue detection system
with the existing LangGraph-style supervisor.
"""

from typing import Dict, List, Any, Optional
from langgraph_supervisor import LangGraphSupervisorAgent
from stuck_issue_detector import StuckIssueDetector, StuckIssueRecovery


class LangGraphSupervisorWithStuckDetection(LangGraphSupervisorAgent):
    """Enhanced LangGraph Supervisor with stuck issue detection"""
    
    def __init__(self, 
                 enable_stuck_detection: bool = True,
                 timeout_threshold: int = 300,
                 progress_check_interval: int = 60):
        # Initialize the parent class
        super().__init__()
        
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
    
    def execute_node(self, node_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node/agent with stuck detection"""
        workflow_id = input_data.get("workflow_id", f"workflow_{node_name}")
        
        # Notify stuck detector that agent is starting
        if self.stuck_detector:
            self.stuck_detector.agent_started(node_name, workflow_id)
        
        try:
            # Call the parent method
            result = super().execute_node(node_name, input_data)
            
            # Notify stuck detector that agent made progress
            if self.stuck_detector:
                self.stuck_detector.agent_progress(node_name, workflow_id)
            
            return result
            
        except Exception as e:
            # Notify stuck detector of failure
            if self.stuck_detector:
                self.stuck_detector.agent_completed(node_name, workflow_id)
            raise
        
        finally:
            # Notify stuck detector that agent completed
            if self.stuck_detector:
                self.stuck_detector.agent_completed(node_name, workflow_id)
    
    def run_workflow(self, initial_input: Dict[str, Any], max_iterations: int = 20) -> Dict[str, Any]:
        """Run the workflow with stuck detection"""
        # Add workflow ID to input if not present
        workflow_id = initial_input.get("workflow_id", f"workflow_{self.graph.start_node}")
        workflow_input = initial_input.copy()
        workflow_input["workflow_id"] = workflow_id
        
        # Notify stuck detector that workflow is starting
        if self.stuck_detector:
            self.stuck_detector.workflow_started(workflow_id, workflow_input)
        
        try:
            # Call the parent method
            result = super().run_workflow(workflow_input, max_iterations)
            
            # Add stuck issue information to results
            if self.stuck_detector:
                active_issues = self.stuck_detector.get_active_issues()
                issues_summary = self.stuck_detector.get_issue_summary()
                
                result["stuck_issues"] = {
                    "active_count": len(active_issues),
                    "summary": issues_summary
                }
            
            return result
            
        finally:
            # Notify stuck detector that workflow completed
            if self.stuck_detector:
                self.stuck_detector.workflow_completed(workflow_id)
    
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


# Demo function
def demo_langgraph_with_stuck_detection():
    """Demonstrate LangGraph supervisor with stuck issue detection"""
    from langgraph_supervisor import (
        input_processing_agent, analysis_agent, decision_agent, 
        execution_agent, validation_agent, output_agent
    )
    
    print("🚀 LangGraph Supervisor with Stuck Detection Demo")
    print("=" * 55)
    
    # Create enhanced supervisor with stuck detection
    supervisor = LangGraphSupervisorWithStuckDetection(
        enable_stuck_detection=True,
        timeout_threshold=3,  # 3 seconds for demo
        progress_check_interval=1
    )
    
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
    
    print("🔄 Running workflow with stuck issue detection...")
    result = supervisor.run_workflow(initial_input)
    
    print("\n" + "="*55)
    print("📋 WORKFLOW EXECUTION SUMMARY")
    print("="*55)
    
    print(f"✅ Completed Nodes: {len(result['completed_nodes'])}")
    print(f"🔄 Total Iterations: {result['total_iterations']}")
    print(f"📊 Execution Log Entries: {len(result['execution_log'])}")
    
    # Show stuck issues
    if "stuck_issues" in result:
        issues = result["stuck_issues"]
        print(f"🚨 Stuck Issues Detected: {issues['active_count']}")
        
        if issues['active_count'] > 0:
            print("\n📋 Issue Summary:")
            for issue_type, count in issues['summary']['by_type'].items():
                print(f"  - {issue_type}: {count}")
    
    print("\n🔍 Execution Details:")
    for log_entry in result['execution_log']:
        status_icon = "✅" if log_entry['status'] == 'completed' else "❌"
        print(f"  {status_icon} Iteration {log_entry['iteration']}: {log_entry['node']} - {log_entry['status']}")
    
    # Stop monitoring
    supervisor.stop_monitoring()
    
    print("\n✅ Demo completed!")


if __name__ == "__main__":
    demo_langgraph_with_stuck_detection()